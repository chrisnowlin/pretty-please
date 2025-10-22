"""Tests for multimodal processing functionality."""

import tempfile
from pathlib import Path
from PIL import Image
import numpy as np
import pytest

from src.jina_rag_pipeline.multimodal import (
    ImageProcessor,
    VisualDocumentProcessor,
    CrossModalSearch
)


class TestImageProcessor:
    """Test image processing functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create image processor instance."""
        return ImageProcessor()
    
    @pytest.fixture
    def test_image(self):
        """Create a test image."""
        return Image.new('RGB', (300, 200), color='red')
    
    def test_image_loading(self, processor):
        """Test image loading from file."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            # Create and save test image
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(tmp.name)
            
            # Load image
            loaded = processor.load_image(tmp.name)
            assert loaded is not None
            assert loaded.size == (100, 100)
            
            # Clean up
            Path(tmp.name).unlink()
    
    def test_image_from_bytes(self, processor, test_image):
        """Test loading image from bytes."""
        # Convert image to bytes
        import io
        buffer = io.BytesIO()
        test_image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        # Load from bytes
        loaded = processor.load_from_bytes(image_bytes)
        assert loaded is not None
        assert loaded.size == test_image.size
    
    def test_image_from_base64(self, processor, test_image):
        """Test loading image from base64."""
        import base64
        import io
        
        # Convert to base64
        buffer = io.BytesIO()
        test_image.save(buffer, format='PNG')
        base64_str = base64.b64encode(buffer.getvalue()).decode()
        
        # Load from base64
        loaded = processor.load_from_base64(base64_str)
        assert loaded is not None
        assert loaded.size == test_image.size
    
    def test_preprocessing(self, processor, test_image):
        """Test image preprocessing."""
        tensor = processor.preprocess(test_image)
        
        assert tensor is not None
        assert tensor.shape[0] == 3  # RGB channels
        assert tensor.shape[1] == processor.target_size[0]
        assert tensor.shape[2] == processor.target_size[1]
    
    def test_batch_preprocessing(self, processor):
        """Test batch image preprocessing."""
        images = [
            Image.new('RGB', (100, 100), color='red'),
            Image.new('RGB', (200, 200), color='green'),
            Image.new('RGB', (150, 150), color='blue'),
        ]
        
        batch_tensor = processor.batch_preprocess(images)
        assert batch_tensor.shape[0] == 3  # Batch size
        assert batch_tensor.shape[1] == 3  # Channels
    
    def test_image_validation(self, processor):
        """Test image validation."""
        # Valid image
        valid_img = Image.new('RGB', (100, 100))
        assert processor.validate_image(valid_img) is True
        
        # Too small
        small_img = Image.new('RGB', (5, 5))
        assert processor.validate_image(small_img) is False
        
        # None image
        assert processor.validate_image(None) is False
    
    def test_patch_extraction(self, processor):
        """Test patch extraction from image."""
        large_img = Image.new('RGB', (500, 500), color='white')
        
        patches = processor.extract_patches(large_img, patch_size=100, stride=100)
        
        assert len(patches) > 0
        assert all(p.size == (100, 100) for p in patches)
    
    def test_image_stats(self, processor, test_image):
        """Test image statistics extraction."""
        stats = processor.get_image_stats(test_image)
        
        assert 'width' in stats
        assert 'height' in stats
        assert 'pixels' in stats
        assert 'aspect_ratio' in stats
        assert stats['width'] == 300
        assert stats['height'] == 200


class TestVisualDocumentProcessor:
    """Test visual document processing."""
    
    @pytest.fixture
    def processor(self):
        """Create visual document processor."""
        return VisualDocumentProcessor()
    
    def test_region_detection(self, processor):
        """Test region detection in image."""
        # Create image with distinct regions
        img = Image.new('RGB', (400, 400), color='white')
        
        regions = processor.detect_regions(img)
        assert isinstance(regions, list)
        
        # Each region should have required fields
        for region in regions:
            assert 'bbox' in region
            assert 'type' in region
            assert 'confidence' in region
    
    def test_region_feature_extraction(self, processor):
        """Test feature extraction from regions."""
        img = Image.new('RGB', (400, 400), color='white')
        
        # Create mock regions
        regions = [
            {'bbox': [0, 0, 100, 100], 'type': 'text'},
            {'bbox': [100, 100, 200, 200], 'type': 'image'},
        ]
        
        regions_with_features = processor.extract_region_features(img, regions)
        
        for region in regions_with_features:
            assert 'features' in region
            assert 'size' in region['features']
            assert 'position' in region['features']
            assert 'relative_position' in region['features']
            assert 'image' in region
    
    def test_layout_description(self, processor):
        """Test layout description generation."""
        regions = [
            {'type': 'text', 'features': {'relative_position': (0.2, 0.2)}},
            {'type': 'image', 'features': {'relative_position': (0.5, 0.5)}},
            {'type': 'text', 'features': {'relative_position': (0.8, 0.8)}},
        ]
        
        description = processor.generate_layout_description(regions, (800, 600))
        
        assert isinstance(description, str)
        assert 'Document layout' in description
        assert '2 text' in description
        assert '1 visual' in description
    
    def test_document_processing(self, processor):
        """Test end-to-end document processing."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            # Create test image document
            img = Image.new('RGB', (400, 600), color='white')
            img.save(tmp.name)
            
            # Process document
            result = processor.process_document(tmp.name)
            
            assert 'path' in result
            assert 'type' in result
            assert 'num_pages' in result
            assert 'pages' in result
            assert len(result['pages']) == 1
            
            # Check page data
            page = result['pages'][0]
            assert 'page_number' in page
            assert 'size' in page
            assert 'regions' in page
            assert 'layout_description' in page
            
            # Clean up
            Path(tmp.name).unlink()


class TestCrossModalSearch:
    """Test cross-modal search functionality."""
    
    @pytest.fixture
    def mock_embedder(self):
        """Create mock embedder."""
        class MockEmbedder:
            def encode_text(self, text, **kwargs):
                # Return deterministic embedding based on text length
                return np.random.randn(768).astype(np.float32)
            
            def encode_image(self, image, **kwargs):
                # Return deterministic embedding
                return np.random.randn(768).astype(np.float32)
        
        return MockEmbedder()
    
    @pytest.fixture
    def mock_storage(self):
        """Create mock storage."""
        class MockStorage:
            def __init__(self):
                self.data = []
            
            def add_embeddings(self, collection_name, embeddings, ids, metadatas, documents):
                for i in range(len(embeddings)):
                    self.data.append({
                        'embedding': embeddings[i],
                        'text': documents[i],
                        'metadata': metadatas[i],
                        'id': ids[i]
                    })
            
            def similarity_search(self, collection_name, query_embedding, top_k, metadata_filter=None):
                # Return mock results
                results = []
                for item in self.data:
                    if metadata_filter:
                        # Simple filter check
                        if 'content_type' in metadata_filter:
                            if item['metadata'].get('content_type') != metadata_filter['content_type']:
                                continue
                    
                    results.append({
                        'id': item['id'],
                        'text': item['text'],
                        'metadata': item['metadata'],
                        'distance': np.random.random()
                    })
                
                return results[:top_k]
        
        return MockStorage()
    
    def test_text_to_image_search(self, mock_embedder, mock_storage):
        """Test text-to-image search."""
        search = CrossModalSearch(mock_embedder, mock_storage)
        
        # Index some images
        search.index_multimodal_document(
            'doc1',
            image_content='test.jpg',
            metadata={'title': 'Test Image'}
        )
        
        # Search
        results = search.search_text_to_image('find images', n_results=5)
        
        assert isinstance(results, list)
    
    def test_image_to_text_search(self, mock_embedder, mock_storage):
        """Test image-to-text search."""
        search = CrossModalSearch(mock_embedder, mock_storage)
        
        # Index some text
        search.index_multimodal_document(
            'doc1',
            text_content='This is a test document',
            metadata={'title': 'Test Doc'}
        )
        
        # Search with image
        test_img = Image.new('RGB', (100, 100))
        results = search.search_image_to_text(test_img, n_results=5)
        
        assert isinstance(results, list)
    
    def test_image_to_image_search(self, mock_embedder, mock_storage):
        """Test image-to-image similarity search."""
        search = CrossModalSearch(mock_embedder, mock_storage)
        
        # Index multiple images
        for i in range(3):
            search.index_multimodal_document(
                f'doc{i}',
                image_content=f'image{i}.jpg',
                metadata={'index': i}
            )
        
        # Search
        test_img = Image.new('RGB', (100, 100))
        results = search.search_image_to_image(test_img, n_results=2)
        
        assert isinstance(results, list)
    
    def test_unified_search(self, mock_embedder, mock_storage):
        """Test unified search across content types."""
        search = CrossModalSearch(mock_embedder, mock_storage)
        
        # Index mixed content
        search.index_multimodal_document(
            'doc1',
            text_content='Text content',
            image_content='image.jpg',
            metadata={'type': 'mixed'}
        )
        
        # Text query
        text_results = search.unified_search('search query', n_results=10)
        assert isinstance(text_results, list)
        
        # Image query
        img = Image.new('RGB', (100, 100))
        img_results = search.unified_search(img, n_results=10)
        assert isinstance(img_results, list)
    
    def test_multimodal_indexing(self, mock_embedder, mock_storage):
        """Test indexing documents with both text and images."""
        search = CrossModalSearch(mock_embedder, mock_storage)
        
        # Index document with both text and image
        search.index_multimodal_document(
            'doc1',
            text_content='Document text',
            image_content='document.jpg',
            metadata={'author': 'Test'}
        )
        
        # Check storage
        assert len(mock_storage.data) == 2  # One for text, one for image
        
        text_item = next((d for d in mock_storage.data if d['id'] == 'doc1_text'), None)
        assert text_item is not None
        assert text_item['metadata']['content_type'] == 'text'
        
        image_item = next((d for d in mock_storage.data if d['id'] == 'doc1_image'), None)
        assert image_item is not None
        assert image_item['metadata']['content_type'] == 'image'
    
    def test_result_reranking(self, mock_embedder, mock_storage):
        """Test result reranking."""
        search = CrossModalSearch(mock_embedder, mock_storage)
        
        # Mock results
        results = [
            {'text': 'Result 1', 'distance': 0.8, 'metadata': {'content_type': 'text'}},
            {'text': 'Result 2', 'distance': 0.5, 'metadata': {'content_type': 'image'}},
            {'text': 'Result 3', 'distance': 0.6, 'metadata': {'content_type': 'text'}},
        ]
        
        # Rerank
        reranked = search.rerank_results(results, 'query text')
        
        assert isinstance(reranked, list)
        assert len(reranked) == len(results)
        assert all('cross_modal_score' in r for r in reranked)