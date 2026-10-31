"""
Hybrid retriever for HBP 2022 data.
Combines dense semantic vector retrieval with BM25 sparse keyword matching in Qdrant,
with an automatic local semantic/keyword fallback over the official NHA HBP 2022 Master dataset
when the vector database is initializing or running in standalone mode.
"""

import os
import re
import json
import logging
from pathlib import Path
from collections import Counter
from typing import List, Dict, Tuple, Any
from google import genai

from app.config import settings
from app.rag.qdrant_store import qdrant_manager

logger = logging.getLogger(__name__)

# Global vocabulary cache for BM25 sparse encoding
_vocab: Dict[str, int] = {}
_vocab_counter = 0

# Cache for local HBP master dataset
_hbp_cache: List[Dict[str, Any]] = []


def _load_local_hbp_cache() -> List[Dict[str, Any]]:
    """Loads and caches the official NHA HBP 2022 dataset for instant fallback matching."""
    global _hbp_cache
    if _hbp_cache:
        return _hbp_cache

    try:
        data_path = Path(__file__).parent.parent.parent / "data" / "hbp_2022_master.json"
        if data_path.exists():
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _hbp_cache = data.get("packages", [])
                logger.info(f"Loaded {len(_hbp_cache)} official packages into HBP memory cache")
    except Exception as e:
        logger.warning(f"Could not load local HBP cache: {e}")

    return _hbp_cache


def _tokenize(text: str) -> List[str]:
    """Tokenize and filter text for keyword matching."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = text.split()
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to",
        "for", "of", "and", "or", "with", "as", "by", "from", "item", "charge",
        "fees", "charges", "cost", "total", "rate",
    }
    return [t for t in tokens if t not in stopwords and len(t) > 1]


def _get_sparse_vector(text: str) -> Tuple[List[int], List[float]]:
    """Generate a sparse TF vector for BM25."""
    global _vocab, _vocab_counter

    tokens = _tokenize(text)
    if not tokens:
        return [], []

    tf = Counter(tokens)
    indices = []
    values = []

    for token, count in tf.items():
        if token not in _vocab:
            _vocab[token] = _vocab_counter
            _vocab_counter += 1
        indices.append(_vocab[token])
        values.append(float(count))

    return indices, values


async def get_embedding(text: str) -> List[float]:
    """Get dense embedding from Gemini embedding model."""
    if not settings.has_gemini_key:
        return [0.0] * 768

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        result = client.models.embed_content(
            model="text-embedding-004",
            contents=text,
        )
        return result.embeddings[0].values
    except Exception as e:
        logger.warning(f"Dense embedding generation failed: {e}. Returning zero vector.")
        return [0.0] * 768


def _search_local_hbp(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Direct lexical / keyword matcher over the authentic NHA HBP 2022 Master
    used when Qdrant is offline or not yet connected.
    """
    packages = _load_local_hbp_cache()
    if not packages:
        return []

    tokens = set(_tokenize(query))
    if not tokens:
        return []

    scored_results = []
    for pkg in packages:
        pkg_text = (
            f"{pkg.get('package_code', '')} {pkg.get('procedure_name', '')} {pkg.get('specialty', '')} "
            f"{' '.join(pkg.get('bundled_items', []))}"
        ).lower()

        # Score based on token frequency
        score = sum(1 for t in tokens if t in pkg_text)
        if score > 0:
            formatted_text = (
                f"NHA PM-JAY HBP 2022 Package: [{pkg.get('package_code')}] {pkg.get('procedure_name')}\n"
                f"Specialty: {pkg.get('specialty')}\n"
                f"Rates: Tier 1 (Metro/NABH): ₹{pkg.get('rate_tier1', 0):,} | Tier 2: ₹{pkg.get('rate_tier2', 0):,} | Tier 3: ₹{pkg.get('rate_tier3', 0):,}\n"
                f"Coverage: {pkg.get('included_ward_days', 0)} ward days, {pkg.get('included_icu_days', 0)} ICU days included.\n"
                f"Implant Ceiling: ₹{pkg.get('implant_ceiling_inr', 0):,}\n"
                f"Bundled Items: {', '.join(pkg.get('bundled_items', []))}\n"
                f"Statutory PM-JAY Rule: All bundled items, nursing, bed charges and standard pre/post op tests must be 100% cashless."
            )
            scored_results.append({
                "id": pkg.get("package_code"),
                "text": formatted_text,
                "metadata": pkg,
                "score": float(score),
            })

    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]


async def hybrid_retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Perform hybrid retrieval combining dense semantic search with BM25 sparse search.
    Falls back gracefully to local authentic HBP master database if Qdrant is unavailable.
    """
    # 1. Try Qdrant if client is connected
    if qdrant_manager.client:
        try:
            dense_vector = await get_embedding(query)
            sparse_indices, sparse_values = _get_sparse_vector(query)

            if sparse_indices:
                results = qdrant_manager.search_hybrid(
                    dense_vector=dense_vector,
                    sparse_indices=sparse_indices,
                    sparse_values=sparse_values,
                    top_k=top_k,
                )
            else:
                results = qdrant_manager.search_dense(dense_vector, top_k)

            if results:
                return results
        except Exception as e:
            logger.warning(f"Qdrant retrieval attempt failed: {e}")

    # 2. Local authentic HBP master dataset query
    return _search_local_hbp(query, top_k=top_k)
