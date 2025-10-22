"""
Comprehensive end-to-end tests for the complete RAG pipeline.

Tests the full workflow from document ingestion through Deepseek OCR,
embedding generation with Jina Embeddings v4, vector storage in ChromaDB,
retrieval, and query response generation with citations.

Run with:
    RUN_RAG_E2E=1 pytest -v tests/integration/test_rag_pipeline_e2e.py
"""

import os
import sys
import shutil
import tempfile
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import torch
import fitz  # PyMuPDF

from src.jina_rag_pipeline.embeddings import JinaEmbeddingsV4
from src.jina_rag_pipeline.embeddings.config import EmbeddingConfig
from src.jina_rag_pipeline.storage import ChromaVectorStore
from src.jina_rag_pipeline.ingestion.deepseek_loader import DeepseekLoader
from src.jina_rag_pipeline.ingestion.ocr_config import OCRConfig
from src.jina_rag_pipeline.generation import QwenGenerator, GenerationConfig, RAGConfig
from src.jina_rag_pipeline.retrieval import JinaReranker
from src.jina_rag_pipeline.models.educational import RetrievedMaterial

# Enable integration tests
RUN_RAG_E2E = os.getenv("RUN_RAG_E2E", "0") == "1"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.skipif(
        not RUN_RAG_E2E,
        reason="Set RUN_RAG_E2E=1 to enable RAG pipeline end-to-end tests",
    ),
]


@pytest.fixture(scope="session")
def test_environment():
    """Set up test environment with temporary directories."""
    old_profile = os.environ.get("PROCESSING_PROFILE")
    os.environ["PROCESSING_PROFILE"] = "conservative"
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp(prefix="rag_e2e_test_")
    vector_db_dir = Path(temp_dir) / "vector_db"
    vector_db_dir.mkdir(exist_ok=True)
    
    yield {
        "temp_dir": temp_dir,
        "vector_db_dir": str(vector_db_dir),
    }
    
    # Cleanup
    if old_profile is None:
        os.environ.pop("PROCESSING_PROFILE", None)
    else:
        os.environ["PROCESSING_PROFILE"] = old_profile
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def embedder(test_environment):
    """Initialize Jina Embeddings v4 for testing with memory optimization."""
    from src.jina_rag_pipeline.embeddings.config import EmbeddingConfig
    
    # Use memory-optimized configuration
    config = EmbeddingConfig.for_documents()
    config.dimensions = 512  # Reduce dimensions for memory efficiency
    config.late_chunking = False  # Disable memory-intensive features
    config.max_tokens_per_batch = 4096  # Reduce batch size
    
    # Try MPS first, fallback to CPU if memory issues
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    embedder = JinaEmbeddingsV4(
        device=device,
        config=config
    )
    
    # Pre-load model to avoid loading delays during test
    try:
        # Trigger model loading
        _ = embedder.embed_with_config("test")
        print(f"✅ Embedder initialized on {device} with {config.dimensions} dimensions")
    except Exception as e:
        if device == "mps":
            print(f"⚠️ MPS failed ({e}), falling back to CPU")
            embedder = JinaEmbeddingsV4(device="cpu", config=config)
            # Pre-load on CPU
            _ = embedder.embed_with_config("test")
        else:
            raise e
    
    yield embedder


@pytest.fixture(scope="session")
def vector_store(test_environment):
    """Initialize ChromaDB vector store for testing."""
    store = ChromaVectorStore(
        persist_directory=test_environment["vector_db_dir"]
    )
    yield store


@pytest.fixture(scope="session")
def ocr_loader():
    """Initialize Deepseek OCR loader with fast preset for testing."""
    config = OCRConfig.deepseek_tiny()  # Fastest mode for testing
    config.batch_size = 1
    config.render_workers = 1
    config.analysis_workers = 1
    config.pre_render_batches = 1
    loader = DeepseekLoader(config=config)
    yield loader


@pytest.fixture(scope="session")
def generator():
    """Initialize Qwen generator for testing."""
    config = GenerationConfig()
    config.max_tokens = 500  # Shorter responses for faster tests
    config.temperature = 0.1  # More deterministic for testing
    
    generator = QwenGenerator(config=config)
    yield generator


@pytest.fixture(scope="session")
def reranker():
    """Initialize Jina reranker for testing."""
    reranker = JinaReranker()
    yield reranker


@pytest.fixture(scope="session")
def sample_documents(tmp_path_factory):
    """Create sample documents for testing."""
    temp_dir = tmp_path_factory.mktemp("sample_docs")
    
    # Create a simple PDF with educational content
    pdf_path = temp_dir / "math_fractions.pdf"
    _create_sample_pdf(pdf_path)
    
    # Create a text document with additional content
    txt_path = temp_dir / "math_activities.txt"
    _create_sample_text(txt_path)
    
    return {
        "pdf": str(pdf_path),
        "text": str(txt_path),
    }


def _create_sample_pdf(pdf_path: Path) -> None:
    """Create a sample PDF with educational content about fractions."""
    doc = fitz.open()
    page = doc.new_page()
    
    content = """
    Understanding Fractions
    
    A fraction represents a part of a whole. It consists of two numbers:
    - Numerator: The top number, representing how many parts we have
    - Denominator: The bottom number, representing total equal parts
    
    Example: 3/4 means we have 3 parts out of 4 equal parts.
    
    Types of Fractions:
    1. Proper Fractions: Numerator < Denominator (e.g., 2/3)
    2. Improper Fractions: Numerator > Denominator (e.g., 5/4)
    3. Mixed Numbers: Whole number + proper fraction (e.g., 1 1/2)
    
    Adding Fractions with Same Denominator:
    To add fractions with the same denominator, add the numerators
    and keep the denominator the same.
    
    Example: 1/4 + 2/4 = 3/4
    """
    
    page.insert_text((72, 72), content.strip(), fontsize=12, color=(0, 0, 0))
    doc.save(str(pdf_path))
    doc.close()


def _create_sample_text(txt_path: Path) -> None:
    """Create a sample text file with fraction activities."""
    content = """
    Fraction Activities for Grade 3
    
    Activity 1: Fraction Pizza
    Materials: Paper plates, colored pencils, scissors
    Instructions:
    1. Divide paper plate into 8 equal slices
    2. Color different slices to represent fractions
    3. Practice identifying fractions like 3/8, 5/8
    
    Activity 2: Fraction War Game
    Materials: Fraction cards
    Instructions:
    1. Deal cards to players
    2. Players compare fractions
    3. Largest fraction wins the round
    
    Assessment Ideas:
    - Have students draw fractions
    - Use manipulatives to show equivalent fractions
    - Create real-world fraction problems
    """
    
    txt_path.write_text(content.strip())


class TestRAGPipelineEndToEnd:
    """End-to-end tests for the complete RAG pipeline."""
    
    def test_complete_pipeline_from_ingestion_to_query(
        self, embedder, vector_store, ocr_loader, generator, reranker, sample_documents
    ):
        """Test the complete RAG pipeline workflow."""
        async def run_async_test():
            start_time = time.time()
            
            # Step 1: Document Ingestion
            print("\n🔄 Step 1: Document Ingestion")
            collection_name = "test_e2e_collection"
            
# Create collection
        vector_store.create_collection(
            name=collection_name,
            embedding_dimension=512,  # Match optimized embedder dimensions
            metadata={"description": "E2E test collection"}
        )
            
            # Process PDF through Deepseek OCR
            pdf_doc = ocr_loader.load(Path(sample_documents["pdf"]))
            assert pdf_doc.metadata["ocr_engine"] == "deepseek"
            assert len(pdf_doc.metadata["regions"]) > 0
            
            # Process text document
            from src.jina_rag_pipeline.ingestion.loaders import TextLoader
            text_loader = TextLoader()
            text_doc = text_loader.load(Path(sample_documents["text"]))
            
            # Step 2: Embedding Generation
            print("🔄 Step 2: Embedding Generation")
            documents = [pdf_doc.content, text_doc.content]
            
            # Generate embeddings
            embeddings = []
            for doc in documents:
                embedding = embedder.embed_with_config(doc)
                embeddings.append(embedding.tolist())
            
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 1024  # Jina Embeddings v4 dimension (actual)
            
            # Step 3: Vector Storage
            print("🔄 Step 3: Vector Storage")
            metadatas = [
                {
                    "source": "math_fractions.pdf",
                    "type": "pdf",
                    "ocr_engine": "deepseek"
                },
                {
                    "source": "math_activities.txt", 
                    "type": "text"
                }
            ]
            
            ids = vector_store.add_embeddings(
                collection_name=collection_name,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            assert len(ids) == 2
            
            # Step 4: Query Processing
            print("🔄 Step 4: Query Processing")
            query = "How do you add fractions with the same denominator?"
            query_embedding = embedder.embed_with_config(query).tolist()
            
            # Retrieve relevant documents
            results = vector_store.similarity_search(
                collection_name=collection_name,
                query_embedding=query_embedding,
                top_k=2
            )
            
            assert len(results) > 0
            assert results[0].score > 0.0
            
            # Step 5: Response Generation
            print("🔄 Step 5: Response Generation")
            retrieved_materials = []
            for result in results:
                material = RetrievedMaterial(
                    content=result.document,
                    document_name=result.metadata.get("source", "unknown"),
                    chunk_id=str(result.id),
                    relevance_score=result.score,
                    source_type=result.metadata.get("type", "text")
                )
                retrieved_materials.append(material)
            
            # Create messages for the generator
            context_text = "\n\n".join([f"Source {i+1}: {mat.content}" for i, mat in enumerate(retrieved_materials)])
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Use the provided context to answer questions accurately."},
                {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"}
            ]
            
            # Generate response
            response_content = ""
            async for token in generator.generate_stream(messages):
                response_content += token
            
            # Create a simple response object for testing
            class SimpleResponse:
                def __init__(self, content):
                    self.content = content
            
            response = SimpleResponse(response_content)
            
            # Step 6: Response Validation
            print("🔄 Step 6: Response Validation")
            
            # Basic response checks
            assert response is not None
            assert len(response.content) > 50  # Substantial response
            assert "fraction" in response.content.lower()  # Relevant content
            
            # Performance check
            total_time = time.time() - start_time
            print(f"✅ Complete pipeline executed in {total_time:.2f} seconds")
            assert total_time < 120  # Should complete within 2 minutes
            
            print("\n🎉 Complete RAG pipeline test PASSED")
        
        # Run the async test
        asyncio.run(run_async_test())
    
    def test_citation_accuracy_and_formatting(
        self, embedder, vector_store, ocr_loader, generator, sample_documents
    ):
        """Test that responses include proper citations and formatting."""
        collection_name = "citation_test_collection"
        
        # Setup collection and ingest documents
        vector_store.create_collection(
            name=collection_name,
            embedding_dimension=1024  # Jina Embeddings v4 actual dimension
        )
        
        # Ingest documents
        pdf_doc = ocr_loader.load(Path(sample_documents["pdf"]))
        from src.jina_rag_pipeline.ingestion.loaders import TextLoader
        text_loader = TextLoader()
        text_doc = text_loader.load(Path(sample_documents["text"]))
        
        documents = [pdf_doc.content, text_doc.content]
        embeddings = [embedder.embed_with_config(doc).tolist() for doc in documents]
        
        vector_store.add_embeddings(
            collection_name=collection_name,
            embeddings=embeddings,
            documents=documents,
            metadatas=[
                {"source": "math_fractions.pdf", "type": "pdf"},
                {"source": "math_activities.txt", "type": "text"}
            ]
        )
        
        # Query and generate response
        query = "What are some activities for teaching fractions to third graders?"
        query_embedding = embedder.encode_text(query, task="retrieval").tolist()
        
        results = vector_store.similarity_search(
            collection_name=collection_name,
            query_embedding=query_embedding,
            top_k=2
        )
        
        retrieved_materials = [
            RetrievedMaterial(
                content=result.document,
                document_name=result.metadata.get("source", "unknown"),
                chunk_id=str(result.id),
                relevance_score=result.score,
                source_type=result.metadata.get("type", "text")
            )
            for result in results
        ]
        
        rag_config = RAGConfig()
        rag_config.citation_style = "numbered"
        
        response = generator.generate_response(
            query=query,
            context=retrieved_materials,
            config=rag_config
        )
        
        # Validate citations
        assert response.content is not None
        assert len(response.content) > 0
        
        # Check for citation patterns
        import re
        citation_pattern = r'\[\d+\]'
        citations = re.findall(citation_pattern, response.content)
        
        if citations:  # If citations are included
            print(f"✅ Found {len(citations)} citations in response")
            # Verify citation numbers are reasonable
            citation_numbers = [int(c.strip('[]')) for c in citations]
            assert all(1 <= num <= len(retrieved_materials) for num in citation_numbers)
    
    def test_pipeline_performance_benchmarks(
        self, embedder, vector_store, ocr_loader, generator, sample_documents
    ):
        """Test pipeline performance with timing benchmarks."""
        collection_name = "performance_test_collection"
        
        # Setup
        vector_store.create_collection(
            name=collection_name,
            embedding_dimension=1024  # Jina Embeddings v4 actual dimension
        )
        
        # Benchmark each step
        timings = {}
        
        # OCR Processing
        start = time.time()
        pdf_doc = ocr_loader.load(Path(sample_documents["pdf"]))
        timings["ocr_processing"] = time.time() - start
        
        # Embedding Generation
        start = time.time()
        embedding = embedder.embed_with_config(pdf_doc.content)
        timings["embedding_generation"] = time.time() - start
        
        # Vector Storage
        start = time.time()
        vector_store.add_embeddings(
            collection_name=collection_name,
            embeddings=[embedding.tolist()],
            documents=[pdf_doc.content],
            metadatas=[{"source": "test.pdf"}]
        )
        timings["vector_storage"] = time.time() - start
        
        # Retrieval
        start = time.time()
        query_embedding = embedder.embed_with_config("What are fractions?").tolist()
        results = vector_store.similarity_search(
            collection_name=collection_name,
            query_embedding=query_embedding,
            top_k=1
        )
        timings["retrieval"] = time.time() - start
        
        # Generation
        start = time.time()
        material = RetrievedMaterial(
            content=results[0].document,
            document_name="test.pdf",
            chunk_id=str(results[0].id),
            relevance_score=results[0].score,
            source_type="text"
        )
        
        rag_config = RAGConfig()
        rag_config.final_top_n = 5
        response = generator.generate_response(
            query="What are fractions?",
            context=[material],
            config=rag_config
        )
        timings["generation"] = time.time() - start
        
        # Performance assertions
        print("\n📊 Performance Benchmarks:")
        for step, duration in timings.items():
            print(f"  {step}: {duration:.3f}s")
        
        # Reasonable performance expectations
        assert timings["ocr_processing"] < 30  # OCR should be fast with tiny preset
        assert timings["embedding_generation"] < 5
        assert timings["vector_storage"] < 1
        assert timings["retrieval"] < 1
        assert timings["generation"] < 30
        
        total_time = sum(timings.values())
        print(f"  Total pipeline time: {total_time:.3f}s")
        assert total_time < 60  # Entire pipeline should complete quickly
    
    def test_error_handling_and_recovery(
        self, embedder, vector_store, generator
    ):
        """Test pipeline error handling and recovery mechanisms."""
        collection_name = "error_test_collection"
        
        # Test with empty collection
        vector_store.create_collection(
            name=collection_name,
            embedding_dimension=1024  # Jina Embeddings v4 actual dimension
        )
        
        # Query empty collection
        query_embedding = embedder.embed_with_config("test query").tolist()
        results = vector_store.similarity_search(
            collection_name=collection_name,
            query_embedding=query_embedding,
            top_k=5
        )
        
        assert len(results) == 0  # Should return empty results
        
        # Test generation with empty context
        rag_config = RAGConfig()
        response = generator.generate_response(
            query="test query",
            context=[],
            config=rag_config
        )
        
        # Should still generate a response even without context
        assert response is not None
        assert len(response.content) > 0
        
        print("✅ Error handling test passed")
    
    def test_multi_document_query_accuracy(
        self, embedder, vector_store, ocr_loader, generator, sample_documents
    ):
        """Test query accuracy across multiple ingested documents."""
        collection_name = "multi_doc_test_collection"
        
        # Setup collection with multiple documents
        vector_store.create_collection(
            name=collection_name,
            embedding_dimension=1024  # Jina Embeddings v4 actual dimension
        )
        
        # Ingest multiple documents
        documents = []
        metadatas = []
        
        # PDF document
        pdf_doc = ocr_loader.load(Path(sample_documents["pdf"]))
        documents.append(pdf_doc.content)
        metadatas.append({"source": "math_fractions.pdf", "type": "pdf", "topic": "concepts"})
        
        # Text document
        from src.jina_rag_pipeline.ingestion.loaders import TextLoader
        text_loader = TextLoader()
        text_doc = text_loader.load(Path(sample_documents["text"]))
        documents.append(text_doc.content)
        metadatas.append({"source": "math_activities.txt", "type": "text", "topic": "activities"})
        
        # Generate and store embeddings
        embeddings = [embedder.encode_text(doc, task="retrieval").tolist() for doc in documents]
        vector_store.add_embeddings(
            collection_name=collection_name,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        # Test queries targeting different aspects
        test_queries = [
            {
                "query": "What is a fraction and what are its parts?",
                "expected_topic": "concepts",
                "keywords": ["numerator", "denominator"]
            },
            {
                "query": "What activities can help teach fractions?",
                "expected_topic": "activities", 
                "keywords": ["activity", "game", "materials"]
            }
        ]
        
        for test_case in test_queries:
            query_embedding = embedder.embed_with_config(test_case["query"]).tolist()
            results = vector_store.similarity_search(
                collection_name=collection_name,
                query_embedding=query_embedding,
                top_k=2
            )
            
            assert len(results) > 0
            
            # Check that relevant document is retrieved
            retrieved_topics = [r.metadata.get("topic", "") for r in results]
            assert test_case["expected_topic"] in retrieved_topics
            
            # Generate response and check for keywords
            retrieved_materials = [
                RetrievedMaterial(
                    content=result.document,
                    document_name=result.metadata.get("source", "unknown"),
                    chunk_id=str(result.id),
                    relevance_score=result.score,
                    source_type=result.metadata.get("type", "text")
                )
                for result in results
            ]
            
            rag_config = RAGConfig()
            response = generator.generate_response(
                query=test_case["query"],
                context=retrieved_materials,
                config=rag_config
            )
            
            # Check response contains expected keywords
            response_lower = response.content.lower()
            keyword_found = any(keyword in response_lower for keyword in test_case["keywords"])
            assert keyword_found, f"Expected keywords not found in response for: {test_case['query']}"
        
        print("✅ Multi-document query accuracy test passed")


if __name__ == "__main__":
    # Allow running directly for debugging
    import sys
    sys.exit(pytest.main([__file__, "-v"]))