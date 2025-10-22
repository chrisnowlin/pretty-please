"""Integration test for PowerPoint loading with Nanonets."""

import pytest
from pathlib import Path
from src.jina_rag_pipeline.ingestion.loaders import PowerPointLoader
from src.jina_rag_pipeline.ingestion.nanonets_layout import NANONETS_AVAILABLE


@pytest.mark.skipif(not NANONETS_AVAILABLE, reason="Nanonets dependencies not installed")
class TestPowerPointNanonets:
    """Test PowerPoint loading with Nanonets analyzer."""

    def test_initialization_with_layout_analysis(self):
        """Test that PowerPointLoader can be initialized with layout analysis."""
        loader = PowerPointLoader(use_layout_analysis=True)
        assert loader.use_layout_analysis is True
        assert loader.layout_analyzer is not None

    def test_initialization_without_layout_analysis(self):
        """Test simple mode still works."""
        loader = PowerPointLoader(use_layout_analysis=False)
        assert loader.use_layout_analysis is False
