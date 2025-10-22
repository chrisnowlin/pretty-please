from .base import Document, DocumentLoader
from .chunking import Chunk, ChunkingStrategy, FixedSizeChunker, SentenceChunker, SlidingWindowChunker
from .loaders import (
    DocxLoader,
    LoaderFactory,
    MarkdownLoader,
    PDFLoader,
    TextLoader,
    OCRLoader,
)
from .markdown_parser import MarkdownParser, RegionStub
from .pipeline import DocumentProcessor
from .semantic_region import SemanticRegion, BoundingBox
from .semantic_chunking import SemanticRegionChunker
from .checkpoint import CheckpointManager, Checkpoint

from .analysis_pipeline import AnalysisPipeline
from .ocr_config import OCRConfig
from .deepseek_loader import DeepseekLoader
from .unified_ocr_loader import UnifiedOCRLoader, create_ocr_loader

# Deepseek analyzer (optional dependency)
try:
    from .deepseek_layout import DeepseekLayoutAnalyzer, create_analyzer as create_deepseek_analyzer
except ImportError:  # pragma: no cover - depends on optional deps
    DeepseekLayoutAnalyzer = None  # type: ignore

    def create_deepseek_analyzer(*args, **kwargs):  # type: ignore
        raise ImportError(
            "Deepseek layout analyzer not available. Install pillow, torch, and transformers."
        )

__all__ = [
    "Document",
    "DocumentLoader",
    "Chunk",
    "ChunkingStrategy",
    "FixedSizeChunker",
    "SentenceChunker",
    "SlidingWindowChunker",
    "SemanticRegionChunker",
    "TextLoader",
    "MarkdownLoader",
    "PDFLoader",
    "DocxLoader",
    "LoaderFactory",
    "OCRLoader",
    "DeepseekLoader",
    "DocumentProcessor",
    "MarkdownParser",
    "RegionStub",
    "SemanticRegion",
    "BoundingBox",
    "DeepseekLayoutAnalyzer",
    "AnalysisPipeline",
    "OCRConfig",
    "create_deepseek_analyzer",
    "create_analyzer",
    "UnifiedOCRLoader",
    "create_ocr_loader",
    "CheckpointManager",
    "Checkpoint",
]

# Backward compatibility aliases
create_analyzer = create_deepseek_analyzer
