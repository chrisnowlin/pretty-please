#!/usr/bin/env python3
"""
DeepseekOCR Quality Level Comparison Test

Tests all DeepseekOCR quality presets to compare:
- Processing speed
- Memory usage
- Content extraction quality
- Tradeoffs between modes

Quality Levels Tested:
1. deepseek_tiny - Maximum speed (512x512, 64 tokens)
2. deepseek_small - Speed/quality balance (640x640, 100 tokens)
3. deepseek_balanced - Default quality (1024x1024, 256 tokens)
4. deepseek_high_quality - Maximum quality (1280x1280, 400 tokens)
5. deepseek_gundam - Dynamic multi-resolution
6. deepseek_production - vLLM accelerated (requires vLLM installed)
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import psutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.jina_rag_pipeline.ingestion import create_ocr_loader, OCRConfig


def get_memory_usage():
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


# Define all quality levels to test
QUALITY_LEVELS = [
    {
        "name": "tiny",
        "config_method": "deepseek_tiny",
        "description": "Maximum speed (512x512, 64 tokens)",
        "best_for": "Simple text-heavy documents, high-volume processing",
        "expected_performance": "2-3x faster than balanced",
    },
    {
        "name": "small",
        "config_method": "deepseek_small",
        "description": "Speed/quality balance (640x640, 100 tokens)",
        "best_for": "Mixed simple/moderate documents",
        "expected_performance": "~1.5x faster than balanced",
    },
    {
        "name": "balanced",
        "config_method": "deepseek_balanced",
        "description": "Default quality (1024x1024, 256 tokens)",
        "best_for": "General document processing (recommended default)",
        "expected_performance": "Baseline performance",
    },
    {
        "name": "high_quality",
        "config_method": "deepseek_high_quality",
        "description": "Maximum quality (1280x1280, 400 tokens)",
        "best_for": "Complex documents with dense tables/equations",
        "expected_performance": "~30% slower than balanced",
    },
    {
        "name": "gundam",
        "config_method": "deepseek_gundam",
        "description": "Dynamic multi-resolution",
        "best_for": "Documents with variable complexity",
        "expected_performance": "Variable (adapts per page)",
    },
    {
        "name": "production",
        "config_method": "deepseek_production",
        "description": "vLLM accelerated (requires vLLM)",
        "best_for": "Production deployments, high-volume processing",
        "expected_performance": "5-10x faster than balanced (with GPU)",
    },
]


def test_quality_level(
    test_file: Path,
    quality_level: Dict[str, str],
    test_index: int,
    total_tests: int
) -> Dict[str, Any]:
    """Test a single quality level and collect metrics."""

    name = quality_level["name"]
    config_method = quality_level["config_method"]

    print(f"\n{'='*70}")
    print(f"Test {test_index}/{total_tests}: {name.upper()} Mode")
    print(f"{'='*70}")
    print(f"Description: {quality_level['description']}")
    print(f"Best for: {quality_level['best_for']}")
    print(f"Expected: {quality_level['expected_performance']}")
    print("-" * 70)

    result = {
        "quality_level": name,
        "config_method": config_method,
        "description": quality_level["description"],
        "test_timestamp": datetime.now().isoformat(),
        "test_file": str(test_file),
        "success": False,
    }

    try:
        # Record memory before
        mem_before = get_memory_usage()
        print(f"Memory before: {mem_before:.2f} MB")

        # Get config
        config = getattr(OCRConfig, config_method)()
        print(f"Config: resolution_mode={config.resolution_mode}, "
              f"grounding={config.enable_grounding}, "
              f"compression={config.enable_compression}, "
              f"vllm={config.use_vllm}")

        # Create loader
        print(f"Creating loader...")
        loader = create_ocr_loader(backend='deepseek', config=config)

        # Process document
        print(f"Processing: {test_file.name} ({test_file.stat().st_size / 1024:.2f} KB)")
        start_time = time.time()
        document = loader.load(test_file)
        processing_time = time.time() - start_time

        # Record memory after
        mem_after = get_memory_usage()
        mem_delta = mem_after - mem_before

        # Calculate metrics
        content_length = len(document.content)
        throughput = content_length / processing_time if processing_time > 0 else 0

        # Collect results
        result.update({
            "success": True,
            "processing_time_seconds": processing_time,
            "content_length_chars": content_length,
            "memory_before_mb": mem_before,
            "memory_after_mb": mem_after,
            "memory_delta_mb": mem_delta,
            "throughput_chars_per_sec": throughput,
            "content_preview": document.content[:500],
            "full_content": document.content,
            "config": {
                "resolution_mode": config.resolution_mode,
                "enable_grounding": config.enable_grounding,
                "enable_compression": config.enable_compression,
                "use_vllm": config.use_vllm,
                "batch_size": config.batch_size,
                "render_workers": config.render_workers,
                "analysis_workers": config.analysis_workers,
            },
            "metadata": {k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                       for k, v in (document.metadata or {}).items()
                       if k not in ['page_boundaries', 'regions', 'details']}
        })

        # Print results
        print(f"\n✓ SUCCESS")
        print(f"  Processing time: {processing_time:.2f}s")
        print(f"  Content extracted: {content_length:,} characters")
        print(f"  Memory used: {mem_delta:.2f} MB")
        print(f"  Throughput: {throughput:.1f} chars/sec")

        # Show content sample
        print(f"\n  Content preview (first 200 chars):")
        print(f"  {'-' * 66}")
        preview = document.content[:200].replace('\n', '\n  ')
        print(f"  {preview}")
        if len(document.content) > 200:
            print(f"  ... ({len(document.content) - 200} more characters)")
        print(f"  {'-' * 66}")

    except Exception as e:
        result["error"] = str(e)
        result["error_type"] = type(e).__name__
        print(f"\n✗ FAILED: {type(e).__name__}")
        print(f"  Error: {e}")

        # For vLLM errors, provide helpful context
        if "vllm" in str(e).lower() or config_method == "deepseek_production":
            print(f"\n  Note: vLLM mode requires 'pip install vllm>=0.8.5' and GPU support.")
            print(f"        This is expected to fail without vLLM installed.")

    return result


def generate_comparison_report(results: List[Dict[str, Any]], output_file: Path) -> None:
    """Generate a comprehensive comparison report."""

    print(f"\n{'='*70}")
    print("QUALITY LEVEL COMPARISON REPORT")
    print(f"{'='*70}")

    # Filter successful results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    if not successful:
        print("\n⚠️  No successful tests to compare")
        return

    # Find fastest and best quality
    fastest = min(successful, key=lambda r: r["processing_time_seconds"])
    most_content = max(successful, key=lambda r: r["content_length_chars"])
    most_efficient = max(successful, key=lambda r: r["throughput_chars_per_sec"])

    print(f"\n1. PERFORMANCE SUMMARY")
    print(f"{'-'*70}")
    print(f"{'Quality Level':<20} {'Time (s)':<12} {'Content':<12} {'Memory (MB)':<15} {'Throughput':<15}")
    print(f"{'-'*70}")

    for result in successful:
        time_str = f"{result['processing_time_seconds']:.2f}s"
        content_str = f"{result['content_length_chars']:,} ch"
        memory_str = f"{result['memory_delta_mb']:.0f} MB"
        throughput_str = f"{result['throughput_chars_per_sec']:.1f} ch/s"

        marker = ""
        if result == fastest:
            marker = " ⚡ FASTEST"
        elif result == most_content:
            marker = " 📝 MOST CONTENT"
        elif result == most_efficient:
            marker = " 🎯 MOST EFFICIENT"

        print(f"{result['quality_level']:<20} {time_str:<12} {content_str:<12} {memory_str:<15} {throughput_str:<15}{marker}")

    print(f"\n2. SPEED COMPARISON (relative to balanced)")
    print(f"{'-'*70}")

    # Find balanced mode for comparison
    balanced = next((r for r in successful if r["quality_level"] == "balanced"), None)
    if balanced:
        baseline_time = balanced["processing_time_seconds"]
        for result in successful:
            speedup = baseline_time / result["processing_time_seconds"]
            if speedup > 1:
                comparison = f"{speedup:.2f}x FASTER"
            elif speedup < 1:
                comparison = f"{1/speedup:.2f}x SLOWER"
            else:
                comparison = "BASELINE"
            print(f"{result['quality_level']:<20} {comparison}")

    print(f"\n3. CONTENT QUALITY COMPARISON")
    print(f"{'-'*70}")
    for result in successful:
        content_len = result["content_length_chars"]
        print(f"\n{result['quality_level'].upper()} ({content_len:,} characters):")
        print(f"{'-'*70}")
        preview = result["content_preview"].replace('\n', '\n  ')
        print(f"  {preview}")
        if len(result.get("full_content", "")) > 500:
            print(f"  ... (truncated)")

    print(f"\n4. RECOMMENDATIONS")
    print(f"{'-'*70}")

    if fastest:
        print(f"⚡ For maximum speed: Use '{fastest['quality_level']}' mode")
        print(f"   → {fastest['processing_time_seconds']:.2f}s processing time")

    if most_content:
        print(f"📝 For maximum content extraction: Use '{most_content['quality_level']}' mode")
        print(f"   → {most_content['content_length_chars']:,} characters extracted")

    if most_efficient:
        print(f"🎯 For best throughput: Use '{most_efficient['quality_level']}' mode")
        print(f"   → {most_efficient['throughput_chars_per_sec']:.1f} chars/sec")

    # Recommendations based on use case
    print(f"\n5. USE CASE RECOMMENDATIONS")
    print(f"{'-'*70}")
    print(f"📄 Simple text documents: 'tiny' or 'small' mode")
    print(f"📊 Mixed content (text + tables): 'balanced' mode (default)")
    print(f"🔬 Complex layouts (equations, dense tables): 'high_quality' mode")
    print(f"🔄 Variable complexity documents: 'gundam' mode")
    print(f"🚀 Production high-volume: 'production' mode (requires vLLM + GPU)")

    if failed:
        print(f"\n6. FAILED TESTS")
        print(f"{'-'*70}")
        for result in failed:
            print(f"✗ {result['quality_level']}: {result.get('error_type', 'Unknown error')}")
            if result.get('error'):
                print(f"  {result['error'][:200]}")

    print(f"\n{'='*70}")
    print(f"✓ Detailed results saved to: {output_file}")
    print(f"{'='*70}\n")


def main():
    """Run the quality comparison test."""

    # Test file
    test_file = Path("test_2pages.pdf")

    if not test_file.exists():
        print(f"✗ Test file not found: {test_file}")
        print(f"  Please ensure {test_file} exists in the current directory.")
        return 1

    print(f"\n{'='*70}")
    print("DeepseekOCR Quality Level Comparison Test")
    print(f"{'='*70}")
    print(f"Test file: {test_file.name} ({test_file.stat().st_size / 1024:.2f} KB)")
    print(f"Testing {len(QUALITY_LEVELS)} quality levels")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run tests
    results = []
    for i, quality_level in enumerate(QUALITY_LEVELS, 1):
        result = test_quality_level(test_file, quality_level, i, len(QUALITY_LEVELS))
        results.append(result)

        # Small delay between tests to allow memory to settle
        if i < len(QUALITY_LEVELS):
            time.sleep(2)

    # Save detailed results
    output_file = Path("deepseek_quality_comparison_results.json")
    with open(output_file, "w") as f:
        json.dump({
            "test_timestamp": datetime.now().isoformat(),
            "test_file": str(test_file),
            "test_file_size_kb": test_file.stat().st_size / 1024,
            "python_version": sys.version,
            "results": results,
        }, f, indent=2)

    # Generate comparison report
    generate_comparison_report(results, output_file)

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    print(f"\nTEST SUMMARY:")
    print(f"  ✓ Successful: {successful}/{len(results)}")
    if failed > 0:
        print(f"  ✗ Failed: {failed}/{len(results)}")

    return 0 if successful > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
