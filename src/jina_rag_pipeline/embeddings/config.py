"""Embedding configuration module."""

from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class EmbeddingConfig:
    """Configuration for Jina Embeddings v4."""

    task: Literal[
        "retrieval.query",
        "retrieval.passage",
        "text-matching",
        "classification",
        "separation",
        "code.query",
        "code.passage"
    ] = "retrieval.passage"

    dimensions: Literal[128, 256, 512, 1024, 2048] = 2048
    late_chunking: bool = True
    return_multivector: bool = True
    embedding_format: Literal["float", "base64", "binary", "ubinary"] = "float"
    batch_size: int = 32
    max_tokens_per_batch: int = 8192

    @classmethod
    def for_documents(cls) -> "EmbeddingConfig":
        """Configuration for document embeddings."""
        return cls(
            task="retrieval.passage",
            dimensions=2048,
            late_chunking=True,
            return_multivector=True,
            batch_size=32,
            max_tokens_per_batch=8192,
        )

    @classmethod
    def for_query(cls) -> "EmbeddingConfig":
        """Configuration for query embeddings."""
        return cls(
            task="retrieval.query",
            dimensions=2048,
            late_chunking=True,
            return_multivector=True,
            batch_size=32,
            max_tokens_per_batch=8192,
        )

    @classmethod
    def storage_optimized(cls) -> "EmbeddingConfig":
        """Configuration for storage-optimized embeddings."""
        return cls(
            task="retrieval.passage",
            dimensions=256,
            late_chunking=False,
            embedding_format="ubinary",
            batch_size=64,
            max_tokens_per_batch=16384,
        )

    @classmethod
    def fast(cls) -> "EmbeddingConfig":
        """Configuration for fast embeddings."""
        return cls(
            task="retrieval.passage",
            dimensions=512,
            late_chunking=False,
            batch_size=64,
            max_tokens_per_batch=16384,
        )

    @classmethod
    def memory_constrained(cls) -> "EmbeddingConfig":
        """Configuration for memory-constrained environments."""
        return cls(
            task="retrieval.passage",
            dimensions=256,
            late_chunking=False,
            batch_size=8,
            max_tokens_per_batch=2048,
        )
