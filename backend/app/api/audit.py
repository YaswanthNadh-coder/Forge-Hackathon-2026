"""
Audit API endpoints for hospital bill ingestion, PII redaction, status querying,
report retrieval, and Sarvam AI vernacular voice generation.
"""

import uuid
import logging
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from io import BytesIO

from app.config import settings
from app.models.bill import PatientDetails, BillUploadResponse
from app.models.audit import AuditResult, VoiceRequest
from app.privacy.redactor import redactor
from app.voice.sarvam import sarvam_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

# In-memory store for audit results
audit_store: dict[str, AuditResult] = {}


@router.post("/upload", response_model=BillUploadResponse)
async def upload_bill(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    city: str = Form(...),
    district: str = Form(""),
    state: str = Form(...),
    hospital_name: str = Form(...),
    pmjay_card_status: str = Form("active"),
    admission_date: str = Form(""),
    discharge_date: str = Form(""),
    pmjay_id: str = Form(""),
):
    """
    Ingests a hospital bill (photo or PDF) alongside patient admission details.
    Strips sensitive identity and financial PII locally before cloud processing,
    then launches the autonomous LangGraph audit pipeline.
    """
    allowed_types = [
        "image/jpeg", "image/png", "image/webp", "image/tiff", "application/pdf"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file.content_type}'. Please upload JPEG, PNG, WebP, or PDF.",
        )

    contents = await file.read()
    if len(contents) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum permissible size of {settings.max_upload_size_mb} MB.",
        )

    audit_id = str(uuid.uuid4())
    upload_dir = Path(settings.upload_dir) / audit_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / (file.filename or "bill.pdf")
    file_path.write_bytes(contents)

    # Local PII redaction on patient metadata
    metadata_text = f"PMJAY_ID: {pmjay_id}, Patient from: {city}, {state}, Hospital: {hospital_name}"
    redacted_meta, pii_detections = redactor.redact_text(metadata_text)
    logger.info(f"Local PII scan sanitized {len(pii_detections)} sensitive tokens before pipeline ingestion")

    # Local OpenCV redaction on image if photo
    redacted_img_bytes = None
    if file.content_type and file.content_type.startswith("image/"):
        redacted_img_bytes = redactor.redact_image(contents)
        redacted_path = upload_dir / f"sanitized_{file.filename or 'bill.png'}"
        redacted_path.write_bytes(redacted_img_bytes)

    # Initial state record
    patient = PatientDetails(
        city=city,
        district=district,
        state=state,
        hospital_name=hospital_name,
        pmjay_card_status=pmjay_card_status if pmjay_card_status in ("active", "inactive", "pending") else "active",
        admission_date=None,
        discharge_date=None,
        pmjay_id=redacted_meta if pmjay_id else None,
    )

    audit_store[audit_id] = AuditResult(
        id=audit_id,
        status="processing",
        violations=[],
        total_billed=Decimal("0"),
        total_allowed=Decimal("0"),
        total_excess=Decimal("0"),
        hospital_verified=False,
        hospital_tier="tier2",
        audit_score=0,
        created_at=datetime.utcnow(),
    )

    # Launch pipeline via FastAPI BackgroundTasks
    from app.agents.graph import run_audit_pipeline

    background_tasks.add_task(
        run_audit_pipeline,
        audit_id=audit_id,
        file_path=str(file_path),
        file_type=file.content_type or "image/jpeg",
        patient_details=patient,
        redacted_image=redacted_img_bytes,
        audit_store=audit_store,
    )

    return BillUploadResponse(
        audit_id=audit_id,
        status="processing",
        message="Hospital bill ingested. PII redacted locally. Autonomous audit pipeline running.",
    )


@router.get("/{audit_id}", response_model=AuditResult)
async def get_audit_result(audit_id: str):
    """Retrieve audit status, extracted bill, compliance violations, and financial reconciliation."""
    if audit_id not in audit_store:
        raise HTTPException(status_code=404, detail="Audit session not found.")
    return audit_store[audit_id]


@router.get("/{audit_id}/report")
async def download_report(audit_id: str):
    """Download official Audit Evidence PDF Annexure for CGRMS submission."""
    if audit_id not in audit_store:
        raise HTTPException(status_code=404, detail="Audit session not found.")

    report_path = Path(settings.reports_dir) / f"{audit_id}.pdf"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Audit evidence PDF not ready yet.")

    return FileResponse(
        path=str(report_path),
        filename=f"ayushman_shield_audit_{audit_id[:8].upper()}.pdf",
        media_type="application/pdf",
    )


@router.get("/{audit_id}/voice")
@router.post("/{audit_id}/voice")
async def get_voice_explanation(audit_id: str, lang: str = "hi"):
    """
    Generate or retrieve a vernacular audio explanation of the audit findings
    powered by Sarvam AI (bulbul:v1 TTS & mayura:v1 translation).
    """
    if audit_id not in audit_store:
        raise HTTPException(status_code=404, detail="Audit session not found.")

    audit = audit_store[audit_id]
    if audit.status != "completed":
        raise HTTPException(status_code=400, detail="Audit must be complete before generating audio.")

    voice_path = Path(settings.voice_dir) / f"{audit_id}_{lang}.wav"
    if voice_path.exists():
        return FileResponse(
            path=str(voice_path),
            filename=f"audit_explanation_{lang}.wav",
            media_type="audio/wav",
        )

    summary_text = _build_voice_summary(audit)
    translated_text, audio_bytes = await sarvam_client.generate_audit_explanation(summary_text, language=lang)

    if not audio_bytes:
        raise HTTPException(status_code=503, detail="Sarvam AI speech synthesis service unavailable.")

    voice_path.parent.mkdir(parents=True, exist_ok=True)
    voice_path.write_bytes(audio_bytes)

    return StreamingResponse(
        BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={"Content-Disposition": f'attachment; filename="audit_summary_{lang}.wav"'},
    )


def _build_voice_summary(audit: AuditResult) -> str:
    """Build a natural conversational audit summary for vernacular speech synthesis."""
    hosp = audit.bill.hospital_name if audit.bill else "the hospital"
    lines = [
        f"Ayushman Shield Audit Report for {hosp}.",
        f"Your hospital bill had total charges of ₹{audit.total_billed:,.0f}.",
        f"According to the official PM-JAY package guidelines, the permissible amount is ₹{audit.total_allowed:,.0f}.",
        f"We found an illegal out-of-pocket overbilling of ₹{audit.total_excess:,.0f}.",
    ]
    if audit.violations:
        lines.append(f"A total of {len(audit.violations)} statutory bundling violations were detected.")
        top_v = audit.violations[0]
        lines.append(
            f"The primary overcharge was {top_v.description}, billed at ₹{top_v.billed_amount:,.0f} "
            f"against allowed ₹{top_v.allowed_amount:,.0f}."
        )
    lines.append(
        "You have the statutory right under PM-JAY to full reimbursement. "
        "You can now submit an official grievance to CGRMS through our portal."
    )
    return " ".join(lines)

