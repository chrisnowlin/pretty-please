#!/usr/bin/env python3
"""
Sequential MLX document processing with checkpoint support.

Processes pages one at a time with automatic checkpointing to allow
resuming from interruptions or failures.

Features:
- Sequential page processing (reliable, no multi-process issues)
- Checkpoint after every page (can resume from any point)
- Progress tracking and ETA calculation
- Error recovery and retry logic
- Detailed logging
"""

import sys
import time
import json
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "src"))

import fitz  # PyMuPDF
from jina_rag_pipeline.ingestion.nanonets_mlx import NanonetsMLXAnalyzer

# Configuration
MODEL_PATH = "./models/nanonets-ocr2-3b-mlx"  # Use 8-bit (4-bit produces garbage)
PDF_PATH = "./tests/fixtures/classroom_music_5pages.pdf"
OUTPUT_DIR = Path("./output/sequential_mlx")
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"
RENDER_DPI = 200
MAX_RETRIES = 3  # Retry failed pages up to 3 times


def load_checkpoint() -> Dict[str, Any]:
    """Load checkpoint from disk if it exists."""
    if CHECKPOINT_FILE.exists():
        try:
            data = json.loads(CHECKPOINT_FILE.read_text())
            print(f"✓ Loaded checkpoint: {data['pages_completed']}/{data['total_pages']} pages completed")
            return data
        except Exception as e:
            print(f"⚠️  Failed to load checkpoint: {e}")
            print("   Starting from beginning...")
    return None


def save_checkpoint(checkpoint: Dict[str, Any]):
    """Save checkpoint to disk."""
    try:
        CHECKPOINT_FILE.write_text(json.dumps(checkpoint, indent=2))
    except Exception as e:
        print(f"⚠️  Failed to save checkpoint: {e}")


def process_page(
    analyzer: NanonetsMLXAnalyzer,
    page_num: int,
    pdf_path: str,
    output_dir: Path,
    dpi: int,
    retry_count: int = 0
) -> Dict[str, Any]:
    """
    Process a single page with retry logic.

    Args:
        analyzer: MLX analyzer instance
        page_num: Page number to process
        pdf_path: Path to PDF file
        output_dir: Directory for temp files
        dpi: Rendering DPI
        retry_count: Current retry attempt (0-based)

    Returns:
        Dict with page results and metadata
    """
    start_time = time.time()

    try:
        # Render page to image
        doc = fitz.open(pdf_path)
        page = doc[page_num]

        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Save to temp file
        temp_dir = output_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        image_path = temp_dir / f"page_{page_num:04d}.png"
        pix.save(str(image_path))

        doc.close()

        render_time = time.time() - start_time

        # Analyze with MLX
        analysis_start = time.time()
        markdown = analyzer.analyze_document(str(image_path))
        regions = analyzer.extract_regions(str(image_path), page_number=page_num)
        analysis_time = time.time() - analysis_start

        total_time = time.time() - start_time

        # Clean up temp image
        image_path.unlink()

        # Save page result to individual file
        page_result_file = output_dir / "pages" / f"page_{page_num:04d}.json"
        page_result_file.parent.mkdir(parents=True, exist_ok=True)

        result = {
            "page_num": page_num,
            "success": True,
            "markdown": markdown,
            "num_regions": len(regions),
            "timing": {
                "render_sec": round(render_time, 2),
                "analysis_sec": round(analysis_time, 2),
                "total_sec": round(total_time, 2),
            },
            "retry_count": retry_count,
            "timestamp": datetime.now().isoformat(),
        }

        page_result_file.write_text(json.dumps(result, indent=2))

        return result

    except Exception as e:
        error_time = time.time() - start_time

        print(f"  ❌ Error processing page {page_num}: {e}")

        # Retry if we haven't exceeded max retries
        if retry_count < MAX_RETRIES - 1:
            print(f"  🔄 Retrying page {page_num} (attempt {retry_count + 2}/{MAX_RETRIES})...")
            time.sleep(2)  # Brief delay before retry
            return process_page(analyzer, page_num, pdf_path, output_dir, dpi, retry_count + 1)

        # Max retries exceeded
        return {
            "page_num": page_num,
            "success": False,
            "error": str(e),
            "timing": {"total_sec": round(error_time, 2)},
            "retry_count": retry_count,
            "timestamp": datetime.now().isoformat(),
        }


def format_time(seconds: float) -> str:
    """Format seconds as human-readable time."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds / 3600:.1f}h"


def main():
    print("=" * 80)
    print("SEQUENTIAL MLX DOCUMENT PROCESSING")
    print("=" * 80)
    print()
    print(f"Model: {MODEL_PATH}")
    print(f"PDF: {PDF_PATH}")
    print(f"Render DPI: {RENDER_DPI}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    # Check if PDF exists
    if not Path(PDF_PATH).exists():
        print(f"❌ PDF not found: {PDF_PATH}")
        return 1

    # Check if model exists
    if not Path(MODEL_PATH).exists():
        print(f"❌ Model not found: {MODEL_PATH}")
        return 1

    # Get page count
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    doc.close()

    print(f"Total pages: {total_pages}")
    print()

    # Determine pages to process
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        pages_to_process = list(range(total_pages))
        print("Processing FULL document")
    else:
        pages_to_process = list(range(min(10, total_pages)))
        print(f"Processing first {len(pages_to_process)} pages (test mode)")
        print("Use --full flag to process entire document")

    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load checkpoint
    checkpoint = load_checkpoint()

    if checkpoint:
        completed_pages = set(checkpoint.get("completed_pages", []))
        start_page_idx = len(completed_pages)
        results = checkpoint.get("results", [])
        session_start = checkpoint.get("session_start")
    else:
        completed_pages = set()
        start_page_idx = 0
        results = []
        session_start = datetime.now().isoformat()
        checkpoint = {
            "session_start": session_start,
            "total_pages": len(pages_to_process),
            "pages_completed": 0,
            "completed_pages": [],
            "results": [],
            "config": {
                "model_path": MODEL_PATH,
                "pdf_path": PDF_PATH,
                "render_dpi": RENDER_DPI,
            }
        }

    # Load MLX model
    print("-" * 80)
    print("Loading MLX model...")
    print("-" * 80)
    print()

    load_start = time.time()
    analyzer = NanonetsMLXAnalyzer(model_path=MODEL_PATH)
    load_time = time.time() - load_start

    print(f"✓ Model loaded in {load_time:.1f} seconds")
    print()

    # Process pages
    print("-" * 80)
    print("Processing pages...")
    print("-" * 80)
    print()

    processing_start = time.time()
    page_times = []

    for idx, page_num in enumerate(pages_to_process):
        # Skip if already completed
        if page_num in completed_pages:
            print(f"[{idx + 1}/{len(pages_to_process)}] Page {page_num}: ✓ Already completed (skipped)")
            continue

        page_start = time.time()

        # Process page
        print(f"[{idx + 1}/{len(pages_to_process)}] Page {page_num}: Processing...", end=" ", flush=True)

        result = process_page(analyzer, page_num, PDF_PATH, OUTPUT_DIR, RENDER_DPI)

        page_time = time.time() - page_start
        page_times.append(page_time)

        if result["success"]:
            print(f"✓ {page_time:.1f}s")
            completed_pages.add(page_num)
            results.append(result)
        else:
            print(f"❌ Failed after {MAX_RETRIES} retries")
            results.append(result)

        # Update checkpoint
        checkpoint["pages_completed"] = len(completed_pages)
        checkpoint["completed_pages"] = sorted(list(completed_pages))
        checkpoint["results"] = results
        save_checkpoint(checkpoint)

        # Show progress and ETA
        if len(page_times) >= 3:
            avg_time = sum(page_times[-10:]) / len(page_times[-10:])  # Rolling avg of last 10
            remaining_pages = len(pages_to_process) - len(completed_pages)
            eta_seconds = avg_time * remaining_pages

            print(f"  Progress: {len(completed_pages)}/{len(pages_to_process)} pages "
                  f"({len(completed_pages) / len(pages_to_process) * 100:.1f}%)")
            print(f"  Avg time: {avg_time:.1f}s/page, ETA: {format_time(eta_seconds)}")
            print()

    total_time = time.time() - processing_start

    # Final summary
    print()
    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print()

    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]

    print(f"Pages processed: {len(successful)}/{len(pages_to_process)}")
    if failed:
        print(f"Failed pages: {len(failed)}")
        for r in failed:
            print(f"  - Page {r['page_num']}: {r.get('error', 'Unknown error')}")

    print()
    print(f"Total time: {total_time / 60:.2f} minutes ({total_time:.1f} seconds)")
    if successful:
        print(f"Average per page: {total_time / len(successful):.2f} seconds")
    print()

    # Save final results
    final_output = OUTPUT_DIR / f"sequential_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output_data = {
        "session_start": session_start,
        "session_end": datetime.now().isoformat(),
        "config": checkpoint["config"],
        "performance": {
            "total_time_sec": round(total_time, 2),
            "model_load_time_sec": round(load_time, 2),
            "pages_processed": len(successful),
            "pages_failed": len(failed),
            "avg_time_per_page_sec": round(total_time / len(successful), 2) if successful else 0,
        },
        "results": results,
    }

    final_output.write_text(json.dumps(output_data, indent=2))
    print(f"✓ Results saved to: {final_output}")

    # Clean up checkpoint if fully completed
    if len(completed_pages) == len(pages_to_process):
        CHECKPOINT_FILE.unlink(missing_ok=True)
        print(f"✓ Checkpoint cleaned up (all pages completed)")

    print()

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
