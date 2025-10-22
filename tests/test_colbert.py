"""Tests for ColBERT-style multi-vector retrieval."""

import numpy as np
import pytest

from src.jina_rag_pipeline.multimodal.colbert import ColBERTRetriever, OptimizedMultiVectorSearch


class MockMultiVectorEmbedder:
    """Mock embedder with multi-vector support."""
    
    def encode_text(self, text, **kwargs):
        """Mock multi-vector encoding."""
        return_multivector = kwargs.get('return_multivector', False)
        prompt_name = kwargs.get('prompt_name', 'query')
        
        if return_multivector:
            # Return multiple vectors (one per "token")
            num_tokens = min(len(text.split()), 10)
            embeddings = np.random.randn(num_tokens, 768).astype(np.float32)
            
            # Make query and passage embeddings slightly different
            if prompt_name == 'query':
                embeddings *= 0.9
            return embeddings
        else:
            # Return single vector
            return np.random.randn(768).astype(np.float32)


class MockStorage:
    """Mock storage for testing."""
    
    def __init__(self):
        self.documents = []
        
    def add(self, embeddings, texts, metadata, ids, collection_name):
        """Add documents to storage."""
        for i in range(len(embeddings)):
            self.documents.append({
                'id': ids[i],
                'embedding': embeddings[i],
                'text': texts[i],
                'metadata': metadata[i] if i < len(metadata) else {}
            })
    
    def search(self, query_embedding, collection_name, n_results, metadata_filter=None):
        """Search for similar documents."""
        results = []
        
        for doc in self.documents:
            # Simple cosine similarity
            similarity = np.dot(query_embedding, doc['embedding']) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc['embedding'])
            )
            
            results.append({
                'id': doc['id'],
                'text': doc['text'],
                'metadata': doc['metadata'],
                'distance': 1 - similarity  # Convert to distance
            })
        
        # Sort by distance
        results.sort(key=lambda x: x['distance'])
        return results[:n_results]


class TestColBERTRetriever:
    """Test ColBERT retriever functionality."""
    
    @pytest.fixture
    def retriever(self):
        """Create retriever with mock components."""
        embedder = MockMultiVectorEmbedder()
        storage = MockStorage()
        return ColBERTRetriever(embedder, storage)
    
    def test_query_multivector_encoding(self, retriever):
        """Test query multi-vector encoding."""
        query = "What is machine learning?"
        
        embeddings = retriever.encode_query_multivector(query)
        
        assert isinstance(embeddings, np.ndarray)
        assert len(embeddings.shape) == 2  # (num_tokens, embedding_dim)
        assert embeddings.shape[1] == 768  # Embedding dimension
        assert embeddings.shape[0] > 0  # At least one token
    
    def test_document_multivector_encoding(self, retriever):
        """Test document multi-vector encoding."""
        document = "Machine learning is a subset of artificial intelligence."
        
        embeddings = retriever.encode_document_multivector(document)
        
        assert isinstance(embeddings, np.ndarray)
        assert len(embeddings.shape) == 2
        assert embeddings.shape[1] == 768
        assert embeddings.shape[0] > 0
    
    def test_late_interaction_scoring(self, retriever):
        """Test late interaction score calculation."""
        # Create mock query and document embeddings
        query_embeddings = np.random.randn(5, 768).astype(np.float32)
        doc_embeddings = np.random.randn(10, 768).astype(np.float32)
        
        # Test MaxSim scoring
        score_maxsim = retriever.late_interaction_score(
            query_embeddings, doc_embeddings, use_max_sim=True
        )
        assert isinstance(score_maxsim, float)
        
        # Test average scoring
        score_avg = retriever.late_interaction_score(
            query_embeddings, doc_embeddings, use_max_sim=False
        )
        assert isinstance(score_avg, float)
        
        # Scores should be different
        assert score_maxsim != score_avg
    
    def test_search_with_late_interaction(self, retriever):
        """Test end-to-end search with late interaction."""
        # Index some documents
        documents = [
            "Machine learning is fascinating.",
            "Deep learning uses neural networks.",
            "Natural language processing is complex."
        ]
        
        retriever.index_with_multivector(documents, collection="test")
        
        # Search
        results = retriever.search_with_late_interaction(
            "What is deep learning?",
            collection="test",
            n_results=2,
            initial_candidates=3
        )
        
        assert len(results) <= 2
        for result in results:
            assert 'colbert_score' in result
            assert 'original_distance' in result
            assert 'text' in result
    
    def test_multivector_indexing(self, retriever):
        """Test indexing with multi-vector representations."""
        documents = ["Doc 1", "Doc 2", "Doc 3"]
        ids = ["d1", "d2", "d3"]
        metadata = [{"type": "test"} for _ in documents]
        
        retriever.index_with_multivector(
            documents, ids=ids, metadata=metadata, collection="test"
        )
        
        # Check storage
        storage_docs = retriever.storage.documents
        assert len(storage_docs) == 3
        
        for doc in storage_docs:
            assert 'has_multivector' in doc['metadata']
            assert doc['metadata']['has_multivector'] is True
            assert 'num_vectors' in doc['metadata']
            assert doc['metadata']['num_vectors'] > 0


class TestOptimizedMultiVectorSearch:
    """Test optimized multi-vector search."""
    
    @pytest.fixture
    def optimized_search(self):
        """Create optimized search instance."""
        embedder = MockMultiVectorEmbedder()
        storage = MockStorage()
        retriever = ColBERTRetriever(embedder, storage)
        return OptimizedMultiVectorSearch(retriever)
    
    def test_caching(self, optimized_search):
        """Test multi-vector caching."""
        query = "Test query"
        
        # First encoding - not cached
        embeddings1 = optimized_search._get_cached_multivector(query, is_query=True)
        assert embeddings1 is None
        
        # Encode and cache
        embeddings = np.random.randn(5, 768).astype(np.float32)
        optimized_search._cache_multivector(query, embeddings, is_query=True)
        
        # Second encoding - should be cached
        embeddings2 = optimized_search._get_cached_multivector(query, is_query=True)
        assert embeddings2 is not None
        np.testing.assert_array_equal(embeddings2, embeddings)
    
    def test_batch_search(self, optimized_search):
        """Test batch search with late interaction."""
        # Index documents
        documents = ["Doc A", "Doc B", "Doc C"]
        optimized_search.retriever.index_with_multivector(documents)
        
        # Batch search
        queries = ["Query 1", "Query 2", "Query 3"]
        results = optimized_search.batch_late_interaction_search(
            queries, n_results=2, initial_candidates=3
        )
        
        assert len(results) == 3  # One result list per query
        for query_results in results:
            assert isinstance(query_results, list)
            assert len(query_results) <= 2
    
    def test_cache_limit(self, optimized_search):
        """Test cache size limiting."""
        optimized_search._max_cache_size = 5
        
        # Add more than max cache size
        for i in range(10):
            text = f"Text {i}"
            embeddings = np.random.randn(5, 768).astype(np.float32)
            optimized_search._cache_multivector(text, embeddings)
        
        # Cache should not exceed max size
        assert len(optimized_search._cache) <= 5
    
    def test_clear_cache(self, optimized_search):
        """Test cache clearing."""
        # Add to cache
        for i in range(3):
            text = f"Text {i}"
            embeddings = np.random.randn(5, 768).astype(np.float32)
            optimized_search._cache_multivector(text, embeddings)
        
        assert len(optimized_search._cache) == 3
        
        # Clear cache
        optimized_search.clear_cache()
        assert len(optimized_search._cache) == 0


class TestColBERTScoring:
    """Test ColBERT scoring algorithms."""
    
    def test_maxsim_scoring(self):
        """Test MaxSim scoring correctness."""
        retriever = ColBERTRetriever(MockMultiVectorEmbedder(), MockStorage())
        
        # Create controlled embeddings
        query_embeddings = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ], dtype=np.float32)
        
        doc_embeddings = np.array([
            [1, 0, 0],  # Perfect match for query token 1
            [0.5, 0.5, 0],  # Partial match
            [0, 0, 1],  # Perfect match for query token 3
        ], dtype=np.float32)
        
        score = retriever.late_interaction_score(
            query_embeddings, doc_embeddings, use_max_sim=True
        )
        
        # Score should be high due to perfect matches
        assert score > 0.5
    
    def test_average_scoring(self):
        """Test average scoring correctness."""
        retriever = ColBERTRetriever(MockMultiVectorEmbedder(), MockStorage())
        
        # Random embeddings
        query_embeddings = np.random.randn(3, 768).astype(np.float32)
        doc_embeddings = np.random.randn(5, 768).astype(np.float32)
        
        score = retriever.late_interaction_score(
            query_embeddings, doc_embeddings, use_max_sim=False
        )
        
        # Manual calculation for verification
        similarities = np.dot(query_embeddings, doc_embeddings.T)
        expected_score = np.mean(similarities)
        
        np.testing.assert_almost_equal(score, expected_score, decimal=5)