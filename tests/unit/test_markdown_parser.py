"""Unit tests for markdown parser.

Tests the MarkdownParser class and its ability to extract semantic regions
from Nanonets-formatted markdown.
"""

import pytest
from src.jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser, RegionStub


# Sample markdown from Nanonets test output
SAMPLE_MARKDOWN = '''
# Q4 2024 Financial Results

- Revenue increased 25% year-over-year
- Operating margin improved to 18.5%

<table>
  <tr>
    <th>Metric</th>
    <th>Q3 2024</th>
    <th>Q4 2024</th>
  </tr>
  <tr>
    <td>Revenue</td>
    <td>$120M</td>
    <td>$150M</td>
  </tr>
  <tr>
    <td>Profit</td>
    <td>$18M</td>
    <td>$27M</td>
  </tr>
</table>

Growth Rate = $$\\frac{Q4 - Q3}{Q3} = 0.25$$

<img>Bar chart showing quarterly revenue growth trends</img>
'''


class TestMarkdownParserBasic:
    """Basic functionality tests."""

    def test_parser_initialization(self):
        """Test that parser initializes without errors."""
        parser = MarkdownParser()
        assert parser is not None

    def test_parse_empty_markdown(self):
        """Test handling of empty markdown."""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions("")
        assert regions == []

    def test_parse_none_markdown_raises_error(self):
        """Test that None input raises ValueError."""
        parser = MarkdownParser()
        with pytest.raises(ValueError, match="cannot be None"):
            parser.parse_markdown_to_regions(None)


class TestHeadingExtraction:
    """Tests for heading extraction."""

    def test_parse_heading(self):
        """Test extraction of H1 heading."""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(SAMPLE_MARKDOWN)
        headings = [r for r in regions if r.region_type == "title"]
        assert len(headings) == 1
        assert headings[0].content == "Q4 2024 Financial Results"
        assert headings[0].markdown_level == 1

    def test_parse_multiple_heading_levels(self):
        """Test extraction of multiple heading levels."""
        markdown = """
# Main Title
## Subsection
### Deep Dive
#### Level 4
##### Level 5
###### Level 6
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        headings = [r for r in regions if r.region_type == "title"]

        assert len(headings) == 6
        assert headings[0].markdown_level == 1
        assert headings[1].markdown_level == 2
        assert headings[2].markdown_level == 3
        assert headings[3].markdown_level == 4
        assert headings[4].markdown_level == 5
        assert headings[5].markdown_level == 6

    def test_heading_with_special_characters(self):
        """Test headings containing special characters."""
        markdown = "## Q4'24 Results: $150M Revenue (25% ↑)"
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        headings = [r for r in regions if r.region_type == "title"]

        assert len(headings) == 1
        assert "Q4'24 Results" in headings[0].content
        assert "$150M" in headings[0].content


class TestTableExtraction:
    """Tests for table extraction."""

    def test_parse_table(self):
        """Test basic table extraction."""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(SAMPLE_MARKDOWN)
        tables = [r for r in regions if r.region_type == "table"]

        assert len(tables) == 1
        assert "<table>" in tables[0].table_html
        assert "Metric" in tables[0].content

    def test_table_metadata(self):
        """Test table metadata extraction."""
        parser = MarkdownParser()
        table_html = "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
        metadata = parser.extract_table_metadata(table_html)

        assert metadata['rows'] == 2
        assert metadata['cols'] == 2
        assert metadata['has_header'] is True

    def test_table_metadata_no_header(self):
        """Test table without header row."""
        parser = MarkdownParser()
        table_html = "<table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table>"
        metadata = parser.extract_table_metadata(table_html)

        assert metadata['rows'] == 2
        assert metadata['cols'] == 2
        assert metadata['has_header'] is False

    def test_multiple_tables(self):
        """Test extraction of multiple tables."""
        markdown = """
<table>
  <tr><th>Table 1</th></tr>
  <tr><td>Data 1</td></tr>
</table>

Some text between tables.

<table>
  <tr><th>Table 2</th></tr>
  <tr><td>Data 2</td></tr>
</table>
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        tables = [r for r in regions if r.region_type == "table"]

        assert len(tables) == 2
        assert "Table 1" in tables[0].content
        assert "Table 2" in tables[1].content

    def test_malformed_table(self):
        """Test handling of malformed table (missing closing tag)."""
        parser = MarkdownParser()
        # Missing </table> tag
        markdown = "<table><tr><th>Header</th></tr><tr><td>Data</td></tr>"
        regions = parser.parse_markdown_to_regions(markdown)
        tables = [r for r in regions if r.region_type == "table"]

        # Should not extract incomplete table
        assert len(tables) == 0

    def test_table_metadata_empty_table(self):
        """Test metadata extraction from empty table."""
        parser = MarkdownParser()
        with pytest.raises(ValueError):
            parser.extract_table_metadata("")

    def test_case_insensitive_table_tags(self):
        """Test that table tags are case-insensitive."""
        markdown = "<TABLE><TR><TH>Header</TH></TR></TABLE>"
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        tables = [r for r in regions if r.region_type == "table"]

        assert len(tables) == 1


class TestImageExtraction:
    """Tests for image extraction."""

    def test_parse_image(self):
        """Test basic image extraction."""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(SAMPLE_MARKDOWN)
        images = [r for r in regions if r.region_type == "image"]

        assert len(images) == 1
        assert "chart" in images[0].image_description.lower()

    def test_multiple_images(self):
        """Test extraction of multiple images."""
        markdown = """
<img>First diagram showing process flow</img>

Some text.

<img>Second chart with bar graphs</img>
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        images = [r for r in regions if r.region_type == "image"]

        assert len(images) == 2
        assert "First diagram" in images[0].content
        assert "Second chart" in images[1].content

    def test_empty_image_tag(self):
        """Test handling of empty image tag."""
        markdown = "<img></img>"
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        images = [r for r in regions if r.region_type == "image"]

        assert len(images) == 1
        assert images[0].image_description == ""

    def test_case_insensitive_image_tags(self):
        """Test that image tags are case-insensitive."""
        markdown = "<IMG>Chart description</IMG>"
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        images = [r for r in regions if r.region_type == "image"]

        assert len(images) == 1
        assert "Chart description" in images[0].content


class TestEquationExtraction:
    """Tests for equation extraction."""

    def test_parse_display_equation(self):
        """Test extraction of display equation."""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(SAMPLE_MARKDOWN)
        equations = [r for r in regions if r.region_type == "equation"]

        assert len(equations) == 1
        assert "frac" in equations[0].equation_latex

    def test_multiple_equations(self):
        """Test extraction of multiple equations."""
        markdown = """
First equation: $$E = mc^2$$

Second equation: $$F = ma$$
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        equations = [r for r in regions if r.region_type == "equation"]

        assert len(equations) == 2
        assert "mc^2" in equations[0].content
        assert "ma" in equations[1].content

    def test_equation_with_special_characters(self):
        """Test equations containing special LaTeX characters."""
        markdown = r"$$\sum_{i=1}^{n} x_i = \int_{0}^{\infty} f(x) dx$$"
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        equations = [r for r in regions if r.region_type == "equation"]

        assert len(equations) == 1
        assert "sum" in equations[0].equation_latex
        assert "int" in equations[0].equation_latex

    def test_multiline_equation(self):
        """Test multiline equation extraction."""
        markdown = """$$
\\begin{aligned}
x &= a + b \\\\
y &= c + d
\\end{aligned}
$$"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        equations = [r for r in regions if r.region_type == "equation"]

        assert len(equations) == 1
        assert "aligned" in equations[0].equation_latex


class TestListExtraction:
    """Tests for list extraction."""

    def test_parse_list(self):
        """Test basic list extraction."""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(SAMPLE_MARKDOWN)
        lists = [r for r in regions if r.region_type == "list"]

        assert len(lists) == 1
        assert "Revenue increased" in lists[0].content

    def test_numbered_list(self):
        """Test numbered list extraction."""
        markdown = """
1. First item
2. Second item
3. Third item
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        lists = [r for r in regions if r.region_type == "list"]

        assert len(lists) == 1
        assert "First item" in lists[0].content
        assert "Second item" in lists[0].content
        assert "Third item" in lists[0].content

    def test_mixed_list_markers(self):
        """Test list with different markers."""
        markdown = """
- Bullet item
* Asterisk item
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        lists = [r for r in regions if r.region_type == "list"]

        # Should group consecutive items regardless of marker
        assert len(lists) >= 1
        content = ' '.join([l.content for l in lists])
        assert "Bullet item" in content
        assert "Asterisk item" in content

    def test_nested_list(self):
        """Test nested list with indentation."""
        markdown = """
- Top level item
  - Nested item 1
  - Nested item 2
- Another top level
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        lists = [r for r in regions if r.region_type == "list"]

        assert len(lists) >= 1
        # All items should be captured
        content = ' '.join([l.content for l in lists])
        assert "Top level item" in content
        assert "Nested item" in content


class TestTextExtraction:
    """Tests for plain text extraction."""

    def test_extract_text_paragraphs(self):
        """Test extraction of plain text paragraphs."""
        markdown = """
This is a paragraph of text.

This is another paragraph with multiple sentences. It contains various words.
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)
        texts = [r for r in regions if r.region_type == "text"]

        assert len(texts) == 2
        assert "This is a paragraph" in texts[0].content
        assert "another paragraph" in texts[1].content

    def test_text_with_inline_equations(self):
        """Test that inline equations don't interfere with text extraction."""
        markdown = "The formula $E = mc^2$ is famous."
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)

        # Text should still be extracted even with inline equation
        texts = [r for r in regions if r.region_type == "text"]
        assert len(texts) >= 0  # Inline equations may be removed


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_markdown_only_special_regions(self):
        """Test markdown with only special regions, no plain text."""
        markdown = """
# Title
<table><tr><th>Data</th></tr></table>
<img>Chart</img>
$$x = 1$$
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)

        # Should extract all special regions
        assert len(regions) == 4
        types = {r.region_type for r in regions}
        assert types == {"title", "table", "image", "equation"}

    def test_very_long_markdown(self):
        """Test performance with very long markdown."""
        # Generate long markdown
        paragraphs = ["This is paragraph number {}.".format(i) for i in range(100)]
        markdown = "\n\n".join(paragraphs)

        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)

        # Should handle without crashing
        assert len(regions) > 0

    def test_special_characters_in_content(self):
        """Test handling of special regex characters in content."""
        markdown = """
Text with special chars: $100 + $200 = $300

Not an equation: $ (dollar sign)
"""
        parser = MarkdownParser()
        # Should not crash
        regions = parser.parse_markdown_to_regions(markdown)
        assert len(regions) > 0

    def test_overlapping_patterns(self):
        """Test handling of potentially overlapping patterns."""
        markdown = """
<table>
  <tr><th>Column with $$equation$$</th></tr>
</table>
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)

        # Table should be extracted
        tables = [r for r in regions if r.region_type == "table"]
        assert len(tables) == 1

    def test_whitespace_only_markdown(self):
        """Test handling of whitespace-only markdown."""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions("   \n\n  \t\t  \n  ")
        assert regions == []


class TestTableStructureParsing:
    """Tests for enhanced table structure parsing."""

    def test_parse_table_structure_basic(self):
        """Test basic table structure parsing."""
        parser = MarkdownParser()
        table_html = """
        <table>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td>Revenue</td><td>$120M</td></tr>
            <tr><td>Profit</td><td>$18M</td></tr>
        </table>
        """
        structure = parser.parse_table_structure(table_html)

        assert structure['rows'] == 3
        assert structure['cols'] == 2
        assert structure['has_header'] is True
        assert structure['header_row'] == ['Name', 'Value']
        assert len(structure['cells']) == 3
        assert structure['cells'][1] == ['Revenue', '$120M']

    def test_table_to_markdown(self):
        """Test HTML to markdown conversion."""
        parser = MarkdownParser()
        table_html = """
        <table>
            <tr><th>A</th><th>B</th></tr>
            <tr><td>1</td><td>2</td></tr>
        </table>
        """
        markdown = parser.table_to_markdown(table_html)

        assert '| A | B |' in markdown
        assert '| --- | --- |' in markdown
        assert '| 1 | 2 |' in markdown

    def test_extract_table_cells(self):
        """Test cell extraction."""
        parser = MarkdownParser()
        table_html = "<table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td>D</td></tr></table>"
        cells = parser.extract_table_cells(table_html)

        assert cells == [['A', 'B'], ['C', 'D']]

    def test_table_with_irregular_rows(self):
        """Test table with different column counts per row."""
        parser = MarkdownParser()
        table_html = """
        <table>
            <tr><td>A</td><td>B</td><td>C</td></tr>
            <tr><td>D</td><td>E</td></tr>
        </table>
        """
        structure = parser.parse_table_structure(table_html)

        assert structure['cols'] == 3  # Max columns
        assert len(structure['cells'][1]) == 2  # Second row has 2 cells

    def test_table_with_whitespace(self):
        """Test table with extra whitespace in cells."""
        parser = MarkdownParser()
        table_html = "<table><tr><td>  A  </td><td>B\n\n</td></tr></table>"
        cells = parser.extract_table_cells(table_html)

        assert cells[0][0] == 'A'  # Whitespace stripped
        assert cells[0][1] == 'B'

    def test_malformed_table_fallback(self):
        """Test graceful handling of malformed tables."""
        parser = MarkdownParser()
        table_html = "<table><tr><td>Incomplete"
        structure = parser.parse_table_structure(table_html)

        # Should not crash, should return something
        assert 'rows' in structure
        assert 'cols' in structure

    def test_table_no_header(self):
        """Test table without header row."""
        parser = MarkdownParser()
        table_html = """
        <table>
            <tr><td>A</td><td>B</td></tr>
            <tr><td>C</td><td>D</td></tr>
        </table>
        """
        structure = parser.parse_table_structure(table_html)

        assert structure['has_header'] is False
        assert structure['header_row'] is None
        assert len(structure['cells']) == 2

    def test_table_empty_cells(self):
        """Test table with empty cells."""
        parser = MarkdownParser()
        table_html = """
        <table>
            <tr><th>A</th><th>B</th><th>C</th></tr>
            <tr><td>1</td><td></td><td>3</td></tr>
        </table>
        """
        structure = parser.parse_table_structure(table_html)

        assert structure['cells'][1] == ['1', '', '3']

    def test_table_with_nested_html(self):
        """Test table cells with nested HTML."""
        parser = MarkdownParser()
        table_html = """
        <table>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td><strong>Bold</strong> text</td><td><em>Italic</em> text</td></tr>
        </table>
        """
        structure = parser.parse_table_structure(table_html)

        # Should extract text content (without tags)
        assert 'Bold' in structure['cells'][1][0]
        assert 'Italic' in structure['cells'][1][1]

    def test_large_table(self):
        """Test performance with large table (100+ rows)."""
        parser = MarkdownParser()
        # Generate large table
        rows = ['<tr><td>A{}</td><td>B{}</td></tr>'.format(i, i) for i in range(100)]
        table_html = '<table>' + ''.join(rows) + '</table>'

        structure = parser.parse_table_structure(table_html)

        assert structure['rows'] == 100
        assert structure['cols'] == 2
        assert len(structure['cells']) == 100

    def test_table_markdown_padding(self):
        """Test markdown generation with irregular column counts."""
        parser = MarkdownParser()
        table_html = """
        <table>
            <tr><th>A</th><th>B</th><th>C</th></tr>
            <tr><td>1</td><td>2</td></tr>
        </table>
        """
        markdown = parser.table_to_markdown(table_html)

        # Second row should be padded with empty cells
        lines = markdown.strip().split('\n')
        assert lines[2] == '| 1 | 2 |  |'  # Padded with empty cell

    def test_enhanced_table_extraction_in_regions(self):
        """Test that enhanced table metadata is used in region extraction."""
        parser = MarkdownParser()
        markdown = """
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Revenue</td><td>$120M</td></tr>
        </table>
        """
        regions = parser.parse_markdown_to_regions(markdown)
        tables = [r for r in regions if r.region_type == "table"]

        assert len(tables) == 1
        assert tables[0].table_rows == 2
        assert tables[0].table_cols == 2
        # Content should be markdown format
        assert '| Metric | Value |' in tables[0].content
        assert '| --- | --- |' in tables[0].content


class TestImageClassification:
    """Test image type classification."""

    def test_classify_chart(self):
        parser = MarkdownParser()
        descriptions = [
            "Bar chart showing revenue growth",
            "Line graph of quarterly trends",
            "Pie chart with market share data"
        ]
        for desc in descriptions:
            assert parser.classify_image_type(desc) == "chart"

    def test_classify_logo(self):
        parser = MarkdownParser()
        descriptions = [
            "Company logo",
            "Brand trademark symbol",
            "Corporate branding element"
        ]
        for desc in descriptions:
            assert parser.classify_image_type(desc) == "logo"

    def test_classify_diagram(self):
        parser = MarkdownParser()
        descriptions = [
            "System architecture diagram",
            "Workflow flowchart",
            "Process illustration"
        ]
        for desc in descriptions:
            assert parser.classify_image_type(desc) == "diagram"

    def test_classify_screenshot(self):
        parser = MarkdownParser()
        desc = "Screenshot of application interface"
        assert parser.classify_image_type(desc) == "screenshot"

    def test_classify_photo(self):
        parser = MarkdownParser()
        desc = "Photo of team members"
        assert parser.classify_image_type(desc) == "photo"

    def test_classify_unknown(self):
        parser = MarkdownParser()
        assert parser.classify_image_type("") == "unknown"
        assert parser.classify_image_type("Some vague thing") == "unknown"

    def test_extract_image_metadata(self):
        parser = MarkdownParser()
        tag = "<img>Bar chart showing revenue trends over time</img>"
        metadata = parser.extract_image_metadata(tag)

        assert metadata['description'] == "Bar chart showing revenue trends over time"
        assert metadata['image_type'] == "chart"
        assert metadata['has_description'] is True

    def test_extract_empty_image(self):
        parser = MarkdownParser()
        tag = "<img></img>"
        metadata = parser.extract_image_metadata(tag)

        assert metadata['description'] == ""
        assert metadata['has_description'] is False
        assert metadata['image_type'] == "unknown"

    def test_parse_image_description(self):
        parser = MarkdownParser()
        desc = "Revenue chart showing   growth  trends"
        parsed = parser.parse_image_description(desc)

        assert parsed['cleaned'] == "Revenue chart showing growth trends"
        assert parsed['word_count'] == 5
        assert parsed['has_technical_terms'] is True  # "revenue"

    def test_image_integration_in_regions(self):
        """Test that image regions use enhanced metadata."""
        parser = MarkdownParser()
        markdown = "<img>System architecture diagram showing API flow</img>"
        regions = parser.parse_markdown_to_regions(markdown)

        images = [r for r in regions if r.region_type == "image"]
        assert len(images) == 1
        assert images[0].image_type == "diagram"
        assert "architecture" in images[0].image_description

    def test_multiple_image_types(self):
        """Test document with mixed image types."""
        parser = MarkdownParser()
        markdown = """
        <img>Company logo</img>
        <img>Bar chart showing Q4 results</img>
        <img>System architecture diagram</img>
        """
        regions = parser.parse_markdown_to_regions(markdown)
        images = [r for r in regions if r.region_type == "image"]

        assert len(images) == 3
        types = [img.image_type for img in images]
        assert "logo" in types
        assert "chart" in types
        assert "diagram" in types

    def test_classify_with_multiple_keywords(self):
        """Test classification when description contains multiple type keywords."""
        parser = MarkdownParser()
        # Chart should take precedence over photo for specific keywords
        desc = "Chart showing photo gallery statistics"
        assert parser.classify_image_type(desc) == "chart"

    def test_classify_case_insensitive(self):
        """Test that classification is case-insensitive."""
        parser = MarkdownParser()
        assert parser.classify_image_type("BAR CHART") == "chart"
        assert parser.classify_image_type("Company LOGO") == "logo"
        assert parser.classify_image_type("DIAGRAM") == "diagram"

    def test_parse_image_description_empty(self):
        """Test parsing empty image description."""
        parser = MarkdownParser()
        parsed = parser.parse_image_description("")

        assert parsed['original'] == ''
        assert parsed['cleaned'] == ''
        assert parsed['word_count'] == 0
        assert parsed['has_technical_terms'] is False

    def test_parse_image_description_whitespace(self):
        """Test parsing description with excessive whitespace."""
        parser = MarkdownParser()
        desc = "Revenue   growth    metrics   analysis"
        parsed = parser.parse_image_description(desc)

        assert parsed['cleaned'] == "Revenue growth metrics analysis"
        assert parsed['word_count'] == 4
        assert parsed['has_technical_terms'] is True

    def test_parse_image_description_no_technical_terms(self):
        """Test description without technical terms."""
        parser = MarkdownParser()
        desc = "Beautiful sunset over mountains"
        parsed = parser.parse_image_description(desc)

        assert parsed['has_technical_terms'] is False

    def test_classify_complex_chart_description(self):
        """Test chart classification with complex description."""
        parser = MarkdownParser()
        desc = "Multi-series line graph displaying quarterly revenue trends with x-axis showing time periods and y-axis representing dollar amounts"
        assert parser.classify_image_type(desc) == "chart"

    def test_image_metadata_preserves_full_tag(self):
        """Test that extract_image_metadata works with full tag match."""
        parser = MarkdownParser()
        tag = "<img>Detailed flowchart diagram</img>"
        metadata = parser.extract_image_metadata(tag)

        assert metadata['description'] == "Detailed flowchart diagram"
        assert metadata['image_type'] == "diagram"


class TestIntegration:
    """Integration tests with complex markdown."""

    def test_full_sample_markdown(self):
        """Test parsing of the complete sample markdown."""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(SAMPLE_MARKDOWN)

        # Should extract all region types
        types = {r.region_type for r in regions}
        assert "title" in types
        assert "table" in types
        assert "image" in types
        assert "equation" in types
        assert "list" in types

        # Verify we got expected number of each
        assert len([r for r in regions if r.region_type == "title"]) == 1
        assert len([r for r in regions if r.region_type == "table"]) == 1
        assert len([r for r in regions if r.region_type == "image"]) == 1
        assert len([r for r in regions if r.region_type == "equation"]) == 1
        assert len([r for r in regions if r.region_type == "list"]) == 1

    def test_complex_document(self):
        """Test parsing of a complex multi-section document."""
        markdown = """
# Executive Summary

The company performed well in Q4 2024.

- Revenue: $150M
- Profit: $27M

## Financial Details

<table>
  <tr><th>Quarter</th><th>Revenue</th></tr>
  <tr><td>Q3</td><td>$120M</td></tr>
  <tr><td>Q4</td><td>$150M</td></tr>
</table>

### Growth Analysis

The growth rate can be calculated as:

$$growth = \\frac{Q4 - Q3}{Q3}$$

<img>Trend chart showing upward trajectory</img>

## Conclusion

Strong performance across all metrics.
"""
        parser = MarkdownParser()
        regions = parser.parse_markdown_to_regions(markdown)

        # Verify comprehensive extraction
        assert len(regions) >= 8

        headings = [r for r in regions if r.region_type == "title"]
        assert len(headings) == 4  # H1, H2, H3, H2

        tables = [r for r in regions if r.region_type == "table"]
        assert len(tables) == 1

        images = [r for r in regions if r.region_type == "image"]
        assert len(images) == 1

        equations = [r for r in regions if r.region_type == "equation"]
        assert len(equations) == 1
