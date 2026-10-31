"""Pydantic v2 models for CGRMS grievance filing."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


__all__ = [
    "GrievanceRequest",
    "GrievanceOtpSubmit",
    "GrievanceStatus",
    "GrievanceResponse",
]


class GrievanceRequest(BaseModel):
    """Request to start a grievance filing session."""

    audit_id: str


class GrievanceOtpSubmit(BaseModel):
    """Submit OTP for the HITL gate during CGRMS filing."""

    thread_id: str
    otp: str


class GrievanceStatus(BaseModel):
    """Current status of a grievance filing session."""

    stage: Literal[
        "idle",
        "navigating",
        "filling_form",
        "awaiting_otp",
        "otp_submitted",
        "completed",
        "error",
    ]
    message: str
    screenshot_url: Optional[str] = None
    grievance_id: Optional[str] = None
    browser_frame: Optional[str] = None


class GrievanceResponse(BaseModel):
    """Response for grievance filing operations."""

    thread_id: str
    status: GrievanceStatus
