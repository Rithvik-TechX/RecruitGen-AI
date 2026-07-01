"""
ChromaDB Vector Store — manages vector storage and similarity search.
"""

from __future__ import annotations

from typing import Any

import chromadb
import structlog
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings

logger = structlog.get_logger(__name__)

_chroma_client: chromadb.HttpClient | None = None


def get_chroma_client() -> chromadb.HttpClient:
    """Return a lazily-initialised ChromaDB client singleton."""
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        logger.info(
            "connecting_to_chromadb",
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        _chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info("chromadb_connected")
    return _chroma_client


def get_or_create_collection(collection_name: str) -> chromadb.Collection:
    """Get or create a ChromaDB collection with cosine distance."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


class VectorStore:
    """ChromaDB vector store operations for candidates and jobs."""

    def __init__(self) -> None:
        settings = get_settings()
        self.candidate_collection = get_or_create_collection(
            settings.CHROMA_COLLECTION_CANDIDATES,
        )
        self.job_collection = get_or_create_collection(
            settings.CHROMA_COLLECTION_JOBS,
        )

    # ── Candidate Operations ────────────────────────────────

    def upsert_candidate_embedding(
        self,
        candidate_id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        document: str | None = None,
    ) -> None:
        """Insert or update a candidate embedding."""
        self.candidate_collection.upsert(
            ids=[candidate_id],
            embeddings=[embedding],
            metadatas=[metadata or {}],
            documents=[document or ""],
        )
        logger.info("candidate_embedding_upserted", candidate_id=candidate_id)

    def search_similar_candidates(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for similar candidates by embedding."""
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where
        results = self.candidate_collection.query(**kwargs)
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
        }

    def get_candidate_embedding(self, candidate_id: str) -> dict[str, Any] | None:
        """Get a specific candidate's embedding."""
        try:
            result = self.candidate_collection.get(
                ids=[candidate_id],
                include=["embeddings", "metadatas", "documents"],
            )
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "embedding": result["embeddings"][0] if result["embeddings"] else None,
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                    "document": result["documents"][0] if result["documents"] else "",
                }
        except Exception:
            pass
        return None

    def delete_candidate_embedding(self, candidate_id: str) -> None:
        """Delete a candidate's embedding."""
        try:
            self.candidate_collection.delete(ids=[candidate_id])
            logger.info("candidate_embedding_deleted", candidate_id=candidate_id)
        except Exception as exc:
            logger.warning("candidate_embedding_delete_failed", error=str(exc))

    # ── Job Operations ──────────────────────────────────────

    def upsert_job_embedding(
        self,
        job_id: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
        document: str | None = None,
    ) -> None:
        """Insert or update a job embedding."""
        self.job_collection.upsert(
            ids=[job_id],
            embeddings=[embedding],
            metadatas=[metadata or {}],
            documents=[document or ""],
        )
        logger.info("job_embedding_upserted", job_id=job_id)

    def search_similar_jobs(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for similar jobs by embedding."""
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where
        results = self.job_collection.query(**kwargs)
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
        }

    def get_job_embedding(self, job_id: str) -> dict[str, Any] | None:
        """Get a specific job's embedding."""
        try:
            result = self.job_collection.get(
                ids=[job_id],
                include=["embeddings", "metadatas", "documents"],
            )
            if result["ids"]:
                return {
                    "id": result["ids"][0],
                    "embedding": result["embeddings"][0] if result["embeddings"] else None,
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                    "document": result["documents"][0] if result["documents"] else "",
                }
        except Exception:
            pass
        return None

    def delete_job_embedding(self, job_id: str) -> None:
        """Delete a job's embedding."""
        try:
            self.job_collection.delete(ids=[job_id])
            logger.info("job_embedding_deleted", job_id=job_id)
        except Exception as exc:
            logger.warning("job_embedding_delete_failed", error=str(exc))

    # ── Utility ─────────────────────────────────────────────

    def get_collection_count(self, collection_type: str = "candidates") -> int:
        """Get the count of items in a collection."""
        if collection_type == "candidates":
            return self.candidate_collection.count()
        elif collection_type == "jobs":
            return self.job_collection.count()
        return 0
