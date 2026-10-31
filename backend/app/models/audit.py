"""Pydantic v2 models for audit results and violations."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .bill import ExtractedBill


__all__ = [
    "AuditViolation",
    "AuditResult",
    "VoiceRequest",
]


class AuditViolation(BaseModel):
    """A single violation detected during the audit."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    line_item_id: str
    violation_type: Literal[
        "overbilling",
        "double_billing",
        "unbundling",
        "rate_violation",
        "package_inclusion",
        "bed_cap_exceeded",
    ]
    severity: Literal["critical", "high", "medium", "low"]
    description: str
    billed_amount: Decimal
    allowed_amount: Decimal
    excess_amount: Decimal
    hbp_reference: str
    evidence: str


class AuditResult(BaseModel):
    """Full audit result with status tracking, bill, violations, and scores."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal[
        "processing",
        "extracting",
        "verifying",
        "auditing",
        "generating_report",
        "completed",
        "error",
    ]
    bill: Optional[ExtractedBill] = None
    violations: list[AuditViolation] = []
    total_billed: Decimal = Decimal("0")
    total_allowed: Decimal = Decimal("0")
    total_excess: Decimal = Decimal("0")
    hospital_verified: bool = False
    hospital_tier: str = "unknown"
    patient_state: Optional[str] = None
    patient_city: Optional[str] = None
    audit_score: int = Field(default=0, ge=0, le=100)
    pdf_report_url: Optional[str] = None
    voice_explanation_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


class VoiceRequest(BaseModel):
    """Request to generate a vernacular voice explanation of audit results."""

    audit_id: str
    language: str = "hi"
