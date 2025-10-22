#!/usr/bin/env python3
"""
DeepseekOCR standalone test - Test and collect metrics for DeepseekOCR backend.
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import psutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.jina_rag_pipeline.ingestion import create_ocr_loader, OCRConfig


def get_memory_usage():
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def test_deepseek_ocr(test_file: Path):
    """Test DeepseekOCR and collect detailed metrics."""
    print("="*60)
    print("DeepseekOCR Standalone Test")
    print("="*60)

    result = {
        "backend": "deepseek",
        "test_file": str(test_file),
        "test_timestamp": datetime.now().isoformat(),
        "success": False,
    }

    try:
        # Record memory before
        mem_before = get_memory_usage()
        print(f"\nMemory before: {mem_before:.2f} MB")

        # Create loader
        print("Creating DeepseekOCR loader...")
        config = OCRConfig.deepseek_balanced()
        loader = create_ocr_loader(backend='deepseek', config=config)

        # Get backend info
        info = loader.get_backend_info()
        print(f"✓ Analyzer: {info.get('analyzer_type')}")
        print(f"✓ Config: {config.__dict__}")

        # Load and process document
        print(f"\nProcessing: {test_file.name} ({test_file.stat().st_size / 1024:.2f} KB)")
        start_time = time.time()
        document = loader.load(test_file)
        processing_time = time.time() - start_time

        # Record memory after
        mem_after = get_memory_usage()
        mem_delta = mem_after - mem_before

        # Collect results
        result.update({
            "success": True,
            "processing_time_seconds": processing_time,
            "content_length_chars": len(document.content),
            "memory_before_mb": mem_before,
            "memory_after_mb": mem_after,
            "memory_delta_mb": mem_delta,
            "content_preview": document.content[:1000],  # First 1000 chars
            "metadata": {k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                        for k, v in (document.metadata or {}).items()}
        })

        # Print results
        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"✓ Processing time: {processing_time:.2f}s")
        print(f"✓ Content extracted: {len(document.content):,} characters")
        print(f"✓ Memory used: {mem_delta:.2f} MB")
        print(f"✓ Throughput: {len(document.content) / processing_time:.0f} chars/sec")

        # Show content sample
        print(f"\nContent preview (first 500 chars):")
        print("-" * 60)
        print(document.content[:500])
        print("-" * 60)

        # Metadata
        print(f"\nDocument metadata:")
        for key, value in (document.metadata or {}).items():
            if key != 'page_boundaries':  # Skip page boundaries for cleaner output
                print(f"  {key}: {value}")

    except Exception as e:
        result["error"] = str(e)
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return result

    # Save results to JSON
    output_file = Path("deepseek_test_results.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n✓ Results saved to: {output_file}")

    return result


def main():
    """Run the test."""
    test_file = Path("test_2pages.pdf")

    if not test_file.exists():
        print(f"✗ Test file not found: {test_file}")
        return 1

    result = test_deepseek_ocr(test_file)

    print("\n" + "="*60)
    if result["success"]:
        print("✓ TEST PASSED")
        print("="*60)
        print(f"\nDeepseekOCR successfully processed the document!")
        print(f"Time: {result['processing_time_seconds']:.2f}s")
        print(f"Content: {result['content_length_chars']:,} characters")
        print(f"Memory: {result['memory_delta_mb']:.2f} MB")
        return 0
    else:
        print("✗ TEST FAILED")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
