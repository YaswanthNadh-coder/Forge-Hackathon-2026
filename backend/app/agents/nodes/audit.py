"""
RAG Audit node — cross-audits extracted line items against HBP 2022 packages.
Uses Qdrant hybrid search to find matching packages and detect violations.
Includes a statutory rule-based compliance engine for resilient fallback.
"""

import re
import json
import uuid
import asyncio
import logging
from typing import Dict, Any, List, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.config import settings
from app.agents.state import AuditState, AuditViolation
from app.rag.retriever import hybrid_retrieve, _load_local_hbp_cache

logger = logging.getLogger(__name__)


def get_gemini_client() -> Optional[Any]:
    """Lazily initialize Gemini Client with verified API key."""
    if not settings.has_gemini_key or not genai:
        return None
    return genai.Client(api_key=settings.gemini_api_key)


AUDIT_PROMPT = """You are an expert PM-JAY (Ayushman Bharat) medical billing auditor with deep knowledge of the NHA Health Benefit Package (HBP) 2022 Master.

## Context: HBP 2022 Reference Data
The following are the relevant HBP 2022 packages and rates retrieved from the official NHA database:

{hbp_context}

## Hospital Details
- Hospital Name: {hospital_name}
- Hospital Tier: {hospital_tier} (tier1=highest rates, tier3=lowest)
- State: {state}

## PM-JAY Cashless Bundling Rules
Under PM-JAY, the following are ALWAYS INCLUDED in the package rate and CANNOT be billed separately:
1. Registration/admission charges
2. Bed charges (General Ward) for the approved duration
3. Nursing and boarding charges
4. Surgeon, anesthesiologist, medical practitioner fees
5. Anesthesia, blood transfusion, OT charges
6. Medicines and consumables required during hospitalization
7. Food for the patient
8. Pre-hospitalization diagnostics (up to 3 days before)
9. Post-hospitalization medication (up to 15 days after)
10. Standard diagnostics related to the procedure

Items that CAN be billed additionally (with limits):
- Implants (up to the notified implant ceiling for the package)
- ICU charges beyond package-included ICU days (at notified daily cap)
- Extended stay beyond approved duration (at daily cap)

## Billed Line Items to Audit
{line_items_json}

## Your Task
For EACH line item, determine:
1. Is this item included in the applicable HBP package (i.e., should NOT be billed separately)?
2. Does the billed rate exceed the HBP 2022 tier-adjusted package rate?
3. Is this item duplicated/double-billed?
4. For implants: does the price exceed the NHA implant ceiling?
5. For bed/ICU charges: does the daily rate exceed the notified cap?

Return a JSON object:
{{
  "violations": [
    {{
      "line_item_id": "id of the violating line item",
      "violation_type": "overbilling|double_billing|unbundling|rate_violation|package_inclusion|bed_cap_exceeded",
      "severity": "critical|high|medium|low",
      "description": "Clear explanation of the violation",
      "billed_amount": number,
      "allowed_amount": number,
      "excess_amount": number,
      "hbp_reference": "HBP package code and name reference",
      "evidence": "Specific HBP 2022 rule or rate being violated"
    }}
  ],
  "total_allowed": number,
  "audit_score": number
}}
"""


async def audit_bill(state: AuditState) -> dict:
    """
    Cross-audit extracted bill items against HBP 2022 using RAG and statutory bundling rules.
    """
    logger.info(f"Starting RAG audit for {state['audit_id']}")

    line_items = state.get("line_items", [])
    if not line_items:
        return {
            "violations": [],
            "total_allowed": 0.0,
            "total_excess": 0.0,
            "audit_score": 100,
            "current_node": "report",
            "status": "generating_report",
            "error_message": "No line items to audit",
        }

    # Query HBP 2022 database via hybrid retrieval
    search_queries = []
    for item in line_items:
        search_queries.append(item.get("description", ""))
        if item.get("category") == "procedure":
            search_queries.append(f"{item.get('description')} rate")

    hbp_context_parts = []
    seen_chunks = set()

    for query in search_queries[:12]:
        try:
            results = await hybrid_retrieve(query, top_k=3)
            for r in results:
                chunk_id = r.get("id", r.get("text", "")[:40])
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    hbp_context_parts.append(r.get("text", ""))
        except Exception as e:
            logger.warning(f"Retrieval note for query '{query}': {e}")

    hbp_context = "\n\n---\n\n".join(hbp_context_parts) if hbp_context_parts else (
        "NHA HBP 2022 Cashless Mandate: Registration, bed charges, routine consumables, and pre-op diagnostics are 100% bundled."
    )

    audit_result = None

    # Call Gemini if API key is provided
    if settings.has_gemini_key:
        try:
            prompt = AUDIT_PROMPT.format(
                hbp_context=hbp_context,
                hospital_name=state.get("hospital_name", "Unknown"),
                hospital_tier=state.get("hospital_tier", "tier2"),
                state=state.get("patient_state", "Unknown"),
                line_items_json=json.dumps(line_items, indent=2),
            )

            client = get_gemini_client()
            if client:
                candidate_models = [settings.gemini_model, "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
                for mod in candidate_models:
                    try:
                        response = await asyncio.to_thread(
                            client.models.generate_content,
                            model=mod,
                            contents=[prompt],
                            config=types.GenerateContentConfig(
                                temperature=0.1,
                                max_output_tokens=8192,
                                response_mime_type="application/json",
                            ),
                        )
                        result_text = (response.text or "").strip()
                        if "```json" in result_text:
                            result_text = result_text.split("```json")[1].split("```")[0].strip()
                        elif "```" in result_text:
                            result_text = result_text.split("```")[1].split("```")[0].strip()

                        audit_result = json.loads(result_text)
                        logger.info(f"Successfully audited bill line items using Gemini ({mod})")
                        break
                    except Exception as model_err:
                        logger.warning(f"Gemini model {mod} audit attempt: {model_err}")
        except Exception as e:
            logger.warning(f"Gemini audit call returned error: {e}. Executing statutory rule-based evaluator.")

    # Fallback to statutory rule-based compliance evaluator
    if not audit_result or not isinstance(audit_result, dict):
        audit_result = _fallback_rule_based_audit(line_items, hbp_context_parts, state)

    # Process violations
    violations = []
    for v in audit_result.get("violations", []):
        violations.append({
            "id": str(uuid.uuid4()),
            "line_item_id": str(v.get("line_item_id", "")),
            "violation_type": v.get("violation_type", "overbilling"),
            "severity": v.get("severity", "medium"),
            "description": v.get("description", "Billing violation"),
            "billed_amount": float(v.get("billed_amount", 0)),
            "allowed_amount": float(v.get("allowed_amount", 0)),
            "excess_amount": float(v.get("excess_amount", 0)),
            "hbp_reference": v.get("hbp_reference", "NHA HBP 2022"),
            "evidence": v.get("evidence", "PM-JAY cashless bundling rules violation"),
        })

    total_billed = float(state.get("total_billed", 0))
    total_allowed = float(audit_result.get("total_allowed", max(0, total_billed - sum(v["excess_amount"] for v in violations))))
    total_excess = max(0.0, total_billed - total_allowed)
    audit_score = int(audit_result.get("audit_score", max(0, min(100, int((total_allowed / max(1, total_billed)) * 100)))))

    return {
        "violations": violations,
        "total_allowed": total_allowed,
        "total_excess": total_excess,
        "audit_score": audit_score,
        "current_node": "report",
        "status": "generating_report",
    }


def _fallback_rule_based_audit(line_items: List[dict], hbp_context_parts: List[str], state: AuditState) -> Dict[str, Any]:
    """
    Statutory rule-based compliance evaluator strictly implementing NHA HBP 2022 bundling mandates
    dynamically cross-referencing the official NHA HBP 2022 master package registry.
    """
    violations = []
    tier = state.get("hospital_tier", "tier2").lower()
    tier_key = f"rate_{tier}" if f"rate_{tier}" in ["rate_tier1", "rate_tier2", "rate_tier3"] else "rate_tier2"

    packages = _load_local_hbp_cache()

    for item in line_items:
        desc = item.get("description", "").lower()
        cat = item.get("category", "")
        billed = float(item.get("total_price", 0))

        # Check for procedure match against official HBP packages
        if (cat == "procedure" or any(w in desc for w in ["replacement", "surgery", "resection", "angioplasty", "cabg", "appendectomy", "cholecystectomy", "mastectomy", "craniotomy", "herniotomy", "fess"])) and not any(non_proc in desc for non_proc in ["bed", "ward", "room", "registration", "admission", "glove", "syringe", "drape", "gauze"]):
            for pkg in packages:
                proc_name = pkg.get("procedure_name", "").lower()
                code = pkg.get("package_code", "")

                # Check if procedure name or key tokens match
                tokens = [t for t in re.findall(r"\w+", proc_name) if len(t) > 3 and t not in ["with", "without", "single", "open", "care", "unit", "ward", "general"]]
                match_count = sum(1 for t in tokens if t in desc)

                if match_count >= 2 or (tokens and tokens[0] in desc and cat == "procedure"):
                    allowed = float(pkg.get(tier_key, pkg.get("rate_tier2", 0)))
                    if allowed > 0 and billed > allowed:
                        violations.append({
                            "line_item_id": item.get("id"),
                            "violation_type": "rate_violation",
                            "severity": "critical",
                            "description": f"Package rate exceeds NHA HBP 2022 notified tariff for {pkg.get('procedure_name')}",
                            "billed_amount": billed,
                            "allowed_amount": allowed,
                            "excess_amount": billed - allowed,
                            "hbp_reference": f"{code} ({tier.upper()})",
                            "evidence": f"Official NHA HBP 2022 ceiling for {pkg.get('procedure_name')} in {tier.upper()} is ₹{allowed:,.0f}. Billed rate of ₹{billed:,.0f} constitutes an unauthorized rate violation under Section 4.2."
                        })
                    break

        # Check for implant ceiling
        if cat == "implant" or any(w in desc for w in ["implant", "prosthesis", "stent", "mesh"]):
            for pkg in packages:
                implant_ceiling = float(pkg.get("implant_ceiling_inr", 0))
                if implant_ceiling > 0:
                    pkg_tokens = [t for t in re.findall(r"\w+", pkg.get("procedure_name", "").lower()) if len(t) > 3 and t not in ["with", "without", "single", "open", "care", "unit", "ward", "general"]]
                    if any(t in desc for t in pkg_tokens):
                        if billed > implant_ceiling:
                            violations.append({
                                "line_item_id": item.get("id"),
                                "violation_type": "rate_violation",
                                "severity": "high",
                                "description": f"Implant charges exceed NPPA/NHA notified ceiling for {pkg.get('procedure_name')}",
                                "billed_amount": billed,
                                "allowed_amount": implant_ceiling,
                                "excess_amount": billed - implant_ceiling,
                                "hbp_reference": f"{pkg.get('package_code')} Implant Ceiling",
                                "evidence": f"Under NPPA price notification and NHA HBP 2022 rules, maximum permissible reimbursement for this implant category is ₹{implant_ceiling:,.0f}. Margin markup of ₹{billed - implant_ceiling:,.0f} is prohibited."
                            })
                        break

        # Check for bundled items (Registration, bed, consumables, diagnostics)
        if any(w in desc for w in ["admission", "registration", "file charge"]):
            violations.append({
                "line_item_id": item.get("id"),
                "violation_type": "package_inclusion",
                "severity": "high",
                "description": "Admission / Registration charges billed separately",
                "billed_amount": billed,
                "allowed_amount": 0,
                "excess_amount": billed,
                "hbp_reference": "HBP 2022 General Bundling Rule 1",
                "evidence": "Hospital registration and admission documentation fees are 100% bundled into every PM-JAY package and cannot be billed out-of-pocket."
            })
        elif cat == "consumable" or any(w in desc for w in ["glove", "syringe", "drape", "consumable", "disposable"]):
            violations.append({
                "line_item_id": item.get("id"),
                "violation_type": "unbundling",
                "severity": "critical",
                "description": "Routine surgical consumables unbundled and billed to patient",
                "billed_amount": billed,
                "allowed_amount": 0,
                "excess_amount": billed,
                "hbp_reference": "NHA Section 4.2 Cashless Bundling",
                "evidence": "Under Section 4.2 of the NHA Empanelment Agreement, surgical gloves, syringes, drapes and disposables are strictly bundled inside package rates."
            })
        elif cat == "bed_charge" or any(w in desc for w in ["ward bed", "bed charge", "room charge"]):
            violations.append({
                "line_item_id": item.get("id"),
                "violation_type": "package_inclusion",
                "severity": "high",
                "description": "General Ward bed charges billed during package covered stay",
                "billed_amount": billed,
                "allowed_amount": 0,
                "excess_amount": billed,
                "hbp_reference": "HBP 2022 Package Stay Inclusions",
                "evidence": "PM-JAY surgical packages include full General Ward bed stay for the approved procedure duration. Charging separate bed rent violates cashless guidelines."
            })
        elif cat == "diagnostic" or any(w in desc for w in ["pre-operative", "pre op blood", "profile", "x-ray", "routine ecg"]):
            violations.append({
                "line_item_id": item.get("id"),
                "violation_type": "double_billing",
                "severity": "medium",
                "description": "Standard pre-operative diagnostics billed additionally",
                "billed_amount": billed,
                "allowed_amount": 0,
                "excess_amount": billed,
                "hbp_reference": "HBP 2022 Diagnostic Bundling",
                "evidence": "Routine pre-op diagnostics conducted up to 3 days prior to hospitalization are bundled into the primary procedure rate."
            })

    total_billed = sum(float(it.get("total_price", 0)) for it in line_items)
    total_excess = sum(v["excess_amount"] for v in violations)
    total_allowed = max(0.0, total_billed - total_excess)
    score = max(0, min(100, int((total_allowed / max(1.0, total_billed)) * 100)))

    return {
        "violations": violations,
        "total_allowed": total_allowed,
        "audit_score": score,
    }
