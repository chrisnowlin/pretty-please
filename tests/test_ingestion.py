import tempfile
from pathlib import Path

import pytest

from src.jina_rag_pipeline.ingestion import (
    Chunk,
    Document,
    DocumentProcessor,
    FixedSizeChunker,
    LoaderFactory,
    MarkdownLoader,
    SentenceChunker,
    SlidingWindowChunker,
    TextLoader,
)


class TestDocumentLoaders:
    def test_text_loader(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_content = "This is a test document."
        test_file.write_text(test_content)
        
        loader = TextLoader()
        assert loader.supports(test_file)
        
        doc = loader.load(test_file)
        assert doc.content == test_content
        assert doc.source == str(test_file)
    
    def test_markdown_loader(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.md"
        test_content = "# Header\n\nThis is markdown."
        test_file.write_text(test_content)
        
        loader = MarkdownLoader()
        assert loader.supports(test_file)
        
        doc = loader.load(test_file)
        assert doc.content == test_content
        assert doc.metadata["format"] == "markdown"
    
    def test_loader_factory(self, tmp_path: Path) -> None:
        factory = LoaderFactory()
        
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Text content")
        
        loader = factory.get_loader(txt_file)
        assert loader is not None
        assert isinstance(loader, TextLoader)
        
        doc = factory.load(txt_file)
        assert doc.content == "Text content"
    
    def test_loader_factory_unsupported(self, tmp_path: Path) -> None:
        factory = LoaderFactory()
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("content")
        
        loader = factory.get_loader(unsupported_file)
        assert loader is None
        
        with pytest.raises(ValueError):
            factory.load(unsupported_file)


class TestChunking:
    def test_fixed_size_chunker(self) -> None:
        doc = Document(content="a" * 1000, source="test")
        chunker = FixedSizeChunker(chunk_size=100, overlap=10)
        
        chunks = chunker.chunk(doc)
        
        assert len(chunks) > 0
        assert chunks[0].content == "a" * 100
        assert chunks[0].metadata["chunking_strategy"] == "fixed_size"
        assert chunks[0].start_index == 0
        assert chunks[0].end_index == 100
    
    def test_fixed_size_chunker_no_overlap(self) -> None:
        doc = Document(content="a" * 200, source="test")
        chunker = FixedSizeChunker(chunk_size=100, overlap=0)
        
        chunks = chunker.chunk(doc)
        
        assert len(chunks) == 2
        assert chunks[0].end_index == 100
        assert chunks[1].start_index == 100
    
    def test_fixed_size_chunker_validation(self) -> None:
        with pytest.raises(ValueError):
            FixedSizeChunker(chunk_size=0)
        
        with pytest.raises(ValueError):
            FixedSizeChunker(chunk_size=100, overlap=-1)
        
        with pytest.raises(ValueError):
            FixedSizeChunker(chunk_size=100, overlap=100)
    
    def test_sentence_chunker(self) -> None:
        doc = Document(
            content="First sentence. Second sentence. Third sentence.",
            source="test"
        )
        chunker = SentenceChunker(max_chunk_size=30, overlap_sentences=1)
        
        chunks = chunker.chunk(doc)
        
        assert len(chunks) > 0
        assert chunks[0].metadata["chunking_strategy"] == "sentence"
        assert "sentence_count" in chunks[0].metadata
    
    def test_sliding_window_chunker(self) -> None:
        doc = Document(content="a" * 500, source="test")
        chunker = SlidingWindowChunker(window_size=100, step_size=50)
        
        chunks = chunker.chunk(doc)
        
        assert len(chunks) > 0
        assert chunks[0].content == "a" * 100
        assert chunks[1].start_index == 50
        assert chunks[0].metadata["chunking_strategy"] == "sliding_window"
    
    def test_sliding_window_validation(self) -> None:
        with pytest.raises(ValueError):
            SlidingWindowChunker(window_size=0, step_size=50)
        
        with pytest.raises(ValueError):
            SlidingWindowChunker(window_size=100, step_size=0)
        
        with pytest.raises(ValueError):
            SlidingWindowChunker(window_size=100, step_size=100)


class TestDocumentProcessor:
    def test_process_document(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("a" * 1000)
        
        processor = DocumentProcessor(
            chunking_strategy=FixedSizeChunker(chunk_size=100, overlap=10)
        )
        
        chunks = processor.process(test_file)
        
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)
    
    def test_fingerprinting(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        processor = DocumentProcessor()
        
        fp1 = processor.compute_fingerprint(test_file)
        fp2 = processor.compute_fingerprint(test_file)
        assert fp1 == fp2
        
        test_file.write_text("different content")
        fp3 = processor.compute_fingerprint(test_file)
        assert fp1 != fp3
    
    def test_incremental_processing(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("a" * 100)
        
        processor = DocumentProcessor(
            chunking_strategy=FixedSizeChunker(chunk_size=50, overlap=0)
        )
        
        chunks1 = processor.process(test_file, skip_if_processed=True)
        assert len(chunks1) > 0
        
        chunks2 = processor.process(test_file, skip_if_processed=True)
        assert len(chunks2) == 0
        
        chunks3 = processor.process(test_file, force_reprocess=True)
        assert len(chunks3) > 0
    
    def test_batch_processing(self, tmp_path: Path) -> None:
        files = []
        for i in range(3):
            f = tmp_path / f"test_{i}.txt"
            f.write_text(f"content {i}")
            files.append(f)
        
        processor = DocumentProcessor(
            chunking_strategy=FixedSizeChunker(chunk_size=50, overlap=0)
        )
        
        results = processor.process_batch(files)
        
        assert len(results) == 3
        assert all(str(f) in results for f in files)
    
    def test_clear_cache(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        processor = DocumentProcessor()
        processor.process(test_file)
        
        assert len(processor.get_processed_files()) == 1
        
        processor.clear_processed_cache()
        assert len(processor.get_processed_files()) == 0


class TestDocument:
    def test_document_creation(self) -> None:
        doc = Document(content="test content", metadata={"key": "value"})
        assert doc.content == "test content"
        assert doc.metadata["key"] == "value"
    
    def test_document_with_source(self) -> None:
        doc = Document(content="test", source="/path/to/file.txt")
        assert doc.source == "/path/to/file.txt"
        assert doc.metadata["source"] == "/path/to/file.txt"
    
    def test_document_metadata_source_override(self) -> None:
        doc = Document(
            content="test",
            source="/path/to/file.txt",
            metadata={"source": "/different/path.txt"}
        )
        assert doc.metadata["source"] == "/different/path.txt"
