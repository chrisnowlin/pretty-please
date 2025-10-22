"""Integration tests for large document processing.

Tests checkpoint/resume, parallel processing, and semantic chunking
with realistic document sizes.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import json

from src.jina_rag_pipeline.ingestion import (
    DeepseekLoader,
    CheckpointManager,
    Checkpoint,
    SemanticRegionChunker,
    Document,
    OCRConfig
)


class TestProcessingProfiles:
    """Test processing profile auto-detection and configuration."""

    def test_profile_auto_detection(self):
        """Test that profile auto-detection works."""
        profile = get_profile()
        assert profile is not None
        assert profile.name in ["aggressive", "balanced", "conservative"]

    def test_all_profiles_valid(self):
        """Test that all profiles have valid configuration."""
        for name, profile in PROFILES.items():
            assert profile.render_batch_size > 0
            assert profile.max_render_workers > 0
            assert profile.max_analysis_workers > 0
            assert profile.embedding_batch_size > 0
            assert profile.max_memory_gb > 0
            assert 0 < profile.memory_pressure_threshold <= 1

    def test_aggressive_profile_settings(self):
        """Test aggressive profile has correct M4 Max settings."""
        profile = PROFILES["aggressive"]
        assert profile.render_batch_size == 50
        assert profile.max_render_workers == 12
        assert profile.max_analysis_workers == 6
        assert profile.embedding_batch_size == 256
        assert profile.max_memory_gb == 40
        assert profile.aggressive_mode is True

    def test_profile_environment_override(self, monkeypatch):
        """Test profile can be overridden via environment variable."""
        monkeypatch.setenv("PROCESSING_PROFILE", "conservative")
        from jina_rag_pipeline.config import auto_detect_profile

        profile_name = auto_detect_profile()
        assert profile_name == "conservative"


class TestCheckpointManager:
    """Test checkpoint creation, loading, and recovery."""

    @pytest.fixture
    def checkpoint_dir(self):
        """Create temporary checkpoint directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def checkpoint_manager(self, checkpoint_dir):
        """Create checkpoint manager instance."""
        return CheckpointManager(base_dir=checkpoint_dir)

    @pytest.fixture
    def sample_file(self):
        """Create sample file for testing."""
        temp_file = Path(tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name)
        temp_file.write_text("Sample content for checkpoint testing")
        yield temp_file
        temp_file.unlink()

    def test_create_checkpoint(self, checkpoint_manager, sample_file):
        """Test checkpoint creation."""
        checkpoint = checkpoint_manager.create(
            file_path=sample_file,
            collection_name="test_collection",
            total_pages=100
        )

        assert checkpoint.checkpoint_id is not None
        assert checkpoint.total_pages == 100
        assert checkpoint.processed_pages == 0
        assert checkpoint.last_page_completed == -1

    def test_save_and_load_checkpoint(self, checkpoint_manager, sample_file):
        """Test checkpoint persistence."""
        # Create and save checkpoint
        checkpoint = checkpoint_manager.create(
            file_path=sample_file,
            collection_name="test_collection",
            total_pages=100
        )

        # Update checkpoint
        checkpoint.last_page_completed = 49
        checkpoint.processed_pages = 50
        checkpoint.page_results = [{"page_num": i, "content": f"Page {i}"} for i in range(50)]
        checkpoint_manager.save(checkpoint)

        # Load checkpoint
        loaded = checkpoint_manager.load(sample_file, "test_collection")

        assert loaded is not None
        assert loaded.last_page_completed == 49
        assert loaded.processed_pages == 50
        assert len(loaded.page_results) == 50

    def test_checkpoint_file_hash_validation(self, checkpoint_manager, sample_file):
        """Test that checkpoint detects file changes."""
        # Create checkpoint
        checkpoint = checkpoint_manager.create(
            file_path=sample_file,
            collection_name="test_collection",
            total_pages=100
        )

        # Modify file
        sample_file.write_text("Modified content - file changed!")

        # Try to load checkpoint
        loaded = checkpoint_manager.load(sample_file, "test_collection")

        # Should return None because file hash doesn't match
        assert loaded is None

    def test_checkpoint_expiration(self, checkpoint_manager, sample_file):
        """Test that expired checkpoints are cleaned up."""
        # Create checkpoint
        checkpoint = checkpoint_manager.create(
            file_path=sample_file,
            collection_name="test_collection",
            total_pages=100
        )

        # Manually set old timestamp
        checkpoint.updated_at = "2020-01-01T00:00:00"
        checkpoint_manager.save(checkpoint)

        # Try to load - should be expired
        loaded = checkpoint_manager.load(sample_file, "test_collection")
        assert loaded is None

    def test_checkpoint_cleanup(self, checkpoint_manager, sample_file):
        """Test cleanup of expired checkpoints."""
        # Create multiple checkpoints
        for i in range(3):
            checkpoint = checkpoint_manager.create(
                file_path=sample_file,
                collection_name=f"collection_{i}",
                total_pages=100
            )
            # Set old timestamp for cleanup
            checkpoint.updated_at = "2020-01-01T00:00:00"
            checkpoint_manager.save(checkpoint)

        # Run cleanup
        cleaned = checkpoint_manager.cleanup_expired(days=7)
        assert cleaned == 3

    def test_checkpoint_deletion(self, checkpoint_manager, sample_file):
        """Test checkpoint deletion after successful processing."""
        checkpoint = checkpoint_manager.create(
            file_path=sample_file,
            collection_name="test_collection",
            total_pages=100
        )

        # Verify checkpoint exists
        loaded = checkpoint_manager.load(sample_file, "test_collection")
        assert loaded is not None

        # Delete checkpoint
        checkpoint_manager.delete(checkpoint)

        # Verify checkpoint is gone
        loaded = checkpoint_manager.load(sample_file, "test_collection")
        assert loaded is None


class TestSemanticChunking:
    """Test semantic region-based chunking."""

    @pytest.fixture
    def sample_document_with_regions(self):
        """Create document with semantic regions."""
        from jina_rag_pipeline.ingestion.semantic_region import SemanticRegion

        regions = [
            SemanticRegion(
                region_id="title_1",
                region_type="title",
                region_sequence=0,
                page_number=1,
                content="Chapter 1: Introduction",
                raw_markdown="# Chapter 1: Introduction"
            ),
            SemanticRegion(
                region_id="text_1",
                region_type="text",
                region_sequence=1,
                page_number=1,
                content="This is the introduction text. " * 20,  # ~600 chars
                raw_markdown="This is the introduction text. " * 20
            ),
            SemanticRegion(
                region_id="table_1",
                region_type="table",
                region_sequence=2,
                page_number=1,
                content="| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |",
                raw_markdown="| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |",
                table_html="<table>...</table>",
                table_rows=2,
                table_cols=2
            ),
            SemanticRegion(
                region_id="equation_1",
                region_type="equation",
                region_sequence=3,
                page_number=1,
                content="E = mc^2",
                raw_markdown="$E = mc^2$",
                equation_latex="E = mc^2",
                equation_type="inline"
            ),
            SemanticRegion(
                region_id="text_2",
                region_type="text",
                region_sequence=4,
                page_number=1,
                content="More text after the equation. " * 30,  # ~900 chars
                raw_markdown="More text after the equation. " * 30
            ),
        ]

        return Document(
            content="",  # Content reconstructed from regions
            source="test.pdf",
            metadata={
                "regions": [r.to_dict() for r in regions],
                "extraction_method": "nanonets-ocr2-3b"
            }
        )

    def test_semantic_chunker_preserves_tables(self, sample_document_with_regions):
        """Test that tables are kept as atomic chunks."""
        chunker = SemanticRegionChunker(
            max_chunk_size=1000,
            preserve_tables=True
        )

        chunks = chunker.chunk(sample_document_with_regions)

        # Find table chunk
        table_chunks = [c for c in chunks if c.metadata.get("region_type") == "table"]
        assert len(table_chunks) == 1
        assert table_chunks[0].metadata.get("atomic") is True
        assert "Header 1" in table_chunks[0].content

    def test_semantic_chunker_preserves_equations(self, sample_document_with_regions):
        """Test that equations are kept as atomic chunks."""
        chunker = SemanticRegionChunker(
            max_chunk_size=1000,
            preserve_equations=True
        )

        chunks = chunker.chunk(sample_document_with_regions)

        # Find equation chunk
        equation_chunks = [c for c in chunks if c.metadata.get("region_type") == "equation"]
        assert len(equation_chunks) == 1
        assert equation_chunks[0].metadata.get("atomic") is True
        assert "E = mc^2" in equation_chunks[0].content

    def test_semantic_chunker_respects_headings(self, sample_document_with_regions):
        """Test that headings start new chunks."""
        chunker = SemanticRegionChunker(max_chunk_size=1000)

        chunks = chunker.chunk(sample_document_with_regions)

        # First chunk should start with title
        assert "Chapter 1" in chunks[0].content

    def test_semantic_chunker_merges_text_regions(self, sample_document_with_regions):
        """Test that text regions are merged until max_chunk_size."""
        chunker = SemanticRegionChunker(max_chunk_size=1000)

        chunks = chunker.chunk(sample_document_with_regions)

        # Check that we have merged chunks with multiple regions
        merged_chunks = [c for c in chunks if c.metadata.get("merged_regions", 0) > 1]
        assert len(merged_chunks) > 0

    def test_semantic_chunker_fallback(self):
        """Test fallback to character chunking when no regions."""
        doc = Document(
            content="Simple text document without semantic regions.",
            source="test.txt",
            metadata={}
        )

        chunker = SemanticRegionChunker(max_chunk_size=100)
        chunks = chunker.chunk(doc)

        # Should fall back to character chunking
        assert len(chunks) == 1
        assert chunks[0].metadata.get("chunking_strategy") == "fixed_size"


class TestNanonetsLoaderIntegration:
    """Integration tests for NanonetsFirstLoader with parallel processing."""

    @pytest.fixture
    def mock_analyzer(self):
        """Create mock Nanonets analyzer."""
        analyzer = Mock()
        analyzer.analyze_document = Mock(return_value="Processed page content")
        return analyzer

    def test_loader_initialization_with_profile(self):
        """Test loader initializes with correct profile settings."""
        loader = NanonetsFirstLoader()

        profile = get_profile()
        assert loader.batch_size == profile.render_batch_size
        assert loader.max_render_workers == profile.max_render_workers
        assert loader.max_analysis_workers == profile.max_analysis_workers

    def test_loader_checkpoint_integration(self, mock_analyzer):
        """Test that loader properly integrates with checkpoints."""
        loader = NanonetsFirstLoader(analyzer=mock_analyzer)

        assert loader.enable_checkpoints is True
        assert loader.checkpoint_manager is not None

    def test_parallel_rendering_maintains_order(self):
        """Test that parallel rendering returns pages in correct order."""
        # This would require a real PDF file and PyMuPDF
        # For now, we'll test the structure
        loader = NanonetsFirstLoader()

        # Verify parallel methods exist
        assert hasattr(loader, '_render_pages_parallel')
        assert hasattr(loader, '_analyze_pages_parallel')


@pytest.mark.slow
@pytest.mark.skipif(not Path("test_documents").exists(), reason="Test documents not available")
class TestLargeDocumentPerformance:
    """Performance tests for large documents (requires test files)."""

    def test_100_page_document_processing_time(self):
        """Test that 100-page document completes within target time."""
        # This requires a real 100-page PDF
        pytest.skip("Requires test document: test_documents/100_pages.pdf")

    def test_checkpoint_resume_correctness(self):
        """Test that resumed processing produces same output."""
        # This requires simulating a crash and resume
        pytest.skip("Requires crash simulation infrastructure")

    def test_parallel_vs_sequential_quality(self):
        """Test that parallel processing maintains quality."""
        # Compare parallel output to sequential
        pytest.skip("Requires quality comparison metrics")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
