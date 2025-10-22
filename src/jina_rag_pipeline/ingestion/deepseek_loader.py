"""
DeepseekLoader provides configuration-driven access to the Deepseek OCR pipeline.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from .ocr_config import OCRConfig
from .loaders import OCRLoader

try:
    from .deepseek_layout import create_analyzer as create_deepseek_analyzer
except ImportError:  # pragma: no cover - handled at runtime
    create_deepseek_analyzer = None  # type: ignore

logger = logging.getLogger(__name__)


class DeepseekLoader(OCRLoader):
    """Configuration-driven Deepseek OCR loader."""

    def __init__(self, config: Optional[OCRConfig] = None, analyzer=None) -> None:
        if config is None:
            config = OCRConfig.deepseek_balanced()
            logger.info("Auto-selected Deepseek OCR config: deepseek_balanced")

        if analyzer is None:
            if create_deepseek_analyzer is None:
                raise ImportError(
                    "Deepseek analyzer not available. Install dependencies with: "
                    "pip install pillow torch transformers"
                )

            analyzer = create_deepseek_analyzer(
                resolution_mode=config.resolution_mode,
                enable_grounding=config.enable_grounding,
                enable_compression=config.enable_compression,
                use_vllm=config.use_vllm,
            )

        super().__init__(
            analyzer=analyzer,
            progressive=True,
            batch_size=config.batch_size,
            max_render_workers=config.render_workers,
            max_analysis_workers=config.analysis_workers,
            enable_checkpoints=config.checkpoint_enabled,
            checkpoint_dir=Path("./checkpoints")
        )
        self.config = config
        # Override pre_render_batches from config (parent may have set default)
        self.pre_render_batches = config.pre_render_batches

        logger.info(
            "DeepseekLoader initialized: resolution_mode=%s grounding=%s compression=%s",
            config.resolution_mode,
            config.enable_grounding,
            config.enable_compression,
        )
