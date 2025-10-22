"""Export lesson plans to various formats (PDF, JSON)."""

import re
import json
import logging
from typing import Dict, Any, Optional
from io import BytesIO

logger = logging.getLogger(__name__)


class LessonExportError(Exception):
    """Error during lesson export."""
    pass


class LessonExporter:
    """
    Export lesson plans to different formats.

    Supports:
    - PDF export with professional styling
    - JSON export with structured data
    """

    def __init__(self):
        """Initialize the lesson exporter."""
        self._pdf_available = self._check_pdf_dependencies()

    def _check_pdf_dependencies(self) -> bool:
        """Check if PDF export dependencies are available."""
        try:
            import markdown
            import weasyprint
            return True
        except (ImportError, OSError) as e:
            logger.warning(
                f"PDF export not available: {e}. "
                "On macOS, install system dependencies: brew install pango"
            )
            return False

    def markdown_to_pdf(
        self,
        markdown_content: str,
        output_path: Optional[str] = None,
        style: str = "color"
    ) -> bytes:
        """
        Convert markdown lesson plan to PDF.

        Args:
            markdown_content: Markdown content to convert
            output_path: Optional path to save PDF file
            style: PDF style - "color" or "bw" (black & white)

        Returns:
            PDF content as bytes

        Raises:
            LessonExportError: If PDF generation fails
        """
        if not self._pdf_available:
            raise LessonExportError(
                "PDF export not available. "
                "Install dependencies: pip install markdown weasyprint"
            )

        try:
            import markdown
            import weasyprint

            # Extract and format metadata from frontmatter
            metadata_html = self._extract_and_format_metadata(markdown_content, style=style)

            # Remove frontmatter from content
            cleaned_content = self._remove_frontmatter(markdown_content)

            # Convert markdown to HTML
            html_content = markdown.markdown(
                cleaned_content,
                extensions=['extra', 'codehilite', 'tables', 'toc']
            )

            # Prepend metadata box if available
            if metadata_html:
                html_content = metadata_html + html_content

            # Wrap in professional HTML template (color or B&W)
            if style == "bw":
                full_html = self._create_pdf_html_template_bw(html_content)
            else:
                full_html = self._create_pdf_html_template(html_content)

            # Convert HTML to PDF
            pdf_doc = weasyprint.HTML(string=full_html)

            if output_path:
                pdf_doc.write_pdf(output_path)
                logger.info(f"PDF saved to: {output_path}")

            # Return PDF as bytes
            pdf_bytes = pdf_doc.write_pdf()
            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise LessonExportError(f"Failed to generate PDF: {e}") from e

    def _remove_frontmatter(self, markdown_content: str) -> str:
        """Remove YAML frontmatter from markdown content."""
        # Remove all frontmatter blocks (there might be multiple)
        cleaned = re.sub(
            r'^---\n.*?\n---\n+',
            '',
            markdown_content,
            flags=re.DOTALL | re.MULTILINE
        )
        return cleaned.strip()

    def _extract_and_format_metadata(self, markdown_content: str, style: str = "color") -> str:
        """Extract metadata from frontmatter and format as HTML box."""
        # Look for the second frontmatter block (the actual lesson metadata)
        frontmatter_blocks = re.findall(
            r'^---\n(.*?)\n---',
            markdown_content,
            re.DOTALL | re.MULTILINE
        )

        if len(frontmatter_blocks) < 2:
            return ""

        # Use the second frontmatter block (lesson metadata)
        metadata_text = frontmatter_blocks[1]
        metadata = {}

        for line in metadata_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                metadata[key] = value

        # Format as HTML
        if not metadata:
            return ""

        # Create a nice metadata box (use different class for B&W)
        metadata_class = "lesson-metadata-bw" if style == "bw" else "lesson-metadata"
        html_parts = [f'<div class="{metadata_class}">']

        # Add title prominently if available
        if 'title' in metadata:
            title_class = "lesson-title-bw" if style == "bw" else "lesson-title"
            html_parts.append(f'<h1 class="{title_class}">{metadata["title"]}</h1>')

        # Add other metadata in a grid
        html_parts.append('<div class="metadata-grid">')

        metadata_labels = {
            'grade': 'Grade Level',
            'subject': 'Subject',
            'duration': 'Duration',
            'teaching_style': 'Teaching Style',
            'generated': 'Generated'
        }

        for key, label in metadata_labels.items():
            if key in metadata:
                value = metadata[key]
                # Format duration
                if key == 'duration':
                    value = f"{value} minutes"
                # Format teaching style
                elif key == 'teaching_style':
                    value = value.replace('_', ' ').title()
                # Format generated timestamp
                elif key == 'generated':
                    # Simplify the timestamp
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        value = dt.strftime('%B %d, %Y at %I:%M %p')
                    except:
                        pass

                html_parts.append(
                    f'<div class="metadata-item">'
                    f'<span class="metadata-label">{label}:</span> '
                    f'<span class="metadata-value">{value}</span>'
                    f'</div>'
                )

        html_parts.append('</div>')  # Close metadata-grid
        html_parts.append('</div>')  # Close lesson-metadata

        return '\n'.join(html_parts)

    def _create_pdf_html_template(self, body_html: str) -> str:
        """
        Create HTML template with CSS styling for PDF.

        Args:
            body_html: HTML content for body

        Returns:
            Complete HTML document with styling
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: Letter;
            margin: 0.85in 0.75in 1in 0.75in;

            @top-right {{
                content: "Lesson Plan";
                font-size: 9pt;
                color: #7f8c8d;
                font-family: 'Helvetica', 'Arial', sans-serif;
            }}

            @bottom-center {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #7f8c8d;
                font-family: 'Helvetica', 'Arial', sans-serif;
            }}
        }}

        /* Modern, readable font stack */
        body {{
            font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.7;
            color: #2c3e50;
            max-width: 100%;
            background: white;
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
        }}

        /* Lesson metadata box at the top */
        .lesson-metadata {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5em 2em;
            margin: 0 0 1em 0;
            border-radius: 8px;
            page-break-inside: avoid;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.25);
        }}

        .lesson-title {{
            font-size: 28pt;
            font-weight: 700;
            color: white;
            margin: 0 0 0.8em 0;
            padding: 0;
            border: none;
            letter-spacing: -0.02em;
        }}

        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.8em;
            font-size: 10pt;
        }}

        .metadata-item {{
            background: rgba(255, 255, 255, 0.15);
            padding: 0.6em 0.9em;
            border-radius: 4px;
            border-left: 3px solid rgba(255, 255, 255, 0.5);
        }}

        .metadata-label {{
            font-weight: 700;
            color: rgba(255, 255, 255, 0.9);
        }}

        .metadata-value {{
            color: white;
            font-weight: 500;
        }}

        /* Main title - make it stand out */
        h1 {{
            font-size: 26pt;
            font-weight: 700;
            color: #1a1a1a;
            margin-top: 0.2em;
            margin-bottom: 0.8em;
            padding-bottom: 0.4em;
            border-bottom: 3px solid #3498db;
            letter-spacing: -0.02em;
            page-break-after: avoid;
        }}

        /* Section headers - clear hierarchy */
        h2 {{
            font-size: 16pt;
            font-weight: 700;
            color: #2c3e50;
            margin-top: 1.8em;
            margin-bottom: 0.7em;
            padding: 0.4em 0.6em;
            background: linear-gradient(to right, #e8f4f8 0%, #ffffff 100%);
            border-left: 4px solid #3498db;
            page-break-after: avoid;
        }}

        /* Subsection headers */
        h3 {{
            font-size: 13pt;
            font-weight: 600;
            color: #34495e;
            margin-top: 1.3em;
            margin-bottom: 0.6em;
            padding-left: 0.3em;
            border-left: 2px solid #95a5a6;
            page-break-after: avoid;
        }}

        /* Smaller headers */
        h4 {{
            font-size: 11.5pt;
            font-weight: 600;
            color: #7f8c8d;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }}

        /* Paragraphs with better spacing */
        p {{
            margin: 0.6em 0;
            text-align: left;
            orphans: 3;
            widows: 3;
        }}

        /* Lists with better readability */
        ul, ol {{
            margin: 0.8em 0;
            padding-left: 1.8em;
            line-height: 1.8;
        }}

        li {{
            margin: 0.5em 0;
            padding-left: 0.3em;
        }}

        /* Nested lists */
        li ul, li ol {{
            margin-top: 0.4em;
            margin-bottom: 0.4em;
        }}

        /* Emphasis and strong */
        strong {{
            font-weight: 700;
            color: #1a1a1a;
        }}

        em {{
            font-style: italic;
            color: #555;
        }}

        /* Inline code */
        code {{
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            background-color: #f5f7f9;
            padding: 0.15em 0.4em;
            border-radius: 3px;
            font-size: 10pt;
            border: 1px solid #e1e4e8;
            color: #e83e8c;
        }}

        /* Code blocks and equations */
        pre {{
            background-color: #f8f9fb;
            border: 1px solid #e1e4e8;
            border-left: 4px solid #3498db;
            padding: 1.2em;
            margin: 1.2em 0;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 10pt;
            line-height: 1.5;
            page-break-inside: avoid;
        }}

        pre code {{
            background: none;
            border: none;
            padding: 0;
            color: #24292e;
        }}

        /* Blockquotes */
        blockquote {{
            border-left: 5px solid #3498db;
            background-color: #f8f9fb;
            padding: 0.8em 1em;
            margin: 1.2em 0;
            color: #555;
            font-style: italic;
            border-radius: 0 4px 4px 0;
            page-break-inside: avoid;
        }}

        /* Tables with professional styling */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1.2em 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }}

        th, td {{
            border: 1px solid #cbd5e0;
            padding: 0.7em 0.9em;
            text-align: left;
        }}

        th {{
            background-color: #edf2f7;
            font-weight: 700;
            color: #2d3748;
        }}

        tr:nth-child(even) {{
            background-color: #f7fafc;
        }}

        /* Horizontal rules */
        hr {{
            border: none;
            border-top: 2px solid #e2e8f0;
            margin: 2em 0;
        }}

        /* Images and figures */
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1.2em auto;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            page-break-inside: avoid;
        }}

        /* Image captions */
        em {{
            display: block;
            text-align: center;
            font-size: 9pt;
            color: #718096;
            margin-top: 0.5em;
        }}

        /* Citation styling */
        sup {{
            color: #3498db;
            font-weight: 700;
            font-size: 9pt;
        }}

        a[href] {{
            color: #3498db;
            text-decoration: none;
        }}

        /* Avoid breaking these elements */
        h1, h2, h3, h4, h5, h6 {{
            page-break-inside: avoid;
            page-break-after: avoid;
        }}

        /* Better page break behavior */
        ul, ol, dl {{
            page-break-before: avoid;
        }}

        /* Metadata box at the top */
        .metadata-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.2em 1.5em;
            margin: 0 0 1em 0;
            border-radius: 6px;
            font-size: 10pt;
            page-break-inside: avoid;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }}

        .metadata-box p {{
            margin: 0.4em 0;
            font-weight: 500;
        }}

        .metadata-box strong {{
            color: #fff;
            font-weight: 700;
        }}

        /* Highlight boxes for key sections */
        .objectives-box, .materials-box, .assessment-box {{
            border-left: 5px solid #3498db;
            background-color: #f0f8ff;
            padding: 1em 1.2em;
            margin: 1em 0;
            border-radius: 0 4px 4px 0;
            page-break-inside: avoid;
        }}

        .materials-box {{
            border-left-color: #2ecc71;
            background-color: #f0fdf4;
        }}

        .assessment-box {{
            border-left-color: #f39c12;
            background-color: #fffbf0;
        }}

        /* Print optimizations */
        @media print {{
            body {{
                background: white;
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
            }}
        }}
    </style>
</head>
<body>
{body_html}
</body>
</html>
"""

    def _create_pdf_html_template_bw(self, body_html: str) -> str:
        """
        Create minimal black & white HTML template for printer-friendly PDF.

        Args:
            body_html: HTML content for body

        Returns:
            Complete HTML document with B&W styling
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: Letter;
            margin: 0.75in;

            @top-right {{
                content: "Lesson Plan";
                font-size: 9pt;
                color: #000;
                font-family: 'Helvetica', 'Arial', sans-serif;
            }}

            @bottom-center {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #000;
                font-family: 'Helvetica', 'Arial', sans-serif;
            }}
        }}

        /* Clean, readable font stack */
        body {{
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #000;
            max-width: 100%;
            background: white;
            word-wrap: break-word;
            overflow-wrap: break-word;
            hyphens: auto;
        }}

        /* B&W Metadata box - simple border */
        .lesson-metadata-bw {{
            border: 2px solid #000;
            padding: 1.2em 1.5em;
            margin: 0 0 0.8em 0;
            page-break-inside: avoid;
        }}

        .lesson-title-bw {{
            font-size: 20pt;
            font-weight: 700;
            color: #000;
            margin: 0 0 0.8em 0;
            padding: 0 0 0.5em 0;
            border-bottom: 2px solid #000;
        }}

        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.6em;
            font-size: 9pt;
        }}

        .metadata-item {{
            border: 1px solid #000;
            padding: 0.4em 0.6em;
        }}

        .metadata-label {{
            font-weight: 700;
            color: #000;
        }}

        .metadata-value {{
            color: #000;
        }}

        /* Main heading */
        h1 {{
            font-size: 18pt;
            font-weight: 700;
            color: #000;
            margin-top: 1em;
            margin-bottom: 0.6em;
            padding-bottom: 0.3em;
            border-bottom: 2px solid #000;
            page-break-after: avoid;
        }}

        /* Section headers */
        h2 {{
            font-size: 14pt;
            font-weight: 700;
            color: #000;
            margin-top: 1.5em;
            margin-bottom: 0.6em;
            padding: 0.3em 0;
            border-top: 1px solid #000;
            border-bottom: 1px solid #000;
            page-break-after: avoid;
        }}

        /* Subsection headers */
        h3 {{
            font-size: 12pt;
            font-weight: 600;
            color: #000;
            margin-top: 1.2em;
            margin-bottom: 0.5em;
            text-decoration: underline;
            page-break-after: avoid;
        }}

        h4 {{
            font-size: 11pt;
            font-weight: 600;
            color: #000;
            margin-top: 1em;
            margin-bottom: 0.4em;
        }}

        /* Paragraphs */
        p {{
            margin: 0.5em 0;
            text-align: left;
            orphans: 3;
            widows: 3;
        }}

        /* Lists */
        ul, ol {{
            margin: 0.6em 0;
            padding-left: 1.5em;
            line-height: 1.7;
        }}

        li {{
            margin: 0.4em 0;
        }}

        li ul, li ol {{
            margin-top: 0.3em;
            margin-bottom: 0.3em;
        }}

        /* Emphasis */
        strong {{
            font-weight: 700;
            color: #000;
        }}

        em {{
            font-style: italic;
        }}

        /* Code */
        code {{
            font-family: 'Courier New', monospace;
            border: 1px solid #000;
            padding: 0.1em 0.3em;
            font-size: 10pt;
        }}

        /* Code blocks */
        pre {{
            border: 1px solid #000;
            padding: 0.8em;
            margin: 1em 0;
            font-size: 10pt;
            line-height: 1.4;
            page-break-inside: avoid;
        }}

        pre code {{
            border: none;
            padding: 0;
        }}

        /* Blockquotes */
        blockquote {{
            border-left: 3px solid #000;
            padding-left: 1em;
            margin: 1em 0;
            font-style: italic;
            page-break-inside: avoid;
        }}

        /* Tables */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }}

        th, td {{
            border: 1px solid #000;
            padding: 0.5em;
            text-align: left;
        }}

        th {{
            font-weight: 700;
            background-color: #f0f0f0;
        }}

        /* Horizontal rules */
        hr {{
            border: none;
            border-top: 1px solid #000;
            margin: 1.5em 0;
        }}

        /* Images */
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1em auto;
            border: 1px solid #000;
            page-break-inside: avoid;
        }}

        /* Image captions */
        em {{
            display: block;
            text-align: center;
            font-size: 9pt;
            margin-top: 0.4em;
        }}

        /* Citations */
        sup {{
            font-weight: 700;
            font-size: 9pt;
        }}

        a[href] {{
            color: #000;
            text-decoration: underline;
        }}

        /* Page break handling */
        h1, h2, h3, h4, h5, h6 {{
            page-break-inside: avoid;
            page-break-after: avoid;
        }}

        ul, ol, dl {{
            page-break-before: avoid;
        }}

        /* Print optimizations */
        @media print {{
            body {{
                background: white;
                color: black;
            }}
        }}
    </style>
</head>
<body>
{body_html}
</body>
</html>
"""

    def markdown_to_json(self, markdown_content: str) -> Dict[str, Any]:
        """
        Convert markdown lesson plan to structured JSON.

        Args:
            markdown_content: Markdown content to convert

        Returns:
            Dictionary with structured lesson data

        Raises:
            LessonExportError: If JSON conversion fails
        """
        try:
            # Extract YAML frontmatter
            metadata = self._extract_frontmatter(markdown_content)

            # Remove frontmatter from content
            content_without_frontmatter = re.sub(
                r'^---\n.*?\n---\n',
                '',
                markdown_content,
                count=1,
                flags=re.DOTALL
            )

            # Parse sections
            sections = self._parse_sections(content_without_frontmatter)

            # Extract citations
            citations = self._extract_citations(content_without_frontmatter)

            # Build JSON structure
            lesson_json = {
                "metadata": metadata,
                "sections": sections,
                "citations": citations,
                "raw_markdown": markdown_content,
            }

            return lesson_json

        except Exception as e:
            logger.error(f"JSON conversion failed: {e}")
            raise LessonExportError(f"Failed to convert to JSON: {e}") from e

    def _extract_frontmatter(self, markdown_content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from markdown."""
        frontmatter_match = re.search(
            r'^---\n(.*?)\n---',
            markdown_content,
            re.DOTALL
        )

        if not frontmatter_match:
            return {}

        frontmatter_text = frontmatter_match.group(1)
        metadata = {}

        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')

                # Try to convert to appropriate type
                # Keep grade as string, but convert duration to int
                if key == 'duration' and value.isdigit():
                    metadata[key] = int(value)
                elif key != 'grade' and value.isdigit():
                    metadata[key] = int(value)
                elif value.lower() in ('true', 'false'):
                    metadata[key] = value.lower() == 'true'
                else:
                    metadata[key] = value

        return metadata

    def _parse_sections(self, content: str) -> list[Dict[str, Any]]:
        """Parse markdown into sections based on headers."""
        sections = []
        current_section = None

        lines = content.split('\n')

        for line in lines:
            # Check for headers
            if line.startswith('# '):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "level": 1,
                    "title": line[2:].strip(),
                    "content": []
                }
            elif line.startswith('## '):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "level": 2,
                    "title": line[3:].strip(),
                    "content": []
                }
            elif line.startswith('### '):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "level": 3,
                    "title": line[4:].strip(),
                    "content": []
                }
            else:
                if current_section and line.strip():
                    current_section["content"].append(line)

        # Add last section
        if current_section:
            sections.append(current_section)

        # Join content lines
        for section in sections:
            section["content"] = '\n'.join(section["content"]).strip()

        return sections

    def _extract_citations(self, content: str) -> list[str]:
        """Extract citation numbers from content."""
        citation_pattern = r'\[(\d+)\]'
        citations = re.findall(citation_pattern, content)
        return sorted(list(set(citations)), key=int)

    def json_to_markdown(self, lesson_json: Dict[str, Any]) -> str:
        """
        Convert JSON lesson back to markdown (round-trip).

        Args:
            lesson_json: Structured lesson data

        Returns:
            Markdown content

        Raises:
            LessonExportError: If conversion fails
        """
        try:
            # Check if raw markdown is available (easiest round-trip)
            if "raw_markdown" in lesson_json:
                return lesson_json["raw_markdown"]

            # Otherwise, reconstruct from structured data
            parts = []

            # Add frontmatter
            if "metadata" in lesson_json:
                parts.append("---")
                for key, value in lesson_json["metadata"].items():
                    if isinstance(value, str):
                        parts.append(f'{key}: "{value}"')
                    else:
                        parts.append(f'{key}: {value}')
                parts.append("---")
                parts.append("")

            # Add sections
            if "sections" in lesson_json:
                for section in lesson_json["sections"]:
                    level = section.get("level", 1)
                    title = section.get("title", "")
                    content = section.get("content", "")

                    parts.append(f"{'#' * level} {title}")
                    parts.append("")
                    parts.append(content)
                    parts.append("")

            return '\n'.join(parts)

        except Exception as e:
            logger.error(f"Markdown reconstruction failed: {e}")
            raise LessonExportError(f"Failed to convert JSON to markdown: {e}") from e
