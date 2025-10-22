"""
Unified OCR Loader for DeepseekOCR backend.

After comprehensive testing, DeepseekOCR with GUNDAM mode has been selected
as the primary OCR solution for the Jina embeddings RAG pipeline.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .ocr_config import OCRConfig
from .loaders import OCRLoader
from .deepseek_loader import DeepseekLoader

logger = logging.getLogger(__name__)


class UnifiedOCRLoader(OCRLoader):
    """
    OCR loader using DeepseekOCR with GUNDAM mode.

    After comprehensive performance testing, DeepseekOCR with GUNDAM mode
    has been selected as the primary OCR backend for optimal performance
    with Jina embeddings RAG pipeline.

    Usage:
        # Basic usage with defaults (GUNDAM mode)
        loader = UnifiedOCRLoader()

        # With custom config
        loader = UnifiedOCRLoader(config=OCRConfig.deepseek_gundam())

        # Via environment variable
        os.environ['OCR_BACKEND'] = 'deepseek'  # DeepseekOCR is the default
        loader = UnifiedOCRLoader()
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        config: Optional[OCRConfig] = None,
        analyzer_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize OCR loader with DeepseekOCR backend.

        Args:
            backend: Currently only 'deepseek' is supported (default).
                    Kept for backward compatibility, but PaddleOCR support
                    has been removed in favor of GUNDAM mode.
            config: Optional OCR configuration (defaults to GUNDAM mode)
            **kwargs: Additional arguments passed to DeepseekLoader
        """
        # Determine backend (only deepseek is supported now)
        if backend is None:
            backend = os.environ.get('OCR_BACKEND', 'deepseek').lower()

        if backend != 'deepseek':
            logger.warning(
                f"Backend '{backend}' requested but only 'deepseek' is supported. "
                f"Using DeepseekOCR with GUNDAM mode instead."
            )
            backend = 'deepseek'

        self.backend = backend
        self._analyzer_init_kwargs = dict(analyzer_kwargs or {})
        logger.info(f"Initializing OCR loader with backend: {backend} (GUNDAM mode)")

        # Initialize with DeepseekOCR
        self._init_deepseek(config, **kwargs)

    def _init_deepseek(self, config: Optional[OCRConfig] = None, **kwargs):
        """Initialize with DeepseekOCR backend (GUNDAM mode as default)."""
        from .deepseek_loader import DeepseekLoader

        if config is None:
            # Default to GUNDAM mode for optimal performance with Jina embeddings
            config = OCRConfig.deepseek_gundam()
            logger.info("Using default DeepseekOCR config: GUNDAM mode")

        # Create Deepseek loader
        deepseek_loader = DeepseekLoader(config=config, **kwargs)

        # Inherit all attributes and methods
        self.__dict__.update(deepseek_loader.__dict__)
        self._backend_loader = deepseek_loader

    def get_backend_info(self) -> dict:
        """Get information about the current backend."""
        return {
            "backend": self.backend,
            "config": self.config.__dict__ if hasattr(self, 'config') else None,
            "analyzer_type": type(self._get_analyzer()).__name__ if self._get_analyzer() else None
        }


def create_ocr_loader(
    backend: Optional[str] = None,
    config: Optional[OCRConfig] = None,
    analyzer_kwargs: Optional[Dict[str, Any]] = None,
    **kwargs
) -> UnifiedOCRLoader:
    """
    Factory function to create an OCR loader using DeepseekOCR + GUNDAM mode.

    After comprehensive performance testing, DeepseekOCR with GUNDAM mode
    has been selected as the primary OCR solution for Jina embeddings RAG pipeline.

    Args:
        backend: For backward compatibility, accepts any value but always uses 'deepseek'
        config: OCR configuration (defaults to GUNDAM mode)
        analyzer_kwargs: Optional analyzer keyword arguments
        **kwargs: Additional configuration passed to UnifiedOCRLoader

    Returns:
        UnifiedOCRLoader instance configured with DeepseekOCR + GUNDAM mode

    Example:
        # Quick creation with defaults (GUNDAM mode)
        loader = create_ocr_loader()

        # With custom config
        from src.jina_rag_pipeline.ingestion import OCRConfig
        loader = create_ocr_loader(config=OCRConfig.deepseek_gundam())

        # For Jina embeddings RAG pipeline
        document = loader.load('document.pdf')
        embeddings = jina_model.embed(document.content)
    """
    return UnifiedOCRLoader(backend=backend, config=config, analyzer_kwargs=analyzer_kwargs, **kwargs)
