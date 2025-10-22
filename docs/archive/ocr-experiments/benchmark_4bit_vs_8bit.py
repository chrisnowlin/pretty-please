#!/usr/bin/env python3
"""
Benchmark 4-bit vs 8-bit quantization.

Compares inference speed and memory usage between 4-bit and 8-bit
quantized versions of the Nanonets OCR model.
"""

import sys
import time
import psutil
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from jina_rag_pipeline.ingestion.nanonets_mlx import NanonetsMLXAnalyzer

# Test configuration
TEST_IMAGE = "/var/folders/_1/66qwm39s5vg8tgtylwl5hvkh0000gn/T/tmp0a6etio8.png"
NUM_ITERATIONS = 5  # Test each model 5 times
MODELS = {
    "8-bit": "./models/nanonets-ocr2-3b-mlx",
    "4-bit": "./models/nanonets-ocr2-3b-mlx-4bit"
}

print("=" * 80)
print("4-BIT vs 8-BIT QUANTIZATION BENCHMARK")
print("=" * 80)
print()
print(f"Test image: {Path(TEST_IMAGE).name}")
print(f"Iterations per model: {NUM_ITERATIONS}")
print()


def benchmark_model(model_path: str, model_name: str) -> dict:
    """Benchmark a single model."""
    print("-" * 80)
    print(f"TESTING: {model_name}")
    print("-" * 80)
    print()

    # Monitor memory
    process = psutil.Process()
    start_memory = process.memory_info().rss / (1024 * 1024)

    # Initialize analyzer
    print(f"Loading model from: {model_path}")
    analyzer = NanonetsMLXAnalyzer(model_path=model_path)
    print("✓ Model loaded")
    print()

    # Measure model load memory
    after_load_memory = process.memory_info().rss / (1024 * 1024)
    model_memory = after_load_memory - start_memory

    print(f"Model memory: {model_memory:.1f} MB")
    print()

    # Warm-up run (first inference is slower)
    print("Warm-up inference...")
    analyzer.analyze_document(TEST_IMAGE)
    print("✓ Warm-up complete")
    print()

    # Benchmark runs
    print(f"Running {NUM_ITERATIONS} benchmark iterations...")
    times = []
    peak_memory = after_load_memory

    for i in range(NUM_ITERATIONS):
        start = time.time()
        markdown = analyzer.analyze_document(TEST_IMAGE)
        elapsed = time.time() - start
        times.append(elapsed)

        # Update peak memory
        current_memory = process.memory_info().rss / (1024 * 1024)
        peak_memory = max(peak_memory, current_memory)

        print(f"  Run {i+1}/{NUM_ITERATIONS}: {elapsed:.2f} seconds")

    print()

    # Calculate statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    result = {
        "model": model_name,
        "model_path": model_path,
        "iterations": NUM_ITERATIONS,
        "avg_time_sec": round(avg_time, 2),
        "min_time_sec": round(min_time, 2),
        "max_time_sec": round(max_time, 2),
        "model_memory_mb": round(model_memory, 1),
        "peak_memory_mb": round(peak_memory, 1),
        "output_length": len(markdown),
        "timestamp": datetime.now().isoformat()
    }

    print("Results:")
    print(f"  Average: {avg_time:.2f} sec")
    print(f"  Min: {min_time:.2f} sec")
    print(f"  Max: {max_time:.2f} sec")
    print(f"  Memory: {model_memory:.1f} MB model, {peak_memory:.1f} MB peak")
    print()

    return result


def main():
    # Check if test image exists
    if not Path(TEST_IMAGE).exists():
        print(f"❌ Test image not found: {TEST_IMAGE}")
        print("Please run a previous test to generate a sample image.")
        return 1

    # Check if models exist
    for name, path in MODELS.items():
        if not Path(path).exists():
            print(f"❌ {name} model not found: {path}")
            if name == "4-bit":
                print("Run ./convert_4bit.sh first to create the 4-bit model.")
            return 1

    # Benchmark each model
    results = []

    for name, path in MODELS.items():
        result = benchmark_model(path, name)
        results.append(result)
        print()

    # Save results
    results_file = Path("4bit_8bit_benchmark_results.json")
    results_file.write_text(json.dumps(results, indent=2))
    print(f"✓ Results saved to: {results_file}")
    print()

    # Comparison summary
    print("=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print()

    bit8 = next(r for r in results if r["model"] == "8-bit")
    bit4 = next(r for r in results if r["model"] == "4-bit")

    speedup = bit8["avg_time_sec"] / bit4["avg_time_sec"]
    memory_ratio = bit4["model_memory_mb"] / bit8["model_memory_mb"]

    print(f"{'Metric':<25} {'8-bit':<15} {'4-bit':<15} {'Improvement':<15}")
    print("-" * 80)
    print(f"{'Avg inference time':<25} {bit8['avg_time_sec']:.2f} sec     {bit4['avg_time_sec']:.2f} sec     {speedup:.2f}x faster")
    print(f"{'Model memory':<25} {bit8['model_memory_mb']:.1f} MB      {bit4['model_memory_mb']:.1f} MB      {memory_ratio:.2f}x smaller")
    print(f"{'Peak memory':<25} {bit8['peak_memory_mb']:.1f} MB      {bit4['peak_memory_mb']:.1f} MB      {bit8['peak_memory_mb']/bit4['peak_memory_mb']:.2f}x")
    print()

    # Extrapolate to 96 pages
    print("Projected performance for 96 pages:")
    print("-" * 80)

    time_8bit_min = (bit8["avg_time_sec"] * 96) / 60
    time_4bit_min = (bit4["avg_time_sec"] * 96) / 60
    time_saved_min = time_8bit_min - time_4bit_min

    print(f"8-bit: {time_8bit_min:.1f} minutes")
    print(f"4-bit: {time_4bit_min:.1f} minutes")
    print(f"Time saved: {time_saved_min:.1f} minutes ({speedup:.2f}x speedup)")
    print()

    # Multi-process projection
    print("With 10 parallel processes:")
    print(f"  8-bit: {time_8bit_min/10:.1f} minutes")
    print(f"  4-bit: {time_4bit_min/10:.1f} minutes  ← Target: <10 minutes!")
    print()

    # Recommendation
    if speedup >= 1.8:
        print("✅ RECOMMENDATION: 4-bit quantization provides excellent speedup")
        print(f"   {speedup:.2f}x faster with {memory_ratio:.2f}x less memory")
        print()
        print("Next step: Run quality comparison with compare_quality.py")
    elif speedup >= 1.3:
        print("⚠️  RECOMMENDATION: Moderate speedup, check quality carefully")
        print(f"   {speedup:.2f}x faster might not justify quality loss")
    else:
        print("❌ RECOMMENDATION: Insufficient speedup for 4-bit conversion")
        print(f"   {speedup:.2f}x faster - consider other approaches")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
