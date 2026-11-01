"""
Qdrant vector store management for HBP 2022 package data.
Supports hybrid search with dense embeddings + BM25 sparse vectors.
"""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

try:
    from qdrant_client import QdrantClient, models
except ImportError:
    QdrantClient = None
    models = None

from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = settings.qdrant_collection
DENSE_DIM = 3072  # Standard dimension for Gemini embeddings


class QdrantManager:
    """Manages Qdrant vector store for HBP 2022 data."""

    def __init__(self):
        self.client: Optional[QdrantClient] = None

    async def initialize(self):
        """Initialize Qdrant client and ensure collection exists."""
        if not QdrantClient:
            logger.warning("qdrant_client library not installed; operating in local dataset mode.")
            self.client = None
            return

        try:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=5,
            )

            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if COLLECTION_NAME not in collection_names:
                logger.info(f"Creating Qdrant collection: {COLLECTION_NAME}")
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config={
                        "dense": models.VectorParams(
                            size=DENSE_DIM,
                            distance=models.Distance.COSINE,
                        ),
                    },
                    sparse_vectors_config={
                        "bm25": models.SparseVectorParams(
                            modifier=models.Modifier.IDF,
                        ),
                    },
                )
                logger.info(f"Collection {COLLECTION_NAME} created with hybrid search support")
            else:
                logger.info(f"Collection {COLLECTION_NAME} already exists")

        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}: {e}")
            self.client = None

    def upsert_documents(self, points: List[models.PointStruct]):
        """Insert or update documents in the collection."""
        if not self.client:
            logger.warning("Qdrant client not initialized, skipping upsert")
            return

        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )
        logger.info(f"Upserted {len(points)} points to {COLLECTION_NAME}")

    def search_hybrid(
        self,
        dense_vector: List[float],
        sparse_indices: List[int],
        sparse_values: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid dense + sparse search."""
        if not self.client:
            return []

        try:
            results = self.client.query_points(
                collection_name=COLLECTION_NAME,
                prefetch=[
                    models.Prefetch(
                        query=dense_vector,
                        using="dense",
                        limit=top_k * 2,
                    ),
                    models.Prefetch(
                        query=models.SparseVector(
                            indices=sparse_indices,
                            values=sparse_values,
                        ),
                        using="bm25",
                        limit=top_k * 2,
                    ),
                ],
                query=models.FusionQuery(
                    fusion=models.Fusion.RRF,
                ),
                limit=top_k,
            )

            return [
                {
                    "id": str(point.id),
                    "text": point.payload.get("text", "") if point.payload else "",
                    "metadata": point.payload.get("metadata", {}) if point.payload else {},
                    "score": point.score,
                }
                for point in results.points
            ]
        except Exception as e:
            logger.warning(f"Hybrid search failed: {e}. Falling back to dense search.")
            return self.search_dense(dense_vector, top_k)

    def search_dense(self, dense_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search using only dense vectors."""
        if not self.client:
            return []

        try:
            results = self.client.query_points(
                collection_name=COLLECTION_NAME,
                query=dense_vector,
                using="dense",
                limit=top_k,
            )

            return [
                {
                    "id": str(point.id),
                    "text": point.payload.get("text", "") if point.payload else "",
                    "metadata": point.payload.get("metadata", {}) if point.payload else {},
                    "score": point.score,
                }
                for point in results.points
            ]
        except Exception as e:
            logger.warning(f"Dense search failed: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection stats."""
        if not self.client:
            return {"status": "not_connected"}

        try:
            info = self.client.get_collection(COLLECTION_NAME)
            return {
                "status": "connected",
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


qdrant_manager = QdrantManager()

