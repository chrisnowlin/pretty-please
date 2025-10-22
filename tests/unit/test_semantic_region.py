"""Unit tests for SemanticRegion dataclass.

Tests cover:
- Basic instantiation with required fields
- Serialization/deserialization (dict and JSON)
- Path handling for image content
- All region types (text, table, image, equation, list, title)
- Type-specific field validation
- Default values
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from src.jina_rag_pipeline.ingestion.semantic_region import SemanticRegion


class TestBasicInstantiation:
    """Test basic creation of SemanticRegion instances."""

    def test_minimal_text_region(self):
        """Test creation with minimal required fields."""
        region = SemanticRegion(
            region_id="reg_001",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="Simple text content",
            raw_markdown="Simple text content"
        )

        assert region.region_id == "reg_001"
        assert region.region_type == "text"
        assert region.region_sequence == 0
        assert region.page_number == 1
        assert region.content == "Simple text content"
        assert region.raw_markdown == "Simple text content"
        assert region.model == "nanonets-ocr2-3b"  # default value
        assert region.semantic_tags == []  # default empty list
        assert region.extraction_timestamp is not None

    def test_text_region_with_semantic_tags(self):
        """Test text region with semantic metadata."""
        region = SemanticRegion(
            region_id="reg_002",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="Revenue increased 25% year-over-year",
            raw_markdown="Revenue increased 25% year-over-year",
            semantic_tags=["financial", "growth"]
        )

        assert region.region_type == "text"
        assert "financial" in region.semantic_tags
        assert "growth" in region.semantic_tags
        assert len(region.semantic_tags) == 2


class TestRegionTypes:
    """Test all supported region types."""

    def test_table_region(self):
        """Test table region with table-specific fields."""
        region = SemanticRegion(
            region_id="reg_003",
            region_type="table",
            region_sequence=1,
            page_number=1,
            content="Financial metrics table",
            raw_markdown="| Metric | Value |\n|--------|-------|\n| Revenue | $1M |",
            table_html="<table><tr><th>Metric</th><th>Value</th></tr><tr><td>Revenue</td><td>$1M</td></tr></table>",
            table_rows=2,
            table_cols=2
        )

        assert region.region_type == "table"
        assert region.table_rows == 2
        assert region.table_cols == 2
        assert region.table_html is not None
        assert "<table>" in region.table_html

    def test_image_region(self):
        """Test image region with image-specific fields."""
        region = SemanticRegion(
            region_id="reg_004",
            region_type="image",
            region_sequence=2,
            page_number=1,
            content=Path("./images/chart.png"),
            raw_markdown="![Bar chart showing revenue growth](./images/chart.png)",
            image_description="Bar chart showing revenue growth over 5 years",
            image_type="chart"
        )

        assert region.region_type == "image"
        assert isinstance(region.content, Path)
        assert region.image_type == "chart"
        assert region.image_description == "Bar chart showing revenue growth over 5 years"

    def test_equation_region(self):
        """Test equation region with equation-specific fields."""
        region = SemanticRegion(
            region_id="reg_005",
            region_type="equation",
            region_sequence=3,
            page_number=2,
            content="E = mc^2",
            raw_markdown="$$E = mc^2$$",
            equation_latex="E = mc^2",
            equation_type="display"
        )

        assert region.region_type == "equation"
        assert region.equation_latex == "E = mc^2"
        assert region.equation_type == "display"

    def test_list_region(self):
        """Test list region."""
        region = SemanticRegion(
            region_id="reg_006",
            region_type="list",
            region_sequence=4,
            page_number=2,
            content="1. First item\n2. Second item\n3. Third item",
            raw_markdown="1. First item\n2. Second item\n3. Third item",
            semantic_tags=["numbered_list"]
        )

        assert region.region_type == "list"
        assert "numbered_list" in region.semantic_tags

    def test_title_region(self):
        """Test title region with markdown level."""
        region = SemanticRegion(
            region_id="reg_007",
            region_type="title",
            region_sequence=0,
            page_number=1,
            content="Introduction to Machine Learning",
            raw_markdown="# Introduction to Machine Learning",
            markdown_level=1
        )

        assert region.region_type == "title"
        assert region.markdown_level == 1


class TestSerialization:
    """Test serialization and deserialization."""

    def test_to_dict_basic(self):
        """Test conversion to dictionary."""
        region = SemanticRegion(
            region_id="reg_008",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="Test content",
            raw_markdown="Test content"
        )

        data = region.to_dict()

        assert isinstance(data, dict)
        assert data["region_id"] == "reg_008"
        assert data["region_type"] == "text"
        assert data["content"] == "Test content"
        assert "extraction_timestamp" in data

    def test_to_dict_with_path(self):
        """Test dictionary conversion with Path content."""
        region = SemanticRegion(
            region_id="reg_009",
            region_type="image",
            region_sequence=0,
            page_number=1,
            content=Path("/path/to/image.png"),
            raw_markdown="![image](image.png)"
        )

        data = region.to_dict()

        # Path should be converted to string
        assert isinstance(data["content"], str)
        assert data["content"] == "/path/to/image.png"

    def test_from_dict_basic(self):
        """Test creation from dictionary."""
        data = {
            "region_id": "reg_010",
            "region_type": "text",
            "region_sequence": 0,
            "page_number": 1,
            "content": "Test content",
            "raw_markdown": "Test content",
            "semantic_tags": ["test"],
            "markdown_level": None,
            "table_html": None,
            "table_rows": None,
            "table_cols": None,
            "image_description": None,
            "image_type": None,
            "equation_latex": None,
            "equation_type": None,
            "extraction_timestamp": "2025-10-17T10:00:00",
            "model": "nanonets-ocr2-3b"
        }

        region = SemanticRegion.from_dict(data)

        assert region.region_id == "reg_010"
        assert region.region_type == "text"
        assert region.semantic_tags == ["test"]

    def test_from_dict_with_path(self):
        """Test creation from dictionary with path content."""
        data = {
            "region_id": "reg_011",
            "region_type": "image",
            "region_sequence": 0,
            "page_number": 1,
            "content": "/path/to/image.png",
            "raw_markdown": "![image](image.png)",
            "semantic_tags": [],
            "markdown_level": None,
            "table_html": None,
            "table_rows": None,
            "table_cols": None,
            "image_description": "Test image",
            "image_type": "photo",
            "equation_latex": None,
            "equation_type": None,
            "extraction_timestamp": "2025-10-17T10:00:00",
            "model": "nanonets-ocr2-3b"
        }

        region = SemanticRegion.from_dict(data)

        # String starting with / should be converted to Path
        assert isinstance(region.content, Path)
        assert str(region.content) == "/path/to/image.png"

    def test_dict_round_trip(self):
        """Test to_dict() -> from_dict() round trip."""
        original = SemanticRegion(
            region_id="reg_012",
            region_type="table",
            region_sequence=1,
            page_number=2,
            content="Table content",
            raw_markdown="| A | B |\n|---|---|",
            table_html="<table><tr><th>A</th><th>B</th></tr></table>",
            table_rows=1,
            table_cols=2,
            semantic_tags=["financial", "data"]
        )

        data = original.to_dict()
        restored = SemanticRegion.from_dict(data)

        assert restored.region_id == original.region_id
        assert restored.region_type == original.region_type
        assert restored.table_rows == original.table_rows
        assert restored.table_cols == original.table_cols
        assert restored.semantic_tags == original.semantic_tags

    def test_to_json(self):
        """Test JSON serialization."""
        region = SemanticRegion(
            region_id="reg_013",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="JSON test",
            raw_markdown="JSON test"
        )

        json_str = region.to_json()

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["region_id"] == "reg_013"
        assert data["content"] == "JSON test"

    def test_from_json(self):
        """Test JSON deserialization."""
        json_str = '''
        {
            "region_id": "reg_014",
            "region_type": "equation",
            "region_sequence": 0,
            "page_number": 1,
            "content": "x = y + z",
            "raw_markdown": "$x = y + z$",
            "semantic_tags": [],
            "markdown_level": null,
            "table_html": null,
            "table_rows": null,
            "table_cols": null,
            "image_description": null,
            "image_type": null,
            "equation_latex": "x = y + z",
            "equation_type": "inline",
            "extraction_timestamp": "2025-10-17T10:00:00",
            "model": "nanonets-ocr2-3b"
        }
        '''

        region = SemanticRegion.from_json(json_str)

        assert region.region_id == "reg_014"
        assert region.region_type == "equation"
        assert region.equation_latex == "x = y + z"
        assert region.equation_type == "inline"

    def test_json_round_trip(self):
        """Test to_json() -> from_json() round trip."""
        original = SemanticRegion(
            region_id="reg_015",
            region_type="image",
            region_sequence=2,
            page_number=1,
            content=Path("./images/diagram.png"),
            raw_markdown="![System architecture diagram](./images/diagram.png)",
            image_description="System architecture diagram showing microservices",
            image_type="diagram",
            semantic_tags=["technical", "architecture"]
        )

        json_str = original.to_json()
        restored = SemanticRegion.from_json(json_str)

        assert restored.region_id == original.region_id
        assert restored.image_type == original.image_type
        assert restored.image_description == original.image_description
        assert restored.semantic_tags == original.semantic_tags
        # Content will be a string after JSON round-trip (Path -> str -> Path)
        assert str(restored.content) == str(original.content)


class TestDefaultValues:
    """Test default value handling."""

    def test_default_semantic_tags(self):
        """Test default empty list for semantic_tags."""
        region = SemanticRegion(
            region_id="reg_016",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="Test",
            raw_markdown="Test"
        )

        assert region.semantic_tags == []
        assert isinstance(region.semantic_tags, list)

    def test_default_extraction_timestamp(self):
        """Test automatic timestamp generation."""
        region = SemanticRegion(
            region_id="reg_017",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="Test",
            raw_markdown="Test"
        )

        assert region.extraction_timestamp is not None
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(region.extraction_timestamp)

    def test_default_model(self):
        """Test default model value."""
        region = SemanticRegion(
            region_id="reg_018",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="Test",
            raw_markdown="Test"
        )

        assert region.model == "nanonets-ocr2-3b"


class TestPathHandling:
    """Test Path object handling for image content."""

    def test_path_object_content(self):
        """Test using Path object as content."""
        path = Path("/images/test.png")
        region = SemanticRegion(
            region_id="reg_019",
            region_type="image",
            region_sequence=0,
            page_number=1,
            content=path,
            raw_markdown="![test](test.png)"
        )

        assert isinstance(region.content, Path)
        assert region.content == path

    def test_relative_path_conversion(self):
        """Test relative path string to Path conversion."""
        data = {
            "region_id": "reg_020",
            "region_type": "image",
            "region_sequence": 0,
            "page_number": 1,
            "content": "./images/relative.png",
            "raw_markdown": "![image](relative.png)",
            "semantic_tags": [],
            "markdown_level": None,
            "table_html": None,
            "table_rows": None,
            "table_cols": None,
            "image_description": None,
            "image_type": None,
            "equation_latex": None,
            "equation_type": None,
            "extraction_timestamp": "2025-10-17T10:00:00",
            "model": "nanonets-ocr2-3b"
        }

        region = SemanticRegion.from_dict(data)

        assert isinstance(region.content, Path)
        # Path normalizes "./images/relative.png" to "images/relative.png"
        assert str(region.content) == "images/relative.png"

    def test_absolute_path_conversion(self):
        """Test absolute path string to Path conversion."""
        data = {
            "region_id": "reg_021",
            "region_type": "image",
            "region_sequence": 0,
            "page_number": 1,
            "content": "/absolute/path/image.png",
            "raw_markdown": "![image](image.png)",
            "semantic_tags": [],
            "markdown_level": None,
            "table_html": None,
            "table_rows": None,
            "table_cols": None,
            "image_description": None,
            "image_type": None,
            "equation_latex": None,
            "equation_type": None,
            "extraction_timestamp": "2025-10-17T10:00:00",
            "model": "nanonets-ocr2-3b"
        }

        region = SemanticRegion.from_dict(data)

        assert isinstance(region.content, Path)
        assert str(region.content) == "/absolute/path/image.png"

    def test_non_path_string_content(self):
        """Test that non-path strings remain as strings."""
        data = {
            "region_id": "reg_022",
            "region_type": "text",
            "region_sequence": 0,
            "page_number": 1,
            "content": "Regular text content",
            "raw_markdown": "Regular text content",
            "semantic_tags": [],
            "markdown_level": None,
            "table_html": None,
            "table_rows": None,
            "table_cols": None,
            "image_description": None,
            "image_type": None,
            "equation_latex": None,
            "equation_type": None,
            "extraction_timestamp": "2025-10-17T10:00:00",
            "model": "nanonets-ocr2-3b"
        }

        region = SemanticRegion.from_dict(data)

        assert isinstance(region.content, str)
        assert region.content == "Regular text content"


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_full_document_structure(self):
        """Test creating a sequence of regions representing a document."""
        regions = [
            SemanticRegion(
                region_id="doc1_reg_000",
                region_type="title",
                region_sequence=0,
                page_number=1,
                content="Annual Financial Report 2024",
                raw_markdown="# Annual Financial Report 2024",
                markdown_level=1,
                semantic_tags=["title", "financial"]
            ),
            SemanticRegion(
                region_id="doc1_reg_001",
                region_type="text",
                region_sequence=1,
                page_number=1,
                content="This report summarizes our financial performance.",
                raw_markdown="This report summarizes our financial performance.",
                semantic_tags=["introduction"]
            ),
            SemanticRegion(
                region_id="doc1_reg_002",
                region_type="table",
                region_sequence=2,
                page_number=1,
                content="Quarterly revenue breakdown",
                raw_markdown="| Quarter | Revenue |\n|---------|---------|",
                table_html="<table><tr><th>Quarter</th><th>Revenue</th></tr></table>",
                table_rows=4,
                table_cols=2,
                semantic_tags=["financial", "data"]
            ),
            SemanticRegion(
                region_id="doc1_reg_003",
                region_type="image",
                region_sequence=3,
                page_number=2,
                content=Path("/charts/revenue_growth.png"),
                raw_markdown="![Revenue growth chart](/charts/revenue_growth.png)",
                image_description="Line chart showing revenue growth from Q1 to Q4",
                image_type="chart",
                semantic_tags=["visual", "financial"]
            )
        ]

        assert len(regions) == 4
        assert all(isinstance(r, SemanticRegion) for r in regions)
        assert regions[0].region_sequence == 0
        assert regions[3].region_sequence == 3

        # Test serialization of entire document
        serialized = [r.to_dict() for r in regions]
        assert len(serialized) == 4

        # Test deserialization
        restored = [SemanticRegion.from_dict(d) for d in serialized]
        assert len(restored) == 4
        assert restored[0].region_type == "title"
        assert restored[3].image_type == "chart"
