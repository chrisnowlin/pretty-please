#!/usr/bin/env python3
"""
1:1 OCR Backend Comparison Test
Compares DeepseekOCR and PaddleOCR performance on the same test file.
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import traceback
import psutil
import os
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.jina_rag_pipeline.ingestion import create_ocr_loader, OCRConfig, SemanticRegion

PADDLE_ANALYZER_KWARGS: dict[str, Any] = {}
DEEPSEEK_CONFIG_PRESET = os.getenv("DEEPSEEK_PRESET")

_opt_level = os.getenv("PADDLE_OPT_LEVEL")
if _opt_level:
    PADDLE_ANALYZER_KWARGS["optimization_level"] = _opt_level

_analyzer_kwargs_env = os.getenv("PADDLE_ANALYZER_KWARGS")
if _analyzer_kwargs_env:
    try:
        parsed_kwargs = json.loads(_analyzer_kwargs_env)
        if isinstance(parsed_kwargs, dict):
            PADDLE_ANALYZER_KWARGS.update(parsed_kwargs)
    except json.JSONDecodeError as exc:
        print(f"⚠️  Failed to parse PADDLE_ANALYZER_KWARGS JSON: {exc}")

def resolve_config(backend: str, config=None):
    if config is not None:
        return config

    if backend == "deepseek" and DEEPSEEK_CONFIG_PRESET:
        preset_name = DEEPSEEK_CONFIG_PRESET.strip()
        factory = getattr(OCRConfig, preset_name, None)
        if callable(factory):
            try:
                preset_config = factory()
                print(f"✓ Using Deepseek preset: {preset_name}")
                return preset_config
            except Exception as exc:  # pragma: no cover - defensive
                print(f"⚠️  Failed to apply Deepseek preset {preset_name}: {exc}")
        else:
            print(f"⚠️  Unknown DEEPSEEK_PRESET '{preset_name}', falling back to balanced.")

    if backend == "deepseek":
        return OCRConfig.deepseek_balanced()
    if backend == "paddleocr":
        return OCRConfig.balanced()
    return config


def make_json_safe(value: Any, *, max_items: int = 10, depth: int = 0, max_depth: int = 4) -> Any:
    """
    Convert nested structures to JSON-serializable representations while keeping
    the output readable. Long lists are truncated with a placeholder entry.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, SemanticRegion):
        return value.to_dict()

    if depth >= max_depth:
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(val, max_items=max_items, depth=depth + 1, max_depth=max_depth)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        items = list(value)
        safe_items = [
            make_json_safe(item, max_items=max_items, depth=depth + 1, max_depth=max_depth)
            for item in items[:max_items]
        ]
        remaining = len(items) - len(safe_items)
        if remaining > 0:
            safe_items.append(f"... {remaining} more")
        return safe_items

    if hasattr(value, "__dict__"):
        return make_json_safe(vars(value), max_items=max_items, depth=depth + 1, max_depth=max_depth)

    return str(value)


def get_memory_usage():
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def test_ocr_backend(backend: str, test_file: Path, config=None):
    """
    Test a single OCR backend and collect detailed metrics.

    Returns dict with:
    - backend: backend name
    - success: bool
    - processing_time: seconds
    - content_length: characters extracted
    - memory_before: MB
    - memory_after: MB
    - memory_delta: MB
    - content_preview: first 500 chars
    - error: error message if failed
    """
    result = {
        "backend": backend,
        "success": False,
        "processing_time": 0,
        "content_length": 0,
        "memory_before": 0,
        "memory_after": 0,
        "memory_delta": 0,
        "content_preview": "",
        "error": None,
        "metadata": {}
    }

    print(f"\n{'='*60}")
    print(f"Testing {backend.upper()} Backend")
    print(f"{'='*60}")

    try:
        # Record memory before
        result["memory_before"] = get_memory_usage()
        print(f"Memory before: {result['memory_before']:.2f} MB")

        # Create loader
        print(f"Creating {backend} loader...")
        start_time = time.time()
        config = resolve_config(backend, config)

        analyzer_kwargs = None
        if backend == "paddleocr" and PADDLE_ANALYZER_KWARGS:
            print(f"✓ Applying Paddle analyzer overrides: {PADDLE_ANALYZER_KWARGS}")
            analyzer_kwargs = dict(PADDLE_ANALYZER_KWARGS)

        loader = create_ocr_loader(backend=backend, config=config, analyzer_kwargs=analyzer_kwargs)
        init_time = time.time() - start_time
        print(f"✓ Loader initialized in {init_time:.2f}s")

        # Get backend info
        info = loader.get_backend_info()
        result["metadata"]["analyzer_type"] = info.get("analyzer_type")
        print(f"✓ Analyzer: {info.get('analyzer_type')}")

        # Load and process document
        print(f"Processing document: {test_file.name}")
        start_time = time.time()
        document = loader.load(test_file)
        result["processing_time"] = time.time() - start_time

        # Collect results
        result["content_length"] = len(document.content)
        result["content_preview"] = document.content[:500]
        metadata = document.metadata or {}
        regions = metadata.get("regions")

        result["metadata"]["source"] = document.source
        if config is not None and hasattr(config, "__dict__"):
            result["metadata"]["config"] = make_json_safe(config.__dict__)
        if backend == "paddleocr":
            try:
                analyzer = loader._get_analyzer()
            except Exception:  # pragma: no cover - defensive
                analyzer = None
            if analyzer is not None:
                result["metadata"]["optimization_level"] = getattr(analyzer, "optimization_level", None)
            result["metadata"]["analyzer_kwargs"] = make_json_safe(analyzer_kwargs or {})
        if isinstance(regions, list) and regions:
            region_types = sorted({getattr(region, "region_type", str(type(region))) for region in regions})
            result["metadata"]["region_count"] = len(regions)
            result["metadata"]["region_types"] = region_types

        result["metadata"]["details"] = make_json_safe(metadata)

        # Record memory after
        result["memory_after"] = get_memory_usage()
        result["memory_delta"] = result["memory_after"] - result["memory_before"]

        result["success"] = True

        # Print results
        print(f"✓ Processing completed in {result['processing_time']:.2f}s")
        print(f"✓ Extracted {result['content_length']:,} characters")
        print(f"✓ Memory after: {result['memory_after']:.2f} MB")
        print(f"✓ Memory delta: {result['memory_delta']:.2f} MB")

    except Exception as e:
        result["error"] = str(e)
        result["error_traceback"] = traceback.format_exc()
        print(f"✗ Error: {e}")
        traceback.print_exc()

    return result


def compare_results(deepseek_result, paddle_result):
    """Generate comparison report."""
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)

    # Success status
    print("\n1. SUCCESS STATUS")
    print("-" * 40)
    print(f"DeepseekOCR: {'✓ PASSED' if deepseek_result['success'] else '✗ FAILED'}")
    print(f"PaddleOCR:   {'✓ PASSED' if paddle_result['success'] else '✗ FAILED'}")

    if not (deepseek_result['success'] and paddle_result['success']):
        print("\n⚠️  Cannot compare - one or both backends failed")
        return

    # Processing time
    print("\n2. PROCESSING TIME")
    print("-" * 40)
    deepseek_time = deepseek_result['processing_time']
    paddle_time = paddle_result['processing_time']
    print(f"DeepseekOCR: {deepseek_time:.2f}s")
    print(f"PaddleOCR:   {paddle_time:.2f}s")

    if deepseek_time < paddle_time:
        speedup = paddle_time / deepseek_time
        print(f"→ DeepseekOCR is {speedup:.2f}x faster")
    else:
        speedup = deepseek_time / paddle_time
        print(f"→ PaddleOCR is {speedup:.2f}x faster")

    # Content extraction
    print("\n3. CONTENT EXTRACTION")
    print("-" * 40)
    deepseek_chars = deepseek_result['content_length']
    paddle_chars = paddle_result['content_length']
    print(f"DeepseekOCR: {deepseek_chars:,} characters")
    print(f"PaddleOCR:   {paddle_chars:,} characters")

    char_diff = abs(deepseek_chars - paddle_chars)
    char_diff_pct = (char_diff / max(deepseek_chars, paddle_chars)) * 100
    print(f"→ Difference: {char_diff:,} characters ({char_diff_pct:.1f}%)")

    # Memory usage
    print("\n4. MEMORY USAGE")
    print("-" * 40)
    deepseek_mem = deepseek_result['memory_delta']
    paddle_mem = paddle_result['memory_delta']
    print(f"DeepseekOCR: {deepseek_mem:.2f} MB delta")
    print(f"PaddleOCR:   {paddle_mem:.2f} MB delta")

    if deepseek_mem < paddle_mem:
        ratio = paddle_mem / deepseek_mem if deepseek_mem > 0 else 0
        print(f"→ DeepseekOCR uses {ratio:.2f}x less memory")
    else:
        ratio = deepseek_mem / paddle_mem if paddle_mem > 0 else 0
        print(f"→ PaddleOCR uses {ratio:.2f}x less memory")

    # Content preview comparison
    print("\n5. CONTENT PREVIEW (first 200 chars)")
    print("-" * 40)
    print("\nDeepseekOCR:")
    print(deepseek_result['content_preview'][:200])
    print("\nPaddleOCR:")
    print(paddle_result['content_preview'][:200])

    # Recommendations
    print("\n6. RECOMMENDATIONS")
    print("-" * 40)

    if deepseek_time < paddle_time and deepseek_chars >= paddle_chars * 0.95:
        print("→ DeepseekOCR: Faster with comparable content extraction")
    elif paddle_time < deepseek_time and paddle_chars >= deepseek_chars * 0.95:
        print("→ PaddleOCR: Faster with comparable content extraction")
    elif deepseek_chars > paddle_chars * 1.1:
        print("→ DeepseekOCR: Extracts significantly more content")
    elif paddle_chars > deepseek_chars * 1.1:
        print("→ PaddleOCR: Extracts significantly more content")
    else:
        print("→ Both backends perform similarly")

    if deepseek_mem < paddle_mem * 0.8:
        print("→ DeepseekOCR: More memory efficient")
    elif paddle_mem < deepseek_mem * 0.8:
        print("→ PaddleOCR: More memory efficient")


def save_results(deepseek_result, paddle_result, test_file):
    """Save detailed results to JSON file."""
    results = {
        "test_timestamp": datetime.now().isoformat(),
        "test_file": str(test_file),
        "test_file_size_mb": test_file.stat().st_size / 1024 / 1024,
        "python_version": sys.version,
        "deepseek": deepseek_result,
        "paddleocr": paddle_result,
    }

    output_file = Path("ocr_comparison_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Detailed results saved to: {output_file}")
    return output_file


def main():
    """Run the comparison test."""
    print("OCR Backend 1:1 Comparison Test")
    print("="*60)

    # Find test file
    test_file = Path("test_2pages.pdf")
    if not test_file.exists():
        print(f"✗ Test file not found: {test_file}")
        return 1

    print(f"Test file: {test_file}")
    print(f"File size: {test_file.stat().st_size / 1024:.2f} KB")

    # Test DeepseekOCR
    deepseek_result = test_ocr_backend(
        backend='deepseek',
        test_file=test_file,
        config=None
    )

    # Small delay to let memory stabilize
    time.sleep(2)

    # Test PaddleOCR
    paddle_result = test_ocr_backend(
        backend='paddleocr',
        test_file=test_file,
        config=None
    )

    # Compare results
    compare_results(deepseek_result, paddle_result)

    # Save detailed results
    output_file = save_results(deepseek_result, paddle_result, test_file)

    # Summary
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

    both_passed = deepseek_result['success'] and paddle_result['success']
    if both_passed:
        print("✓ Both backends completed successfully")
        print(f"\nView detailed results: {output_file}")
    else:
        print("⚠️  One or more backends failed - check errors above")

    return 0 if both_passed else 1


if __name__ == "__main__":
    sys.exit(main())
