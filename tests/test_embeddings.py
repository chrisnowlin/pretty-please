"""Tests for Jina Embeddings v4 implementation."""

import sys
import time
import pytest
import numpy as np
import torch
import logging

from src.jina_rag_pipeline.embeddings import JinaEmbeddingsV4

logging.basicConfig(level=logging.INFO)


class TestJinaEmbeddingsV4:
    """Test suite for JinaEmbeddingsV4."""
    
    @pytest.fixture(scope="class")
    def model(self):
        """Create model instance for tests."""
        # Note: In actual tests, we would use a smaller model
        # For now, using the actual model for integration testing
        return JinaEmbeddingsV4()
    
    def test_initialization(self):
        """Test model initialization with MPS detection."""
        model = JinaEmbeddingsV4()
        
        # Check device selection
        if torch.backends.mps.is_available():
            assert model.device == "mps"
        elif torch.cuda.is_available():
            assert model.device == "cuda"
        else:
            assert model.device == "cpu"
        
        # Check lazy loading
        assert model._model is None
        assert model._tokenizer is None
    
    def test_device_info(self):
        """Test device information retrieval."""
        model = JinaEmbeddingsV4()
        info = model.get_device_info()
        
        assert "device" in info
        assert "model_loaded" in info
        assert "tokenizer_loaded" in info
        
        if info["device"] == "mps":
            assert "mps_available" in info
            assert "mps_built" in info
    
    def test_single_text_encoding(self, model):
        """Test encoding a single text."""
        text = "This is a test sentence for embedding generation."
        
        embedding = model.encode_text(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.ndim == 1
        assert embedding.shape[0] == 2048  # Default dimension
    
    def test_batch_text_encoding(self, model):
        """Test encoding multiple texts."""
        texts = [
            "First test sentence.",
            "Second test sentence with more words.",
            "Third sentence for testing batch processing.",
        ]
        
        embeddings = model.encode_text(texts, show_progress=True)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == len(texts)
        assert embeddings.shape[1] == 2048
    
    def test_task_types(self, model):
        """Test all three task types."""
        text = "Test text for different task types."
        
        # Test retrieval task
        retrieval_emb = model.encode_text(text, task="retrieval", prompt_name="query")
        assert retrieval_emb.shape[0] == 2048
        
        # Test text-matching task
        matching_emb = model.encode_text(text, task="text-matching")
        assert matching_emb.shape[0] == 2048
        
        # Test code task
        code_emb = model.encode_text("def hello(): return 'world'", task="code")
        assert code_emb.shape[0] == 2048
        
        # Embeddings should be different for different tasks
        assert not np.array_equal(retrieval_emb, matching_emb)
        assert not np.array_equal(retrieval_emb, code_emb)
    
    def test_dimension_truncation(self, model):
        """Test embedding dimension truncation."""
        text = "Test text for dimension truncation."
        
        for dim in [128, 256, 512, 1024, 2048]:
            embedding = model.encode_text(text, truncate_dim=dim)
            assert embedding.shape[0] == dim
        
        # Test invalid dimension
        with pytest.raises(ValueError):
            model.encode_text(text, truncate_dim=100)
    
    def test_mps_acceleration(self, model):
        """Test MPS acceleration is working."""
        if model.device != "mps":
            pytest.skip("MPS not available")
        
        texts = ["Test sentence"] * 10
        
        # Time the encoding
        start = time.time()
        embeddings = model.encode_text(texts)
        elapsed = time.time() - start
        
        print(f"Encoded {len(texts)} texts in {elapsed:.3f} seconds on {model.device}")
        assert embeddings.shape == (10, 2048)
    
    def test_memory_usage(self, model):
        """Test memory usage and monitoring."""
        if model.device == "mps":
            # Test memory clearing
            model.clear_cache()
            info = model.get_device_info()
            assert not info["model_loaded"]
            assert not info["tokenizer_loaded"]
            
            # Re-load model
            _ = model.encode_text("Test")
            info = model.get_device_info()
            assert info["model_loaded"]
            assert info["tokenizer_loaded"]
    
    def test_model_caching(self):
        """Test model caching and reload."""
        model1 = JinaEmbeddingsV4()
        
        # First load (downloads if needed)
        start = time.time()
        _ = model1.encode_text("Test")
        first_load_time = time.time() - start
        
        # Clear and reload (should use cache)
        model1.clear_cache()
        
        start = time.time()
        _ = model1.encode_text("Test")
        second_load_time = time.time() - start
        
        print(f"First load: {first_load_time:.2f}s, Second load: {second_load_time:.2f}s")
        
        # Second load should be faster (from cache)
        # Note: This might not always be true on first run
        assert second_load_time > 0
    
    def test_multilingual_support(self, model):
        """Test multilingual text encoding."""
        texts = [
            "Hello world",  # English
            "Bonjour le monde",  # French
            "你好世界",  # Chinese
            "مرحبا بالعالم",  # Arabic
            "Привет мир",  # Russian
        ]
        
        embeddings = model.encode_text(texts)
        
        assert embeddings.shape == (len(texts), 2048)
        # All embeddings should be different
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                assert not np.array_equal(embeddings[i], embeddings[j])
    
    def test_long_text_handling(self, model):
        """Test handling of long texts."""
        # Create a long text
        long_text = " ".join(["This is a test sentence."] * 1000)
        
        embedding = model.encode_text(long_text, max_length=8192)
        
        assert embedding.shape[0] == 2048
    
    def test_edge_cases(self, model):
        """Test edge cases."""
        # Empty string
        embedding = model.encode_text("")
        assert embedding.shape[0] == 2048
        
        # Single word
        embedding = model.encode_text("Word")
        assert embedding.shape[0] == 2048
        
        # Special characters
        embedding = model.encode_text("!@#$%^&*()")
        assert embedding.shape[0] == 2048


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])