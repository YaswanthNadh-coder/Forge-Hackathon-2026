"""
Grievance filing API endpoints for CGRMS browser automation.
Orchestrates live browser automation against https://cgrms.pmjay.gov.in
with Human-in-the-Loop (HITL) OTP verification.
"""

import uuid
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.models.grievance import (
    GrievanceRequest,
    GrievanceOtpSubmit,
    GrievanceResponse,
    GrievanceStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/grievance", tags=["grievance"])

# Active grievance sessions state
grievance_sessions: dict[str, dict] = {}


@router.post("/start", response_model=GrievanceResponse)
async def start_grievance(request: GrievanceRequest, background_tasks: BackgroundTasks):
    """
    Initiate an automated grievance lodging session on the live CGRMS portal.
    Launches Playwright agent and streams browser viewport frames over WebSocket.
    """
    from app.api.audit import audit_store

    if request.audit_id not in audit_store:
        raise HTTPException(status_code=404, detail="Audit session not found.")

    audit = audit_store[request.audit_id]
    if audit.status != "completed":
        raise HTTPException(status_code=400, detail="Audit must be completed before filing grievance.")

    thread_id = str(uuid.uuid4())

    grievance_sessions[thread_id] = {
        "audit_id": request.audit_id,
        "status": GrievanceStatus(
            stage="navigating",
            message="Initializing Playwright browser agent for CGRMS portal...",
        ),
        "graph_config": None,
    }

    from app.agents.graph import run_grievance_pipeline

    background_tasks.add_task(
        run_grievance_pipeline,
        thread_id=thread_id,
        audit_id=request.audit_id,
        audit_result=audit,
        sessions=grievance_sessions,
    )

    return GrievanceResponse(
        thread_id=thread_id,
        status=grievance_sessions[thread_id]["status"],
    )


@router.post("/otp")
async def submit_otp(request: GrievanceOtpSubmit):
    """
    Submit OTP for the Human-in-the-Loop (HITL) gate.
    Resumes LangGraph execution paused at interrupt_before=["submit_otp"].
    """
    if request.thread_id not in grievance_sessions:
        raise HTTPException(status_code=404, detail="Grievance session not found.")

    session = grievance_sessions[request.thread_id]
    current_stage = session["status"].stage

    if current_stage not in ("awaiting_otp", "navigating", "filling_form"):
        raise HTTPException(
            status_code=400,
            detail=f"Session is not awaiting OTP. Current stage: {current_stage}",
        )

    from app.agents.graph import resume_with_otp

    await resume_with_otp(request.thread_id, request.otp, grievance_sessions)

    return {
        "status": "otp_submitted",
        "message": "OTP verified by human agent. Grievance lodging resumed.",
    }


@router.get("/{thread_id}", response_model=GrievanceResponse)
async def get_grievance_status(thread_id: str):
    """Retrieve real-time status and latest browser frame for a grievance session."""
    if thread_id not in grievance_sessions:
        raise HTTPException(status_code=404, detail="Grievance session not found.")

    return GrievanceResponse(
        thread_id=thread_id,
        status=grievance_sessions[thread_id]["status"],
    )

