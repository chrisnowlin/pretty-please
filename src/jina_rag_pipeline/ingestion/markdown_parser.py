"""Markdown parser for converting structured OCR markdown into semantic regions.

Supports Deepseek-OCR markdown output (and legacy formats) by extracting semantic
regions including tables, images, equations, headings, lists, and text paragraphs.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Temporary stub until SemanticRegion is available
@dataclass
class RegionStub:
    """Temporary stub for SemanticRegion.

    Attributes:
        region_type: Type of semantic region (table, image, equation, title, list, text)
        content: Extracted text content
        raw_markdown: Original markdown source
        markdown_level: Heading level (1-6) for titles
        table_html: Full HTML for tables
        table_rows: Number of rows in table
        table_cols: Number of columns in table
        image_description: Description text for images
        image_type: Classification for images (chart, logo, diagram, photo, screenshot, unknown)
        equation_latex: LaTeX equation text
    """
    region_type: str
    content: str
    raw_markdown: str
    markdown_level: Optional[int] = None
    table_html: Optional[str] = None
    table_rows: Optional[int] = None
    table_cols: Optional[int] = None
    image_description: Optional[str] = None
    image_type: Optional[str] = None
    equation_latex: Optional[str] = None


class MarkdownParser:
    """Parses structured OCR markdown into semantic regions.

    This parser handles Deepseek (and legacy Nanonets) markdown formats with semantic tags:
    - <table>...</table> for tables
    - <img>...</img> for image descriptions
    - $$...$$ for display equations
    - $...$ for inline equations (currently extracted but not used in chunking)
    - Standard markdown headings (#, ##, etc.)
    - Standard markdown lists (-, *, numbered)
    """

    # Regex patterns for extraction
    TABLE_PATTERN = re.compile(r'<table>(.*?)</table>', re.DOTALL | re.IGNORECASE)
    IMAGE_PATTERN = re.compile(r'<img>(.*?)</img>', re.DOTALL | re.IGNORECASE)
    DISPLAY_EQUATION_PATTERN = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
    INLINE_EQUATION_PATTERN = re.compile(r'\$(.*?)\$')
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    LIST_PATTERN = re.compile(r'^(\s*)([-*]|\d+\.)\s+(.+)$', re.MULTILINE)

    def __init__(self):
        """Initialize parser."""
        logger.debug("MarkdownParser initialized")

    def parse_markdown_to_regions(
        self,
        markdown: str,
        page_number: int = 1,
        document_id: Optional[str] = None
    ) -> List[RegionStub]:
        """Parse markdown into semantic regions.

        This method extracts all semantic regions from the markdown in a specific order:
        1. Tables
        2. Images
        3. Display equations
        4. Headings
        5. Lists
        6. Plain text paragraphs

        Args:
            markdown: Structured markdown from Nanonets
            page_number: Source page number (for future use)
            document_id: Optional document identifier (for future use)

        Returns:
            List of semantic regions extracted from markdown

        Raises:
            ValueError: If markdown is None
        """
        if markdown is None:
            raise ValueError("Markdown input cannot be None")

        if not markdown.strip():
            logger.warning("Empty markdown provided")
            return []

        regions = []

        try:
            # Extract tables
            for match in self.TABLE_PATTERN.finditer(markdown):
                table_html = match.group(0)

                # Get enhanced structure
                structure = self.parse_table_structure(table_html)

                regions.append(RegionStub(
                    region_type="table",
                    content=structure.get('markdown_table', ''),
                    raw_markdown=table_html,
                    table_html=table_html,
                    table_rows=structure.get('rows'),
                    table_cols=structure.get('cols')
                ))
                logger.debug(f"Extracted table region with {structure.get('rows')} rows and {structure.get('cols')} cols")

            # Extract images
            for match in self.IMAGE_PATTERN.finditer(markdown):
                full_tag = match.group(0)

                # Get enhanced metadata
                metadata = self.extract_image_metadata(full_tag)

                regions.append(RegionStub(
                    region_type="image",
                    content=metadata['description'],
                    raw_markdown=full_tag,
                    image_description=metadata['description'],
                    image_type=metadata['image_type']
                ))
                logger.debug(f"Extracted image region ({metadata['image_type']}): {metadata['description'][:50]}...")

            # Extract display equations ($$...$$)
            for match in self.DISPLAY_EQUATION_PATTERN.finditer(markdown):
                equation = match.group(1).strip()
                regions.append(RegionStub(
                    region_type="equation",
                    content=equation,
                    raw_markdown=match.group(0),
                    equation_latex=equation
                ))
                logger.debug(f"Extracted equation region: {equation[:50]}...")

            # Extract headings
            for match in self.HEADING_PATTERN.finditer(markdown):
                level = len(match.group(1))  # Number of # characters
                heading_text = match.group(2).strip()
                regions.append(RegionStub(
                    region_type="title",
                    content=heading_text,
                    raw_markdown=match.group(0),
                    markdown_level=level
                ))
                logger.debug(f"Extracted heading (level {level}): {heading_text}")

            # Extract lists - group consecutive items
            list_regions = self._extract_lists(markdown)
            regions.extend(list_regions)

            # Extract remaining text (everything not in special tags)
            text_regions = self._extract_text_paragraphs(markdown)
            regions.extend(text_regions)

            logger.info(f"Parsed {len(regions)} semantic regions from markdown")

        except Exception as e:
            logger.error(f"Error parsing markdown: {e}", exc_info=True)
            raise

        return regions

    def _extract_lists(self, markdown: str) -> List[RegionStub]:
        """Extract list items and group consecutive items into list regions.

        Args:
            markdown: Source markdown text

        Returns:
            List of RegionStub objects representing lists
        """
        list_items = []
        for match in self.LIST_PATTERN.finditer(markdown):
            indent = match.group(1)
            marker = match.group(2)
            item_text = match.group(3).strip()
            list_items.append({
                'indent': len(indent),
                'marker': marker,
                'text': item_text,
                'raw': match.group(0),
                'position': match.start()
            })

        if not list_items:
            return []

        # Group consecutive list items (within 2 lines of each other)
        grouped_lists = []
        current_group = [list_items[0]]

        for i in range(1, len(list_items)):
            prev_item = list_items[i - 1]
            curr_item = list_items[i]

            # Check if items are consecutive (simple heuristic based on position)
            # If positions are far apart (> 100 chars), start new group
            if curr_item['position'] - prev_item['position'] > 100:
                grouped_lists.append(current_group)
                current_group = [curr_item]
            else:
                current_group.append(curr_item)

        # Add final group
        if current_group:
            grouped_lists.append(current_group)

        # Convert groups to RegionStub objects
        regions = []
        for group in grouped_lists:
            list_content = '\n'.join(item['text'] for item in group)
            list_markdown = '\n'.join(item['raw'] for item in group)
            regions.append(RegionStub(
                region_type="list",
                content=list_content,
                raw_markdown=list_markdown
            ))
            logger.debug(f"Grouped {len(group)} list items into single region")

        return regions

    def _extract_text_paragraphs(self, markdown: str) -> List[RegionStub]:
        """Extract plain text paragraphs after removing special regions.

        Args:
            markdown: Source markdown text

        Returns:
            List of RegionStub objects representing text paragraphs
        """
        clean_text = self._remove_special_regions(markdown)

        if not clean_text.strip():
            return []

        regions = []

        # Split into paragraphs (double newline separated)
        paragraphs = [p.strip() for p in clean_text.split('\n\n') if p.strip()]

        for para in paragraphs:
            # Skip headings (already extracted)
            if para.startswith('#'):
                continue

            # Skip list items (already extracted)
            if re.match(r'^\s*([-*]|\d+\.)\s+', para):
                continue

            # Skip very short paragraphs (likely artifacts)
            if len(para) < 3:
                continue

            regions.append(RegionStub(
                region_type="text",
                content=para,
                raw_markdown=para
            ))
            logger.debug(f"Extracted text paragraph: {para[:50]}...")

        return regions

    def _remove_special_regions(self, markdown: str) -> str:
        """Remove all special tagged regions to isolate plain text.

        Args:
            markdown: Source markdown text

        Returns:
            Markdown with special regions removed
        """
        text = markdown
        text = self.TABLE_PATTERN.sub('', text)
        text = self.IMAGE_PATTERN.sub('', text)
        text = self.DISPLAY_EQUATION_PATTERN.sub('', text)
        text = self.HEADING_PATTERN.sub('', text)
        text = self.LIST_PATTERN.sub('', text)
        return text

    def extract_table_metadata(self, table_html: str) -> Dict[str, Any]:
        """Extract metadata from HTML table.

        Args:
            table_html: HTML table string

        Returns:
            Dictionary with keys:
                - rows: Number of rows
                - cols: Number of columns
                - has_header: Whether table has header row (th tags)

        Raises:
            ValueError: If table_html is None or empty
        """
        if not table_html:
            raise ValueError("table_html cannot be None or empty")

        try:
            # Count rows
            row_pattern = re.compile(r'<tr>', re.IGNORECASE)
            rows = len(row_pattern.findall(table_html))

            # Count columns (from first row)
            first_row_match = re.search(r'<tr>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
            cols = 0
            if first_row_match:
                cell_pattern = re.compile(r'<t[hd]>', re.IGNORECASE)
                cols = len(cell_pattern.findall(first_row_match.group(1)))

            # Detect header row
            has_header = '<th>' in table_html.lower()

            logger.debug(f"Table metadata: {rows} rows, {cols} cols, header={has_header}")

            return {
                'rows': rows,
                'cols': cols,
                'has_header': has_header
            }

        except Exception as e:
            logger.error(f"Error extracting table metadata: {e}", exc_info=True)
            # Return safe defaults
            return {
                'rows': 0,
                'cols': 0,
                'has_header': False
            }

    def parse_table_structure(self, table_html: str) -> Dict[str, Any]:
        """Parse HTML table into detailed structure.

        Args:
            table_html: HTML table string

        Returns:
            Dictionary with:
            - rows: int - number of rows
            - cols: int - number of columns
            - has_header: bool - whether first row is header
            - cells: List[List[str]] - cell content (2D array)
            - header_row: Optional[List[str]] - header cells if present
            - markdown_table: str - markdown representation
        """
        from html.parser import HTMLParser

        class TableParser(HTMLParser):
            """Custom HTML parser for tables."""
            def __init__(self):
                super().__init__()
                self.rows = []
                self.current_row = []
                self.current_cell = []
                self.in_header = False
                self.in_cell = False
                self.has_th_tag = False

            def handle_starttag(self, tag, attrs):
                if tag == 'tr':
                    self.current_row = []
                elif tag in ('th', 'td'):
                    self.in_cell = True
                    self.current_cell = []
                    if tag == 'th':
                        self.has_th_tag = True

            def handle_endtag(self, tag):
                if tag == 'tr':
                    if self.current_row:
                        self.rows.append(self.current_row)
                elif tag in ('th', 'td'):
                    self.in_cell = False
                    cell_text = ''.join(self.current_cell).strip()
                    self.current_row.append(cell_text)
                    self.current_cell = []

            def handle_data(self, data):
                if self.in_cell:
                    self.current_cell.append(data)

        parser = TableParser()
        try:
            parser.feed(table_html)
        except Exception as e:
            # Fallback to basic extraction
            logger.warning(f"Failed to parse table structure: {e}")
            return self.extract_table_metadata(table_html)

        rows = parser.rows
        if not rows:
            return {
                'rows': 0,
                'cols': 0,
                'has_header': False,
                'cells': [],
                'header_row': None,
                'markdown_table': ''
            }

        num_rows = len(rows)
        num_cols = max(len(row) for row in rows) if rows else 0
        has_header = parser.has_th_tag or '<th>' in table_html.lower()

        # Extract header row
        header_row = rows[0] if has_header and rows else None

        # Convert to markdown
        markdown_lines = []
        for i, row in enumerate(rows):
            # Pad row to match column count
            padded_row = row + [''] * (num_cols - len(row))
            markdown_lines.append('| ' + ' | '.join(padded_row) + ' |')

            # Add separator after header
            if i == 0 and has_header:
                markdown_lines.append('| ' + ' | '.join(['---'] * num_cols) + ' |')

        markdown_table = '\n'.join(markdown_lines)

        return {
            'rows': num_rows,
            'cols': num_cols,
            'has_header': has_header,
            'cells': rows,
            'header_row': header_row,
            'markdown_table': markdown_table
        }

    def table_to_markdown(self, table_html: str) -> str:
        """Convert HTML table to markdown format.

        Args:
            table_html: HTML table string

        Returns:
            Markdown table representation
        """
        structure = self.parse_table_structure(table_html)
        return structure.get('markdown_table', '')

    def extract_table_cells(self, table_html: str) -> List[List[str]]:
        """Extract all cell content from table as 2D array.

        Args:
            table_html: HTML table string

        Returns:
            List of rows, each row is list of cell contents
        """
        structure = self.parse_table_structure(table_html)
        return structure.get('cells', [])

    def classify_image_type(self, description: str) -> str:
        """Classify image type from description text.

        Uses keyword matching to classify images into categories.
        Order matters: more specific keywords are checked first.

        Args:
            description: Image description text

        Returns:
            One of: "chart", "logo", "diagram", "photo", "screenshot", "unknown"
        """
        if not description:
            return "unknown"

        desc_lower = description.lower()

        # Logo keywords (check first - very specific)
        logo_keywords = [
            'logo', 'brand', 'trademark', 'company logo',
            'branding', 'brand mark'
        ]
        if any(kw in desc_lower for kw in logo_keywords):
            return "logo"

        # Screenshot keywords (check before diagram/chart)
        screenshot_keywords = [
            'screenshot', 'screen capture', 'interface',
            'ui', 'user interface', 'application window'
        ]
        if any(kw in desc_lower for kw in screenshot_keywords):
            return "screenshot"

        # Diagram keywords (check before chart since "flowchart" contains "chart")
        diagram_keywords = [
            'diagram', 'flowchart', 'architecture', 'schematic',
            'flow', 'process', 'workflow', 'system design',
            'blueprint', 'illustration', 'drawing'
        ]
        if any(kw in desc_lower for kw in diagram_keywords):
            return "diagram"

        # Chart keywords
        chart_keywords = [
            'chart', 'graph', 'plot', 'bar', 'line', 'pie',
            'histogram', 'scatter', 'trend', 'data visualization',
            'axis', 'x-axis', 'y-axis', 'legend'
        ]
        if any(kw in desc_lower for kw in chart_keywords):
            return "chart"

        # Photo keywords (check last since more generic)
        photo_keywords = [
            'photo', 'photograph', 'image of', 'picture of',
            'showing', 'depicts', 'portrait'
        ]
        if any(kw in desc_lower for kw in photo_keywords):
            return "photo"

        return "unknown"

    def extract_image_metadata(self, image_tag: str) -> Dict[str, Any]:
        """Extract metadata from image tag.

        Args:
            image_tag: Full <img>...</img> tag with content

        Returns:
            Dictionary with:
            - description: str - extracted description
            - image_type: str - classified type
            - has_description: bool - whether description exists
        """
        # Extract description from tag
        match = self.IMAGE_PATTERN.match(image_tag)
        description = ""
        if match:
            description = match.group(1).strip()

        # Classify type
        image_type = self.classify_image_type(description)

        return {
            'description': description,
            'image_type': image_type,
            'has_description': bool(description)
        }

    def parse_image_description(self, description: str) -> Dict[str, Any]:
        """Parse image description for additional insights.

        Args:
            description: Image description text

        Returns:
            Dictionary with:
            - original: str - original description
            - cleaned: str - cleaned description (no extra whitespace)
            - word_count: int - number of words
            - has_technical_terms: bool - contains technical vocabulary
        """
        if not description:
            return {
                'original': '',
                'cleaned': '',
                'word_count': 0,
                'has_technical_terms': False
            }

        # Clean description
        cleaned = ' '.join(description.split())

        # Word count
        word_count = len(cleaned.split())

        # Technical terms detection
        technical_keywords = [
            'revenue', 'profit', 'margin', 'growth', 'metric',
            'api', 'database', 'server', 'algorithm', 'function',
            'architecture', 'system', 'process', 'workflow'
        ]
        has_technical_terms = any(
            kw in cleaned.lower() for kw in technical_keywords
        )

        return {
            'original': description,
            'cleaned': cleaned,
            'word_count': word_count,
            'has_technical_terms': has_technical_terms
        }
