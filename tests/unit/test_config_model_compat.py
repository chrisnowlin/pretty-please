"""Unit tests to ensure configuration models align with dataclasses."""

from src.jina_rag_pipeline.api.models import OCRConfigModel
from src.jina_rag_pipeline.ingestion.ocr_config import OCRConfig


def test_ocr_config_model_matches_dataclass():
    """OCRConfigModel should be directly consumable by the OCRConfig dataclass."""
    model = OCRConfigModel(
        batch_size=18,
        render_workers=5,
        analysis_workers=2,
        pre_render_batches=3,
        checkpoint_enabled=True,
        use_two_tier=True,
        complexity_table_threshold=4,
        complexity_equation_threshold=3,
        complexity_image_threshold=2,
        complexity_min_text_length=120,
    )

    config = OCRConfig(**model.model_dump())

    assert config.batch_size == model.batch_size
    assert config.render_workers == model.render_workers
    assert config.use_two_tier is model.use_two_tier
    assert config.complexity_table_threshold == model.complexity_table_threshold
