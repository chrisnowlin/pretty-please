"""
Document rendering component for PDF and PowerPoint inputs.

Provides specialized renderer classes for different document types:
- PDFRenderer: Renders PDF pages to PNG images using PyMuPDF (fitz) at 150 DPI
- PowerPointRenderer: Renders PowerPoint slides to 1920x1080 PNG images

All renderers support progressive rendering with generators yielding (page_num, image_path) tuples.
"""
from __future__ import annotations

import logging
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)


class BaseDocumentRenderer(ABC):
    """Abstract base class for document renderers."""

    @abstractmethod
    def render_to_images(self, file_path: Path) -> List[Path]:
        """Render all pages/slides to temporary PNG images.

        Args:
            file_path: Path to the document file

        Returns:
            List of paths to temporary PNG image files
        """
        pass

    @abstractmethod
    def render_progressive(self, file_path: Path, batch_size: int) -> Iterable[Tuple[int, Path]]:
        """Render pages/slides progressively in batches.

        Args:
            file_path: Path to the document file
            batch_size: Number of pages to render per batch

        Yields:
            Tuples of (page_number, image_path) for each rendered page (1-indexed)
        """
        pass


class PDFRenderer(BaseDocumentRenderer):
    """Renderer for PDF documents using PyMuPDF (fitz) at 150 DPI."""

    def __init__(self, dpi: int = 150) -> None:
        """Initialize PDF renderer.

        Args:
            dpi: Resolution for rendering (default: 150 DPI)
        """
        self.dpi = dpi

    def render_pages(self, file_path: Path, page_numbers: List[int]) -> Dict[int, Path]:
        """Render specific PDF pages to PNG images.

        Args:
            file_path: Path to PDF file
            page_numbers: List of 0-indexed page numbers to render

        Returns:
            Dictionary mapping 1-indexed page numbers to image paths

        Raises:
            RuntimeError: If rendering fails
        """
        rendered_pages: Dict[int, Path] = {}
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(file_path))
            try:
                for page_num in page_numbers:
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=self.dpi)
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        tmp.write(pix.tobytes("png"))
                        rendered_pages[page_num + 1] = Path(tmp.name)  # 1-indexed for display
            finally:
                doc.close()

            return rendered_pages

        except Exception as e:
            raise RuntimeError(f"Unable to render PDF pages: {e}")

    def render_to_images(self, file_path: Path) -> List[Path]:
        """Render all PDF pages to temporary PNG images.

        Uses PyMuPDF (fitz) as the primary renderer with pdf2image as fallback.

        Args:
            file_path: Path to PDF file

        Returns:
            List of paths to temporary PNG image files

        Raises:
            RuntimeError: If rendering fails with both PyMuPDF and pdf2image
        """
        temp_paths = []
        try:
            # Try PyMuPDF first (no system dependencies required)
            import fitz  # PyMuPDF

            doc = fitz.open(str(file_path))
            try:
                for i in range(doc.page_count):
                    page = doc.load_page(i)
                    pix = page.get_pixmap(dpi=self.dpi)
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        tmp.write(pix.tobytes("png"))
                        temp_paths.append(Path(tmp.name))
            finally:
                doc.close()

            logger.info(f"Rendered {len(temp_paths)} pages from {file_path} using PyMuPDF")
            return temp_paths

        except Exception as e:
            logger.warning(f"PyMuPDF rendering failed: {e}, falling back to pdf2image")
            # Fallback to pdf2image (requires poppler system package)
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(str(file_path), dpi=self.dpi)
                for img in images:
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        img.save(tmp.name, format="PNG")
                        temp_paths.append(Path(tmp.name))

                logger.info(f"Rendered {len(temp_paths)} pages from {file_path} using pdf2image")
                return temp_paths

            except Exception as fallback_error:
                raise RuntimeError(
                    f"Unable to render PDF to images: PyMuPDF failed with '{e}', "
                    f"pdf2image failed with '{fallback_error}'"
                )

    def render_progressive(self, file_path: Path, batch_size: int = 5) -> Iterable[Tuple[int, Path]]:
        """Render PDF pages progressively in batches.

        This approach:
        - Renders pages in batches to manage memory
        - Yields results as they become available
        - Allows processing to start before all pages are rendered
        - Better for very large PDFs (100+ pages)

        Args:
            file_path: Path to PDF file
            batch_size: Number of pages to render per batch (default: 5)

        Yields:
            Tuples of (page_number, image_path) for each rendered page (1-indexed)

        Raises:
            RuntimeError: If rendering fails with both PyMuPDF and pdf2image
        """
        try:
            # Try PyMuPDF first
            import fitz  # PyMuPDF

            doc = fitz.open(str(file_path))
            page_count = doc.page_count

            logger.info(f"Starting progressive PDF rendering of {page_count} pages (batch size: {batch_size})")

            # Process pages in batches
            for batch_start in range(0, page_count, batch_size):
                batch_end = min(batch_start + batch_size, page_count)
                logger.debug(f"Rendering PDF batch: pages {batch_start+1}-{batch_end}/{page_count}")

                # Render pages in this batch
                for page_idx in range(batch_start, batch_end):
                    try:
                        page = doc.load_page(page_idx)
                        pix = page.get_pixmap(dpi=self.dpi)

                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            tmp.write(pix.tobytes("png"))
                            yield (page_idx + 1, Path(tmp.name))  # 1-indexed for display

                    except Exception as e:
                        logger.error(f"Failed to render PDF page {page_idx + 1}: {e}")
                        raise

            doc.close()

        except Exception as e:
            if "PyMuPDF" in str(e) or "fitz" in str(e):
                # Fallback to pdf2image
                logger.warning(f"PyMuPDF progressive rendering failed: {e}, falling back to pdf2image")
                try:
                    from pdf2image import convert_from_path
                    images = convert_from_path(str(file_path), dpi=self.dpi)
                    for page_idx, img in enumerate(images):
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            img.save(tmp.name, format="PNG")
                            yield (page_idx + 1, Path(tmp.name))

                except Exception as fallback_error:
                    raise RuntimeError(
                        f"Unable to render PDF progressively: PyMuPDF failed with '{e}', "
                        f"pdf2image failed with '{fallback_error}'"
                    )
            else:
                raise


class PowerPointRenderer(BaseDocumentRenderer):
    """Renderer for PowerPoint presentations to 1920x1080 PNG images.

    Note: This is a basic text extraction renderer. For production use,
    consider using LibreOffice or other tools for higher quality rendering.
    """

    def __init__(self, width: int = 1920, height: int = 1080) -> None:
        """Initialize PowerPoint renderer.

        Args:
            width: Output image width (default: 1920)
            height: Output image height (default: 1080)
        """
        self.width = width
        self.height = height

    def render_to_images(self, file_path: Path) -> List[Path]:
        """Render all PowerPoint slides to temporary PNG images.

        Uses python-pptx to extract text and PIL to create images.
        This is a basic fallback renderer that extracts text only.

        Args:
            file_path: Path to PowerPoint file (.pptx or .ppt)

        Returns:
            List of paths to temporary PNG image files

        Raises:
            RuntimeError: If rendering fails
        """
        temp_paths = []
        try:
            from pptx import Presentation
            from PIL import Image, ImageDraw

            prs = Presentation(str(file_path))

            for slide_idx, slide in enumerate(prs.slides):
                # Create a blank image for the slide (standard 16:9 aspect ratio)
                img = Image.new('RGB', (self.width, self.height), color='white')
                draw = ImageDraw.Draw(img)

                # Extract text from all shapes in the slide
                y_offset = 50
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        # Simple text rendering (basic fallback)
                        text = shape.text.strip()

                        # Wrap text to fit width
                        lines = self._wrap_text(text, self.width - 100)

                        for line in lines:
                            draw.text((50, y_offset), line, fill='black')
                            y_offset += 30
                        y_offset += 20  # Extra space between shapes

                # Save the rendered slide
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    img.save(tmp.name, format="PNG")
                    temp_paths.append(Path(tmp.name))

            logger.info(f"Rendered {len(temp_paths)} slides from {file_path}")
            return temp_paths

        except Exception as e:
            raise RuntimeError(
                f"Unable to render PowerPoint to images: {e}"
            )

    def render_progressive(self, file_path: Path, batch_size: int = 5) -> Iterable[Tuple[int, Path]]:
        """Render PowerPoint slides progressively in batches.

        Args:
            file_path: Path to PowerPoint file
            batch_size: Number of slides to render per batch (default: 5)

        Yields:
            Tuples of (slide_number, image_path) for each rendered slide (1-indexed)

        Raises:
            RuntimeError: If rendering fails
        """
        try:
            from pptx import Presentation
            from PIL import Image, ImageDraw

            prs = Presentation(str(file_path))
            slides = list(prs.slides)
            total_slides = len(slides)

            logger.info(f"Starting progressive PowerPoint rendering of {total_slides} slides (batch size: {batch_size})")

            # Process slides in batches
            for batch_start in range(0, total_slides, batch_size):
                batch_end = min(batch_start + batch_size, total_slides)
                logger.debug(f"Rendering PowerPoint batch: slides {batch_start+1}-{batch_end}/{total_slides}")

                # Render slides in this batch
                for slide_idx in range(batch_start, batch_end):
                    try:
                        slide = slides[slide_idx]

                        # Create a blank image for the slide
                        img = Image.new('RGB', (self.width, self.height), color='white')
                        draw = ImageDraw.Draw(img)

                        # Extract text from all shapes in the slide
                        y_offset = 50
                        for shape in slide.shapes:
                            if hasattr(shape, "text") and shape.text.strip():
                                text = shape.text.strip()
                                lines = self._wrap_text(text, self.width - 100)

                                for line in lines:
                                    draw.text((50, y_offset), line, fill='black')
                                    y_offset += 30
                                y_offset += 20  # Extra space between shapes

                        # Save the rendered slide
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            img.save(tmp.name, format="PNG")
                            yield (slide_idx + 1, Path(tmp.name))  # 1-indexed for display

                    except Exception as e:
                        logger.error(f"Failed to render PowerPoint slide {slide_idx + 1}: {e}")
                        raise

        except Exception as e:
            raise RuntimeError(
                f"Unable to render PowerPoint progressively: {e}"
            )

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within a maximum width.

        Args:
            text: Text to wrap
            max_width: Maximum width in pixels

        Returns:
            List of wrapped text lines
        """
        lines = []
        words = text.split()
        current_line = []

        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            # Rough estimate: 10 pixels per character
            if len(test_line) * 10 > max_width:
                if len(current_line) > 1:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(test_line)
                    current_line = []

        if current_line:
            lines.append(' '.join(current_line))

        return lines
