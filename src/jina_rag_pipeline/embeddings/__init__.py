"""Embeddings module for Jina Embeddings v4."""

from .jina_v4 import JinaEmbeddingsV4
from .config import EmbeddingConfig
from .multivector import MultiVectorHandler
from .format_converter import FormatConverter
from .batch_processor import BatchProcessor

# Compatibility alias
JinaEmbeddings = JinaEmbeddingsV4

__all__ = [
    "JinaEmbeddingsV4",
    "JinaEmbeddings",
    "EmbeddingConfig",
    "MultiVectorHandler",
    "FormatConverter",
    "BatchProcessor",
]