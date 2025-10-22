from pathlib import Path
from typing import Dict, List, Optional
import logging
import os

from PIL import Image
import numpy as np

from .base import Document, DocumentLoader

from .document_renderer import PDFRenderer, PowerPointRenderer
from .analysis_pipeline import AnalysisPipeline

logger = logging.getLogger(__name__)


class TextLoader(DocumentLoader):
    def __init__(self, encoding: str = "utf-8") -> None:
        self.encoding = encoding

    def load(self, file_path: Path) -> Document:
        with open(file_path, "r", encoding=self.encoding) as f:
            content = f.read()
        return Document(content=content, source=str(file_path))

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".txt"


class MarkdownLoader(DocumentLoader):
    def __init__(self, encoding: str = "utf-8") -> None:
        self.encoding = encoding

    def load(self, file_path: Path) -> Document:
        with open(file_path, "r", encoding=self.encoding) as f:
            content = f.read()
        return Document(content=content, source=str(file_path), metadata={"format": "markdown"})

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in [".md", ".markdown"]


class PDFLoader(DocumentLoader):
    def __init__(self) -> None:
        try:
            import pypdf
            self._pypdf = pypdf
        except ImportError:
            raise ImportError("pypdf is required for PDF loading. Install with: pip install pypdf")

    def load(self, file_path: Path) -> Document:
        with open(file_path, "rb") as f:
            reader = self._pypdf.PdfReader(f)
            pages = []
            page_boundaries = []
            metadata = {}

            if reader.metadata:
                metadata.update({
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                    "producer": reader.metadata.get("/Producer", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                })

            # Extract pages and track boundaries
            current_position = 0
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                pages.append(text)

                # Track where this page starts and ends in the combined content
                page_start = current_position
                page_end = current_position + len(text)
                page_boundaries.append({
                    "page_number": page_num + 1,  # 1-indexed for user display
                    "start_index": page_start,
                    "end_index": page_end,
                })

                # Account for the "\n\n" separator between pages
                current_position = page_end + 2  # +2 for "\n\n"

            content = "\n\n".join(pages)
            metadata["page_count"] = len(pages)
            metadata["format"] = "pdf"
            metadata["page_boundaries"] = page_boundaries

        return Document(content=content, source=str(file_path), metadata=metadata)

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"


class DocxLoader(DocumentLoader):
    def __init__(self) -> None:
        try:
            import docx
            self._docx = docx
        except ImportError:
            raise ImportError("python-docx is required for DOCX loading. Install with: pip install python-docx")

    def load(self, file_path: Path) -> Document:
        doc = self._docx.Document(file_path)

        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        content = "\n\n".join(paragraphs)

        metadata = {
            "format": "docx",
            "paragraph_count": len(paragraphs),
        }

        if doc.core_properties.title:
            metadata["title"] = doc.core_properties.title
        if doc.core_properties.author:
            metadata["author"] = doc.core_properties.author
        if doc.core_properties.created:
            metadata["created"] = doc.core_properties.created.isoformat()
        if doc.core_properties.modified:
            metadata["modified"] = doc.core_properties.modified.isoformat()

        return Document(content=content, source=str(file_path), metadata=metadata)

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in [".docx", ".doc"]


class PowerPointLoader(DocumentLoader):
    """Loader for PowerPoint presentations (.pptx, .ppt).

    Supports two modes:
    - Simple mode: Extract text only
    - Layout-aware mode: Extract regions with layout analysis (optional)
    """

    def __init__(self, use_layout_analysis: bool = False) -> None:
        """Initialize PowerPoint loader.

        Args:
            use_layout_analysis: Enable layout analysis for mixed content processing
        """
        try:
            from pptx import Presentation
            self._pptx = Presentation
        except ImportError:
            raise ImportError(
                "python-pptx is required for PowerPoint loading. "
                "Install with: pip install 'python-pptx>=0.6.21'"
            )

        self.use_layout_analysis = use_layout_analysis

        if use_layout_analysis:
            try:
                from .deepseek_layout import create_analyzer
                self.layout_analyzer = create_analyzer()
                logger.info("DeepseekLayoutAnalyzer initialized for PowerPoint loader")
            except ImportError:
                raise ImportError(
                    "Deepseek dependencies are required for layout-aware mode. "
                    "Install with: pip install pillow torch transformers"
                )

    def load(self, file_path: Path) -> Document:
        """Load PowerPoint file.

        Args:
            file_path: Path to .pptx or .ppt file

        Returns:
            Document with extracted content
        """
        if self.use_layout_analysis:
            # Layout-aware mode will be implemented in Phase 3
            return self._load_with_layout(file_path)
        else:
            return self._load_simple(file_path)

    def _load_simple(self, file_path: Path) -> Document:
        """Simple text-only extraction from PowerPoint.

        Args:
            file_path: Path to PowerPoint file

        Returns:
            Document with combined text from all slides
        """
        try:
            prs = self._pptx(file_path)

            slides_text = []
            slide_metadata = []

            for slide_num, slide in enumerate(prs.slides, start=1):
                slide_text_parts = []

                # Extract text from all shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text_parts.append(shape.text.strip())

                    # Extract text from table cells if present
                    if hasattr(shape, "table"):
                        table = shape.table
                        for row in table.rows:
                            row_text = []
                            for cell in row.cells:
                                if cell.text.strip():
                                    row_text.append(cell.text.strip())
                            if row_text:
                                slide_text_parts.append(" | ".join(row_text))

                # Combine text from this slide
                slide_text = "\n".join(slide_text_parts)
                slides_text.append(f"--- Slide {slide_num} ---\n{slide_text}")

                # Track slide metadata
                slide_metadata.append({
                    "slide_number": slide_num,
                    "shape_count": len(slide.shapes),
                    "text_length": len(slide_text),
                })

            # Combine all slides
            content = "\n\n".join(slides_text)

            # Build document metadata
            metadata = {
                "format": "pptx",
                "slide_count": len(prs.slides),
                "total_shapes": sum(len(slide.shapes) for slide in prs.slides),
                "slides": slide_metadata,
            }

            # Extract presentation properties if available
            if hasattr(prs.core_properties, "title") and prs.core_properties.title:
                metadata["title"] = prs.core_properties.title
            if hasattr(prs.core_properties, "author") and prs.core_properties.author:
                metadata["author"] = prs.core_properties.author
            if hasattr(prs.core_properties, "created") and prs.core_properties.created:
                metadata["created"] = prs.core_properties.created.isoformat()
            if hasattr(prs.core_properties, "modified") and prs.core_properties.modified:
                metadata["modified"] = prs.core_properties.modified.isoformat()

            return Document(content=content, source=str(file_path), metadata=metadata)

        except Exception as e:
            logger.error(f"Failed to load PowerPoint file {file_path}: {e}")
            raise ValueError(f"Failed to load PowerPoint file: {str(e)}")

    def _load_with_layout(self, file_path: Path) -> Document:
        """Load PowerPoint with Deepseek layout analysis.

        Converts slides to images, runs semantic analysis, and extracts regions.

        Args:
            file_path: Path to PowerPoint file

        Returns:
            Document with semantic regions metadata
        """
        import tempfile
        from PIL import Image as PILImage
        import io

        try:
            prs = self._pptx(file_path)

            # Collect all semantic regions from all slides
            all_regions = []
            document_id = file_path.stem

            # Process each slide
            for slide_num, slide in enumerate(prs.slides, start=1):
                logger.info(f"Processing slide {slide_num}/{len(prs.slides)} with Deepseek OCR")

                # Render slide to image for analysis
                # Note: python-pptx doesn't directly export to image
                # We'll use a workaround to export each slide

                # Check if slide has any image shapes we can analyze directly
                has_embedded_images = False
                for shape in slide.shapes:
                    if hasattr(shape, "image"):
                        try:
                            # Extract embedded image
                            image_bytes = shape.image.blob
                            pil_image = PILImage.open(io.BytesIO(image_bytes))

                            # Create temporary file for Deepseek analysis
                            with tempfile.NamedTemporaryFile(
                                suffix=".png", delete=False
                            ) as tmp_file:
                                tmp_path = Path(tmp_file.name)
                                pil_image.save(tmp_path, format="PNG")

                                try:
                                    # Run Deepseek analysis
                                    regions = self.layout_analyzer.extract_regions(
                                        file_path=tmp_path,
                                        page_number=slide_num,
                                        document_id=document_id,
                                    )

                                    all_regions.extend(regions)
                                    has_embedded_images = True

                                finally:
                                    # Clean up temp file
                                    tmp_path.unlink(missing_ok=True)

                        except Exception as e:
                            logger.warning(
                                f"Failed to analyze embedded image in slide {slide_num}: {e}"
                            )

                # If slide has no embedded images, extract text shapes manually
                if not has_embedded_images:
                    from .semantic_region import SemanticRegion
                    from datetime import datetime

                    shape_idx = 0
                    for shape in slide.shapes:
                        if hasattr(shape, "text") and shape.text.strip():
                            region_id = f"{document_id}_slide{slide_num}_shape{shape_idx}"

                            # Determine region type from shape name
                            region_type = "text"
                            if hasattr(shape, "name"):
                                name_lower = shape.name.lower()
                                if "title" in name_lower:
                                    region_type = "title"

                            # Create semantic region for text shape
                            text_region = SemanticRegion(
                                region_id=region_id,
                                region_type=region_type,
                                region_sequence=shape_idx,
                                page_number=slide_num,
                                content=shape.text.strip(),
                                raw_markdown=shape.text.strip(),
                                semantic_tags=["extracted_from_pptx"],
                            )

                            all_regions.append(text_region)
                            shape_idx += 1

            # Create combined content from all regions
            content_parts = []
            for region in all_regions:
                if region.region_type in ["text", "title"]:
                    content_parts.append(
                        f"--- Slide {region.page_number} ({region.region_type}) ---\n{region.content}"
                    )
                elif region.region_type == "table":
                    content_parts.append(
                        f"--- Slide {region.page_number} (table) ---\n{region.table_html or region.content}"
                    )

            content = "\n\n".join(content_parts) if content_parts else "[No content extracted]"

            # Build metadata with semantic regions
            metadata = {
                "format": "pptx",
                "slide_count": len(prs.slides),
                "regions": [region.to_dict() for region in all_regions],
                "layout_analysis_enabled": True,
                "layout_analyzer": "deepseek-ocr",
                "region_count": len(all_regions),
                "region_type_counts": {
                    region_type: sum(1 for r in all_regions if r.region_type == region_type)
                    for region_type in ["text", "table", "image", "equation", "list", "title"]
                },
            }

            # Extract presentation properties
            if hasattr(prs.core_properties, "title") and prs.core_properties.title:
                metadata["title"] = prs.core_properties.title
            if hasattr(prs.core_properties, "author") and prs.core_properties.author:
                metadata["author"] = prs.core_properties.author
            if hasattr(prs.core_properties, "created") and prs.core_properties.created:
                metadata["created"] = prs.core_properties.created.isoformat()

            logger.info(
                f"Deepseek analysis complete: {len(all_regions)} regions from {len(prs.slides)} slides"
            )

            return Document(content=content, source=str(file_path), metadata=metadata)

        except Exception as e:
            logger.error(f"Failed to load PowerPoint with Deepseek OCR: {e}")
            # Fall back to simple mode
            logger.warning("Falling back to simple text extraction")
            return self._load_simple(file_path)

    def supports(self, file_path: Path) -> bool:
        """Check if this loader supports the given file.

        Args:
            file_path: Path to file

        Returns:
            True if file extension is .pptx or .ppt
        """
        return file_path.suffix.lower() in [".pptx", ".ppt"]

class OCRLoader(DocumentLoader):
    """Route supported files through Deepseek OCR (PDFs, images, and PowerPoint).

    Supports progressive rendering with parallel processing and checkpoint recovery:
    - Progressive rendering: Process pages in batches for better memory usage
    - Parallel rendering: Use multiple workers for faster page rendering

    - Checkpoint/resume: Automatically resume processing after crashes

    Falls back to existing loaders only if rendering libraries are unavailable.
    """

    SUPPORTED_FORMATS = [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".pptx", ".ppt"]

    def __init__(
        self,
        analyzer=None,
        progressive: bool = True,  # Now enabled by default
        batch_size: int = None,  # Auto-detect from profile if None
        max_render_workers: int = None,  # Auto-detect from profile if None
        max_analysis_workers: int = None,  # Auto-detect from profile if None
        enable_checkpoints: bool = True,
        checkpoint_dir: Path = None
    ) -> None:
        """Initialize Deepseek OCR loader with aggressive configuration support.

        Args:

            analyzer: Optional pre-initialized analyzer
            progressive: Use progressive PDF rendering (default: True)
            batch_size: Pages per batch (default: auto-detect from profile)
            max_render_workers: Parallel render workers (default: auto-detect from profile)
            max_analysis_workers: Parallel analysis workers (default: auto-detect from profile)
            enable_checkpoints: Enable checkpoint/resume support (default: True)
            checkpoint_dir: Directory for checkpoints (default: ./checkpoints)
        """
        self._analyzer = analyzer
        self._create_analyzer = None
        self.progressive = progressive
        self.enable_checkpoints = enable_checkpoints

        # Configuration: use OCRConfig presets instead of profile system
        # Prefer legacy profile if available to maintain backward compatibility
        profile = None
        try:
            from ..config import get_profile
            profile = get_profile()
            logger.info(f"Loaded processing profile: {profile.name}")
        except Exception:
            profile = None

        if profile:
            self.batch_size = batch_size or profile.render_batch_size
            self.max_render_workers = max_render_workers or profile.max_render_workers
            self.max_analysis_workers = max_analysis_workers or profile.max_analysis_workers
            self.pre_render_batches = 4  # Default for profile-based config
        else:
            try:
                from .ocr_config import OCRConfig
                import platform as _platform
                is_apple = _platform.system() == "Darwin" and _platform.machine().lower().startswith("arm")
                preset = OCRConfig.deepseek_small() if is_apple else OCRConfig.deepseek_balanced()
            except Exception:
                preset = None

            self.batch_size = batch_size or (preset.batch_size if preset else 10)
            self.max_render_workers = max_render_workers or (preset.render_workers if preset else 4)
            self.max_analysis_workers = max_analysis_workers or (preset.analysis_workers if preset else 2)
            self.pre_render_batches = preset.pre_render_batches if preset else 4


        # Components - use specialized renderers
        self.pdf_renderer = PDFRenderer(dpi=150)
        self.pptx_renderer = PowerPointRenderer(width=1920, height=1080)
        self.pipeline = AnalysisPipeline(analysis_workers=self.max_analysis_workers)

        # Initialize checkpoint manager
        if self.enable_checkpoints:
            try:
                from .checkpoint import CheckpointManager
                self.checkpoint_manager = CheckpointManager(
                    base_dir=checkpoint_dir or Path("./checkpoints")
                )
                logger.info("Checkpoint manager initialized")
            except ImportError:
                logger.warning("Checkpoint module not available, disabling checkpoints")
                self.enable_checkpoints = False
                self.checkpoint_manager = None
        else:
            self.checkpoint_manager = None

        logger.info(
            f"Deepseek OCR loader initialized: "
            f"batch_size={self.batch_size}, "
            f"render_workers={self.max_render_workers}, "
            f"analysis_workers={self.max_analysis_workers}, "
            f"checkpoints={self.enable_checkpoints}"
        )

        if self._analyzer is None and self._create_analyzer is None:
            try:
                from .deepseek_layout import create_analyzer
                self._create_analyzer = lambda: create_analyzer()
            except Exception as e:
                raise ImportError(f"Deepseek analyzer not available: {e}") from e

    def _get_analyzer(self):
        if self._analyzer is None:
            # Instantiate lazily; create_analyzer selects best device
            self._analyzer = self._create_analyzer() if self._create_analyzer else None
        return self._analyzer

    def _render_pdf_to_images(self, file_path: Path):
        """Render PDF pages to temporary PNG images and return their Paths.

        Delegates to PDFRenderer component.
        """
        return self.pdf_renderer.render_to_images(file_path)

    def _render_pdf_progressive(self, file_path: Path, batch_size: int = 5):
        """Render PDF pages progressively in batches, yielding (page_num, image_path) tuples.

        Delegates to PDFRenderer component.

        This approach:
        - Renders pages in batches to manage memory
        - Yields results as they become available
        - Allows processing to start before all pages are rendered
        - Better for very large PDFs (100+ pages)

        Args:
            file_path: Path to PDF file
            batch_size: Number of pages to render before yielding (default: 5)

        Yields:
            Tuple of (page_number, image_path) for each rendered page
        """
        return self.pdf_renderer.render_progressive(file_path, batch_size)

    def _render_pptx_to_images(self, file_path: Path):
        """Render PowerPoint slides to temporary PNG images and return their Paths.

        Delegates to PowerPointRenderer component.
        """
        return self.pptx_renderer.render_to_images(file_path)

    def load(
        self,
        file_path: Path,
        progress_callback=None,
        collection_name: str = "default",
        resume: bool = True
    ) -> Document:
        """Load and process document with checkpoint/resume support.

        Args:
            file_path: Path to document
            progress_callback: Optional progress callback (page, total, message)
            collection_name: Collection name for checkpoint isolation
            resume: Auto-resume from checkpoint if available

        Returns:
            Document with extracted content
        """
        analyzer = self._get_analyzer()
        if analyzer is None:
            raise RuntimeError("Deepseek analyzer unavailable")

        suffix = file_path.suffix.lower()
        resolution = getattr(analyzer, "resolution_mode", None)
        if hasattr(resolution, "value"):
            resolution = resolution.value

        metadata = {
            "extraction_method": "deepseek-ocr",
            "ocr_engine": "deepseek",
            "resolution_mode": resolution,
            "grounding_enabled": getattr(analyzer, "enable_grounding", None),
            "compression_enabled": getattr(analyzer, "enable_compression", None),
        }

        try:
            if suffix == ".pdf":
                return self._load_pdf_with_checkpoints(
                    file_path,
                    analyzer,
                    progress_callback,
                    collection_name,
                    resume,
                    metadata
                )
            elif suffix in (".pptx", ".ppt"):
                return self._load_pptx(file_path, analyzer, progress_callback, metadata)
            else:
                # Image-like inputs
                md = analyzer.analyze_document(file_path, page_number=1)
                content = md if md and md.strip() else ""

                if not content:
                    raise RuntimeError("Empty content from Deepseek analyzer")

                metadata["format"] = "image"
                return Document(content=content, source=str(file_path), metadata=metadata)

        except Exception as e:
            logger.error(f"Deepseek OCR extraction failed for {file_path}: {e}")
            raise

    def _load_pdf_with_checkpoints(
        self,
        file_path: Path,
        analyzer,
        progress_callback,
        collection_name: str,
        resume: bool,
        metadata: dict
    ) -> Document:
        """Load PDF with checkpoint/resume and overlapping pipeline parallelism."""
        import fitz
        from concurrent.futures import ThreadPoolExecutor
        from collections import deque

        # Get total page count
        doc = fitz.open(str(file_path))
        total_pages = doc.page_count
        doc.close()
        metadata["page_count"] = total_pages

        logger.info(
            f"Processing PDF: {file_path.name} "
            f"({total_pages} pages, batch_size={self.batch_size}, "
            f"pre_render_batches={self.pre_render_batches})"
        )

        # Load or create checkpoint
        checkpoint = None
        start_page = 0

        if self.enable_checkpoints and resume and self.checkpoint_manager:
            checkpoint = self.checkpoint_manager.load(file_path, collection_name)
            if checkpoint:
                start_page = checkpoint.last_page_completed + 1
                logger.info(
                    f"Resuming from checkpoint: page {start_page + 1}/{total_pages}"
                )

        if not checkpoint and self.enable_checkpoints and self.checkpoint_manager:
            checkpoint = self.checkpoint_manager.create(
                file_path, collection_name, total_pages
            )

        # Process pages in batches with overlapping pipeline
        content_parts = []
        all_semantic_regions = []  # Collect semantic regions for chunking

        if checkpoint:
            # Restore already processed pages
            content_parts = [
                r.get("content", "") for r in checkpoint.page_results
            ]

        # Calculate total batches
        remaining_pages = total_pages - start_page
        total_batches = (remaining_pages + self.batch_size - 1) // self.batch_size

        # Queue of futures for pre-rendered batches
        render_queue = deque()

        source_binding = hasattr(analyzer, "set_source_document")
        if source_binding:
            analyzer.set_source_document(file_path)

        try:
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix="render") as render_executor:
                # Pre-fill the queue with initial batches
                initial_batches = min(self.pre_render_batches, total_batches)
                for batch_idx in range(initial_batches):
                    batch_start = start_page + (batch_idx * self.batch_size)
                    batch_end = min(batch_start + self.batch_size, total_pages)
                    page_numbers = list(range(batch_start, batch_end))

                    future = render_executor.submit(
                        self.pdf_renderer.render_pages,
                        file_path,
                        page_numbers
                    )
                    render_queue.append((batch_start, batch_end, page_numbers, future))

                logger.info(
                    f"Pipeline initialized: {initial_batches} batches pre-submitted for rendering"
                )

                next_batch_idx = initial_batches

                # Process batches in FIFO order (maintains sequential order for checkpointing)
                while render_queue:
                    # Pop the oldest batch from queue
                    batch_start, batch_end, page_numbers, future = render_queue.popleft()

                    # Log pipeline depth (before waiting)
                    logger.info(
                        f"Pipeline depth: {len(render_queue)} batches queued, "
                        f"processing pages {batch_start + 1}-{batch_end}/{total_pages}"
                    )

                    # Wait for this batch to finish rendering
                    rendered_pages = future.result()

                    # Submit next batch to keep queue full
                    if next_batch_idx < total_batches:
                        next_start = start_page + (next_batch_idx * self.batch_size)
                        next_end = min(next_start + self.batch_size, total_pages)
                        next_pages = list(range(next_start, next_end))

                        next_future = render_executor.submit(
                            self.pdf_renderer.render_pages,
                            file_path,
                            next_pages
                        )
                        render_queue.append((next_start, next_end, next_pages, next_future))
                        logger.debug(
                            f"Submitted next batch for rendering: pages {next_start + 1}-{next_end}"
                        )
                        next_batch_idx += 1

                    # Batch analysis with semantic region extraction via component
                    batch_results, batch_regions = self.pipeline.analyze_pages(
                        rendered_pages,
                        analyzer,
                    )

                    # Collect semantic regions for document metadata
                    all_semantic_regions.extend(batch_regions)

                    # Add results to content
                    for page_num, content, img_path in batch_results:
                        content_parts.append(content)

                        # Update checkpoint
                        if checkpoint:
                            checkpoint.page_results.append({
                                "page_num": page_num,
                                "content": content,
                            })
                            checkpoint.last_page_completed = page_num - 1  # 0-indexed
                            checkpoint.processed_pages = len(checkpoint.page_results)

                        # Cleanup temp image
                        try:
                            if img_path and img_path.exists():
                                img_path.unlink()
                        except Exception:
                            pass

                        # Report progress
                        if progress_callback:
                            progress_callback(
                                page_num, total_pages, f"Processed page {page_num}"
                            )

                    # Save checkpoint after each batch
                    if checkpoint and self.checkpoint_manager:
                        self.checkpoint_manager.save(checkpoint)
                        logger.debug(f"Checkpoint saved: {batch_end}/{total_pages} pages")

            # Cleanup checkpoint on success
            if checkpoint and self.checkpoint_manager:
                self.checkpoint_manager.delete(checkpoint)
                logger.info("Processing complete, checkpoint deleted")
        finally:
            if source_binding:
                analyzer.set_source_document(None)

        # Combine content
        content = "\n\n".join(part for part in content_parts if part)
        if not content.strip():
            raise RuntimeError("Empty content from Deepseek analyzer")

        # Add semantic regions to metadata for structure-preserving chunking
        metadata["format"] = "pdf"
        metadata["regions"] = all_semantic_regions  # Used by SemanticRegionChunker
        metadata["region_count"] = len(all_semantic_regions)

        logger.info(
            f"Document processing complete: {len(content)} characters, "
            f"{len(all_semantic_regions)} semantic regions"
        )

        return Document(content=content, source=str(file_path), metadata=metadata)

    def _render_pages_parallel(
        self, file_path: Path, page_numbers: List[int], max_workers: int
    ) -> Dict[int, Path]:
        """Render PDF pages sequentially (PyMuPDF is not thread-safe).

        Note: Despite the name, this renders sequentially because PyMuPDF
        is not thread-safe. Concurrent fitz.open() calls cause semaphore
        leaks and race conditions. The method name is kept for API compatibility.

        Args:
            file_path: Path to PDF
            page_numbers: List of page numbers to render (0-indexed)
            max_workers: Ignored (kept for API compatibility)

        Returns:
            Dict mapping page_number to rendered image path
        """
        import tempfile
        import fitz

        rendered_pages = {}

        try:
            # Open PDF once in main thread (thread-safe)
            doc = fitz.open(str(file_path))

            for page_num in page_numbers:
                try:
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=150)

                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        tmp.write(pix.tobytes("png"))
                        temp_path = Path(tmp.name)
                        rendered_pages[page_num + 1] = temp_path  # 1-indexed

                except Exception as e:
                    logger.error(f"Failed to render page {page_num + 1}: {e}")
                    raise
        finally:
            # Ensure PDF is closed even if rendering fails
            doc.close()

        return rendered_pages

    def _analyze_pages_parallel(
        self,
        rendered_pages: Dict[int, Path],
        analyzer,
        max_workers: int
    ) -> tuple:
        """Analyze pages using batch inference with semantic region extraction.

        Note: Despite the name, this uses batch inference rather than threading
        because PyTorch transformer models are not thread-safe. Batch inference
        provides better performance (25-50% faster) while maintaining thread
        safety. The method name is kept for API compatibility.

        This method also extracts semantic regions (tables, equations, headings)
        which enables structure-preserving chunking downstream.

        Args:
            rendered_pages: Dict of page_num -> image_path
            analyzer: Deepseek analyzer instance
            max_workers: Used as batch_size hint (adjusted by profile)

        Returns:
            Tuple of (results, regions) where:
            - results: List of (page_num, content, img_path) tuples in page order
            - regions: List of all SemanticRegion objects across pages
        """
        from ..config import get_profile

        # Get profile-based batch size
        profile = get_profile()
        # Use aggressive batch sizes: 8 for aggressive, 4 for balanced, 2 for conservative
        batch_size = min(max_workers, profile.max_analysis_workers)

        # Prepare batch inputs in sorted order
        sorted_pages = sorted(rendered_pages.keys())
        img_paths = [rendered_pages[pn] for pn in sorted_pages]

        logger.info(
            f"Analyzing {len(img_paths)} pages using batch inference "
            f"(batch_size={batch_size}, profile={profile.name})"
        )

        try:
            # Batch region extraction - processes multiple images efficiently
            all_regions_list = analyzer.extract_regions_batch(
                file_paths=img_paths,
                page_numbers=sorted_pages,
                batch_size=batch_size
            )

            # Convert regions to markdown content + collect all regions
            results = []
            all_regions = []

            for page_num, regions, img_path in zip(sorted_pages, all_regions_list, img_paths):
                # Convert regions to markdown for document content
                if regions:
                    # Join region content with double newlines
                    content = "\n\n".join(r.content for r in regions if r.content)
                else:
                    content = ""
                    logger.warning(f"No regions extracted from page {page_num}")

                results.append((page_num, content, img_path))
                all_regions.extend(regions)

                logger.debug(
                    f"Page {page_num}: extracted {len(regions)} regions, "
                    f"{len(content)} characters"
                )

            logger.info(
                f"Batch analysis complete: {len(all_regions)} total semantic regions "
                f"from {len(img_paths)} pages"
            )

            return results, all_regions

        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            raise

    def _load_pptx(
        self,
        file_path: Path,
        analyzer,
        progress_callback,
        metadata: dict
    ) -> Document:
        """Load PowerPoint presentation using batch inference with semantic regions."""
        from ..config import get_profile

        slide_image_paths = self._render_pptx_to_images(file_path)
        metadata["slide_count"] = len(slide_image_paths)
        metadata["format"] = "powerpoint"

        logger.info(
            f"Rendering PowerPoint complete: {len(slide_image_paths)} slides to process"
        )

        # Get profile-based batch size
        profile = get_profile()
        batch_size = profile.max_analysis_workers  # 6 for aggressive, 4 for balanced

        # Prepare slide numbers (1-indexed for slides)
        slide_numbers = list(range(1, len(slide_image_paths) + 1))

        try:
            if hasattr(analyzer, "set_source_document"):
                analyzer.set_source_document(file_path)

            # Batch region extraction for all slides
            logger.info(
                f"Analyzing {len(slide_image_paths)} slides using batch inference "
                f"(batch_size={batch_size}, profile={profile.name})"
            )

            all_regions_list = analyzer.extract_regions_batch(
                file_paths=slide_image_paths,
                page_numbers=slide_numbers,
                batch_size=batch_size
            )

            # Convert regions to content and collect all regions
            content_parts = []
            all_semantic_regions = []

            for idx, (img_path, regions) in enumerate(zip(slide_image_paths, all_regions_list), start=1):
                # Convert regions to markdown
                if regions:
                    slide_content = "\n\n".join(r.content for r in regions if r.content)
                else:
                    slide_content = ""
                    logger.warning(f"No regions extracted from slide {idx}")

                content_parts.append(slide_content)
                all_semantic_regions.extend(regions)

                # Report progress
                if progress_callback:
                    progress_callback(idx, len(slide_image_paths), f"Processed slide {idx}")

                # Cleanup temp image
                try:
                    img_path.unlink(missing_ok=True)
                except Exception:
                    pass

        finally:
            if hasattr(analyzer, "set_source_document"):
                analyzer.set_source_document(None)
            # Ensure cleanup of any remaining temp files
            for img_path in slide_image_paths:
                try:
                    img_path.unlink(missing_ok=True)
                except Exception:
                    pass

        content = "\n\n".join(part for part in content_parts if part)
        if not content.strip():
            raise RuntimeError("Empty content from Deepseek analyzer")

        # Add semantic regions to metadata for structure-preserving chunking
        metadata["regions"] = all_semantic_regions  # Used by SemanticRegionChunker
        metadata["region_count"] = len(all_semantic_regions)

        logger.info(
            f"PowerPoint processing complete: {len(content)} characters, "
            f"{len(all_semantic_regions)} semantic regions"
        )

        return Document(content=content, source=str(file_path), metadata=metadata)

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS



class ImageLoader(DocumentLoader):
    """Loader for image files that extracts metadata and validates images."""

    SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]
    MAX_DIMENSION = 10000  # Maximum width or height

    def __init__(self) -> None:
        pass

    def load(self, file_path: Path) -> Document:
        """Load image and extract metadata."""
        try:
            # Load image using PIL
            image = Image.open(file_path)

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Get basic image properties
            width, height = image.size
            format_name = image.format or file_path.suffix.lstrip('.').upper()

            # Validate dimensions
            if width > self.MAX_DIMENSION or height > self.MAX_DIMENSION:
                raise ValueError(f"Image dimensions {width}x{height} exceed maximum of {self.MAX_DIMENSION}px")

            # Extract EXIF metadata if available
            exif_metadata = {}
            try:
                exif = image.getexif()
                if exif:
                    # Extract common EXIF tags
                    from PIL.ExifTags import TAGS
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        # Skip GPS data for privacy
                        if isinstance(tag, str) and 'GPS' not in tag:
                            exif_metadata[tag] = str(value)
            except Exception as e:
                logger.debug(f"Failed to extract EXIF data from {file_path}: {e}")

            # Calculate image statistics
            np_image = np.array(image)
            mean_rgb = np_image.mean(axis=(0, 1)).tolist()
            std_rgb = np_image.std(axis=(0, 1)).tolist()

            # Build metadata
            metadata = {
                "modality": "image",
                "format": format_name.lower(),
                "file_type": file_path.suffix.lower(),
                "width": width,
                "height": height,
                "aspect_ratio": round(width / height, 2),
                "pixels": width * height,
                "mean_rgb": mean_rgb,
                "std_rgb": std_rgb,
                "file_size": file_path.stat().st_size,
            }

            # Add EXIF metadata if available
            if exif_metadata:
                metadata["exif"] = exif_metadata

            # For images, content is empty (embeddings come from visual features)
            # But we include a description for metadata purposes
            content = f"Image: {file_path.name} ({width}x{height}px, {format_name})"

            return Document(content=content, source=str(file_path), metadata=metadata)

        except Exception as e:
            logger.error(f"Failed to load image {file_path}: {e}")
            raise ValueError(f"Failed to load image {file_path}: {str(e)}")

    def supports(self, file_path: Path) -> bool:
        """Check if this loader supports the given file."""
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS


NanonetsFirstLoader = OCRLoader


class LoaderFactory:
    def __init__(self) -> None:
        self._loaders: List[DocumentLoader] = []
        self._register_default_loaders()

    def _register_default_loaders(self) -> None:
        self._loaders.append(TextLoader())
        self._loaders.append(MarkdownLoader())

        # Deepseek OCR routing for PDFs, images, and presentations
        deepseek_flag = os.getenv("DEEPSEEK_OCR_ENABLED", "true")
        deepseek_enabled = deepseek_flag.lower() in ("true", "1", "yes")

        if deepseek_enabled:
            try:
                self._loaders.append(OCRLoader())
                logger.info("Deepseek OCR loader registered (PDFs, PPTX, and images will use Deepseek OCR)")
            except Exception as e:
                logger.warning(f"Deepseek OCR loader unavailable: {e}")
        else:
            logger.info("Deepseek OCR loader disabled via DEEPSEEK_OCR_ENABLED=false")

        # Traditional loaders (used as fallback or when Deepseek disabled)
        self._loaders.append(ImageLoader())

        try:
            self._loaders.append(PDFLoader())
        except ImportError:
            pass

        try:
            self._loaders.append(DocxLoader())
        except ImportError:
            pass

        try:
            self._loaders.append(PowerPointLoader())
        except ImportError:
            logger.warning(
                "PowerPoint loader not available. Install python-pptx to enable .pptx/.ppt support"
            )
            pass

    def register_loader(self, loader: DocumentLoader) -> None:
        self._loaders.append(loader)

    def get_loader(self, file_path: Path) -> Optional[DocumentLoader]:
        for loader in self._loaders:
            if loader.supports(file_path):
                return loader
        return None

    def load(self, file_path: Path) -> Document:
        loader = self.get_loader(file_path)
        if loader is None:
            raise ValueError(f"No loader found for file: {file_path}")
        return loader.load(file_path)
