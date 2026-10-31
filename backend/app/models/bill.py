"""Pydantic v2 models for hospital bill data and upload responses."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


__all__ = [
    "PatientDetails",
    "ExtractedLineItem",
    "ExtractedBill",
    "BillUploadResponse",
]


class PatientDetails(BaseModel):
    """Patient and hospital metadata submitted with the bill upload."""

    city: str
    district: str = ""
    state: str
    hospital_name: str
    pmjay_card_status: Literal["active", "inactive", "pending"]
    admission_date: Optional[date] = None
    discharge_date: Optional[date] = None
    pmjay_id: Optional[str] = None


class ExtractedLineItem(BaseModel):
    """A single line item extracted from the hospital bill."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    category: Literal[
        "procedure",
        "consumable",
        "implant",
        "bed_charge",
        "diagnostic",
        "medicine",
        "other",
    ]
    quantity: int = 1
    unit_price: Decimal
    total_price: Decimal
    hbp_package_code: Optional[str] = None
    hbp_package_name: Optional[str] = None


class ExtractedBill(BaseModel):
    """Structured representation of a hospital bill after Gemini extraction."""

    hospital_name: str
    hospital_nabh: Optional[str] = None
    patient_name: str
    admission_date: Optional[date] = None
    discharge_date: Optional[date] = None
    total_billed: Decimal
    line_items: list[ExtractedLineItem] = []
    raw_text: str


class BillUploadResponse(BaseModel):
    """Response returned immediately after bill upload."""

    audit_id: str
    status: str
    message: str
