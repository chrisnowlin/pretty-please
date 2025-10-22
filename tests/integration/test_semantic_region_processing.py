"""Integration test for SemanticRegion processing in tasks.py."""

import pytest
from pathlib import Path
from src.jina_rag_pipeline.ingestion.semantic_region import SemanticRegion
from src.jina_rag_pipeline.ingestion.base import Document


def test_semantic_region_dict_conversion():
    """Test that SemanticRegion can be converted to/from dict for tasks.py."""
    region = SemanticRegion(
        region_id="test_001",
        region_type="table",
        region_sequence=0,
        page_number=1,
        content="Revenue data",
        raw_markdown="| A | B |",
        table_html="<table><tr><td>A</td><td>B</td></tr></table>",
        table_rows=2,
        table_cols=2,
    )

    # Convert to dict (as stored in Document metadata)
    region_dict = region.to_dict()
    assert region_dict["region_type"] == "table"
    assert region_dict["table_rows"] == 2

    # Reconstruct from dict (as done in tasks.py)
    restored = SemanticRegion.from_dict(region_dict)
    assert restored.region_id == region.region_id
    assert restored.table_html == region.table_html
    assert restored.table_rows == 2


def test_document_with_semantic_regions():
    """Test that Document can store SemanticRegion objects in metadata."""
    region1 = SemanticRegion(
        region_id="r1",
        region_type="text",
        region_sequence=0,
        page_number=1,
        content="Sample text",
        raw_markdown="Sample text",
    )

    region2 = SemanticRegion(
        region_id="r2",
        region_type="equation",
        region_sequence=1,
        page_number=1,
        content="E = mc^2",
        raw_markdown="$$E = mc^2$$",
        equation_latex="E = mc^2",
        equation_type="display",
    )

    # Create document with regions (as done by loaders)
    doc = Document(
        content="Combined content",
        source="test.pptx",
        metadata={
            "regions": [region1.to_dict(), region2.to_dict()],
            "layout_analysis_enabled": True,
        }
    )

    # Verify regions can be extracted
    regions_data = doc.metadata["regions"]
    assert len(regions_data) == 2
    assert regions_data[0]["region_type"] == "text"
    assert regions_data[1]["region_type"] == "equation"
    assert regions_data[1]["equation_latex"] == "E = mc^2"


def test_semantic_region_all_types():
    """Test all supported region types with their specific fields."""

    # Text region
    text_region = SemanticRegion(
        region_id="text_01",
        region_type="text",
        region_sequence=0,
        page_number=1,
        content="This is sample text",
        raw_markdown="This is sample text",
        semantic_tags=["technical", "introduction"],
    )

    # Title region
    title_region = SemanticRegion(
        region_id="title_01",
        region_type="title",
        region_sequence=1,
        page_number=1,
        content="Introduction",
        raw_markdown="# Introduction",
        markdown_level=1,
        semantic_tags=["heading"],
    )

    # Table region
    table_region = SemanticRegion(
        region_id="table_01",
        region_type="table",
        region_sequence=2,
        page_number=1,
        content="| A | B |\n|---|---|\n| 1 | 2 |",
        raw_markdown="| A | B |\n|---|---|\n| 1 | 2 |",
        table_html="<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>",
        table_rows=2,
        table_cols=2,
    )

    # Image region
    image_region = SemanticRegion(
        region_id="image_01",
        region_type="image",
        region_sequence=3,
        page_number=1,
        content="/path/to/image.png",
        raw_markdown="![Chart](image.png)",
        image_description="A bar chart showing quarterly revenue growth",
        image_type="chart",
    )

    # Equation region
    equation_region = SemanticRegion(
        region_id="equation_01",
        region_type="equation",
        region_sequence=4,
        page_number=1,
        content="E = mc^2",
        raw_markdown="$$E = mc^2$$",
        equation_latex="E = mc^2",
        equation_type="display",
    )

    # List region
    list_region = SemanticRegion(
        region_id="list_01",
        region_type="list",
        region_sequence=5,
        page_number=1,
        content="- Item 1\n- Item 2\n- Item 3",
        raw_markdown="- Item 1\n- Item 2\n- Item 3",
        semantic_tags=["enumeration"],
    )

    # Convert all to dict and back
    regions = [
        text_region,
        title_region,
        table_region,
        image_region,
        equation_region,
        list_region,
    ]

    for region in regions:
        region_dict = region.to_dict()
        restored = SemanticRegion.from_dict(region_dict)

        # Verify basic fields
        assert restored.region_id == region.region_id
        assert restored.region_type == region.region_type
        assert restored.region_sequence == region.region_sequence
        assert restored.page_number == region.page_number

        # Verify type-specific fields
        if region.region_type == "table":
            assert restored.table_html == region.table_html
            assert restored.table_rows == region.table_rows
            assert restored.table_cols == region.table_cols
        elif region.region_type == "image":
            assert restored.image_description == region.image_description
            assert restored.image_type == region.image_type
        elif region.region_type == "equation":
            assert restored.equation_latex == region.equation_latex
            assert restored.equation_type == region.equation_type
        elif region.region_type == "title":
            assert restored.markdown_level == region.markdown_level


def test_semantic_region_metadata_fields():
    """Test that semantic metadata fields are properly preserved."""
    region = SemanticRegion(
        region_id="meta_01",
        region_type="text",
        region_sequence=0,
        page_number=1,
        content="Technical content",
        raw_markdown="Technical content",
        semantic_tags=["technical", "finance", "summary"],
        model="nanonets-ocr2-3b",
    )

    region_dict = region.to_dict()

    # Verify metadata fields
    assert region_dict["semantic_tags"] == ["technical", "finance", "summary"]
    assert region_dict["model"] == "nanonets-ocr2-3b"
    assert "extraction_timestamp" in region_dict

    # Restore and verify
    restored = SemanticRegion.from_dict(region_dict)
    assert restored.semantic_tags == ["technical", "finance", "summary"]
    assert restored.model == "nanonets-ocr2-3b"
