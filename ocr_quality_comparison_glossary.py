#!/usr/bin/env python3
"""
DeepseekOCR Quality Level Comparison Test - Glossary Document

Tests all DeepseekOCR quality presets on the Arts Education Standards Glossary.
"""
import sys
from pathlib import Path

# Set test file
TEST_FILE = Path("test_glossary.pdf")

# Import and modify the main test
import ocr_quality_comparison_test

# Replace the test file in main()
original_main = ocr_quality_comparison_test.main

def wrapper_main():
    # Override test file
    ocr_quality_comparison_test.test_file = TEST_FILE
    
    # Run all tests
    import time
    import json
    from datetime import datetime
    
    test_file = TEST_FILE
    
    if not test_file.exists():
        print(f"✗ Test file not found: {test_file}")
        return 1
    
    print(f"\n{'='*70}")
    print("DeepseekOCR Quality Level Comparison Test - Glossary Document")
    print(f"{'='*70}")
    print(f"Test file: {test_file.name} ({test_file.stat().st_size / 1024:.2f} KB)")
    print(f"Testing {len(ocr_quality_comparison_test.QUALITY_LEVELS)} quality levels")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    results = []
    for i, quality_level in enumerate(ocr_quality_comparison_test.QUALITY_LEVELS, 1):
        result = ocr_quality_comparison_test.test_quality_level(
            test_file, quality_level, i, len(ocr_quality_comparison_test.QUALITY_LEVELS)
        )
        results.append(result)
        
        # Small delay between tests
        if i < len(ocr_quality_comparison_test.QUALITY_LEVELS):
            time.sleep(2)
    
    # Save detailed results
    output_file = Path("glossary_quality_comparison_results.json")
    with open(output_file, "w") as f:
        json.dump({
            "test_timestamp": datetime.now().isoformat(),
            "test_file": str(test_file),
            "test_file_size_kb": test_file.stat().st_size / 1024,
            "python_version": sys.version,
            "results": results,
        }, f, indent=2)
    
    # Generate comparison report
    ocr_quality_comparison_test.generate_comparison_report(results, output_file)
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"\nTEST SUMMARY:")
    print(f"  ✓ Successful: {successful}/{len(results)}")
    if failed > 0:
        print(f"  ✗ Failed: {failed}/{len(results)}")
    
    return 0 if successful > 0 else 1

if __name__ == "__main__":
    sys.exit(wrapper_main())
