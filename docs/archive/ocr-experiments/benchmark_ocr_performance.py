#!/usr/bin/env python3
"""
Performance benchmarking suite for OCR pipeline optimization.

Measures:
- Total processing time
- Pages per second throughput
- Memory usage (peak)
- Pipeline depth effectiveness
- Configuration impact

Usage:
    python benchmark_ocr_performance.py <pdf_path>
    python benchmark_ocr_performance.py <pdf_path> --config mlx_optimized
    python benchmark_ocr_performance.py <pdf_path> --compare-configs
"""

import argparse
import json
import logging
import platform
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import psutil
except ImportError:
    psutil = None

from src.jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from src.jina_rag_pipeline.ingestion.ocr_config import OCRConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@contextmanager
def benchmark_timer(description: str):
    """Context manager for timing operations with consistent measurement."""
    start_time = time.perf_counter()
    start_memory = psutil.Process().memory_info().rss / (1024**3) if psutil else 0

    logger.info(f"🚀 Starting: {description}")

    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        end_memory = psutil.Process().memory_info().rss / (1024**3) if psutil else 0
        memory_delta = end_memory - start_memory

        logger.info(f"✅ Completed: {description}")
        logger.info(f"   Time: {elapsed:.2f}s")
        logger.info(f"   Memory delta: {memory_delta:+.2f}GB")


def get_system_info() -> Dict[str, Any]:
    """Gather system information for benchmark context."""
    info = {
        "platform": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }

    if psutil:
        info["cpu_count_physical"] = psutil.cpu_count(logical=False)
        info["cpu_count_logical"] = psutil.cpu_count(logical=True)
        info["total_memory_gb"] = psutil.virtual_memory().total / (1024**3)

    # Detect Apple Silicon
    if info["platform"] == "Darwin" and info["machine"].startswith("arm"):
        info["chipset"] = info["machine"]

    return info


def benchmark_single_config(
    pdf_path: Path,
    config: OCRConfig,
    config_name: str
) -> Dict[str, Any]:
    """Benchmark OCR processing with a specific configuration."""

    logger.info(f"\n{'='*70}")
    logger.info(f"Benchmarking: {config_name}")
    logger.info(f"{'='*70}")
    logger.info(f"Configuration:")
    logger.info(f"  batch_size: {config.batch_size}")
    logger.info(f"  render_workers: {config.render_workers}")
    logger.info(f"  analysis_workers: {config.analysis_workers}")
    logger.info(f"  pre_render_batches: {config.pre_render_batches}")
    logger.info(f"  checkpoint_enabled: {config.checkpoint_enabled}")

    # Initialize loader
    loader = NanonetsLoader(config=config)

    # Measure baseline memory
    baseline_memory = psutil.Process().memory_info().rss / (1024**3) if psutil else 0
    peak_memory = baseline_memory

    # Benchmark processing
    start_time = time.perf_counter()

    try:
        with benchmark_timer(f"Processing {pdf_path.name} with {config_name}"):
            document = loader.load(pdf_path)

            # Track peak memory during processing
            if psutil:
                current_memory = psutil.Process().memory_info().rss / (1024**3)
                peak_memory = max(peak_memory, current_memory)

        elapsed = time.perf_counter() - start_time

        # Calculate metrics
        page_count = document.metadata.get("page_count", 0)
        throughput = page_count / elapsed if elapsed > 0 else 0
        memory_used = peak_memory - baseline_memory

        result = {
            "config_name": config_name,
            "config": {
                "batch_size": config.batch_size,
                "render_workers": config.render_workers,
                "analysis_workers": config.analysis_workers,
                "pre_render_batches": config.pre_render_batches,
            },
            "success": True,
            "elapsed_seconds": round(elapsed, 2),
            "page_count": page_count,
            "throughput_pages_per_second": round(throughput, 3),
            "time_per_page_seconds": round(elapsed / page_count, 2) if page_count > 0 else 0,
            "memory_baseline_gb": round(baseline_memory, 2),
            "memory_peak_gb": round(peak_memory, 2),
            "memory_used_gb": round(memory_used, 2),
            "content_length": len(document.content),
            "extraction_method": document.metadata.get("extraction_method"),
        }

        logger.info(f"\n📊 Results for {config_name}:")
        logger.info(f"   Pages: {page_count}")
        logger.info(f"   Time: {elapsed:.2f}s ({throughput:.3f} pages/sec)")
        logger.info(f"   Memory: {memory_used:.2f}GB used (peak: {peak_memory:.2f}GB)")
        logger.info(f"   Content: {len(document.content):,} characters")

        return result

    except Exception as e:
        logger.error(f"❌ Benchmark failed for {config_name}: {e}")
        return {
            "config_name": config_name,
            "success": False,
            "error": str(e),
        }


def compare_configurations(pdf_path: Path) -> Dict[str, Any]:
    """Compare performance across multiple configurations."""

    configs_to_test = [
        ("mlx_optimized", OCRConfig.mlx_optimized()),
        ("balanced", OCRConfig.balanced()),
        ("memory_constrained", OCRConfig.memory_constrained()),
    ]

    results = {
        "system_info": get_system_info(),
        "pdf_path": str(pdf_path),
        "pdf_size_mb": pdf_path.stat().st_size / (1024**2),
        "benchmark_results": [],
    }

    for config_name, config in configs_to_test:
        result = benchmark_single_config(pdf_path, config, config_name)
        results["benchmark_results"].append(result)

        # Brief pause between runs to allow GC
        time.sleep(2)

    # Calculate relative performance
    successful_results = [r for r in results["benchmark_results"] if r.get("success")]

    if len(successful_results) > 1:
        fastest = min(successful_results, key=lambda x: x["elapsed_seconds"])

        logger.info(f"\n🏆 Performance Comparison:")
        logger.info(f"   Fastest: {fastest['config_name']}")
        logger.info(f"   Time: {fastest['elapsed_seconds']}s")
        logger.info(f"   Throughput: {fastest['throughput_pages_per_second']:.3f} pages/sec")

        logger.info(f"\n   Relative Performance:")
        for result in successful_results:
            speedup = fastest["elapsed_seconds"] / result["elapsed_seconds"]
            logger.info(
                f"   {result['config_name']:20s}: "
                f"{result['elapsed_seconds']:6.2f}s ({speedup:5.2f}x)"
            )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark OCR pipeline performance"
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to PDF file for benchmarking"
    )
    parser.add_argument(
        "--config",
        choices=["mlx_optimized", "balanced", "memory_constrained", "default"],
        default="mlx_optimized",
        help="Configuration preset to use"
    )
    parser.add_argument(
        "--compare-configs",
        action="store_true",
        help="Compare all configuration presets"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    # Validate PDF path
    if not args.pdf_path.exists():
        logger.error(f"❌ PDF not found: {args.pdf_path}")
        sys.exit(1)

    logger.info(f"\n{'='*70}")
    logger.info(f"OCR Pipeline Performance Benchmark")
    logger.info(f"{'='*70}")

    # Display system info
    system_info = get_system_info()
    logger.info(f"\n🖥️  System Information:")
    for key, value in system_info.items():
        logger.info(f"   {key}: {value}")

    # Run benchmark
    if args.compare_configs:
        results = compare_configurations(args.pdf_path)
    else:
        # Single config benchmark
        config_map = {
            "mlx_optimized": OCRConfig.mlx_optimized(),
            "balanced": OCRConfig.balanced(),
            "memory_constrained": OCRConfig.memory_constrained(),
            "default": OCRConfig(),
        }

        config = config_map[args.config]
        result = benchmark_single_config(args.pdf_path, config, args.config)

        results = {
            "system_info": system_info,
            "pdf_path": str(args.pdf_path),
            "benchmark_results": [result],
        }

    # Save results if output specified
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"\n💾 Results saved to: {args.output}")

    logger.info(f"\n{'='*70}")
    logger.info(f"Benchmark Complete")
    logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    main()
