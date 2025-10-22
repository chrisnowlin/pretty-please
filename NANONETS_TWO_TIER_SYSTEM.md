# Nanonets Two-Tier Hybrid System

**Date**: 2025-10-20
**Status**: ✅ **Implemented and Ready for Testing**
**Decision**: Use Nanonets-only approach (no PaddleOCR)

## Overview

The Nanonets Two-Tier System uses **FAST and BALANCED quality presets** to provide optimal speed/quality trade-off without external OCR dependencies. This approach eliminates PaddleOCR stability issues (music notation crashes) while maintaining significant performance improvements over BALANCED-only processing.

## Architecture

```
Input Document (PDF/Image)
     ↓
┌─────────────────────────────┐
│ Phase 1: FAST Preset        │
│ • Lower resolution          │
│ • Fewer tokens (2048)       │
│ • ~60-100 sec/page          │
└────────┬────────────────────┘
         ↓
┌─────────────────────────────┐
│ Markdown Complexity Analysis│
│ ✓ Tables? (<table>)         │
│ ✓ Equations? ($...$ $$...$$)│
│ ✓ Images? (<img>)           │
│ ✓ Structured tags?          │
│ ✓ Checkboxes? (☐ ☑)        │
│ ✓ Text too short?           │
└────────┬────────────────────┘
         │
    ┌────┴────┐
    │         │
    ↓         ↓
┌─────────┐ ┌──────────────────┐
│ Simple  │ │ Complex          │
│ (80%)   │ │ (20%)            │
│ Use     │ │ Phase 2:         │
│ FAST    │ │ BALANCED Preset  │
│ output  │ │ • Higher quality │
│         │ │ • ~199 sec/page  │
└────┬────┘ └────┬─────────────┘
     │           │
     ↓           ↓
┌─────────────────────────────┐
│ Final Markdown Output       │
└─────────────────────────────┘
```

## Key Advantages Over PaddleOCR Hybrid

| Aspect | Nanonets Two-Tier | PaddleOCR Hybrid |
|--------|-------------------|------------------|
| **Stability** | ✅ No crashes on music notation | ❌ Crashes (exit code 138) |
| **Dependencies** | ✅ No external OCR | ❌ +3GB PaddleOCR models |
| **Consistency** | ✅ Same markdown format | ⚠️ Two different formats |
| **Complexity** | ✅ Single technology | ⚠️ Two technologies |
| **Maintenance** | ✅ One codebase | ⚠️ Two systems to maintain |
| **Speed (96 pages)** | ~166 min (2.8 hrs) | ~66 min (1.1 hrs) |
| **vs BALANCED-only** | **2x faster** | **4.8x faster** |

## Performance Expectations

### For 96-Page Document (80% simple, 20% complex)

**Nanonets Two-Tier**:
- Simple pages (77): 77 × 80 sec = 6,160 sec (103 min)
- Complex pages (19): 19 × 199 sec = 3,781 sec (63 min)
- **Total**: ~166 minutes (2.8 hours)
- **vs BALANCED-only**: 2x faster
- **vs PaddleOCR hybrid**: 2.5x slower but more stable

**Best Case** (90% simple):
- Simple: 86 × 80 sec = 6,880 sec (115 min)
- Complex: 10 × 199 sec = 1,990 sec (33 min)
- **Total**: ~148 minutes (2.5 hours)
- **vs BALANCED-only**: 2.2x faster

## Implementation

### Core Classes

#### `MarkdownComplexityAnalyzer`
Analyzes markdown output from FAST preset to detect complexity:

```python
class MarkdownComplexityAnalyzer:
    def is_complex(self, markdown: str) -> Tuple[bool, str]:
        """Returns (is_complex, reason)"""
        # Detects:
        # - Tables (<table>)
        # - LaTeX equations ($...$ or $$...$$)
        # - Images (<img>)
        # - Structured tags (<watermark>, <signature>, etc.)
        # - Checkboxes (☐ ☑)
        # - Very short text (possible poor extraction)
```

**Complexity Indicators**:
1. **HTML Tables**: `<table` tags (threshold: ≥1)
2. **LaTeX Equations**: `$...$`, `$$...$$`, `\frac`, `\sum`, `\int` (threshold: ≥1)
3. **Images**: `<img>` tags (threshold: ≥2)
4. **Structured Tags**: `<watermark>`, `<signature>`, `<page_number>`
5. **Form Checkboxes**: `☐` or `☑` (threshold: ≥3)
6. **Short Text**: < 100 characters (possible poor extraction)

#### `NanonetsHybridAnalyzer`
Main two-tier processing engine:

```python
class NanonetsHybridAnalyzer:
    def analyze_document(self, file_path, page_number=1) -> Tuple[str, bool]:
        """
        Returns: (markdown, used_balanced)

        Process:
        1. Process with FAST preset
        2. Analyze markdown complexity
        3. If complex, re-process with BALANCED
        """
```

### Usage Examples

#### Basic Usage

```python
from src.jina_rag_pipeline.ingestion.nanonets_hybrid import NanonetsHybridAnalyzer

# Initialize analyzer
analyzer = NanonetsHybridAnalyzer(device="mps")

# Process single document
markdown, used_balanced = analyzer.analyze_document("document.pdf", page_number=1)

if used_balanced:
    print("Complex document - re-processed with BALANCED preset")
else:
    print("Simple document - used FAST preset output")
```

#### Batch Processing

```python
from pathlib import Path

# Process multiple documents
file_paths = [Path(f"page{i}.pdf") for i in range(1, 97)]

results, simple_count, complex_count = analyzer.analyze_documents_batch(file_paths)

print(f"Processed {len(file_paths)} documents:")
print(f"  Simple (FAST only):  {simple_count} ({simple_count/len(file_paths)*100:.1f}%)")
print(f"  Complex (BALANCED):  {complex_count} ({complex_count/len(file_paths)*100:.1f}%)")
```

#### Custom Complexity Thresholds

```python
from src.jina_rag_pipeline.ingestion.nanonets_hybrid import (
    NanonetsHybridAnalyzer,
    MarkdownComplexityAnalyzer
)

# Create custom complexity analyzer
complexity_analyzer = MarkdownComplexityAnalyzer(
    table_threshold=2,      # More tables needed to trigger BALANCED
    equation_threshold=3,   # More equations needed
    image_threshold=5,      # More images needed
    min_text_length=200,    # Stricter text length requirement
)

# Use with hybrid analyzer
analyzer = NanonetsHybridAnalyzer(
    device="mps",
    complexity_analyzer=complexity_analyzer
)
```

## Integration Paths

### Option 1: Replace Existing NanonetsLoader

**Current** (BALANCED-only):
```python
from src.jina_rag_pipeline.ingestion.nanonets_layout import NanonetsLayoutAnalyzer

analyzer = NanonetsLayoutAnalyzer(quality_preset="balanced")
markdown = analyzer.analyze_document(page_image, page_number=1)
```

**New** (Two-tier):
```python
from src.jina_rag_pipeline.ingestion.nanonets_hybrid import NanonetsHybridAnalyzer

analyzer = NanonetsHybridAnalyzer(device="mps")
markdown, used_balanced = analyzer.analyze_document(page_image, page_number=1)
```

### Option 2: Add to Loader Registry

```python
# In loaders.py
from .nanonets_hybrid import NanonetsHybridAnalyzer

LOADER_REGISTRY = {
    # ... existing loaders
    "nanonets_hybrid": NanonetsHybridAnalyzer,
}
```

### Option 3: Add to OCRConfig as Preset

```python
@dataclass
class OCRConfig:
    # ... existing fields

    use_two_tier: bool = False  # Enable Nanonets two-tier
    fast_complexity_threshold: float = 0.5  # Complexity score threshold

    @classmethod
    def nanonets_two_tier(cls) -> "OCRConfig":
        """Nanonets two-tier for 2x speedup with stability."""
        return cls(
            use_two_tier=True,
            batch_size=20,
            # ... other settings
        )
```

## Testing

### Test Suite

Run the comprehensive test suite:

```bash
python test_nanonets_hybrid.py
```

**Tests included**:
1. **Single Document Processing** - Validates basic two-tier logic
2. **Complexity Detection** - Tests markdown analysis with various inputs
3. **Batch Processing** - Validates multi-document handling with statistics

### Expected Output

```
================================================================================
NANONETS TWO-TIER HYBRID SYSTEM - TEST SUITE
================================================================================

TEST 1: Single Document Processing
  [Page 1] Phase 1: Processing with FAST preset...
  [Page 1] Complex document detected: tables_detected (3)
  [Page 1] Phase 2: Re-processing with BALANCED preset...
  [Page 1] ✓ BALANCED processing complete

  RESULTS:
    Processing time: 280.5 seconds
    Used BALANCED: True
    Markdown length: 3,456 characters

TEST 2: Complexity Detection
  Simple text:
    Complex: False
    Reason: simple_document
    Score: 0.00

  With table:
    Complex: True
    Reason: tables_detected (1)
    Score: 0.15

TEST 3: Batch Processing
  BATCH PROCESSING COMPLETE
    Total documents: 3
    Simple (FAST only):    2 (66.7%)
    Complex (BALANCED):    1 (33.3%)

ALL TESTS COMPLETE
✅ Nanonets two-tier hybrid system ready for use!
```

## Complexity Detection Details

### Markdown-Based Detection (vs OCR Confidence)

**Why markdown-based detection is better**:
- ✅ **Richer information**: Can inspect actual content (tables, equations, images)
- ✅ **More reliable**: Based on structured output, not OCR confidence scores
- ✅ **Content-aware**: Detects what matters (complexity), not how confident OCR is
- ✅ **No false positives**: Music notation won't crash, just gets BALANCED treatment

**Example detections**:

```python
# Table detected
markdown = "Some text\n<table><tr><td>Data</td></tr></table>"
# → Complex: True, reason: "tables_detected (1)"

# Equation detected
markdown = "The formula $E = mc^2$ shows..."
# → Complex: True, reason: "equations_detected (1)"

# Simple text
markdown = "This is a simple document with just plain text content."
# → Complex: False, reason: "simple_document"
```

### Tuning Complexity Thresholds

Based on production data, you can adjust thresholds:

```python
# More aggressive (fewer BALANCED re-processings)
analyzer = MarkdownComplexityAnalyzer(
    table_threshold=3,     # Require 3+ tables
    equation_threshold=5,  # Require 5+ equations
    image_threshold=10,    # Require 10+ images
)

# More conservative (more BALANCED re-processings)
analyzer = MarkdownComplexityAnalyzer(
    table_threshold=1,     # Any table triggers BALANCED
    equation_threshold=1,  # Any equation triggers BALANCED
    image_threshold=1,     # Any image triggers BALANCED
)
```

## Performance Tuning

### Adjust Quality Presets

The FAST and BALANCED presets are defined in `nanonets_layout.py`:

```python
QUALITY_PRESETS = {
    "fast": {
        "min_pixels": 250_000,    # ~500x500
        "max_pixels": 400_000,    # ~632x632
        "max_new_tokens": 2048,
    },
    "balanced": {
        "min_pixels": 500_000,    # ~707x707
        "max_pixels": 1_200_000,  # ~1095x1095
        "max_new_tokens": 4096,
    },
}
```

**If FAST is too slow**:
- Reduce `min_pixels` / `max_pixels` further
- Reduce `max_new_tokens` to 1024

**If FAST quality is too low**:
- Increase pixels (but will slow down)
- Consider accepting current quality for simple documents

### Parallelize FAST Pass

For large document volumes, process multiple pages with FAST in parallel:

```python
from concurrent.futures import ThreadPoolExecutor

def process_pages_parallel(analyzer, file_paths, max_workers=4):
    """Process FAST pass in parallel, then BALANCED sequentially."""
    # Phase 1: Parallel FAST processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        fast_results = list(executor.map(
            lambda p: analyzer._process_fast(p),
            file_paths
        ))

    # Phase 2: Sequential BALANCED for complex pages
    final_results = []
    for i, (markdown_fast, is_complex) in enumerate(fast_results):
        if is_complex:
            markdown = analyzer._process_balanced(file_paths[i])
        else:
            markdown = markdown_fast
        final_results.append(markdown)

    return final_results
```

## Monitoring and Telemetry

### Key Metrics to Track

```python
import logging

logger = logging.getLogger("nanonets_hybrid")

# Track routing decisions
logger.info(f"Document complexity: {complexity_score:.2f}")
logger.info(f"Routing decision: {'BALANCED' if used_balanced else 'FAST'}")
logger.info(f"Complexity reason: {reason}")

# Track performance
logger.info(f"FAST processing time: {fast_time:.1f}s")
logger.info(f"BALANCED processing time: {balanced_time:.1f}s")
logger.info(f"Total time: {total_time:.1f}s")

# Track statistics
logger.info(f"Batch summary: {simple_count} simple, {complex_count} complex")
logger.info(f"Complexity rate: {complex_count/total*100:.1f}%")
```

### Production Monitoring

Recommended metrics for production:
- **Complexity distribution**: Actual simple/complex ratio (target: 80/20)
- **Processing time**: Average per FAST preset and BALANCED preset
- **Re-processing rate**: Percentage of documents needing BALANCED
- **Speedup achieved**: Actual time vs BALANCED-only baseline
- **Complexity reasons**: Which indicators trigger BALANCED most often

## Benefits Summary

### ✅ Advantages

1. **Stability**: No PaddleOCR crashes on music notation or complex layouts
2. **Simplicity**: Single technology, one model, one codebase
3. **Consistency**: Same markdown format across all documents
4. **Performance**: 2x faster than BALANCED-only
5. **Quality**: Complex documents still get full BALANCED treatment
6. **Transparency**: Clear logging shows routing decisions
7. **Tunable**: Easily adjust complexity thresholds

### ⚠️ Trade-offs

1. **Slower than PaddleOCR hybrid**: 2.5x slower for simple documents
2. **FAST quality lower**: Reduced resolution may miss some details
3. **Re-processing cost**: Complex documents processed twice (FAST → BALANCED)
4. **Still using VLM**: No true "fast mode", just lower quality preset

## Recommendations

### Use Nanonets Two-Tier If:

✅ **Stability is priority** - Music notation, challenging documents
✅ **Prefer simpler architecture** - Single technology
✅ **Can accept 2-3 hour processing** for 96 pages
✅ **Want consistent markdown** across all documents
✅ **Avoiding PaddleOCR maintenance** is valuable

### Use PaddleOCR Hybrid If:

✅ **Speed is critical** - Need < 2 hours for 96 pages
✅ **Documents are mostly simple** text (>80%)
✅ **Can pre-filter** music notation documents
✅ **Willing to maintain** two OCR systems

### Use BALANCED-Only If:

✅ **Small volumes** (<10 pages)
✅ **Maximum quality** required everywhere
✅ **Time not a concern** (5+ hours acceptable)

## Future Enhancements

1. **GGUF Quantization**: Investigate quantized models for 2-4x speedup
2. **Adaptive Quality**: Use complexity score to select FAST/BALANCED/HIGH
3. **Parallel FAST Processing**: Process multiple FAST pages concurrently
4. **Smarter Complexity Detection**: ML-based complexity prediction
5. **Nanonets Feature Request**: Request official "fast mode" from Nanonets

## Files

- **Implementation**: `src/jina_rag_pipeline/ingestion/nanonets_hybrid.py`
- **Tests**: `test_nanonets_hybrid.py`
- **Documentation**: `NANONETS_TWO_TIER_SYSTEM.md` (this file)
- **Strategy Analysis**: `OCR_STRATEGY_OPTIONS.md`

## Conclusion

The Nanonets Two-Tier System provides a **stable, simple, and performant** alternative to the PaddleOCR hybrid approach. By using FAST and BALANCED presets with markdown-based complexity detection, we achieve 2x speedup over BALANCED-only while avoiding stability issues entirely.

**Status**: ✅ Ready for integration and production testing

**Next Step**: Run `test_nanonets_hybrid.py` to validate implementation, then integrate into production loaders.
