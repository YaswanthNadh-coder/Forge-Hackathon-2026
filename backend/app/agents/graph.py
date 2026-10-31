"""
LangGraph StateGraph orchestration for Ayushman-Shield.
Implements the multi-agent pipeline with Human-in-the-Loop (HITL) interrupt_before
for the official CGRMS grievance filing submission step.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AuditState, GrievanceState
from app.agents.nodes.extract import extract_bill
from app.agents.nodes.verify import verify_hospital
from app.agents.nodes.audit import audit_bill
from app.agents.nodes.report import generate_report
from app.agents.nodes.grievance import navigate_to_cgrms, fill_grievance_form, submit_with_otp

logger = logging.getLogger(__name__)

# Checkpointer for Human-In-The-Loop interrupts
memory = MemorySaver()


def build_audit_graph():
    """Build the end-to-end hospital bill audit StateGraph."""
    workflow = StateGraph(AuditState)

    workflow.add_node("extract", extract_bill)
    workflow.add_node("verify", verify_hospital)
    workflow.add_node("audit", audit_bill)
    workflow.add_node("report", generate_report)

    workflow.set_entry_point("extract")

    workflow.add_edge("extract", "verify")
    workflow.add_edge("verify", "audit")
    workflow.add_edge("audit", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


def build_grievance_graph():
    """Build the CGRMS grievance browser automation StateGraph with HITL interrupt."""
    workflow = StateGraph(GrievanceState)

    workflow.add_node("navigate", navigate_to_cgrms)
    workflow.add_node("fill_form", fill_grievance_form)
    workflow.add_node("submit_otp", submit_with_otp)

    workflow.set_entry_point("navigate")

    workflow.add_edge("navigate", "fill_form")
    workflow.add_edge("fill_form", "submit_otp")
    workflow.add_edge("submit_otp", END)

    # Interrupt execution right before submit_otp to require human OTP entry
    return workflow.compile(
        checkpointer=memory,
        interrupt_before=["submit_otp"],
    )


audit_graph = build_audit_graph()
grievance_graph = build_grievance_graph()


async def run_audit_pipeline(
    audit_id: str,
    file_path: str,
    file_type: str,
    patient_details,
    redacted_image: Optional[bytes],
    audit_store: dict,
):
    """
    Executes the autonomous bill audit pipeline and streams status updates.
    """
    from app.api.websocket import broadcast_audit_update

    logger.info(f"Starting audit pipeline execution for {audit_id}")

    initial_state: AuditState = {
        "audit_id": audit_id,
        "file_path": file_path,
        "file_type": file_type,
        "patient_city": patient_details.city,
        "patient_district": patient_details.district,
        "patient_state": patient_details.state,
        "hospital_name": patient_details.hospital_name,
        "pmjay_card_status": patient_details.pmjay_card_status,
        "admission_date": str(patient_details.admission_date) if patient_details.admission_date else None,
        "discharge_date": str(patient_details.discharge_date) if patient_details.discharge_date else None,
        "pmjay_id": patient_details.pmjay_id,
        "redacted_image": redacted_image,
        "extracted_text": "",
        "line_items": [],
        "total_billed": 0.0,
        "hospital_verified": False,
        "hospital_tier": "tier2",
        "hospital_nabh": "",
        "hospital_empanelment_status": "",
        "violations": [],
        "total_allowed": 0.0,
        "total_excess": 0.0,
        "audit_score": 0,
        "pdf_report_path": None,
        "audit_summary_text": "",
        "grievance_stage": "idle",
        "grievance_id": None,
        "otp_value": None,
        "browser_frame": None,
        "current_node": "extract",
        "error_message": None,
        "status": "processing",
    }

    try:
        accumulated_state = dict(initial_state)

        async for event in audit_graph.astream(initial_state):
            for node_name, node_output in event.items():
                logger.info(f"Audit step completed: {node_name}")
                accumulated_state.update(node_output)

                # Broadcast live progress
                await broadcast_audit_update(audit_id, {
                    "type": "node_complete",
                    "node": node_name,
                    "status": node_output.get("status", "processing"),
                    "current_node": node_output.get("current_node", node_name),
                    "total_billed": accumulated_state.get("total_billed", 0),
                    "total_excess": accumulated_state.get("total_excess", 0),
                })

        # Finalize and persist in audit_store
        if audit_id in audit_store:
            from app.models.bill import ExtractedBill, ExtractedLineItem
            from app.models.audit import AuditViolation as AuditViolationModel

            audit = audit_store[audit_id]
            audit.status = accumulated_state.get("status", "completed")
            audit.total_billed = Decimal(str(accumulated_state.get("total_billed", 0)))
            audit.total_allowed = Decimal(str(accumulated_state.get("total_allowed", 0)))
            audit.total_excess = Decimal(str(accumulated_state.get("total_excess", 0)))
            audit.audit_score = accumulated_state.get("audit_score", 0)
            audit.hospital_verified = accumulated_state.get("hospital_verified", False)
            audit.hospital_tier = accumulated_state.get("hospital_tier", "tier2")
            audit.patient_state = patient_details.state
            audit.patient_city = patient_details.city
            audit.pdf_report_url = f"/reports/{audit_id}.pdf" if accumulated_state.get("pdf_report_path") else None
            audit.error_message = accumulated_state.get("error_message")

            # Store structured violations
            raw_violations = accumulated_state.get("violations", [])
            audit.violations = [
                AuditViolationModel(
                    id=v.get("id", ""),
                    line_item_id=v.get("line_item_id", ""),
                    violation_type=v.get("violation_type", "overbilling"),
                    severity=v.get("severity", "medium"),
                    description=v.get("description", ""),
                    billed_amount=Decimal(str(v.get("billed_amount", 0))),
                    allowed_amount=Decimal(str(v.get("allowed_amount", 0))),
                    excess_amount=Decimal(str(v.get("excess_amount", 0))),
                    hbp_reference=v.get("hbp_reference", "HBP 2022"),
                    evidence=v.get("evidence", ""),
                )
                for v in raw_violations
            ]

            # Store extracted bill
            raw_items = accumulated_state.get("line_items", [])
            audit.bill = ExtractedBill(
                hospital_name=accumulated_state.get("hospital_name", patient_details.hospital_name),
                hospital_nabh=accumulated_state.get("hospital_nabh"),
                patient_name="[REDACTED_PMJAY_BENEFICIARY]",
                admission_date=patient_details.admission_date,
                discharge_date=patient_details.discharge_date,
                total_billed=audit.total_billed,
                line_items=[
                    ExtractedLineItem(
                        id=it.get("id", ""),
                        description=it.get("description", ""),
                        category=it.get("category", "other"),
                        quantity=it.get("quantity", 1),
                        unit_price=Decimal(str(it.get("unit_price", 0))),
                        total_price=Decimal(str(it.get("total_price", 0))),
                        hbp_package_code=it.get("hbp_package_code"),
                        hbp_package_name=it.get("hbp_package_name"),
                    )
                    for it in raw_items
                ],
                raw_text=accumulated_state.get("extracted_text", ""),
            )

            await broadcast_audit_update(audit_id, {
                "type": "audit_complete",
                "status": "completed",
                "audit_score": audit.audit_score,
                "total_billed": float(audit.total_billed),
                "total_allowed": float(audit.total_allowed),
                "total_excess": float(audit.total_excess),
                "violations_count": len(audit.violations),
                "pdf_report_url": audit.pdf_report_url,
            })

    except Exception as e:
        logger.error(f"Audit pipeline error: {e}", exc_info=True)
        if audit_id in audit_store:
            audit_store[audit_id].status = "error"
            audit_store[audit_id].error_message = str(e)

        await broadcast_audit_update(audit_id, {
            "type": "error",
            "message": str(e),
        })


async def run_grievance_pipeline(
    thread_id: str,
    audit_id: str,
    audit_result,
    sessions: dict,
):
    """
    Executes the CGRMS browser agent and pauses at the OTP gate.
    """
    from app.api.websocket import broadcast_browser_frame
    from app.models.grievance import GrievanceStatus

    logger.info(f"Starting grievance pipeline for thread {thread_id}")

    violations_summary = "\n".join([
        f"- {v.description}: Billed ₹{v.billed_amount}, Allowed ₹{v.allowed_amount} (Excess: ₹{v.excess_amount})"
        for v in audit_result.violations[:8]
    ])

    initial_state: GrievanceState = {
        "thread_id": thread_id,
        "audit_id": audit_id,
        "audit_summary": f"PM-JAY Audit: Overbilled ₹{audit_result.total_excess:,.2f}",
        "hospital_name": audit_result.bill.hospital_name if audit_result.bill else "Hospital",
        "patient_state": getattr(audit_result, "patient_state", None) or "Delhi",
        "total_excess": float(audit_result.total_excess),
        "violations_summary": violations_summary,
        "pdf_report_path": audit_result.pdf_report_url,
        "current_url": "",
        "current_step": "idle",
        "browser_frame": None,
        "otp_value": None,
        "grievance_id": None,
        "error_message": None,
        "status": "navigating",
    }

    config = {"configurable": {"thread_id": thread_id}}
    sessions[thread_id]["graph_config"] = config

    try:
        async for event in grievance_graph.astream(initial_state, config=config):
            for node_name, output in event.items():
                if node_name == "__interrupt__" or not isinstance(output, dict):
                    logger.info(f"LangGraph HITL interrupt triggered: {node_name}")
                    cur_frame = sessions[thread_id]["status"].browser_frame
                    sessions[thread_id]["status"] = GrievanceStatus(
                        stage="awaiting_otp",
                        message="CGRMS Portal reached statutory submission step. Awaiting OTP verification.",
                        browser_frame=cur_frame,
                    )
                    continue

                logger.info(f"Grievance node executed: {node_name}")
                sessions[thread_id]["status"] = GrievanceStatus(
                    stage=output.get("status", "navigating"),
                    message=f"Agent Step: {output.get('current_step', node_name)}",
                    browser_frame=output.get("browser_frame"),
                    grievance_id=output.get("grievance_id"),
                )

                if output.get("browser_frame"):
                    await broadcast_browser_frame(thread_id, {
                        "type": "browser_frame",
                        "frame": output["browser_frame"],
                        "step": output.get("current_step", ""),
                        "status": output.get("status", ""),
                        "grievance_id": output.get("grievance_id"),
                    })

        logger.info(f"Grievance pipeline paused at Human-in-the-Loop OTP gate for {thread_id}")

    except Exception as e:
        logger.error(f"Grievance pipeline error: {e}", exc_info=True)
        sessions[thread_id]["status"] = GrievanceStatus(
            stage="error",
            message=str(e),
        )


async def resume_with_otp(thread_id: str, otp: str, sessions: dict):
    """
    Resumes the LangGraph grievance pipeline with the verified user OTP.
    """
    from app.api.websocket import broadcast_browser_frame
    from app.models.grievance import GrievanceStatus

    config = sessions[thread_id].get("graph_config")
    if not config:
        raise ValueError(f"No active session config found for thread {thread_id}")

    logger.info(f"Resuming grievance pipeline with OTP for thread {thread_id}")

    try:
        # Update state with verified user OTP to resume the interrupted node
        await grievance_graph.aupdate_state(config, {"otp_value": otp})

        async for event in grievance_graph.astream(
            None,
            config=config,
        ):
            for node_name, output in event.items():
                if node_name == "__interrupt__" or not isinstance(output, dict):
                    continue
                logger.info(f"Grievance post-OTP node: {node_name}")
                sessions[thread_id]["status"] = GrievanceStatus(
                    stage=output.get("status", "completed"),
                    message=f"Status: {output.get('current_step', node_name)}",
                    browser_frame=output.get("browser_frame"),
                    grievance_id=output.get("grievance_id"),
                )

                if output.get("browser_frame"):
                    await broadcast_browser_frame(thread_id, {
                        "type": "browser_frame",
                        "frame": output["browser_frame"],
                        "step": output.get("current_step", ""),
                        "status": output.get("status", ""),
                        "grievance_id": output.get("grievance_id"),
                    })

    except Exception as e:
        logger.error(f"Post-OTP resume failed: {e}")
        sessions[thread_id]["status"] = GrievanceStatus(
            stage="error",
            message=str(e),
        )

