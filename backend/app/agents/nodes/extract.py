"""
Bill extraction node using Google Gemini 2.5 Pro with structured outputs.
Extracts line items, procedures, consumables, implants, and ward charges
from hospital bill images/PDFs.
Includes resilient fallback parsing if Gemini API key is not yet configured.
"""

import re
import json
import uuid
import base64
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.config import settings
from app.agents.state import AuditState

logger = logging.getLogger(__name__)


def get_gemini_client() -> Optional[Any]:
    """Lazily initialize Gemini Client with verified API key."""
    if not settings.has_gemini_key or not genai:
        return None
    return genai.Client(api_key=settings.gemini_api_key)


EXTRACTION_PROMPT = """You are an expert medical billing analyst specializing in Indian hospital bills under the PM-JAY (Pradhan Mantri Jan Arogya Yojana) / Ayushman Bharat scheme.

Analyze this hospital bill image/document and extract ALL line items with extreme precision.

For each line item, identify:
1. **description**: The exact procedure, consumable, implant, medicine, or charge described
2. **category**: Classify as one of: "procedure", "consumable", "implant", "bed_charge", "diagnostic", "medicine", "other"
3. **quantity**: Number of units/days
4. **unit_price**: Price per unit in INR
5. **total_price**: Total charge for this line in INR

Also extract:
- Hospital name and NABH accreditation number (if visible)
- Patient name (will be redacted later)
- Admission and discharge dates
- Total billed amount

Be thorough — do NOT miss any line item. Include registration fees, bed charges (per day), nursing charges, OT charges, surgeon fees, anesthesia fees, medicines, consumables, implants, diagnostic tests (blood tests, X-rays, MRIs, CT scans, etc.), physiotherapy, ambulance charges, etc.

Return your response as a valid JSON object with this exact structure:
{
  "hospital_name": "string",
  "hospital_nabh": "string or empty",
  "patient_name": "string",
  "admission_date": "YYYY-MM-DD or empty",
  "discharge_date": "YYYY-MM-DD or empty",
  "total_billed": number,
  "line_items": [
    {
      "description": "string",
      "category": "procedure|consumable|implant|bed_charge|diagnostic|medicine|other",
      "quantity": number,
      "unit_price": number,
      "total_price": number
    }
  ],
  "raw_text": "full text content of the bill"
}
"""


async def extract_bill(state: AuditState) -> dict:
    """
    Extract itemized charges from the hospital bill using Gemini Vision.
    """
    logger.info(f"Extracting bill for audit {state['audit_id']}")

    file_path = Path(state["file_path"])
    file_type = state["file_type"]

    extracted = None

    # Call Gemini if API key is configured
    if settings.has_gemini_key:
        try:
            client = get_gemini_client()
            if client:
                contents = [EXTRACTION_PROMPT]

                if file_type.startswith("image/"):
                    image_data = state.get("redacted_image") or file_path.read_bytes()
                    mime_map = {
                        "image/jpeg": "image/jpeg",
                        "image/png": "image/png",
                        "image/webp": "image/webp",
                        "image/tiff": "image/tiff",
                    }
                    mime = mime_map.get(file_type, "image/jpeg")
                    contents.append(types.Part.from_bytes(data=image_data, mime_type=mime))
                elif file_type == "application/pdf":
                    pdf_data = file_path.read_bytes()
                    contents.append(types.Part.from_bytes(data=pdf_data, mime_type="application/pdf"))

                candidate_models = [settings.gemini_model, "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
                for mod in candidate_models:
                    try:
                        response = await asyncio.to_thread(
                            client.models.generate_content,
                            model=mod,
                            contents=contents,
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

                        extracted = json.loads(result_text)
                        logger.info(f"Successfully extracted bill line items using Gemini Vision ({mod})")
                        break
                    except Exception as model_err:
                        logger.warning(f"Gemini model {mod} extraction attempt: {model_err}")
        except Exception as e:
            logger.warning(f"Gemini extraction call returned error: {e}. Executing text fallback parser.")

    # Fallback parser if Gemini is offline or not configured
    if not extracted:
        extracted = _fallback_parse_document(file_path, file_type, state)

    line_items = []
    for item in extracted.get("line_items", []):
        unit_p = float(item.get("unit_price", 0))
        qty = int(item.get("quantity", 1))
        tot_p = float(item.get("total_price", unit_p * qty))

        line_items.append({
            "id": str(uuid.uuid4()),
            "description": str(item.get("description", "Medical Item")),
            "category": item.get("category", "other"),
            "quantity": qty,
            "unit_price": unit_p,
            "total_price": tot_p,
            "hbp_package_code": None,
            "hbp_package_name": None,
        })

    total_billed = float(extracted.get("total_billed", sum(it["total_price"] for it in line_items)))

    return {
        "extracted_text": extracted.get("raw_text", ""),
        "line_items": line_items,
        "total_billed": total_billed,
        "hospital_nabh": extracted.get("hospital_nabh", ""),
        "current_node": "verify",
        "status": "verifying",
    }


def _fallback_parse_document(file_path: Path, file_type: str, state: AuditState) -> Dict[str, Any]:
    """
    Rule-based document text parser for PDFs and text documents when cloud vision API is unconfigured.
    Strictly parses authentic text from the document without fabricating mock line items.
    """
    raw_text = ""

    if file_type == "application/pdf":
        try:
            import pdfplumber
            with pdfplumber.open(str(file_path)) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt:
                        raw_text += txt + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber extraction note: {e}")

    hosp = state.get("hospital_name") or "Empanelled Hospital"
    detected_items = []

    if raw_text:
        # Check lines for itemized descriptions and price figures
        # Matches patterns such as:
        #   "Total Knee Replacement   135000"
        #   "Disposable Surgical Gloves  10  50  500"
        #   "Bed charges 5 days  Rs. 12500"
        for line in raw_text.split("\n"):
            line = line.strip()
            if not line or len(line) < 5:
                continue

            # Look for lines with an item description and an amount
            m = re.search(
                r"^([A-Za-z0-9\s\(\)\/\-\+\,\.]{3,50})\s+(?:Rs\.?|INR|₹)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*$",
                line,
            )
            if not m:
                # Try table format: Description followed by numbers, ending with total amount
                m = re.search(
                    r"([A-Za-z\s\(\)\/\-\+]{4,45})\s+(?:(?:\d+\s+)*(?:Rs\.?|INR|₹)?\s*)(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
                    line,
                )

            if m:
                desc = m.group(1).strip()
                # Skip common header or summary lines
                if any(skip_word in desc.lower() for skip_word in ["total", "grand total", "net payable", "sub total", "tax", "gst", "discount"]):
                    continue

                try:
                    amt = float(m.group(2).replace(",", ""))
                except (ValueError, IndexError):
                    continue

                if amt > 0:
                    desc_lower = desc.lower()
                    if any(k in desc_lower for k in ["implant", "prosthesis", "stent", "mesh", "lens", "screw", "plate"]):
                        cat = "implant"
                    elif any(k in desc_lower for k in ["glove", "syringe", "needle", "gauze", "catheter", "disposable", "consumable", "drape"]):
                        cat = "consumable"
                    elif any(k in desc_lower for k in ["bed", "ward", "icu", "room", "nursing"]):
                        cat = "bed_charge"
                    elif any(k in desc_lower for k in ["test", "x-ray", "ct scan", "mri", "blood", "culture", "profile", "ultrasound", "biopsy"]):
                        cat = "diagnostic"
                    elif any(k in desc_lower for k in ["tablet", "injection", "syrup", "infusion", "saline", "paracetamol", "antibiotic", "medicine", "rx"]):
                        cat = "medicine"
                    elif any(k in desc_lower for k in ["surgery", "procedure", "resection", "replacement", "delivery", "cholecystectomy", "operation"]):
                        cat = "procedure"
                    else:
                        cat = "other"

                    detected_items.append({
                        "description": desc,
                        "category": cat,
                        "quantity": 1,
                        "unit_price": amt,
                        "total_price": amt,
                    })

    total_amt = sum(it["total_price"] for it in detected_items)

    return {
        "hospital_name": hosp,
        "hospital_nabh": state.get("hospital_nabh", ""),
        "patient_name": "[REDACTED_PMJAY_BENEFICIARY]",
        "admission_date": state.get("admission_date") or "",
        "discharge_date": state.get("discharge_date") or "",
        "total_billed": total_amt,
        "line_items": detected_items,
        "raw_text": raw_text or f"Document parsed from {file_path.name}. Recognized {len(detected_items)} line items.",
    }
