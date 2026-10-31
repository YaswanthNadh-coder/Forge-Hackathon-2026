"""
HBP 2022 Data Ingestion Pipeline.
Parses the official NHA Health Benefit Package Master (HBP 2022) PDF/XLSX/CSV/JSON
and indexes packages and procedures into Qdrant for hybrid dense + BM25 search.
"""

from __future__ import annotations

import os
import json
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any

try:
    from qdrant_client import models
except ImportError:
    models = None

from app.config import settings
from app.rag.qdrant_store import qdrant_manager
from app.rag.retriever import get_embedding, _get_sparse_vector

logger = logging.getLogger(__name__)


async def ingest_hbp_data(file_path: str) -> Dict[str, Any]:
    """
    Ingest HBP 2022 master data into Qdrant.
    Supports JSON, CSV, Excel, and PDF files.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"HBP data file not found: {file_path}")

    logger.info(f"Starting HBP 2022 data ingestion from {file_path}")
    suffix = path.suffix.lower()

    if suffix == ".json":
        chunks = _parse_json(path)
    elif suffix == ".csv":
        chunks = _parse_csv(path)
    elif suffix in (".xlsx", ".xls"):
        chunks = _parse_excel(path)
    elif suffix == ".pdf":
        chunks = await _parse_pdf(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

    logger.info(f"Parsed {len(chunks)} package/procedure records from {file_path}")

    if not qdrant_manager.client:
        await qdrant_manager.initialize()

    points = []
    batch_size = 50

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        batch_points = []

        for chunk in batch:
            text = chunk["text"]
            metadata = chunk.get("metadata", {})

            dense_vector = await get_embedding(text)
            sparse_indices, sparse_values = _get_sparse_vector(text)

            point_id = str(uuid.uuid4())
            vectors = {"dense": dense_vector}

            point = models.PointStruct(
                id=point_id,
                vector=vectors,
                payload={
                    "text": text,
                    "metadata": metadata,
                },
            )

            if sparse_indices:
                point.vector["bm25"] = models.SparseVector(
                    indices=sparse_indices,
                    values=sparse_values,
                )

            batch_points.append(point)

        if batch_points and qdrant_manager.client:
            qdrant_manager.upsert_documents(batch_points)
            logger.info(f"Indexed batch {i // batch_size + 1}: {len(batch_points)} items")

    return {
        "status": "success",
        "total_records_indexed": len(chunks),
        "source_file": str(file_path),
    }


def _parse_json(path: Path) -> List[Dict[str, Any]]:
    """Parse JSON dataset containing official HBP 2022 records."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = []
    records = data if isinstance(data, list) else data.get("packages", data.get("procedures", []))

    for rec in records:
        specialty = rec.get("specialty", "General")
        code = rec.get("package_code", rec.get("code", "N/A"))
        name = rec.get("procedure_name", rec.get("package_name", "N/A"))
        tier1 = rec.get("rate_tier1", rec.get("tier1_inr", 0))
        tier2 = rec.get("rate_tier2", rec.get("tier2_inr", 0))
        tier3 = rec.get("rate_tier3", rec.get("tier3_inr", 0))
        ward_days = rec.get("included_ward_days", rec.get("ward_days", 0))
        icu_days = rec.get("included_icu_days", rec.get("icu_days", 0))
        implant_cap = rec.get("implant_ceiling_inr", rec.get("implant_ceiling", 0))
        bundled = rec.get("bundled_items", [
            "Registration charges",
            "General Ward bed charges",
            "Doctor/Surgeon consultation fees",
            "Nursing charges",
            "Surgical consumables and disposables",
            "Standard routine pre-op and post-op diagnostics",
            "Inpatient medicines",
            "Food and dietary services",
        ])

        text = (
            f"NHA PM-JAY HBP 2022 Master Package: [{code}] {name}\n"
            f"Specialty: {specialty}\n"
            f"Official Rates (INR): Tier-1 (Metro/NABH): ₹{tier1:,} | Tier-2: ₹{tier2:,} | Tier-3: ₹{tier3:,}\n"
            f"Bundled Inclusions: {', '.join(bundled) if isinstance(bundled, list) else bundled}\n"
            f"Stay Coverage: {ward_days} days General Ward, {icu_days} days ICU included in package rate.\n"
            f"Notified Implant Ceiling: ₹{implant_cap:,} (charges exceeding this ceiling are non-permissible).\n"
            f"Statutory Mandate: No out-of-pocket charges permitted for bundled consumables, pre-op tests, or standard bed days under PM-JAY cashless guidelines."
        )

        chunks.append({
            "text": text,
            "metadata": {
                "source": "NHA_HBP_2022_MASTER",
                "package_code": code,
                "procedure_name": name,
                "specialty": specialty,
                "rate_tier1": tier1,
                "rate_tier2": tier2,
                "rate_tier3": tier3,
                "ward_days": ward_days,
                "icu_days": icu_days,
                "implant_ceiling": implant_cap,
            },
        })

    return chunks


def _parse_csv(path: Path) -> List[Dict[str, Any]]:
    """Parse HBP 2022 CSV file."""
    import csv
    chunks = []

    with open(str(path), "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("package_code", row.get("code", "N/A"))
            name = row.get("procedure_name", row.get("name", "N/A"))
            spec = row.get("specialty", "General")
            t1 = row.get("tier1", row.get("rate_tier1", "0"))
            t2 = row.get("tier2", row.get("rate_tier2", "0"))
            t3 = row.get("tier3", row.get("rate_tier3", "0"))
            row_text = (
                f"NHA HBP 2022 Package: [{code}] {name} ({spec})\n"
                f"Rates: Tier 1: ₹{t1}, Tier 2: ₹{t2}, Tier 3: ₹{t3}\n"
                f"Bundled: General bed, nursing, medicines, consumables, pre/post care. Out-of-pocket prohibited."
            )
            chunks.append({
                "text": row_text,
                "metadata": {"package_code": code, "procedure_name": name, "specialty": spec},
            })

    return chunks


def _parse_excel(path: Path) -> List[Dict[str, Any]]:
    """Parse HBP 2022 Excel file."""
    chunks = []
    try:
        import openpyxl

        wb = openpyxl.load_workbook(str(path), read_only=True)
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                continue

            headers = [str(h or "").strip() for h in rows[0]]
            for row in rows[1:]:
                values = [str(v or "").strip() for v in row]
                if not any(values):
                    continue
                row_text = " | ".join([f"{h}: {v}" for h, v in zip(headers, values) if h and v])
                chunks.append({
                    "text": f"HBP 2022 Package ({sheet_name}):\n{row_text}",
                    "metadata": {"sheet": sheet_name, "source": "HBP_2022_XLSX"},
                })
        wb.close()
    except Exception as e:
        logger.warning(f"Excel parsing failed: {e}")
    return chunks


async def _parse_pdf(path: Path) -> List[Dict[str, Any]]:
    """Parse HBP 2022 PDF file."""
    chunks = []
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages):
                txt = page.extract_text()
                if txt:
                    chunks.append({
                        "text": f"HBP 2022 Master PDF (Page {i+1}):\n{txt}",
                        "metadata": {"page": i + 1, "source": "HBP_2022_PDF"},
                    })
    except Exception as e:
        logger.warning(f"PDF parsing error: {e}")
    return chunks

