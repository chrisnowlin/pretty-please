"""Distributed task definitions for RQ worker processing.

This module defines tasks that can be queued and executed by RQ workers.
Each task is designed to be independently executable and provide progress tracking.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import time

logger = logging.getLogger(__name__)


def process_pdf(
    file_path: str,
    document_id: str,
    progress_callback: Optional[Callable] = None,
    batch_size: int = 5,
) -> Dict[str, Any]:
    """Process PDF through Deepseek OCR in a distributed worker.

    This task is designed to run in an RQ worker for large PDF processing.

    Args:
        file_path: Path to PDF file
        document_id: Unique document identifier
        progress_callback: Optional callback for progress updates
        batch_size: Pages per batch for progressive rendering

    Returns:
        Dict with processing results and metadata
    """
    from ..ingestion.deepseek_loader import DeepseekLoader
    from ..ingestion.ocr_config import OCRConfig

    logger.info(f"Starting RQ task: process_pdf for {file_path}")
    start_time = time.time()

    try:
        file_path = Path(file_path)

        # Use custom batch size for worker processing
        loader = DeepseekLoader(config=OCRConfig(batch_size=batch_size))

        # Process document
        document = loader.load(file_path, progress_callback=progress_callback)

        elapsed = time.time() - start_time

        result = {
            "status": "success",
            "document_id": document_id,
            "file_path": str(file_path),
            "extraction_method": document.metadata.get("extraction_method"),
            "page_count": document.metadata.get("page_count"),
            "content_length": len(document.content),
            "elapsed_seconds": elapsed,
            "metadata": document.metadata,
        }

        logger.info(f"RQ task completed: {result['page_count']} pages in {elapsed:.1f}s")
        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"RQ task failed after {elapsed:.1f}s: {e}")
        return {
            "status": "error",
            "document_id": document_id,
            "file_path": str(file_path),
            "error": str(e),
            "elapsed_seconds": elapsed,
        }


def process_pptx(
    file_path: str,
    document_id: str,
    progress_callback: Optional[Callable] = None,
) -> Dict[str, Any]:
    """Process PowerPoint through Deepseek OCR in a distributed worker.

    Args:
        file_path: Path to PPTX file
        document_id: Unique document identifier
        progress_callback: Optional callback for progress updates

    Returns:
        Dict with processing results and metadata
    """
    from ..ingestion.deepseek_loader import DeepseekLoader
    from ..ingestion.ocr_config import OCRConfig

    logger.info(f"Starting RQ task: process_pptx for {file_path}")
    start_time = time.time()

    try:
        file_path = Path(file_path)

        # Use smaller batch size for PPTX slides
        loader = DeepseekLoader(config=OCRConfig(batch_size=5))

        # Process document
        document = loader.load(file_path, progress_callback=progress_callback)

        elapsed = time.time() - start_time

        result = {
            "status": "success",
            "document_id": document_id,
            "file_path": str(file_path),
            "extraction_method": document.metadata.get("extraction_method"),
            "slide_count": document.metadata.get("slide_count"),
            "content_length": len(document.content),
            "elapsed_seconds": elapsed,
            "metadata": document.metadata,
        }

        logger.info(f"RQ task completed: {result['slide_count']} slides in {elapsed:.1f}s")
        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"RQ task failed after {elapsed:.1f}s: {e}")
        return {
            "status": "error",
            "document_id": document_id,
            "file_path": str(file_path),
            "error": str(e),
            "elapsed_seconds": elapsed,
        }


def process_chunks(
    file_path: str,
    document_id: str,
    chunk_size: int = 1000,
) -> Dict[str, Any]:
    """Process document chunks in a distributed worker.

    Args:
        file_path: Path to document file
        document_id: Unique document identifier
        chunk_size: Size of chunks in characters

    Returns:
        Dict with processing results and metadata
    """
    from ..ingestion import DocumentProcessor

    logger.info(f"Starting RQ task: process_chunks for {file_path}")
    start_time = time.time()

    try:
        file_path = Path(file_path)
        processor = DocumentProcessor()

        # Process chunks
        chunks = processor.process(file_path, skip_if_processed=False)

        elapsed = time.time() - start_time

        result = {
            "status": "success",
            "document_id": document_id,
            "file_path": str(file_path),
            "chunk_count": len(chunks) if chunks else 0,
            "elapsed_seconds": elapsed,
        }

        logger.info(f"RQ task completed: {result['chunk_count']} chunks in {elapsed:.1f}s")
        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"RQ task failed after {elapsed:.1f}s: {e}")
        return {
            "status": "error",
            "document_id": document_id,
            "file_path": str(file_path),
            "error": str(e),
            "elapsed_seconds": elapsed,
        }
