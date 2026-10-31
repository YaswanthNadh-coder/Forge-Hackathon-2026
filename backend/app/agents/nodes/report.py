"""
Report generation node — creates audit evidence PDF using ReportLab.
Generates official audit annexures formatted for submission with CGRMS grievances.
"""

import os
import logging
from pathlib import Path
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
    SEVERITY_COLORS = {
        "critical": colors.HexColor("#DC2626"),
        "high": colors.HexColor("#EA580C"),
        "medium": colors.HexColor("#CA8A04"),
        "low": colors.HexColor("#2563EB"),
    }
except ImportError:
    REPORTLAB_AVAILABLE = False
    SEVERITY_COLORS = {}

from app.config import settings
from app.agents.state import AuditState

logger = logging.getLogger(__name__)

VIOLATION_TYPE_LABELS = {
    "overbilling": "Overbilling",
    "double_billing": "Double Billing",
    "unbundling": "Unbundling (Consumables)",
    "rate_violation": "HBP Rate Violation",
    "package_inclusion": "Illegal Package Inclusion Charge",
    "bed_cap_exceeded": "Bed/ICU Daily Cap Exceeded",
}


async def generate_report(state: AuditState) -> dict:
    """Generate a comprehensive audit evidence PDF report."""
    audit_id = state.get("audit_id", "unknown")
    logger.info(f"Generating PDF report for audit {audit_id}")

    reports_dir = Path(settings.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = reports_dir / f"{audit_id}.pdf"

    if not REPORTLAB_AVAILABLE:
        logger.warning("ReportLab library not available; generating plain text audit evidence annexure.")
        summary_text = (
            f"AYUSHMAN-SHIELD AUDIT EVIDENCE ANNEXURE\n"
            f"Audit Session ID: {audit_id}\n"
            f"Hospital: {state.get('hospital_name', 'EHCP')}\n"
            f"State: {state.get('patient_state', 'N/A')}\n"
            f"Total Billed: INR {float(state.get('total_billed', 0)):,.2f}\n"
            f"Total Permissible (HBP 2022): INR {float(state.get('total_allowed', 0)):,.2f}\n"
            f"Illegal Out-of-Pocket Overbilling: INR {float(state.get('total_excess', 0)):,.2f}\n"
            f"Compliance Rating: {state.get('audit_score', 0)}/100\n"
            f"Violations Identified: {len(state.get('violations', []))}\n"
        )
        pdf_path.write_text(summary_text, encoding="utf-8")
        return {
            "pdf_report_path": str(pdf_path),
            "audit_summary_text": summary_text,
            "current_node": "completed",
            "status": "completed",
        }

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=10,
        spaceAfter=4,
    )
    normal_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    )

    elements = []

    # Header Banner
    elements.append(Paragraph("AYUSHMAN-SHIELD AUDIT EVIDENCE REPORT", title_style))
    elements.append(Paragraph(
        "Autonomous PM-JAY Hospital Bill Compliance Audit & Statutory Grievance Annexure<br/>"
        "Reference: National Health Authority (NHA) Health Benefit Package Master 2022",
        subtitle_style
    ))
    elements.append(Spacer(1, 4 * mm))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB")))
    elements.append(Spacer(1, 4 * mm))

    # Audit Details Metadata Table
    meta_data = [
        [
            Paragraph("<b>Audit ID:</b> " + str(audit_id)[:13].upper(), normal_style),
            Paragraph("<b>Generated:</b> " + datetime.utcnow().strftime("%d-%b-%Y %H:%M UTC"), normal_style)
        ],
        [
            Paragraph("<b>Hospital Name:</b> " + str(state.get("hospital_name", "N/A")), normal_style),
            Paragraph("<b>State/UT:</b> " + str(state.get("patient_state", "N/A")), normal_style)
        ],
        [
            Paragraph("<b>City/District:</b> " + f"{state.get('patient_city', '')} / {state.get('patient_district', '')}", normal_style),
            Paragraph("<b>Empanelment Status:</b> " + ("Verified Empanelled ✓" if state.get("hospital_verified") else "Under Investigation"), normal_style)
        ],
        [
            Paragraph("<b>Hospital Tier:</b> " + str(state.get("hospital_tier", "tier2")).upper(), normal_style),
            Paragraph("<b>PM-JAY Beneficiary Status:</b> " + str(state.get("pmjay_card_status", "active")).title(), normal_style)
        ],
    ]
    meta_table = Table(meta_data, colWidths=[270, 240])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 4 * mm))

    # Financial Summary Table
    elements.append(Paragraph("Financial Audit Summary", heading_style))
    total_billed = float(state.get("total_billed", 0))
    total_allowed = float(state.get("total_allowed", 0))
    total_excess = float(state.get("total_excess", max(0, total_billed - total_allowed)))
    audit_score = int(state.get("audit_score", 0))

    fin_data = [
        ["Audit Metric", "Assessment", "Statutory Rule"],
        ["Total Hospital Charges Billed", f"₹{total_billed:,.2f}", "Hospital itemized billing total"],
        ["Total Permissible under PM-JAY", f"₹{total_allowed:,.2f}", "NHA HBP 2022 Tier-Adjusted Rate"],
        ["Illegal Out-of-Pocket Overbilling", f"₹{total_excess:,.2f}", "Illegal under NHA Empanelment Sec 4.2"],
        ["Compliance Score", f"{audit_score} / 100", "Composite hospital regulatory rating"],
    ]
    fin_table = Table(fin_data, colWidths=[180, 140, 190])
    fin_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TEXTCOLOR", (0, 3), (-1, 3), colors.HexColor("#DC2626")),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 4 * mm))

    # Violations Summary
    violations = state.get("violations", [])
    elements.append(Paragraph(f"Statutory Violations Identified ({len(violations)})", heading_style))

    if violations:
        v_header = ["#", "Violation Type", "Billed Item / Description", "Billed", "Allowed", "Excess", "Severity"]
        v_rows = [v_header]

        for idx, v in enumerate(violations[:15], 1):
            v_rows.append([
                str(idx),
                VIOLATION_TYPE_LABELS.get(v.get("violation_type", ""), v.get("violation_type", "")),
                Paragraph(v.get("description", "")[:80], normal_style),
                f"₹{float(v.get('billed_amount', 0)):,.0f}",
                f"₹{float(v.get('allowed_amount', 0)):,.0f}",
                f"₹{float(v.get('excess_amount', 0)):,.0f}",
                v.get("severity", "MEDIUM").upper(),
            ])

        v_table = Table(v_rows, colWidths=[20, 95, 175, 55, 55, 55, 55])
        v_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("ALIGN", (3, 1), (5, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        for i, v in enumerate(violations[:15], 1):
            sev = v.get("severity", "medium").lower()
            color = SEVERITY_COLORS.get(sev, colors.HexColor("#CA8A04"))
            v_style.append(("TEXTCOLOR", (6, i), (6, i), color))
            v_style.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))

        v_table.setStyle(TableStyle(v_style))
        elements.append(v_table)
    else:
        elements.append(Paragraph(
            "<b>No statutory violations detected.</b> The charges billed conform to the NHA HBP 2022 cashless rate schedules.",
            normal_style
        ))

    elements.append(Spacer(1, 4 * mm))

    # Legal / CGRMS Grievance Submission Notice
    elements.append(Paragraph("Official CGRMS Grievance Endorsement", heading_style))
    notice_text = (
        "<b>LEGAL NOTICE UNDER SECTION 4.2 OF NHA GUIDELINES:</b><br/>"
        "Under the Ayushman Bharat PM-JAY Guidelines, empanelled healthcare providers (EHCPs) are legally barred "
        "from collecting out-of-pocket cash from beneficiaries for any bundled packages, consumables, bed charges, or medicines. "
        f"This document certifies an unauthorized extraction of <b>₹{total_excess:,.2f}</b> from the patient. "
        "This report is formatted as an admissible Annexure for submission to the National Grievance Redressal "
        "System at <i>https://cgrms.pmjay.gov.in</i>."
    )
    elements.append(Paragraph(notice_text, normal_style))
    elements.append(Spacer(1, 4 * mm))
    elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94A3B8")))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        "Generated by Ayushman-Shield Autonomous AI Auditor • Theme 1 Civic Pulse & Digital Governance • NHA PM-JAY Compliant",
        ParagraphStyle("FootNote", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#64748B"), alignment=TA_CENTER)
    ))

    # Build the document
    doc.build(elements)
    logger.info(f"Report PDF successfully written to {pdf_path}")

    summary_text = (
        f"Audit concluded for {state.get('hospital_name', 'hospital')}. "
        f"Total amount billed was ₹{total_billed:,.0f}, while PM-JAY permissible rate is ₹{total_allowed:,.0f}. "
        f"A total unauthorized overbilling of ₹{total_excess:,.0f} was detected across {len(violations)} line item violations."
    )

    return {
        "pdf_report_path": str(pdf_path),
        "audit_summary_text": summary_text,
        "current_node": "completed",
        "status": "completed",
    }

