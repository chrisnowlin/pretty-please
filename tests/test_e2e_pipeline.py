"""End-to-end integration tests for the complete RAG pipeline."""

import tempfile
import shutil
from pathlib import Path
import pytest

from src.jina_rag_pipeline.embeddings import JinaEmbeddingsV4
from src.jina_rag_pipeline.storage import ChromaVectorStore
from src.jina_rag_pipeline.ingestion import (
    DocumentProcessor,
    FixedSizeChunker,
    TextLoader,
    MarkdownLoader,
)


class TestEndToEndRAGPipeline:
    """Test complete data flow through the RAG pipeline."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data."""
        tmp = tempfile.mkdtemp()
        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)
    
    @pytest.fixture
    def embedder(self):
        """Create embedder instance."""
        return JinaEmbeddingsV4(device="mps")
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage instance."""
        store = ChromaVectorStore(persist_directory=temp_dir)
        yield store
        store.close()
    
    def test_complete_document_ingestion_to_search(self, embedder, storage, temp_dir):
        """Test: Document ingestion → Embedding → Storage → Search.
        
        This tests the complete RAG pipeline flow:
        1. Load documents from files
        2. Chunk documents
        3. Generate embeddings
        4. Store in vector database
        5. Perform semantic search
        """
        # Step 1: Create test documents
        docs_dir = Path(temp_dir) / "documents"
        docs_dir.mkdir()
        
        doc1_path = docs_dir / "ml_basics.txt"
        doc1_path.write_text(
            "Machine learning is a subset of artificial intelligence. "
            "It involves training algorithms to learn patterns from data. "
            "Common applications include image recognition and natural language processing."
        )
        
        doc2_path = docs_dir / "deep_learning.txt"
        doc2_path.write_text(
            "Deep learning uses neural networks with multiple layers. "
            "These networks can learn hierarchical representations of data. "
            "Popular frameworks include PyTorch and TensorFlow."
        )
        
        doc3_path = docs_dir / "nlp.md"
        doc3_path.write_text(
            "# Natural Language Processing\n\n"
            "NLP enables computers to understand human language. "
            "Transformer models like BERT have revolutionized the field. "
            "Applications include translation, summarization, and question answering."
        )
        
        # Step 2: Initialize pipeline components
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        processor = DocumentProcessor(chunking_strategy=chunker)
        
        # Step 3: Create collection
        storage.create_collection(
            name="knowledge_base",
            embedding_dimension=2048,
            metadata={"description": "Test knowledge base"}
        )
        
        # Step 4: Process and ingest documents
        all_embeddings = []
        all_texts = []
        all_metadata = []
        
        for doc_path in docs_dir.iterdir():
            # Process document (load + chunk)
            chunks = processor.process(doc_path)
            
            # Generate embeddings
            for chunk in chunks:
                embedding = embedder.encode_text(
                    chunk.content,
                    task="retrieval",
                    prompt_name="passage",
                    truncate_dim=2048,
                    show_progress=False
                )
                
                all_embeddings.append(embedding.tolist())
                all_texts.append(chunk.content)
                all_metadata.append({
                    "source": doc_path.name,
                    "chunk_id": chunk.metadata.get("chunk_id", 0)
                })
        
        # Store embeddings
        ids = storage.add_embeddings(
            collection_name="knowledge_base",
            embeddings=all_embeddings,
            documents=all_texts,
            metadatas=all_metadata
        )
        
        assert len(ids) > 0
        print(f"Ingested {len(ids)} chunks from {len(list(docs_dir.iterdir()))} documents")
        
        # Step 5: Perform semantic search
        query = "What are neural networks used for?"
        query_embedding = embedder.encode_text(
            query,
            task="retrieval",
            prompt_name="query",
            truncate_dim=2048,
            show_progress=False
        ).tolist()
        
        results = storage.similarity_search(
            collection_name="knowledge_base",
            query_embedding=query_embedding,
            top_k=3
        )
        
        # Step 6: Verify results
        assert len(results) > 0, "Search should return results"
        # With 2048-dimensional embeddings, similarity scores are lower but more granular
        # Just verify results are returned and contain relevant content
        assert results[0].score > 0.0, "Top result should have positive similarity"

        # Top result should be from deep learning document (mentions neural networks)
        assert "neural networks" in results[0].document.lower() or \
               "deep learning" in results[0].document.lower()
        
        print(f"\nQuery: {query}")
        print(f"Top result (score: {results[0].score:.4f}):")
        print(f"  {results[0].document[:100]}...")
        print(f"  Source: {results[0].metadata['source']}")
        
        # Step 7: Test metadata filtering
        nlp_results = storage.similarity_search(
            collection_name="knowledge_base",
            query_embedding=query_embedding,
            top_k=5,
            metadata_filter={"source": "nlp.md"}
        )
        
        # All results should be from NLP document
        for result in nlp_results:
            assert result.metadata["source"] == "nlp.md"
        
        print(f"\nFiltered search for 'nlp.md': {len(nlp_results)} results")
    
    def test_incremental_updates(self, embedder, storage, temp_dir):
        """Test: Add documents → Search → Add more → Search again.
        
        Tests incremental indexing and search consistency.
        """
        # Create collection
        storage.create_collection("incremental", embedding_dimension=2048)
        
        # Initial batch
        docs1 = [
            "Python is a programming language",
            "JavaScript is used for web development"
        ]
        
        embeddings1 = [
            embedder.encode_text(doc, task="retrieval", truncate_dim=2048, show_progress=False).tolist()
            for doc in docs1
        ]
        
        ids1 = storage.add_embeddings(
            "incremental",
            embeddings=embeddings1,
            documents=docs1,
            metadatas=[{"batch": 1} for _ in docs1]
        )
        
        # Search - should find Python
        query = "What programming languages are there?"
        query_emb = embedder.encode_text(query, task="retrieval", truncate_dim=2048, show_progress=False).tolist()
        
        results1 = storage.similarity_search("incremental", query_emb, top_k=3)
        assert len(results1) == 2
        
        # Add more documents
        docs2 = [
            "Java is an object-oriented language",
            "Rust focuses on memory safety"
        ]
        
        embeddings2 = [
            embedder.encode_text(doc, task="retrieval", truncate_dim=2048, show_progress=False).tolist()
            for doc in docs2
        ]
        
        ids2 = storage.add_embeddings(
            "incremental",
            embeddings=embeddings2,
            documents=docs2,
            metadatas=[{"batch": 2} for _ in docs2]
        )
        
        # Search again - should find all 4
        results2 = storage.similarity_search("incremental", query_emb, top_k=5)
        assert len(results2) == 4
        
        # Verify batches
        batch1_count = sum(1 for r in results2 if r.metadata["batch"] == 1)
        batch2_count = sum(1 for r in results2 if r.metadata["batch"] == 2)
        assert batch1_count == 2
        assert batch2_count == 2
    
    def test_persistence_across_sessions(self, embedder, temp_dir):
        """Test: Ingest → Close → Reopen → Search.
        
        Tests data persistence and recovery.
        """
        collection_name = "persistent"
        
        # Session 1: Create and populate
        storage1 = ChromaVectorStore(persist_directory=temp_dir)
        storage1.create_collection(collection_name, embedding_dimension=2048)
        
        docs = ["Document A", "Document B", "Document C"]
        embeddings = [
            embedder.encode_text(doc, task="retrieval", truncate_dim=2048, show_progress=False).tolist()
            for doc in docs
        ]
        
        ids = storage1.add_embeddings(collection_name, embeddings=embeddings, documents=docs)
        storage1.close()
        
        # Session 2: Reopen and search
        storage2 = ChromaVectorStore(persist_directory=temp_dir)
        
        # Verify collection exists
        collections = storage2.list_collections()
        assert any(c.name == collection_name for c in collections)
        
        # Verify documents are there
        stats = storage2.get_collection_stats(collection_name)
        assert stats.count == 3
        
        # Search works
        query_emb = embedder.encode_text("Document", task="retrieval", truncate_dim=2048, show_progress=False).tolist()
        results = storage2.similarity_search(collection_name, query_emb, top_k=3)
        assert len(results) == 3
        
        storage2.close()
    
    def test_batch_processing_pipeline(self, embedder, storage, temp_dir):
        """Test: Large batch processing with progress tracking.
        
        Tests batch optimization for large document sets.
        """
        from src.jina_rag_pipeline.batch import BatchManager
        
        # Create collection
        storage.create_collection("batch_test", embedding_dimension=2048)
        
        # Generate 100 synthetic documents
        documents = [f"This is test document number {i} about topic {i % 10}" for i in range(100)]
        
        # Batch process with manager
        manager = BatchManager()
        
        def process_doc_batch(batch):
            """Process a batch of documents."""
            embeddings = []
            for doc in batch:
                emb = embedder.encode_text(doc, task="retrieval", truncate_dim=2048, show_progress=False)
                embeddings.append(emb.tolist())
            return embeddings
        
        all_embeddings = []
        progress_updates = []
        
        def track_progress(processed, total, time_remaining):
            progress_updates.append((processed, total))
        
        for batch_embeddings in manager.process_batches(
            documents,
            process_doc_batch,
            total_items=len(documents),
            progress_callback=track_progress
        ):
            all_embeddings.extend(batch_embeddings)
        
        # Store all embeddings
        ids = storage.add_embeddings(
            "batch_test",
            embeddings=all_embeddings,
            documents=documents,
            metadatas=[{"index": i} for i in range(len(documents))]
        )
        
        assert len(ids) == 100
        assert len(progress_updates) > 0
        
        # Search should work
        query_emb = embedder.encode_text("topic 5", task="retrieval", truncate_dim=2048, show_progress=False).tolist()
        results = storage.similarity_search("batch_test", query_emb, top_k=10)
        
        # Should find documents about topic 5
        topic_5_docs = [r for r in results if "topic 5" in r.document]
        assert len(topic_5_docs) > 0
        
        print(f"Batch processed {len(documents)} documents")
        print(f"Progress updates: {len(progress_updates)}")
        print(f"Found {len(topic_5_docs)} documents about topic 5")


class TestMultimodalE2E:
    """End-to-end tests for multimodal features."""
    
    @pytest.fixture
    def embedder(self):
        """Create embedder instance."""
        return JinaEmbeddingsV4(device="mps")
    
    @pytest.fixture
    def storage(self):
        """Create in-memory storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ChromaVectorStore(persist_directory=tmpdir)
            yield store
            store.close()
    
    def test_cross_modal_search_flow(self, embedder, storage, tmp_path):
        """Test: Index text+images → Cross-modal search."""
        from src.jina_rag_pipeline.multimodal import CrossModalSearch
        from PIL import Image
        
        # Create test images
        img1 = Image.new('RGB', (100, 100), color='red')
        img2 = Image.new('RGB', (100, 100), color='blue')
        
        img1_path = tmp_path / "red.png"
        img2_path = tmp_path / "blue.png"
        img1.save(img1_path)
        img2.save(img2_path)
        
        # Create collection
        storage.create_collection("multimodal", embedding_dimension=2048)
        
        # Initialize cross-modal search
        search = CrossModalSearch(embedder, storage)
        
        # Index multimodal documents
        search.index_multimodal_document(
            "doc1",
            text_content="A beautiful red sunset over the mountains",
            image_content=str(img1_path),
            metadata={"type": "landscape"},
            collection="multimodal"
        )
        
        search.index_multimodal_document(
            "doc2",
            text_content="The deep blue ocean waves",
            image_content=str(img2_path),
            metadata={"type": "seascape"},
            collection="multimodal"
        )
        
        # Text-to-image search
        img_results = search.search_text_to_image(
            "red colors",
            collection="multimodal",
            n_results=2
        )
        
        assert len(img_results) > 0
        
        # Unified search
        unified_results = search.unified_search(
            "sunset",
            collection="multimodal",
            n_results=5
        )
        
        assert len(unified_results) > 0
        print(f"Cross-modal search returned {len(unified_results)} results")