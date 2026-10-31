"""LangGraph state definitions for the Ayushman-Shield audit pipeline."""

from typing import TypedDict, Annotated, Optional, Literal
from decimal import Decimal
from datetime import datetime
import operator


class BillLineItem(TypedDict):
    id: str
    description: str
    category: str
    quantity: int
    unit_price: float
    total_price: float
    hbp_package_code: Optional[str]
    hbp_package_name: Optional[str]


class AuditViolation(TypedDict):
    id: str
    line_item_id: str
    violation_type: str  # overbilling, double_billing, unbundling, rate_violation, package_inclusion, bed_cap_exceeded
    severity: str  # critical, high, medium, low
    description: str
    billed_amount: float
    allowed_amount: float
    excess_amount: float
    hbp_reference: str
    evidence: str


class AuditState(TypedDict):
    """Complete state flowing through the LangGraph audit pipeline."""
    # Input
    audit_id: str
    file_path: str
    file_type: str
    patient_city: str
    patient_district: str
    patient_state: str
    hospital_name: str
    pmjay_card_status: str
    admission_date: Optional[str]
    discharge_date: Optional[str]
    pmjay_id: Optional[str]
    redacted_image: Optional[bytes]

    # Extraction outputs
    extracted_text: str
    line_items: list[BillLineItem]
    total_billed: float

    # Verification outputs
    hospital_verified: bool
    hospital_tier: str  # "tier1", "tier2", "tier3"
    hospital_nabh: str
    hospital_empanelment_status: str

    # Audit outputs
    violations: Annotated[list[AuditViolation], operator.add]
    total_allowed: float
    total_excess: float
    audit_score: int

    # Report outputs
    pdf_report_path: Optional[str]
    audit_summary_text: str

    # Grievance outputs
    grievance_stage: str
    grievance_id: Optional[str]
    otp_value: Optional[str]
    browser_frame: Optional[str]

    # Pipeline metadata
    current_node: str
    error_message: Optional[str]
    status: str


class GrievanceState(TypedDict):
    """State for the CGRMS grievance filing sub-pipeline."""
    thread_id: str
    audit_id: str
    audit_summary: str
    hospital_name: str
    patient_state: str
    total_excess: float
    violations_summary: str
    pdf_report_path: Optional[str]

    # Browser state
    current_url: str
    current_step: str
    browser_frame: Optional[str]

    # HITL
    otp_value: Optional[str]
    grievance_id: Optional[str]
    error_message: Optional[str]
    status: str
