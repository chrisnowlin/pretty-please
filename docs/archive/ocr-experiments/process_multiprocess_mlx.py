#!/usr/bin/env python3
"""
Multi-process MLX document processing.

Uses process-based parallelism to run multiple MLX model instances
simultaneously, bypassing thread-safety limitations.

Each worker process:
- Loads its own MLX model instance
- Processes assigned pages independently
- Returns results to main process

Target: 8 workers for ~6-7 minute processing of 96 pages
"""

import sys
import time
import json
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from multiprocessing import Pool, Manager, cpu_count
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

import fitz  # PyMuPDF
from jina_rag_pipeline.ingestion.nanonets_mlx import NanonetsMLXAnalyzer

# Configuration
NUM_WORKERS = 8
MODEL_PATH = "./models/nanonets-ocr2-3b-mlx-4bit"
PDF_PATH = "./tests/fixtures/classroom_music_5pages.pdf"
OUTPUT_DIR = Path("./output/multiprocess_mlx")
RENDER_DPI = 200  # Lower DPI for faster rendering


def init_worker(model_path: str):
    """Initialize worker process with its own MLX model."""
    global worker_analyzer
    print(f"[Worker {psutil.Process().pid}] Loading MLX model...")
    worker_analyzer = NanonetsMLXAnalyzer(model_path=model_path)
    print(f"[Worker {psutil.Process().pid}] Model loaded, ready to process")


def process_page(args: tuple) -> Dict[str, Any]:
    """
    Process a single page (called by worker process).

    Args:
        args: (page_num, pdf_path, output_dir, dpi)

    Returns:
        Dict with page results and metadata
    """
    page_num, pdf_path, output_dir, dpi = args
    pid = psutil.Process().pid

    start_time = time.time()

    try:
        # Render page to image using PyMuPDF
        doc = fitz.open(pdf_path)
        page = doc[page_num]

        # Render at specified DPI
        zoom = dpi / 72.0  # 72 is default DPI
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Save to temp file
        temp_dir = Path(output_dir) / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        image_path = temp_dir / f"page_{page_num:04d}.png"
        pix.save(str(image_path))

        doc.close()

        render_time = time.time() - start_time

        # Analyze with MLX
        analysis_start = time.time()
        markdown = worker_analyzer.analyze_document(str(image_path))
        regions = worker_analyzer.extract_regions(str(image_path), page_number=page_num)
        analysis_time = time.time() - analysis_start

        total_time = time.time() - start_time

        # Clean up temp image
        image_path.unlink()

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
            "worker_pid": pid,
        }

        print(f"[Worker {pid}] Page {page_num}: {total_time:.1f}s "
              f"(render: {render_time:.1f}s, analysis: {analysis_time:.1f}s)")

        return result

    except Exception as e:
        print(f"[Worker {pid}] ERROR on page {page_num}: {e}")
        return {
            "page_num": page_num,
            "success": False,
            "error": str(e),
            "worker_pid": pid,
        }


def monitor_memory():
    """Get current memory usage."""
    process = psutil.Process()
    children = process.children(recursive=True)

    total_memory = process.memory_info().rss
    for child in children:
        try:
            total_memory += child.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return total_memory / (1024 * 1024 * 1024)  # GB


def main():
    print("=" * 80)
    print("MULTI-PROCESS MLX DOCUMENT PROCESSING")
    print("=" * 80)
    print()
    print(f"Workers: {NUM_WORKERS}")
    print(f"Model: {MODEL_PATH}")
    print(f"PDF: {PDF_PATH}")
    print(f"Render DPI: {RENDER_DPI}")
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
    # For initial test, process first 10 pages
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        pages_to_process = list(range(total_pages))
        print("Processing FULL document")
    else:
        pages_to_process = list(range(min(10, total_pages)))
        print(f"Processing first {len(pages_to_process)} pages (test mode)")
        print("Use --full flag to process entire document")

    print()
    print(f"Pages per worker: ~{len(pages_to_process) / NUM_WORKERS:.1f}")
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Prepare work items
    work_items = [
        (page_num, PDF_PATH, OUTPUT_DIR, RENDER_DPI)
        for page_num in pages_to_process
    ]

    # Start multi-process pool
    print("-" * 80)
    print("Starting worker pool...")
    print("-" * 80)
    print()

    start_time = time.time()
    initial_memory = monitor_memory()

    with Pool(
        processes=NUM_WORKERS,
        initializer=init_worker,
        initargs=(MODEL_PATH,)
    ) as pool:
        print(f"✓ {NUM_WORKERS} workers initialized")
        print()

        # Wait for workers to load models
        time.sleep(5)
        after_load_memory = monitor_memory()
        print(f"Memory after model loading: {after_load_memory:.1f} GB "
              f"(+{after_load_memory - initial_memory:.1f} GB)")
        print()

        # Process pages
        print("-" * 80)
        print("Processing pages...")
        print("-" * 80)
        print()

        results = pool.map(process_page, work_items)

    total_time = time.time() - start_time

    # Analyze results
    print()
    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print()

    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]

    print(f"Pages processed: {len(successful)}/{len(results)}")
    if failed:
        print(f"Failed pages: {len(failed)}")
        for r in failed:
            print(f"  - Page {r['page_num']}: {r.get('error', 'Unknown error')}")

    print()
    print(f"Total time: {total_time / 60:.2f} minutes ({total_time:.1f} seconds)")
    print(f"Average per page: {total_time / len(results):.2f} seconds")
    print()

    # Timing breakdown
    if successful:
        avg_render = sum(r["timing"]["render_sec"] for r in successful) / len(successful)
        avg_analysis = sum(r["timing"]["analysis_sec"] for r in successful) / len(successful)
        avg_total = sum(r["timing"]["total_sec"] for r in successful) / len(successful)

        print("Average timing per page:")
        print(f"  Render:   {avg_render:.2f} sec")
        print(f"  Analysis: {avg_analysis:.2f} sec")
        print(f"  Total:    {avg_total:.2f} sec")
        print()

    # Memory usage
    peak_memory = monitor_memory()
    print(f"Peak memory usage: {peak_memory:.1f} GB")
    print(f"Memory per worker: ~{peak_memory / NUM_WORKERS:.2f} GB")
    print()

    # Speedup calculation
    single_worker_time = sum(r["timing"]["total_sec"] for r in successful)
    actual_time = total_time
    speedup = single_worker_time / actual_time if actual_time > 0 else 0

    print(f"Theoretical single-worker time: {single_worker_time / 60:.2f} minutes")
    print(f"Actual multi-worker time: {actual_time / 60:.2f} minutes")
    print(f"Speedup: {speedup:.2f}x")
    print()

    # Projection for full document
    if len(pages_to_process) < total_pages:
        projected_time = (total_time / len(pages_to_process)) * total_pages
        print(f"Projected time for {total_pages} pages: {projected_time / 60:.1f} minutes")
        print()

    # Save results
    output_file = OUTPUT_DIR / f"multiprocess_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output_data = {
        "config": {
            "num_workers": NUM_WORKERS,
            "model_path": MODEL_PATH,
            "render_dpi": RENDER_DPI,
            "total_pages": total_pages,
            "pages_processed": len(pages_to_process),
        },
        "performance": {
            "total_time_sec": round(total_time, 2),
            "avg_time_per_page_sec": round(total_time / len(results), 2),
            "speedup": round(speedup, 2),
            "peak_memory_gb": round(peak_memory, 2),
        },
        "results": results,
    }

    output_file.write_text(json.dumps(output_data, indent=2))
    print(f"✓ Results saved to: {output_file}")
    print()

    # Recommendation
    if speedup >= 6:
        print("✅ EXCELLENT: Multi-process scaling is working well!")
        print(f"   {speedup:.1f}x speedup with {NUM_WORKERS} workers")
    elif speedup >= 4:
        print("✓ GOOD: Decent multi-process scaling")
        print(f"   {speedup:.1f}x speedup with {NUM_WORKERS} workers")
    else:
        print("⚠️  WARNING: Lower than expected speedup")
        print(f"   Only {speedup:.1f}x speedup with {NUM_WORKERS} workers")
        print("   Expected: ~{} workers = ~{}x speedup".format(NUM_WORKERS, NUM_WORKERS * 0.8))

    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
