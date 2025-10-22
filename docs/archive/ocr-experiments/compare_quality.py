#!/usr/bin/env python3
"""
Compare output quality between 4-bit and 8-bit models.

Analyzes the same document with both models and compares:
- Character-level differences
- Word-level differences
- Structural differences
- Semantic region extraction
"""

import sys
import difflib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from jina_rag_pipeline.ingestion.nanonets_mlx import NanonetsMLXAnalyzer

# Test configuration
TEST_IMAGE = "/var/folders/_1/66qwm39s5vg8tgtylwl5hvkh0000gn/T/tmp0a6etio8.png"
MODELS = {
    "8-bit": "./models/nanonets-ocr2-3b-mlx",
    "4-bit": "./models/nanonets-ocr2-3b-mlx-4bit"
}

print("=" * 80)
print("QUALITY COMPARISON: 4-BIT vs 8-BIT")
print("=" * 80)
print()


def analyze_with_model(model_path: str, model_name: str) -> tuple:
    """Analyze document and return markdown + regions."""
    print(f"Analyzing with {model_name}...")
    analyzer = NanonetsMLXAnalyzer(model_path=model_path)

    markdown = analyzer.analyze_document(TEST_IMAGE)
    regions = analyzer.extract_regions(TEST_IMAGE, page_number=1)

    print(f"  ✓ {len(markdown)} characters extracted")
    print(f"  ✓ {len(regions)} semantic regions")
    print()

    return markdown, regions


def compare_text(text1: str, text2: str, name1: str, name2: str):
    """Compare two text outputs."""
    print("-" * 80)
    print(f"TEXT COMPARISON: {name1} vs {name2}")
    print("-" * 80)
    print()

    # Basic stats
    print("Length:")
    print(f"  {name1}: {len(text1)} characters")
    print(f"  {name2}: {len(text2)} characters")
    print(f"  Difference: {abs(len(text1) - len(text2))} characters ({abs(len(text1) - len(text2)) / len(text1) * 100:.1f}%)")
    print()

    # Character-level similarity
    matcher = difflib.SequenceMatcher(None, text1, text2)
    similarity = matcher.ratio() * 100

    print(f"Character similarity: {similarity:.2f}%")
    print()

    # Word-level comparison
    words1 = text1.split()
    words2 = text2.split()

    common_words = len(set(words1) & set(words2))
    total_words = len(set(words1) | set(words2))
    word_similarity = (common_words / total_words * 100) if total_words > 0 else 0

    print("Word-level:")
    print(f"  {name1}: {len(words1)} words")
    print(f"  {name2}: {len(words2)} words")
    print(f"  Common words: {common_words}/{total_words} ({word_similarity:.1f}% similarity)")
    print()

    # Find differences
    if similarity < 99:
        print("Showing first 10 differences:")
        print()

        opcodes = matcher.get_opcodes()
        diff_count = 0

        for tag, i1, i2, j1, j2 in opcodes:
            if tag != 'equal' and diff_count < 10:
                diff_count += 1
                print(f"  Diff {diff_count}:")
                print(f"    {name1}: '{text1[i1:i2]}'")
                print(f"    {name2}: '{text2[j1:j2]}'")
                print()
    else:
        print("✓ Texts are nearly identical!")
        print()

    return similarity


def compare_regions(regions1: list, regions2: list, name1: str, name2: str):
    """Compare semantic region extraction."""
    print("-" * 80)
    print(f"REGION COMPARISON: {name1} vs {name2}")
    print("-" * 80)
    print()

    print("Region counts:")
    print(f"  {name1}: {len(regions1)} regions")
    print(f"  {name2}: {len(regions2)} regions")
    print()

    # Compare region types
    types1 = {}
    for r in regions1:
        types1[r.region_type] = types1.get(r.region_type, 0) + 1

    types2 = {}
    for r in regions2:
        types2[r.region_type] = types2.get(r.region_type, 0) + 1

    all_types = set(types1.keys()) | set(types2.keys())

    print("Region types:")
    print(f"  {'Type':<15} {name1:<15} {name2:<15} {'Match':<10}")
    print("  " + "-" * 60)

    for rtype in sorted(all_types):
        count1 = types1.get(rtype, 0)
        count2 = types2.get(rtype, 0)
        match = "✓" if count1 == count2 else "✗"
        print(f"  {rtype:<15} {count1:<15} {count2:<15} {match:<10}")

    print()

    # Calculate region similarity
    if len(regions1) == len(regions2):
        print("✓ Same number of regions extracted")
    else:
        diff = abs(len(regions1) - len(regions2))
        print(f"⚠️  Region count differs by {diff}")

    print()


def main():
    # Check if test image exists
    if not Path(TEST_IMAGE).exists():
        print(f"❌ Test image not found: {TEST_IMAGE}")
        return 1

    # Check if models exist
    for name, path in MODELS.items():
        if not Path(path).exists():
            print(f"❌ {name} model not found: {path}")
            return 1

    print(f"Test image: {Path(TEST_IMAGE).name}")
    print()

    # Analyze with both models
    markdown_8bit, regions_8bit = analyze_with_model(MODELS["8-bit"], "8-bit")
    markdown_4bit, regions_4bit = analyze_with_model(MODELS["4-bit"], "4-bit")

    # Compare outputs
    text_similarity = compare_text(markdown_8bit, markdown_4bit, "8-bit", "4-bit")
    compare_regions(regions_8bit, regions_4bit, "8-bit", "4-bit")

    # Final assessment
    print("=" * 80)
    print("QUALITY ASSESSMENT")
    print("=" * 80)
    print()

    if text_similarity >= 98:
        quality_loss = 100 - text_similarity
        print(f"✅ EXCELLENT: {text_similarity:.2f}% similarity")
        print(f"   Quality loss: {quality_loss:.2f}%")
        print()
        print("   4-bit quantization maintains nearly identical quality.")
        print("   Safe to use for production.")
    elif text_similarity >= 95:
        quality_loss = 100 - text_similarity
        print(f"✓ GOOD: {text_similarity:.2f}% similarity")
        print(f"   Quality loss: {quality_loss:.2f}%")
        print()
        print("   Minor differences, acceptable for most use cases.")
        print("   Recommend visual inspection of sample outputs.")
    elif text_similarity >= 90:
        quality_loss = 100 - text_similarity
        print(f"⚠️  ACCEPTABLE: {text_similarity:.2f}% similarity")
        print(f"   Quality loss: {quality_loss:.2f}%")
        print()
        print("   Noticeable differences. Carefully evaluate if acceptable.")
        print("   Test on representative documents before production use.")
    else:
        quality_loss = 100 - text_similarity
        print(f"❌ POOR: {text_similarity:.2f}% similarity")
        print(f"   Quality loss: {quality_loss:.2f}%")
        print()
        print("   Significant quality degradation.")
        print("   4-bit quantization may not be suitable for this model.")

    print()

    # Save sample outputs for manual inspection
    output_dir = Path("quality_comparison_samples")
    output_dir.mkdir(exist_ok=True)

    (output_dir / "8bit_output.md").write_text(markdown_8bit)
    (output_dir / "4bit_output.md").write_text(markdown_4bit)

    print(f"Sample outputs saved to: {output_dir}/")
    print("  - 8bit_output.md")
    print("  - 4bit_output.md")
    print()
    print("Review these files to assess quality differences visually.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
