#!/usr/bin/env python3
"""
Fast MLX Inference Benchmark - Test parallel worker scaling.

Tests pure MLX inference performance with different worker counts.
Uses pre-rendered images to isolate MLX performance from PDF rendering.
"""

import sys
import time
import psutil
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging

sys.path.insert(0, str(Path(__file__).parent / "src"))

from jina_rag_pipeline.ingestion.nanonets_mlx import NanonetsMLXAnalyzer

# Configuration
TEST_IMAGE = "/var/folders/_1/66qwm39s5vg8tgtylwl5hvkh0000gn/T/tmp0a6etio8.png"
NUM_IMAGES = 10  # Process 10 images per test
WORKER_CONFIGS = [1, 2, 3, 4, 5]  # Test these worker counts
RESULTS_FILE = Path("./mlx_benchmark_results.json")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_image(analyzer: NanonetsMLXAnalyzer, image_path: str, index: int) -> dict:
    """Process a single image and return timing info."""
    start = time.time()

    try:
        markdown = analyzer.analyze_document(image_path)
        elapsed = time.time() - start

        return {
            "index": index,
            "success": True,
            "time_sec": round(elapsed, 2),
            "output_len": len(markdown)
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "index": index,
            "success": False,
            "time_sec": round(elapsed, 2),
            "error": str(e)
        }


def run_benchmark(num_workers: int) -> dict:
    """Run benchmark with specified number of workers."""
    logger.info("=" * 80)
    logger.info(f"BENCHMARK: {num_workers} WORKERS")
    logger.info("=" * 80)
    logger.info("")

    # Monitor memory
    process = psutil.Process()
    start_memory_mb = process.memory_info().rss / (1024 * 1024)
    peak_memory_mb = start_memory_mb

    # Initialize analyzer
    logger.info(f"Initializing MLX analyzer...")
    analyzer = NanonetsMLXAnalyzer()
    logger.info(f"✓ Model loaded")
    logger.info("")

    # Update peak memory after model load
    current_mb = process.memory_info().rss / (1024 * 1024)
    peak_memory_mb = max(peak_memory_mb, current_mb)
    model_memory_mb = current_mb - start_memory_mb

    logger.info(f"Configuration:")
    logger.info(f"  Workers: {num_workers}")
    logger.info(f"  Images to process: {NUM_IMAGES}")
    logger.info(f"  Model memory: {model_memory_mb:.1f} MB")
    logger.info("")

    # Start benchmark
    start_time = time.time()
    logger.info(f"Starting at: {datetime.now().strftime('%H:%M:%S')}")
    logger.info("")

    results_list = []

    if num_workers == 1:
        # Sequential processing
        for i in range(NUM_IMAGES):
            logger.info(f"  Processing image {i+1}/{NUM_IMAGES}...")
            result = process_image(analyzer, TEST_IMAGE, i)
            results_list.append(result)

            # Update peak memory
            current_mb = process.memory_info().rss / (1024 * 1024)
            peak_memory_mb = max(peak_memory_mb, current_mb)

    else:
        # Parallel processing
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(process_image, analyzer, TEST_IMAGE, i)
                for i in range(NUM_IMAGES)
            ]

            completed = 0
            for future in as_completed(futures):
                completed += 1
                result = future.result()
                results_list.append(result)
                logger.info(f"  Completed {completed}/{NUM_IMAGES} images ({result['time_sec']:.1f}s)")

                # Update peak memory
                current_mb = process.memory_info().rss / (1024 * 1024)
                peak_memory_mb = max(peak_memory_mb, current_mb)

    # Calculate metrics
    elapsed_sec = time.time() - start_time
    elapsed_min = elapsed_sec / 60

    successful = [r for r in results_list if r["success"]]
    failed = [r for r in results_list if not r["success"]]

    if successful:
        avg_time = sum(r["time_sec"] for r in successful) / len(successful)
        total_inference_time = sum(r["time_sec"] for r in successful)
        throughput = len(successful) / elapsed_sec  # images per second
    else:
        avg_time = 0
        total_inference_time = 0
        throughput = 0

    memory_delta = peak_memory_mb - start_memory_mb

    result = {
        "workers": num_workers,
        "images_processed": len(successful),
        "images_failed": len(failed),
        "wall_time_sec": round(elapsed_sec, 2),
        "wall_time_min": round(elapsed_min, 2),
        "avg_inference_sec": round(avg_time, 2),
        "total_inference_sec": round(total_inference_time, 2),
        "throughput_img_per_sec": round(throughput, 3),
        "memory_start_mb": round(start_memory_mb, 1),
        "memory_peak_mb": round(peak_memory_mb, 1),
        "memory_delta_mb": round(memory_delta, 1),
        "model_memory_mb": round(model_memory_mb, 1),
        "timestamp": datetime.now().isoformat()
    }

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"RESULTS: {num_workers} WORKERS")
    logger.info("=" * 80)
    logger.info(f"Wall time: {elapsed_min:.2f} minutes ({elapsed_sec:.1f} seconds)")
    logger.info(f"Images processed: {len(successful)}/{NUM_IMAGES}")
    logger.info(f"Avg inference time: {avg_time:.1f} sec/image")
    logger.info(f"Throughput: {throughput:.2f} images/sec")
    logger.info(f"Memory: {peak_memory_mb:.1f} MB peak (+{memory_delta:.1f} MB)")
    logger.info("")

    if failed:
        logger.warning(f"Failed: {len(failed)} images")

    return result


def calculate_speedup(results: list) -> list:
    """Calculate speedup and efficiency metrics."""
    # Find baseline (1 worker)
    baseline = next((r for r in results if r["workers"] == 1), None)

    if not baseline:
        return results

    baseline_time = baseline["wall_time_sec"]

    for result in results:
        result["speedup"] = round(baseline_time / result["wall_time_sec"], 2)
        result["efficiency"] = round((result["speedup"] / result["workers"]) * 100, 1)

        # Parallel efficiency: how well we're utilizing workers
        # 100% = perfect scaling, 50% = each worker is 50% as effective
        theoretical_max = baseline_time / result["workers"]
        actual = result["wall_time_sec"]
        result["parallel_efficiency"] = round((theoretical_max / actual) * 100, 1)

    return results


def print_summary(results: list):
    """Print benchmark summary table."""
    logger.info("")
    logger.info("=" * 110)
    logger.info("MLX INFERENCE BENCHMARK SUMMARY")
    logger.info("=" * 110)
    logger.info("")

    # Header
    logger.info(f"{'Workers':<10} {'Wall Time':<12} {'Avg/Image':<12} {'Throughput':<14} {'Speedup':<10} {'Efficiency':<12} {'Memory':<15}")
    logger.info(f"{'':10} {'(sec)':<12} {'(sec)':<12} {'(img/sec)':<14} {'':<10} {'(%)':<12} {'(MB)':<15}")
    logger.info("-" * 110)

    # Results
    for r in results:
        workers = r["workers"]
        wall_time = r["wall_time_sec"]
        avg_time = r["avg_inference_sec"]
        throughput = r["throughput_img_per_sec"]
        speedup = r.get("speedup", "-")
        efficiency = r.get("efficiency", "-")
        memory = r["memory_peak_mb"]

        logger.info(
            f"{workers:<10} "
            f"{wall_time:<12.1f} "
            f"{avg_time:<12.1f} "
            f"{throughput:<14.2f} "
            f"{speedup:<10} "
            f"{efficiency:<12} "
            f"{memory:<15.1f}"
        )

    logger.info("")
    logger.info("=" * 110)
    logger.info("")

    # Find optimal
    best_throughput = max(results, key=lambda x: x["throughput_img_per_sec"])
    best_efficiency = max(results, key=lambda x: x.get("efficiency", 0))
    best_speedup = max(results, key=lambda x: x.get("speedup", 0))

    logger.info("OPTIMAL CONFIGURATIONS:")
    logger.info("")
    logger.info(f"Best Throughput: {best_throughput['workers']} workers")
    logger.info(f"  → {best_throughput['throughput_img_per_sec']:.2f} images/sec")
    logger.info(f"  → {best_throughput['speedup']:.2f}x speedup")
    logger.info(f"  → {best_throughput['memory_peak_mb']:.1f} MB memory")
    logger.info("")

    logger.info(f"Best Efficiency: {best_efficiency['workers']} workers")
    logger.info(f"  → {best_efficiency['efficiency']:.1f}% parallel efficiency")
    logger.info(f"  → {best_efficiency['speedup']:.2f}x speedup")
    logger.info(f"  → {best_efficiency['memory_delta_mb']:.1f} MB per worker (avg)")
    logger.info("")

    logger.info("Memory Scaling Analysis:")
    for r in results:
        mb_per_worker = r["memory_delta_mb"] / r["workers"]
        logger.info(f"  {r['workers']} workers: {r['memory_peak_mb']:.1f} MB total, {mb_per_worker:.1f} MB/worker")
    logger.info("")

    logger.info("RECOMMENDATION for 96-page document:")
    optimal = best_throughput
    pages_per_min = optimal['throughput_img_per_sec'] * 60
    time_for_96 = 96 / pages_per_min if pages_per_min > 0 else float('inf')
    logger.info(f"  Use {optimal['workers']} workers")
    logger.info(f"  Expected: {pages_per_min:.1f} pages/min")
    logger.info(f"  Est. time for 96 pages: {time_for_96:.1f} minutes")
    logger.info(f"  Memory needed: ~{optimal['memory_peak_mb']:.1f} MB")
    logger.info("")


def main():
    logger.info("")
    logger.info("=" * 110)
    logger.info("MLX INFERENCE BENCHMARK - Worker Scaling Test")
    logger.info("=" * 110)
    logger.info("")
    logger.info(f"Test image: {Path(TEST_IMAGE).name}")
    logger.info(f"Images per test: {NUM_IMAGES}")
    logger.info(f"Worker configurations: {WORKER_CONFIGS}")
    logger.info(f"Model: Nanonets OCR2-3B (MLX, 8-bit quantized)")
    logger.info("")

    # Verify image exists
    if not Path(TEST_IMAGE).exists():
        logger.error(f"Test image not found: {TEST_IMAGE}")
        return 1

    # Run benchmarks
    results = []

    for num_workers in WORKER_CONFIGS:
        logger.info(f"Testing {num_workers} workers...")
        logger.info("")

        result = run_benchmark(num_workers)
        results.append(result)

        # Save intermediate results
        RESULTS_FILE.write_text(json.dumps(results, indent=2))

        # Pause between tests
        if num_workers < max(WORKER_CONFIGS):
            logger.info(f"Waiting 5 seconds before next test...")
            logger.info("")
            time.sleep(5)

    # Calculate speedups
    results = calculate_speedup(results)

    # Save final results
    RESULTS_FILE.write_text(json.dumps(results, indent=2))
    logger.info(f"✓ Results saved to: {RESULTS_FILE}")
    logger.info("")

    # Print summary
    print_summary(results)

    logger.info("Benchmark complete!")
    logger.info("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
