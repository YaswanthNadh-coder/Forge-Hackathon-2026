"""
Hospital verification node.
Checks hospital empanelment status against live PM-JAY directories.
"""

import httpx
import logging
from app.agents.state import AuditState

logger = logging.getLogger(__name__)

PMJAY_HOSPITAL_SEARCH_URL = "https://hospitals.pmjay.gov.in"


async def verify_hospital(state: AuditState) -> dict:
    """
    Verify hospital empanelment status and determine tier.
    Queries PM-JAY hospital directory for verification.
    """
    hospital_name = state["hospital_name"]
    patient_state = state["patient_state"]

    logger.info(f"Verifying hospital: {hospital_name} in {patient_state}")

    hospital_verified = False
    hospital_tier = "unknown"
    empanelment_status = "unverified"

    try:
        # Attempt to query PM-JAY hospital directory
        async with httpx.AsyncClient(timeout=3.5, follow_redirects=True) as client:
            # Try the public hospital search API
            response = await client.get(
                f"{PMJAY_HOSPITAL_SEARCH_URL}/search",
                params={
                    "hospital_name": hospital_name,
                    "state": patient_state,
                },
                headers={"Accept": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("hospitals"):
                    hospital_data = data["hospitals"][0]
                    hospital_verified = True
                    hospital_tier = _determine_tier(hospital_data)
                    empanelment_status = hospital_data.get("status", "empanelled")
                    logger.info(f"Hospital verified: {hospital_name} - Tier: {hospital_tier}")
                else:
                    logger.warning(f"Hospital not found in PM-JAY directory: {hospital_name}")
            else:
                logger.warning(f"PM-JAY directory returned status {response.status_code}")

    except httpx.TimeoutException:
        logger.warning("PM-JAY hospital directory request timed out")
    except Exception as e:
        logger.warning(f"Hospital verification failed: {e}")

    # Fallback tier determination based on NABH and hospital name heuristics
    if hospital_tier == "unknown":
        hospital_tier = _infer_tier(hospital_name, state.get("hospital_nabh", ""))

    return {
        "hospital_verified": hospital_verified,
        "hospital_tier": hospital_tier,
        "hospital_empanelment_status": empanelment_status,
        "current_node": "audit",
        "status": "auditing",
    }


def _determine_tier(hospital_data: dict) -> str:
    """Determine hospital tier from PM-JAY data."""
    nabh = hospital_data.get("nabh_accredited", False)
    bed_count = hospital_data.get("bed_count", 0)
    specialty_count = hospital_data.get("specialties", 0)

    if nabh and bed_count >= 100:
        return "tier1"
    elif bed_count >= 50 or specialty_count >= 5:
        return "tier2"
    else:
        return "tier3"


def _infer_tier(hospital_name: str, nabh: str) -> str:
    """Infer hospital tier from name and NABH status when API is unavailable."""
    name_lower = hospital_name.lower()

    # Government medical colleges and AIIMS are typically tier 1
    if any(kw in name_lower for kw in ["aiims", "medical college", "pgimer", "jipmer", "nimhans"]):
        return "tier1"

    # Large private hospital chains
    if any(kw in name_lower for kw in ["apollo", "fortis", "max", "medanta", "manipal", "narayana"]):
        return "tier1" if nabh else "tier2"

    # District hospitals
    if any(kw in name_lower for kw in ["district hospital", "civil hospital", "general hospital"]):
        return "tier2"

    # Default based on NABH
    return "tier2" if nabh else "tier3"
