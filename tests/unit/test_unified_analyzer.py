"""
Unit tests for Deepseek loader initialization helpers.
"""

import pytest

from src.jina_rag_pipeline.ingestion.deepseek_loader import DeepseekLoader
from src.jina_rag_pipeline.ingestion.ocr_config import OCRConfig


def test_deepseek_loader_uses_factory(monkeypatch):
    """Ensure DeepseekLoader calls factory with config-derived arguments."""
    captured = {}

    def fake_factory(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        "src.jina_rag_pipeline.ingestion.deepseek_loader.create_deepseek_analyzer",
        fake_factory,
    )

    config = OCRConfig.deepseek_small()
    loader = DeepseekLoader(config=config, analyzer=None)

    assert captured["resolution_mode"] == "small"
    assert captured["enable_grounding"] is True
    assert loader.config is config
    assert loader._get_analyzer() is not None


def test_deepseek_loader_requires_dependencies(monkeypatch):
    """DeepseekLoader should raise if analyzer factory unavailable."""
    monkeypatch.setattr(
        "src.jina_rag_pipeline.ingestion.deepseek_loader.create_deepseek_analyzer",
        None,
    )

    with pytest.raises(ImportError):
        DeepseekLoader(config=OCRConfig.deepseek_balanced(), analyzer=None)
