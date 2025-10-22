"""Integration tests for NanonetsLayoutAnalyzer."""

import pytest
from pathlib import Path
from src.jina_rag_pipeline.ingestion.nanonets_layout import (
    NanonetsLayoutAnalyzer,
    create_analyzer,
    NANONETS_AVAILABLE
)


@pytest.mark.skipif(not NANONETS_AVAILABLE, reason="Nanonets dependencies not installed")
class TestNanonetsLayoutAnalyzer:
    """Test NanonetsLayoutAnalyzer functionality."""

    def test_initialization(self):
        """Test analyzer can be initialized."""
        analyzer = NanonetsLayoutAnalyzer()
        assert analyzer.model_name == "nanonets/Nanonets-OCR2-3B"
        assert analyzer.device == "mps"
        assert analyzer.enable_tables is True

    def test_factory_function(self):
        """Test create_analyzer factory."""
        analyzer = create_analyzer()
        assert isinstance(analyzer, NanonetsLayoutAnalyzer)

    def test_prompt_generation(self):
        """Test prompt is generated correctly."""
        analyzer = NanonetsLayoutAnalyzer()
        prompt = analyzer._create_prompt()

        assert "Extract the text" in prompt
        assert "html format" in prompt  # tables enabled
        assert "LaTeX" in prompt  # equations enabled
        assert "<img></img>" in prompt  # images enabled

    def test_prompt_generation_selective_features(self):
        """Test prompt generation with selective features."""
        analyzer = NanonetsLayoutAnalyzer(
            enable_tables=False,
            enable_equations=True,
            enable_image_descriptions=False
        )
        prompt = analyzer._create_prompt()

        assert "Extract the text" in prompt
        assert "html format" not in prompt  # tables disabled
        assert "LaTeX" in prompt  # equations enabled
        assert "<img></img>" not in prompt  # images disabled

    def test_custom_configuration(self):
        """Test analyzer with custom configuration."""
        analyzer = NanonetsLayoutAnalyzer(
            device="cpu",
            enable_tables=False,
            max_new_tokens=2048
        )
        assert analyzer.device == "cpu"
        assert analyzer.enable_tables is False
        assert analyzer.max_new_tokens == 2048

    def test_lazy_loading(self):
        """Test that model is not loaded on initialization."""
        analyzer = NanonetsLayoutAnalyzer()
        assert analyzer._model is None
        assert analyzer._processor is None
        assert analyzer._tokenizer is None

    def test_parser_initialization(self):
        """Test that MarkdownParser is initialized."""
        analyzer = NanonetsLayoutAnalyzer()
        assert analyzer.parser is not None
        from src.jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser
        assert isinstance(analyzer.parser, MarkdownParser)

    # Skip actual inference tests (requires model download)
    # These would be run manually or in CI with model cache


def test_import_available():
    """Test that nanonets_layout module can be imported."""
    from src.jina_rag_pipeline.ingestion import nanonets_layout
    assert hasattr(nanonets_layout, 'NanonetsLayoutAnalyzer')
    assert hasattr(nanonets_layout, 'create_analyzer')
    assert hasattr(nanonets_layout, 'NANONETS_AVAILABLE')


def test_missing_dependencies_handling():
    """Test that missing dependencies are handled gracefully."""
    # This test just verifies the import structure
    from src.jina_rag_pipeline.ingestion.nanonets_layout import NANONETS_AVAILABLE
    # NANONETS_AVAILABLE should be True if PIL, torch, transformers are available
    # or False if they're not - either case is valid
    assert isinstance(NANONETS_AVAILABLE, bool)


@pytest.mark.skipif(not NANONETS_AVAILABLE, reason="Nanonets dependencies not installed")
def test_factory_with_custom_device():
    """Test factory function with custom device."""
    analyzer = create_analyzer(device="cpu")
    assert analyzer.device == "cpu"


@pytest.mark.skipif(not NANONETS_AVAILABLE, reason="Nanonets dependencies not installed")
def test_factory_with_kwargs():
    """Test factory function passes through kwargs."""
    analyzer = create_analyzer(
        device="cpu",
        enable_tables=False,
        max_new_tokens=2048
    )
    assert analyzer.device == "cpu"
    assert analyzer.enable_tables is False
    assert analyzer.max_new_tokens == 2048
