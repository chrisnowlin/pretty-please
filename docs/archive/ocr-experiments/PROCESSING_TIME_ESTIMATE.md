# Processing Time Estimate: Teach Like a Champion 3 (893 pages)

**Date**: 2025-10-18
**Configuration**: Aggressive profile (M4 Max, 48GB RAM)
**Enhancement**: Batch inference with semantic region extraction

---

## Executive Summary

**Estimated Total Time: 1.5 - 3.7 hours**

- **Best case**: ~90 minutes (1.5 hours)
- **Typical case**: ~2.5 hours
- **Worst case**: ~220 minutes (3.7 hours)

---

## Empirical Data from Tests

### Test Results (First 6 Pages)

From `test_batch_simple.py` actual run:

| Batch | Pages | Rendering | Analysis | Total | Per-Page |
|-------|-------|-----------|----------|-------|----------|
| 1 | 0-1 (2 pages) | ~1 sec | 27 sec | 28 sec | 14 sec/page |
| 2 | 2-3 (2 pages) | ~1 sec | 74 sec | 75 sec | 37.5 sec/page |
| 3 | 4-5 (2 pages) | ~1 sec | 51 sec | 52 sec | 26 sec/page |
| **Average** | - | ~1 sec | **51 sec** | **52 sec** | **26 sec/page** |

**Key Observations**:
- Rendering is fast: ~0.5-1 sec per page (PyMuPDF is efficient)
- Analysis dominates: ~13-37 sec per page (Nanonets inference)
- Page complexity varies: Simple pages (cover, TOC) are faster than dense content pages
- Model is already loaded (3-5 sec one-time cost)

---

## Full Document Processing Breakdown

### Configuration

**Aggressive Profile Settings**:
```python
render_batch_size = 50      # Pages per processing cycle
max_analysis_workers = 6    # Images per Nanonets batch call
```

**Processing Flow**:
```
893 pages → 18 batches of 50 pages (last batch = 43 pages)

Each 50-page batch:
├── Render 50 pages sequentially (PyMuPDF)
└── Analyze in sub-batches of 6 (Nanonets batch API)
    ├── Batch 1: 6 images
    ├── Batch 2: 6 images
    ├── ...
    └── Batch 9: 2 images (remainder)
```

### Time Calculation

#### Per 50-Page Batch

**1. Rendering Phase** (Sequential):
- 50 pages × 0.5-1.0 sec/page = **25-50 seconds**

**2. Analysis Phase** (Batch inference):
- 50 pages ÷ 6 images/batch = 9 Nanonets batch calls
- Per Nanonets batch: 27-74 seconds (empirical average: ~51 sec)
- Total: 9 × 51 sec = **459 seconds** (7.7 minutes)
- Range: 9 × (27-74) = 243-666 seconds = **4-11 minutes**

**Total per 50-page batch**: 25-50 sec + 4-11 min = **4.5-12 minutes**

#### Full Document (893 Pages)

**Number of batches**: 893 ÷ 50 = 17.86 ≈ **18 batches**

**Processing time**:
- Best case: 18 × 4.5 min = 81 minutes (**1.4 hours**)
- Typical: 18 × 7.5 min = 135 minutes (**2.25 hours**)
- Worst case: 18 × 12 min = 216 minutes (**3.6 hours**)

**One-time overhead**:
- Model loading: 3-5 minutes (first batch only)

**Total Estimate**:
- Best case: 81 + 5 = **86 minutes** (1.4 hours)
- Typical: 135 + 5 = **140 minutes** (2.3 hours)
- Worst case: 216 + 5 = **221 minutes** (3.7 hours)

---

## Factors Affecting Processing Time

### Speed Variations

**Faster pages** (13-20 sec/page):
- Cover pages, blank pages
- Simple layouts (single column text)
- Few or no complex structures

**Slower pages** (30-40 sec/page):
- Dense multi-column layouts
- Tables with many rows/columns
- Equations and complex formatting
- Images requiring descriptions

**Typical textbook pages**: 20-30 sec/page

### Bottleneck Analysis

| Phase | Time | % of Total | Parallelizable? |
|-------|------|------------|-----------------|
| **PDF Rendering** | ~0.5-1 sec/page | 5-10% | No (PyMuPDF not thread-safe) |
| **Nanonets OCR** | ~13-37 sec/page | 90-95% | Via batching (6 images) |
| **Region Parsing** | <0.1 sec/page | <1% | N/A (fast) |
| **Checkpointing** | ~0.1 sec/batch | <1% | N/A (minimal) |

**Primary bottleneck**: Nanonets OCR inference (GPU-bound, MPS backend)

---

## Performance Improvements vs Previous

### Before Batch Inference

**Sequential processing**:
- 893 model calls (one per page)
- No batching overhead reduction
- Estimated: **30-90 minutes** (but with deadlocks = ∞)

**Issues**:
- Frequent deadlocks (unusable)
- Semaphore leaks
- No semantic regions

### After Batch Inference ✅

**Batch processing**:
- ~149 batch calls (6 pages per batch) for analysis
- Batch overhead reduction
- Estimated: **1.5-3.7 hours**

**Benefits**:
- No deadlocks (thread-safe)
- No semaphore leaks
- Full semantic region extraction
- Structure-preserving chunking

**Net result**: Actually works! (vs. infinite time before)

---

## Real-Time Progress Estimate

For user monitoring during processing:

| Milestone | Pages Processed | Time Elapsed | % Complete |
|-----------|-----------------|--------------|------------|
| Batch 1 complete | 50 | 5-12 min | 5.6% |
| Batch 5 complete | 250 | 22-60 min | 28% |
| Batch 10 complete | 500 | 45-120 min | 56% |
| Batch 15 complete | 750 | 67-180 min | 84% |
| **Final batch complete** | **893** | **86-221 min** | **100%** |

**Average pace**: ~6-12 pages per minute

---

## Optimization Opportunities

### Potential Improvements

1. **Larger Batch Sizes** (Current: 6 images/batch)
   - Test batch_size=8 or 10 for better GPU utilization
   - Potential speedup: 10-20%
   - Risk: Memory pressure on complex pages

2. **Parallel Rendering** (Current: Sequential)
   - Use ProcessPoolExecutor to render in parallel
   - Potential speedup: 5-10% (rendering is only 5-10% of time)
   - Complexity: Moderate (process coordination)

3. **Page Complexity Detection**
   - Skip OCR for blank/simple pages
   - Potential speedup: 5-15% (depends on document)
   - Complexity: Low

4. **GPU Optimization**
   - Optimize MPS backend settings
   - Batch size tuning based on available VRAM
   - Potential speedup: 15-25%
   - Complexity: High (requires experimentation)

### Best Quick Win

**Increase Nanonets batch_size from 6 to 8**:
```python
# In profiles.py aggressive profile
max_analysis_workers = 8  # Was 6
```

Expected improvement:
- 893 pages ÷ 8 = 112 batches (vs. 149 batches at 6)
- Estimated time: **1.2-3.0 hours** (20% faster)

---

## Comparison with Alternatives

### Cloud OCR Services

**Google Cloud Vision API**:
- Speed: ~1-3 sec/page (parallel, cloud resources)
- Cost: ~$1.50 per 1000 pages = **$1.34 for 893 pages**
- Limitations: Data privacy, internet required

**AWS Textract**:
- Speed: ~2-5 sec/page
- Cost: ~$1.50 per 1000 pages
- Same limitations

### Local Alternatives

**Tesseract OCR** (CPU-based):
- Speed: ~5-10 sec/page (no table/equation extraction)
- Quality: Lower than Nanonets
- Time: 74-149 minutes (1.2-2.5 hours)

**Nanonets (our implementation)**:
- Speed: ~13-37 sec/page (full semantic extraction)
- Quality: Best (tables, equations, structure)
- Time: 86-221 minutes (1.4-3.7 hours)
- Cost: $0 (local processing)

---

## Recommendations

### For This Document (893 pages)

**Best approach**:
1. Use aggressive profile (already configured)
2. Enable checkpoints: `enable_checkpoints=True`
3. Start processing overnight or during lunch
4. Expected completion: **2-3 hours** (typical)

**Command**:
```python
from jina_rag_pipeline.ingestion import NanonetsFirstLoader

loader = NanonetsFirstLoader(
    batch_size=50,  # Aggressive profile default
    enable_checkpoints=True,  # Resume on crash
)

document = loader.load(
    file_path="Teach Like a Champion 3 edited.pdf",
    collection_name="tlac3",
    resume=True  # Continue from checkpoint if interrupted
)
```

**Monitoring**: Watch logs for progress updates every batch

### For Future Large Documents

**< 100 pages**: Direct processing (~10-30 min)
**100-500 pages**: Enable checkpoints (~30-120 min)
**500-1000 pages**: Enable checkpoints, consider overnight (~1-3 hours)
**> 1000 pages**: Enable checkpoints, run overnight (~3+ hours)

---

## Summary

**For 893-page "Teach Like a Champion 3"**:

| Metric | Value |
|--------|-------|
| **Estimated Time** | 1.5 - 3.7 hours |
| **Typical Time** | ~2.5 hours |
| **Pages per Hour** | 240-600 pages/hour |
| **Semantic Regions** | ~3,000-8,000 expected |
| **Final Chunks** | ~500-1,500 (depends on settings) |
| **Thread Safety** | ✅ No deadlocks |
| **Resumable** | ✅ With checkpoints |
| **Cost** | $0 (local processing) |

**Bottom Line**: Plan for **2-3 hours** of processing time with the current batch inference implementation. The enhancement makes it actually feasible (vs. infinite deadlock time before), with full semantic structure extraction for high-quality chunking.
