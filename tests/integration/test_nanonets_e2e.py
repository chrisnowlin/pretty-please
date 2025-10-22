"""End-to-end integration test for Nanonets migration.

This test validates the complete pipeline from PowerPoint loading
through semantic region extraction to embedding storage.
"""

import pytest
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageFont

from src.jina_rag_pipeline.ingestion.loaders import PowerPointLoader
from src.jina_rag_pipeline.ingestion.nanonets_layout import (
    NanonetsLayoutAnalyzer,
    create_analyzer,
    NANONETS_AVAILABLE
)
from src.jina_rag_pipeline.ingestion.semantic_region import SemanticRegion


@pytest.mark.skipif(not NANONETS_AVAILABLE, reason="Nanonets dependencies not installed")
class TestNanonetsEndToEnd:
    """End-to-end integration tests for Nanonets pipeline."""

    def test_nanonets_analyzer_with_synthetic_image(self):
        """Test NanonetsLayoutAnalyzer with a synthetic test image."""
        # Create synthetic slide image
        img = Image.new('RGB', (1920, 1080), color='white')
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        except:
            font = ImageFont.load_default()

        # Add title
        draw.text((100, 100), "Test Slide Title", fill='black', font=font)

        # Add text
        draw.text((100, 300), "This is sample content", fill='black', font=font)

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            img.save(tmp_path, format="PNG")

        try:
            # Create analyzer
            analyzer = create_analyzer()

            # Extract regions
            regions = analyzer.extract_regions(
                file_path=tmp_path,
                page_number=1,
                document_id="test_doc"
            )

            # Validate results
            assert len(regions) > 0, "Should extract at least one region"
            assert all(isinstance(r, SemanticRegion) for r in regions), "Should return SemanticRegion objects"

            # Check that we got expected content
            all_content = " ".join(str(r.content) for r in regions)
            assert "Test" in all_content or "Slide" in all_content, "Should extract some text"

            # Validate region structure
            for region in regions:
                assert region.region_id is not None
                assert region.region_type in ["text", "table", "image", "equation", "list", "title"]
                assert region.region_sequence >= 0
                assert region.page_number == 1
                assert region.model == "nanonets-ocr2-3b"

        finally:
            # Cleanup
            tmp_path.unlink(missing_ok=True)

    def test_semantic_region_serialization_roundtrip(self):
        """Test that SemanticRegion survives serialization/deserialization."""
        # Create a complex region with all fields
        original = SemanticRegion(
            region_id="test_region_001",
            region_type="table",
            region_sequence=0,
            page_number=1,
            content="Revenue data",
            raw_markdown="| Q1 | Q2 | Q3 | Q4 |",
            semantic_tags=["financial", "quarterly"],
            markdown_level=None,
            table_html="<table><tr><th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th></tr></table>",
            table_rows=2,
            table_cols=4,
        )

        # Serialize to dict (as done by loaders)
        region_dict = original.to_dict()

        # Deserialize (as done by tasks.py)
        restored = SemanticRegion.from_dict(region_dict)

        # Verify all fields preserved
        assert restored.region_id == original.region_id
        assert restored.region_type == original.region_type
        assert restored.content == original.content
        assert restored.table_html == original.table_html
        assert restored.table_rows == original.table_rows
        assert restored.table_cols == original.table_cols
        assert restored.semantic_tags == original.semantic_tags

    def test_all_region_types_supported(self):
        """Test that all 6 region types are properly defined."""
        region_types = ["text", "title", "list", "image", "table", "equation"]

        for region_type in region_types:
            region = SemanticRegion(
                region_id=f"test_{region_type}",
                region_type=region_type,
                region_sequence=0,
                page_number=1,
                content=f"Test {region_type} content",
                raw_markdown=f"Test {region_type} markdown",
            )

            assert region.region_type == region_type

            # Verify serialization works
            region_dict = region.to_dict()
            assert region_dict["region_type"] == region_type

    def test_powerpoint_loader_initialization(self):
        """Test that PowerPointLoader can initialize with Nanonets."""
        # Test with layout analysis enabled
        loader_with_layout = PowerPointLoader(use_layout_analysis=True)
        assert loader_with_layout.use_layout_analysis is True
        assert loader_with_layout.layout_analyzer is not None

        # Test without layout analysis
        loader_simple = PowerPointLoader(use_layout_analysis=False)
        assert loader_simple.use_layout_analysis is False

    def test_markdown_parser_integration(self):
        """Test that MarkdownParser correctly parses Nanonets output."""
        from src.jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser

        # Sample Nanonets-style markdown
        markdown = """
# Q4 2024 Results

Revenue increased 25% year-over-year.

<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Revenue</td><td>$150M</td></tr>
</table>

<img>Bar chart showing revenue trends</img>

$$E = mc^2$$
"""

        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown, page_number=1)

        # Should extract all major types
        region_types = [r.region_type for r in regions]
        assert "title" in region_types or "text" in region_types
        assert "table" in region_types
        assert "image" in region_types
        assert "equation" in region_types

        # Verify table has HTML
        tables = [r for r in regions if r.region_type == "table"]
        assert len(tables) > 0
        assert tables[0].table_html is not None
        assert "<table>" in tables[0].table_html

        # Verify image has description
        images = [r for r in regions if r.region_type == "image"]
        assert len(images) > 0
        assert images[0].image_description is not None

        # Verify equation has LaTeX
        equations = [r for r in regions if r.region_type == "equation"]
        assert len(equations) > 0
        assert equations[0].equation_latex is not None

    def test_image_classification_accuracy(self):
        """Test image type classification with various descriptions."""
        from src.jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser

        parser = MarkdownParser()

        test_cases = [
            ("Bar chart showing revenue growth", "chart"),
            ("Company logo", "logo"),
            ("System architecture diagram", "diagram"),
            ("Screenshot of dashboard", "screenshot"),
            ("Photo of team members", "photo"),
            ("Some unclear image", "unknown"),
        ]

        for description, expected_type in test_cases:
            classified_type = parser.classify_image_type(description)
            assert classified_type == expected_type, \
                f"Expected '{expected_type}' for '{description}', got '{classified_type}'"

    def test_table_structure_extraction(self):
        """Test table metadata extraction."""
        from src.jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser

        parser = MarkdownParser()

        table_html = """
        <table>
            <tr><th>Name</th><th>Value</th><th>Change</th></tr>
            <tr><td>Revenue</td><td>$150M</td><td>+25%</td></tr>
            <tr><td>Profit</td><td>$27M</td><td>+50%</td></tr>
        </table>
        """

        structure = parser.parse_table_structure(table_html)

        assert structure["rows"] == 3
        assert structure["cols"] == 3
        assert structure["has_header"] is True
        assert len(structure["cells"]) == 3
        assert structure["cells"][0] == ["Name", "Value", "Change"]

        # Verify markdown conversion
        markdown = structure["markdown_table"]
        assert "| Name | Value | Change |" in markdown
        assert "| --- | --- | --- |" in markdown


@pytest.mark.skipif(not NANONETS_AVAILABLE, reason="Nanonets dependencies not installed")
def test_nanonets_import_chain():
    """Test that all Nanonets modules import correctly."""
    # Test imports work
    from src.jina_rag_pipeline.ingestion import (
        SemanticRegion,
        MarkdownParser,
        NanonetsLayoutAnalyzer,
        create_analyzer,
    )

    assert SemanticRegion is not None
    assert MarkdownParser is not None
    assert NanonetsLayoutAnalyzer is not None
    assert create_analyzer is not None


def test_migration_backward_compatibility():
    """Test that non-Nanonets functionality still works."""
    from src.jina_rag_pipeline.ingestion.loaders import PowerPointLoader

    # Simple mode should work without Nanonets
    loader = PowerPointLoader(use_layout_analysis=False)
    assert loader.use_layout_analysis is False
    assert not hasattr(loader, 'layout_analyzer') or loader.layout_analyzer is None


@pytest.mark.skipif(not NANONETS_AVAILABLE, reason="Nanonets dependencies not installed")
class TestSemanticRegionAdvanced:
    """Advanced tests for SemanticRegion functionality."""

    def test_region_json_serialization(self):
        """Test JSON serialization and deserialization."""
        original = SemanticRegion(
            region_id="json_test_001",
            region_type="text",
            region_sequence=0,
            page_number=1,
            content="Test content",
            raw_markdown="Test markdown",
            semantic_tags=["test", "json"],
        )

        # Convert to JSON
        json_str = original.to_json()
        assert isinstance(json_str, str)
        assert "json_test_001" in json_str

        # Convert back from JSON
        restored = SemanticRegion.from_json(json_str)
        assert restored.region_id == original.region_id
        assert restored.semantic_tags == original.semantic_tags

    def test_region_with_image_metadata(self):
        """Test region with image-specific metadata."""
        region = SemanticRegion(
            region_id="img_test_001",
            region_type="image",
            region_sequence=0,
            page_number=1,
            content="Revenue chart",
            raw_markdown="<img>Revenue chart</img>",
            image_description="Bar chart showing Q4 revenue trends",
            image_type="chart",
        )

        assert region.region_type == "image"
        assert region.image_description is not None
        assert region.image_type == "chart"

        # Test serialization preserves image metadata
        region_dict = region.to_dict()
        assert region_dict["image_description"] == "Bar chart showing Q4 revenue trends"
        assert region_dict["image_type"] == "chart"

    def test_region_with_equation_metadata(self):
        """Test region with equation-specific metadata."""
        region = SemanticRegion(
            region_id="eq_test_001",
            region_type="equation",
            region_sequence=0,
            page_number=1,
            content="E = mc^2",
            raw_markdown="$$E = mc^2$$",
            equation_latex="E = mc^2",
            equation_type="display",
        )

        assert region.region_type == "equation"
        assert region.equation_latex == "E = mc^2"
        assert region.equation_type == "display"

        # Test serialization
        restored = SemanticRegion.from_dict(region.to_dict())
        assert restored.equation_latex == region.equation_latex
        assert restored.equation_type == region.equation_type


@pytest.mark.skipif(not NANONETS_AVAILABLE, reason="Nanonets dependencies not installed")
class TestMarkdownParserAdvanced:
    """Advanced tests for MarkdownParser functionality."""

    def test_nested_table_structure(self):
        """Test parsing complex table structures."""
        from src.jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser

        parser = MarkdownParser()

        complex_table = """
        <table>
            <tr>
                <th>Quarter</th>
                <th>Revenue</th>
                <th>Profit</th>
                <th>Margin</th>
            </tr>
            <tr>
                <td>Q1</td>
                <td>$120M</td>
                <td>$18M</td>
                <td>15%</td>
            </tr>
            <tr>
                <td>Q2</td>
                <td>$135M</td>
                <td>$21M</td>
                <td>15.5%</td>
            </tr>
            <tr>
                <td>Q3</td>
                <td>$142M</td>
                <td>$24M</td>
                <td>16.9%</td>
            </tr>
            <tr>
                <td>Q4</td>
                <td>$150M</td>
                <td>$27M</td>
                <td>18%</td>
            </tr>
        </table>
        """

        structure = parser.parse_table_structure(complex_table)

        assert structure["rows"] == 5  # 1 header + 4 data rows
        assert structure["cols"] == 4
        assert structure["has_header"] is True
        assert structure["cells"][0] == ["Quarter", "Revenue", "Profit", "Margin"]
        assert structure["cells"][1] == ["Q1", "$120M", "$18M", "15%"]

    def test_multiple_equations_parsing(self):
        """Test parsing multiple equations in document."""
        from src.jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser

        parser = MarkdownParser()

        markdown = """
The fundamental equations of physics:

$$E = mc^2$$

And the wave equation:

$$\\frac{\\partial^2 u}{\\partial t^2} = c^2 \\nabla^2 u$$

With the Schrödinger equation:

$$i\\hbar\\frac{\\partial}{\\partial t}\\Psi = \\hat{H}\\Psi$$
"""

        regions = parser.parse_markdown_to_regions(markdown, page_number=1)
        equations = [r for r in regions if r.region_type == "equation"]

        assert len(equations) == 3
        assert "E = mc^2" in equations[0].equation_latex
        assert "partial" in equations[1].equation_latex
        assert "Psi" in equations[2].equation_latex

    def test_list_grouping(self):
        """Test that consecutive list items are grouped correctly."""
        from src.jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser

        parser = MarkdownParser()

        markdown = """
Key findings:

- Revenue increased 25%
- Profit margin improved to 18%
- Customer retention at 95%

Separate list:

- New product launch
- Market expansion
"""

        regions = parser.parse_markdown_to_regions(markdown, page_number=1)
        lists = [r for r in regions if r.region_type == "list"]

        # Should extract list regions (current implementation groups closely-spaced items)
        assert len(lists) >= 1, "Should extract at least one list region"

        # Verify list contains multiple items
        all_list_content = '\n'.join(r.content for r in lists)
        assert "Revenue increased 25%" in all_list_content
        assert "New product launch" in all_list_content

        # Verify all expected items are present
        list_items = all_list_content.split('\n')
        assert len(list_items) >= 5, "Should have at least 5 list items total"

    def test_mixed_content_extraction(self):
        """Test parsing document with all content types."""
        from src.jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser

        parser = MarkdownParser()

        markdown = """
# Q4 2024 Financial Report

Revenue growth exceeded expectations this quarter.

<table>
  <tr><th>Metric</th><th>Q3</th><th>Q4</th><th>Change</th></tr>
  <tr><td>Revenue</td><td>$142M</td><td>$150M</td><td>+5.6%</td></tr>
</table>

<img>Chart showing revenue trends across quarters</img>

Key achievements:
- Launched new product line
- Expanded into APAC market
- Increased team by 25%

The growth model follows:

$$R(t) = R_0 e^{kt}$$

Where k represents the growth constant.
"""

        regions = parser.parse_markdown_to_regions(markdown, page_number=1)

        # Verify all types are present
        region_types = [r.region_type for r in regions]
        assert "title" in region_types
        assert "text" in region_types
        assert "table" in region_types
        assert "image" in region_types
        assert "list" in region_types
        assert "equation" in region_types

        # Verify counts
        assert len([r for r in regions if r.region_type == "title"]) >= 1
        assert len([r for r in regions if r.region_type == "table"]) == 1
        assert len([r for r in regions if r.region_type == "image"]) == 1
        assert len([r for r in regions if r.region_type == "equation"]) == 1


@pytest.mark.skipif(not NANONETS_AVAILABLE, reason="Nanonets dependencies not installed")
class TestNanonetsAnalyzerAdvanced:
    """Advanced tests for NanonetsLayoutAnalyzer."""

    def test_analyzer_initialization_options(self):
        """Test analyzer initialization with different options."""
        # Test with tables disabled
        analyzer_no_tables = NanonetsLayoutAnalyzer(
            enable_tables=False,
            enable_equations=True,
            enable_image_descriptions=True,
        )
        assert analyzer_no_tables.enable_tables is False
        assert analyzer_no_tables.enable_equations is True

        # Test with equations disabled
        analyzer_no_equations = NanonetsLayoutAnalyzer(
            enable_tables=True,
            enable_equations=False,
            enable_image_descriptions=True,
        )
        assert analyzer_no_equations.enable_tables is True
        assert analyzer_no_equations.enable_equations is False

    def test_create_analyzer_factory(self):
        """Test the create_analyzer factory function."""
        analyzer = create_analyzer()

        assert isinstance(analyzer, NanonetsLayoutAnalyzer)
        assert analyzer.device in ["mps", "cuda", "cpu"]
        assert analyzer.enable_tables is True
        assert analyzer.enable_equations is True
        assert analyzer.enable_image_descriptions is True

    def test_analyzer_prompt_generation(self):
        """Test that analyzer generates correct prompts."""
        # Analyzer with all features
        analyzer_full = NanonetsLayoutAnalyzer(
            enable_tables=True,
            enable_equations=True,
            enable_image_descriptions=True,
        )
        prompt_full = analyzer_full._create_prompt()
        assert "tables in html format" in prompt_full.lower()
        assert "latex" in prompt_full.lower()
        assert "image" in prompt_full.lower()

        # Analyzer with minimal features
        analyzer_minimal = NanonetsLayoutAnalyzer(
            enable_tables=False,
            enable_equations=False,
            enable_image_descriptions=False,
        )
        prompt_minimal = analyzer_minimal._create_prompt()
        assert "tables" not in prompt_minimal.lower() or "html" not in prompt_minimal.lower()


def test_error_handling():
    """Test error handling in various scenarios."""
    from src.jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser
    from src.jina_rag_pipeline.ingestion.semantic_region import SemanticRegion

    parser = MarkdownParser()

    # Test parsing None markdown
    with pytest.raises(ValueError, match="Markdown input cannot be None"):
        parser.parse_markdown_to_regions(None, page_number=1)

    # Test parsing empty markdown
    regions = parser.parse_markdown_to_regions("", page_number=1)
    assert len(regions) == 0

    # Test table metadata extraction with invalid input
    with pytest.raises(ValueError, match="table_html cannot be None or empty"):
        parser.extract_table_metadata(None)

    with pytest.raises(ValueError, match="table_html cannot be None or empty"):
        parser.extract_table_metadata("")


def test_semantic_region_edge_cases():
    """Test edge cases for SemanticRegion."""
    from pathlib import Path

    # Test region with Path content
    region_with_path = SemanticRegion(
        region_id="path_test",
        region_type="image",
        region_sequence=0,
        page_number=1,
        content=Path("/tmp/test_image.png"),
        raw_markdown="<img>Test image</img>",
    )

    # Test serialization preserves Path
    region_dict = region_with_path.to_dict()
    assert isinstance(region_dict["content"], str)
    assert "test_image.png" in region_dict["content"]

    # Test deserialization
    restored = SemanticRegion.from_dict(region_dict)
    assert isinstance(restored.content, (str, Path))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
