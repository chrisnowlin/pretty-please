"""
Unit tests for Deepseek-OCR integration components.

Tests:
- BoundingBox dataclass and methods
- DeepseekLayoutAnalyzer initialization
- OCRConfig Deepseek presets
"""

import pytest
from src.jina_rag_pipeline.ingestion.semantic_region import BoundingBox, SemanticRegion
from src.jina_rag_pipeline.ingestion.ocr_config import OCRConfig


class TestBoundingBox:
    """Test BoundingBox dataclass."""

    def test_valid_bbox_creation(self):
        """Test creating a valid bounding box."""
        bbox = BoundingBox(x_min=0.1, y_min=0.2, x_max=0.9, y_max=0.8)
        assert bbox.x_min == 0.1
        assert bbox.y_min == 0.2
        assert bbox.x_max == 0.9
        assert bbox.y_max == 0.8
        assert bbox.confidence is None

    def test_bbox_with_confidence(self):
        """Test bounding box with confidence score."""
        bbox = BoundingBox(x_min=0.1, y_min=0.2, x_max=0.9, y_max=0.8, confidence=0.95)
        assert bbox.confidence == 0.95

    def test_bbox_area(self):
        """Test area calculation."""
        bbox = BoundingBox(x_min=0.1, y_min=0.2, x_max=0.9, y_max=0.8)
        assert pytest.approx(bbox.area(), 0.001) == 0.48  # (0.9-0.1) * (0.8-0.2) = 0.48

    def test_bbox_width_height(self):
        """Test width and height calculations."""
        bbox = BoundingBox(x_min=0.1, y_min=0.2, x_max=0.9, y_max=0.8)
        assert pytest.approx(bbox.width(), 0.001) == 0.8
        assert pytest.approx(bbox.height(), 0.001) == 0.6

    def test_bbox_center(self):
        """Test center point calculation."""
        bbox = BoundingBox(x_min=0.0, y_min=0.0, x_max=1.0, y_max=1.0)
        center_x, center_y = bbox.center()
        assert pytest.approx(center_x, 0.001) == 0.5
        assert pytest.approx(center_y, 0.001) == 0.5

    def test_bbox_iou(self):
        """Test Intersection over Union calculation."""
        bbox1 = BoundingBox(x_min=0.0, y_min=0.0, x_max=0.5, y_max=0.5)
        bbox2 = BoundingBox(x_min=0.25, y_min=0.25, x_max=0.75, y_max=0.75)

        iou = bbox1.iou(bbox2)
        # Intersection: (0.25, 0.25) to (0.5, 0.5) = 0.0625
        # Union: 0.25 + 0.25 - 0.0625 = 0.4375
        # IoU: 0.0625 / 0.4375 = 0.142857
        assert pytest.approx(iou, 0.001) == 0.142857

    def test_bbox_iou_no_overlap(self):
        """Test IoU with non-overlapping boxes."""
        bbox1 = BoundingBox(x_min=0.0, y_min=0.0, x_max=0.3, y_max=0.3)
        bbox2 = BoundingBox(x_min=0.7, y_min=0.7, x_max=1.0, y_max=1.0)
        assert bbox1.iou(bbox2) == 0.0

    def test_bbox_contains(self):
        """Test containment check."""
        outer = BoundingBox(x_min=0.0, y_min=0.0, x_max=1.0, y_max=1.0)
        inner = BoundingBox(x_min=0.2, y_min=0.3, x_max=0.8, y_max=0.7)

        assert outer.contains(inner) is True
        assert inner.contains(outer) is False

    def test_bbox_overlaps(self):
        """Test overlap detection."""
        bbox1 = BoundingBox(x_min=0.0, y_min=0.0, x_max=0.5, y_max=0.5)
        bbox2 = BoundingBox(x_min=0.4, y_min=0.4, x_max=0.9, y_max=0.9)
        bbox3 = BoundingBox(x_min=0.6, y_min=0.6, x_max=1.0, y_max=1.0)

        assert bbox1.overlaps(bbox2) is True
        assert bbox1.overlaps(bbox3) is False

    def test_bbox_validation_x_range(self):
        """Test validation of x coordinates."""
        with pytest.raises(ValueError, match="x coordinates must be in"):
            BoundingBox(x_min=-0.1, y_min=0.0, x_max=0.5, y_max=0.5)

        with pytest.raises(ValueError, match="x coordinates must be in"):
            BoundingBox(x_min=0.0, y_min=0.0, x_max=1.5, y_max=0.5)

    def test_bbox_validation_y_range(self):
        """Test validation of y coordinates."""
        with pytest.raises(ValueError, match="y coordinates must be in"):
            BoundingBox(x_min=0.0, y_min=-0.1, x_max=0.5, y_max=0.5)

        with pytest.raises(ValueError, match="y coordinates must be in"):
            BoundingBox(x_min=0.0, y_min=0.0, x_max=0.5, y_max=1.5)

    def test_bbox_validation_min_max(self):
        """Test validation that min < max."""
        with pytest.raises(ValueError, match="x_min must be < x_max"):
            BoundingBox(x_min=0.8, y_min=0.0, x_max=0.2, y_max=0.5)

        with pytest.raises(ValueError, match="y_min must be < y_max"):
            BoundingBox(x_min=0.0, y_min=0.8, x_max=0.5, y_max=0.2)

    def test_bbox_validation_confidence(self):
        """Test validation of confidence score."""
        with pytest.raises(ValueError, match="confidence must be in"):
            BoundingBox(x_min=0.0, y_min=0.0, x_max=0.5, y_max=0.5, confidence=-0.1)

        with pytest.raises(ValueError, match="confidence must be in"):
            BoundingBox(x_min=0.0, y_min=0.0, x_max=0.5, y_max=0.5, confidence=1.5)

    def test_bbox_serialization(self):
        """Test to_dict and from_dict."""
        bbox = BoundingBox(x_min=0.1, y_min=0.2, x_max=0.9, y_max=0.8, confidence=0.95)
        bbox_dict = bbox.to_dict()

        assert bbox_dict == {
            'x_min': 0.1,
            'y_min': 0.2,
            'x_max': 0.9,
            'y_max': 0.8,
            'confidence': 0.95
        }

        bbox_restored = BoundingBox.from_dict(bbox_dict)
        assert bbox_restored.x_min == bbox.x_min
        assert bbox_restored.y_min == bbox.y_min
        assert bbox_restored.x_max == bbox.x_max
        assert bbox_restored.y_max == bbox.y_max
        assert bbox_restored.confidence == bbox.confidence


class TestSemanticRegionWithBbox:
    """Test SemanticRegion with bbox field."""

    def test_region_without_bbox(self):
        """Test creating region without bbox (backward compatibility)."""
        region = SemanticRegion(
            region_id="test_1",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="Test content",
            raw_markdown="Test content"
        )
        assert region.bbox is None

    def test_region_with_bbox(self):
        """Test creating region with bbox."""
        bbox = BoundingBox(x_min=0.1, y_min=0.2, x_max=0.9, y_max=0.8)
        region = SemanticRegion(
            region_id="test_1",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="Test content",
            raw_markdown="Test content",
            bbox=bbox
        )
        assert region.bbox is not None
        assert region.bbox.x_min == 0.1

    def test_region_serialization_with_bbox(self):
        """Test serializing region with bbox."""
        bbox = BoundingBox(x_min=0.1, y_min=0.2, x_max=0.9, y_max=0.8)
        region = SemanticRegion(
            region_id="test_1",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="Test content",
            raw_markdown="Test content",
            bbox=bbox
        )

        region_dict = region.to_dict()
        assert 'bbox' in region_dict
        assert region_dict['bbox']['x_min'] == 0.1

        # Test deserialization
        region_restored = SemanticRegion.from_dict(region_dict)
        assert region_restored.bbox is not None
        assert region_restored.bbox.x_min == 0.1


class TestOCRConfigDeepseekPresets:
    """Test Deepseek-specific OCRConfig presets."""

    def test_deepseek_tiny_preset(self):
        """Test TINY preset configuration."""
        config = OCRConfig.deepseek_tiny()
        assert config.resolution_mode == "tiny"
        assert config.enable_grounding is False  # Disabled for speed
        assert config.enable_compression is True
        assert config.use_vllm is False
        assert config.batch_size == 30

    def test_deepseek_small_preset(self):
        """Test SMALL preset configuration."""
        config = OCRConfig.deepseek_small()
        assert config.resolution_mode == "small"
        assert config.enable_grounding is True
        assert config.enable_compression is True
        assert config.use_vllm is False
        assert config.batch_size == 25

    def test_deepseek_balanced_preset(self):
        """Test BALANCED (BASE) preset configuration."""
        config = OCRConfig.deepseek_balanced()
        assert config.resolution_mode == "base"
        assert config.enable_grounding is True
        assert config.enable_compression is True
        assert config.use_vllm is False
        assert config.batch_size == 20

    def test_deepseek_high_quality_preset(self):
        """Test HIGH QUALITY (LARGE) preset configuration."""
        config = OCRConfig.deepseek_high_quality()
        assert config.resolution_mode == "large"
        assert config.enable_grounding is True
        assert config.enable_compression is True
        assert config.use_vllm is False
        assert config.batch_size == 15  # Smaller batches for quality

    def test_deepseek_gundam_preset(self):
        """Test GUNDAM preset configuration."""
        config = OCRConfig.deepseek_gundam()
        assert config.resolution_mode == "gundam"
        assert config.enable_grounding is True
        assert config.enable_compression is True
        assert config.use_vllm is False

    def test_deepseek_production_preset(self):
        """Test PRODUCTION preset with vLLM."""
        config = OCRConfig.deepseek_production()
        assert config.resolution_mode == "gundam"
        assert config.enable_grounding is True
        assert config.enable_compression is True
        assert config.use_vllm is True
        assert config.analysis_workers == 4  # Higher parallelism


class TestDeepseekLayoutAnalyzerInit:
    """Test DeepseekLayoutAnalyzer initialization (without model loading)."""

    def test_analyzer_init_defaults(self):
        """Test analyzer initialization with default settings."""
        # Note: This will not actually load the model
        # We're just testing the initialization logic
        try:
            from jina_rag_pipeline.ingestion.deepseek_layout import DeepseekLayoutAnalyzer

            # Mock minimal initialization (will raise if dependencies missing)
            # In actual use, the model would be lazy-loaded
            # For this test, we just verify the class can be imported
            assert DeepseekLayoutAnalyzer is not None
        except ImportError as e:
            pytest.skip(f"Deepseek dependencies not available: {e}")

    def test_resolution_mode_enum(self):
        """Test ResolutionMode enum."""
        try:
            from jina_rag_pipeline.ingestion.deepseek_layout import ResolutionMode

            assert ResolutionMode.TINY.value == "tiny"
            assert ResolutionMode.SMALL.value == "small"
            assert ResolutionMode.BASE.value == "base"
            assert ResolutionMode.LARGE.value == "large"
            assert ResolutionMode.GUNDAM.value == "gundam"
        except ImportError:
            pytest.skip("Deepseek module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
