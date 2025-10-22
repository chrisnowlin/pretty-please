"""Retrieval performance metrics tracking."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class RetrievalMetrics:
    """
    Metrics for retrieval performance tracking.

    Tracks timing information and document counts through the retrieval pipeline.
    """

    # Timing metrics (all in milliseconds)
    vector_search_time_ms: float = 0.0
    reranking_time_ms: float = 0.0
    total_time_ms: float = 0.0

    # Document counts
    documents_retrieved: int = 0
    documents_after_rerank: int = 0
    images_retrieved: int = 0

    # Flags
    hybrid_search_used: bool = False
    reranking_enabled: bool = False
    compression_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "vector_search_time_ms": round(self.vector_search_time_ms, 2),
            "reranking_time_ms": round(self.reranking_time_ms, 2),
            "total_time_ms": round(self.total_time_ms, 2),
            "documents_retrieved": self.documents_retrieved,
            "documents_after_rerank": self.documents_after_rerank,
            "images_retrieved": self.images_retrieved,
            "hybrid_search_used": self.hybrid_search_used,
            "reranking_enabled": self.reranking_enabled,
            "compression_enabled": self.compression_enabled,
        }
