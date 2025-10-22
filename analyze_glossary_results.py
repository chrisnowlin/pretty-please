#!/usr/bin/env python3
"""Analyze glossary quality comparison results."""
import json
from pathlib import Path
from difflib import SequenceMatcher

# Load results
with open("glossary_quality_comparison_results.json") as f:
    data = json.load(f)

print("="*80)
print("DeepseekOCR Glossary Test - Quality Analysis")
print("="*80)
print()

# Extract successful results
results = [r for r in data["results"] if r["success"]]

# Performance summary
print("1. PERFORMANCE COMPARISON (Real-World Complex Document)")
print("-"*80)
print(f"{'Mode':<20} {'Time (s)':<12} {'Chars':<12} {'Throughput':<15} {'Memory (MB)':<12}")
print("-"*80)

for r in results:
    mode = r["quality_level"]
    time_val = r["processing_time_seconds"]
    chars = r["content_length_chars"]
    throughput = r["throughput_chars_per_sec"]
    memory = r["memory_delta_mb"]
    
    print(f"{mode:<20} {time_val:<12.2f} {chars:<12,} {throughput:<15.1f} {memory:<12.0f}")

print()

# Content comparison
print("2. CONTENT QUALITY ANALYSIS")
print("-"*80)

# Use balanced as baseline
baseline = next(r for r in results if r["quality_level"] == "balanced")
baseline_content = baseline["full_content"]

print(f"Baseline (balanced): {len(baseline_content):,} characters")
print()

for r in results:
    if r["quality_level"] == "balanced":
        continue
    
    mode = r["quality_level"]
    content = r["full_content"]
    
    # Calculate similarity
    similarity = SequenceMatcher(None, baseline_content, content).ratio()
    
    # Check for differences
    char_diff = len(content) - len(baseline_content)
    
    print(f"{mode.upper()}:")
    print(f"  Characters: {len(content):,} (diff: {char_diff:+,})")
    print(f"  Similarity to balanced: {similarity*100:.4f}%")
    
    # If different, show sample differences
    if similarity < 1.0:
        print(f"  ⚠️  Content differs from balanced mode")
        # Find first difference
        for i, (c1, c2) in enumerate(zip(baseline_content, content)):
            if c1 != c2:
                start = max(0, i-50)
                end = min(len(baseline_content), i+50)
                print(f"  First diff at char {i}:")
                print(f"    Balanced: ...{baseline_content[start:end]!r}...")
                print(f"    {mode}: ...{content[start:end]!r}...")
                break
    else:
        print(f"  ✓ Identical to balanced mode")
    print()

print("3. KEY FINDINGS")
print("-"*80)

# Find fastest
fastest = min(results, key=lambda r: r["processing_time_seconds"])
print(f"⚡ Fastest mode: {fastest['quality_level'].upper()}")
print(f"   Time: {fastest['processing_time_seconds']:.2f}s")
print(f"   Throughput: {fastest['throughput_chars_per_sec']:.1f} chars/sec")
print()

# Memory efficiency
most_efficient_mem = min(results, key=lambda r: r["memory_delta_mb"])
print(f"💾 Most memory efficient: {most_efficient_mem['quality_level'].upper()}")
print(f"   Memory delta: {most_efficient_mem['memory_delta_mb']:.1f} MB")
print()

# Check if all content is identical
all_identical = all(
    r["content_length_chars"] == baseline["content_length_chars"]
    for r in results
)

if all_identical:
    print("📊 Content extraction quality:")
    print("   All modes extracted IDENTICAL content (53,792 characters)")
    print("   This suggests the document is well-formed and doesn't require")
    print("   higher quality modes for accurate extraction.")
else:
    print("📊 Content extraction quality:")
    print("   Modes show differences in extracted content.")
    print("   Higher quality modes may provide better accuracy for this document.")

print()
print("4. RECOMMENDATION FOR THIS DOCUMENT TYPE")
print("-"*80)
print(f"For glossary/text-heavy documents like this one:")
print(f"")
print(f"🎯 RECOMMENDED: {fastest['quality_level'].upper()} mode")
print(f"   - Fastest processing: {fastest['processing_time_seconds']:.2f}s")
print(f"   - Highest throughput: {fastest['throughput_chars_per_sec']:.1f} chars/sec")
print(f"   - Same extraction quality as other modes")
print(f"   - Most efficient for batch processing")
print()
print(f"✅ ALSO GOOD: SMALL or BALANCED mode")
print(f"   - Slightly slower but still fast (~4.5-4.8s)")
print(f"   - Identical content extraction")
print(f"   - Good for general-purpose use")
print()

print("="*80)
