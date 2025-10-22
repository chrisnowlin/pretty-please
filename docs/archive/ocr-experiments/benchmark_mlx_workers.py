#!/usr/bin/env python3
"""
MLX Worker Optimization Benchmark

Systematically test different worker configurations to find optimal settings.
Tests 1, 2, 3, 4, and 5 parallel workers on first 10 pages of document.

Metrics tracked:
- Total processing time
- Time per page
- Throughput (pages/minute)
- Memory usage (peak)
- Parallel efficiency
"""

import sys
import time
import psutil
import json
from pathlib import Path
from datetime import datetime
import logging

sys.path.insert(0, str(Path(__file__).parent / "src"))

from jina_rag_pipeline.ingestion import NanonetsFirstLoader

# Configuration
PDF_PATH = Path("/Users/cnowlin/Downloads/_OceanofPDF.com_Classroom_Music_Games_and_Activities_-_Julie_Eisenhauer.pdf")
TEST_PAGES = 10  # Test on first 10 pages for quick iteration
WORKER_CONFIGS = [1, 2, 3, 4, 5]  # Test these worker counts
RESULTS_FILE = Path("./benchmark_results.json")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor memory usage during processing."""

    def __init__(self):
        self.process = psutil.Process()
        self.peak_memory_mb = 0
        self.start_memory_mb = 0

    def start(self):
        """Start monitoring."""
        self.start_memory_mb = self.process.memory_info().rss / (1024 * 1024)
        self.peak_memory_mb = self.start_memory_mb

    def update(self):
        """Update peak memory if current is higher."""
        current_mb = self.process.memory_info().rss / (1024 * 1024)
        if current_mb > self.peak_memory_mb:
            self.peak_memory_mb = current_mb

    def get_stats(self):
        """Get memory statistics."""
        return {
            "start_mb": round(self.start_memory_mb, 1),
            "peak_mb": round(self.peak_memory_mb, 1),
            "delta_mb": round(self.peak_memory_mb - self.start_memory_mb, 1)
        }


def run_benchmark(num_workers: int) -> dict:
    """
    Run benchmark with specified number of workers.

    Args:
        num_workers: Number of parallel analysis workers

    Returns:
        Dict with benchmark results
    """
    logger.info("=" * 80)
    logger.info(f"BENCHMARK: {num_workers} WORKERS")
    logger.info("=" * 80)

    # Initialize memory monitor
    memory_monitor = MemoryMonitor()
    memory_monitor.start()

    # Create unique collection name
    collection_name = f"benchmark_w{num_workers}_{int(time.time())}"

    # Configure loader
    logger.info(f"Configuration:")
    logger.info(f"  Workers: {num_workers}")
    logger.info(f"  Test pages: {TEST_PAGES}")
    logger.info(f"  Backend: MLX (Nanonets OCR2-3B)")

    loader = NanonetsFirstLoader(
        batch_size=TEST_PAGES,  # Process all test pages in one batch
        max_render_workers=num_workers * 4,  # Scale render workers with analysis
        max_analysis_workers=num_workers,
        enable_checkpoints=False,  # Don't save checkpoints for benchmarks
        use_mlx=True
    )

    # Start benchmark
    start_time = time.time()
    start_wall = datetime.now()

    logger.info(f"Starting at: {start_wall.strftime('%H:%M:%S')}")
    logger.info("")

    try:
        # Process document (stop after first batch)
        # We'll manually limit by setting batch_size=TEST_PAGES
        document = loader.load(
            file_path=PDF_PATH,
            collection_name=collection_name,
            resume=False  # Always start fresh for benchmarks
        )

        # Update memory
        memory_monitor.update()

        # Calculate metrics
        elapsed_sec = time.time() - start_time
        elapsed_min = elapsed_sec / 60

        pages = document.metadata.get('page_count', TEST_PAGES)
        regions = document.metadata.get('region_count', 0)

        sec_per_page = elapsed_sec / pages if pages > 0 else 0
        pages_per_min = 60 / sec_per_page if sec_per_page > 0 else 0

        # Parallel efficiency (vs single worker baseline)
        # Ideal: N workers = N times faster
        # Reality: diminishing returns due to overhead
        theoretical_speedup = num_workers

        memory_stats = memory_monitor.get_stats()

        result = {
            "workers": num_workers,
            "success": True,
            "pages": pages,
            "regions": regions,
            "time_sec": round(elapsed_sec, 2),
            "time_min": round(elapsed_min, 2),
            "sec_per_page": round(sec_per_page, 2),
            "pages_per_min": round(pages_per_min, 2),
            "memory": memory_stats,
            "timestamp": start_wall.isoformat()
        }

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"RESULTS: {num_workers} WORKERS")
        logger.info("=" * 80)
        logger.info(f"Total time: {elapsed_min:.2f} minutes ({elapsed_sec:.1f} seconds)")
        logger.info(f"Pages processed: {pages}")
        logger.info(f"Regions extracted: {regions}")
        logger.info(f"Performance: {sec_per_page:.1f} sec/page ({pages_per_min:.1f} pages/min)")
        logger.info(f"Memory: {memory_stats['peak_mb']:.1f} MB peak ({memory_stats['delta_mb']:.1f} MB delta)")
        logger.info("")

        return result

    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)

        elapsed_sec = time.time() - start_time
        memory_stats = memory_monitor.get_stats()

        return {
            "workers": num_workers,
            "success": False,
            "error": str(e),
            "time_sec": round(elapsed_sec, 2),
            "memory": memory_stats,
            "timestamp": start_wall.isoformat()
        }


def calculate_speedup(results: list) -> list:
    """Calculate speedup relative to single worker baseline."""
    # Find baseline (1 worker)
    baseline = next((r for r in results if r["workers"] == 1 and r["success"]), None)

    if not baseline:
        return results

    baseline_time = baseline["sec_per_page"]

    for result in results:
        if result["success"]:
            result["speedup"] = round(baseline_time / result["sec_per_page"], 2)
            result["efficiency"] = round((result["speedup"] / result["workers"]) * 100, 1)
        else:
            result["speedup"] = 0
            result["efficiency"] = 0

    return results


def print_summary(results: list):
    """Print benchmark summary table."""
    logger.info("")
    logger.info("=" * 100)
    logger.info("BENCHMARK SUMMARY")
    logger.info("=" * 100)
    logger.info("")

    # Header
    logger.info(f"{'Workers':<10} {'Time (min)':<12} {'Sec/Page':<12} {'Pages/Min':<12} {'Speedup':<10} {'Efficiency':<12} {'Memory (MB)':<15}")
    logger.info("-" * 100)

    # Results
    for r in results:
        if r["success"]:
            workers = r["workers"]
            time_min = r["time_min"]
            sec_per_page = r["sec_per_page"]
            pages_per_min = r["pages_per_min"]
            speedup = r.get("speedup", "-")
            efficiency = r.get("efficiency", "-")
            memory = r["memory"]["peak_mb"]

            logger.info(
                f"{workers:<10} "
                f"{time_min:<12.2f} "
                f"{sec_per_page:<12.1f} "
                f"{pages_per_min:<12.1f} "
                f"{speedup:<10} "
                f"{efficiency:<12}% "
                f"{memory:<15.1f}"
            )
        else:
            logger.info(f"{r['workers']:<10} FAILED: {r.get('error', 'Unknown error')}")

    logger.info("")
    logger.info("=" * 100)
    logger.info("")

    # Find optimal
    successful = [r for r in results if r["success"]]
    if successful:
        # Best throughput (pages per minute)
        best_throughput = max(successful, key=lambda x: x["pages_per_min"])

        # Best efficiency (speedup per worker)
        best_efficiency = max(successful, key=lambda x: x.get("efficiency", 0))

        # Best speedup
        best_speedup = max(successful, key=lambda x: x.get("speedup", 0))

        logger.info("RECOMMENDATIONS:")
        logger.info("")
        logger.info(f"Best Throughput: {best_throughput['workers']} workers")
        logger.info(f"  → {best_throughput['pages_per_min']:.1f} pages/min")
        logger.info(f"  → {best_throughput['speedup']:.2f}x faster than baseline")
        logger.info("")

        logger.info(f"Best Efficiency: {best_efficiency['workers']} workers")
        logger.info(f"  → {best_efficiency['efficiency']:.1f}% parallel efficiency")
        logger.info(f"  → {best_efficiency['memory']['peak_mb']:.1f} MB memory")
        logger.info("")

        logger.info(f"Best Speedup: {best_speedup['workers']} workers")
        logger.info(f"  → {best_speedup['speedup']:.2f}x faster than baseline")
        logger.info("")

        # Memory analysis
        logger.info("Memory Scaling:")
        for r in successful:
            mb_per_worker = r["memory"]["delta_mb"] / r["workers"]
            logger.info(f"  {r['workers']} workers: {r['memory']['peak_mb']:.1f} MB total ({mb_per_worker:.1f} MB per worker)")
        logger.info("")


def main():
    logger.info("")
    logger.info("=" * 100)
    logger.info("MLX WORKER OPTIMIZATION BENCHMARK")
    logger.info("=" * 100)
    logger.info("")
    logger.info(f"PDF: {PDF_PATH.name}")
    logger.info(f"Test pages: {TEST_PAGES}")
    logger.info(f"Worker configurations: {WORKER_CONFIGS}")
    logger.info(f"Backend: MLX (Nanonets OCR2-3B, 3.1GB per worker)")
    logger.info("")

    # Verify PDF exists
    if not PDF_PATH.exists():
        logger.error(f"PDF not found: {PDF_PATH}")
        return 1

    # Run benchmarks
    results = []

    for num_workers in WORKER_CONFIGS:
        logger.info(f"Testing configuration: {num_workers} workers...")
        logger.info("")

        result = run_benchmark(num_workers)
        results.append(result)

        # Save intermediate results
        RESULTS_FILE.write_text(json.dumps(results, indent=2))

        # Short pause between tests
        logger.info(f"Waiting 5 seconds before next test...")
        logger.info("")
        time.sleep(5)

    # Calculate speedups
    results = calculate_speedup(results)

    # Save final results
    RESULTS_FILE.write_text(json.dumps(results, indent=2))
    logger.info(f"Results saved to: {RESULTS_FILE}")

    # Print summary
    print_summary(results)

    logger.info("Benchmark complete!")
    logger.info("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
