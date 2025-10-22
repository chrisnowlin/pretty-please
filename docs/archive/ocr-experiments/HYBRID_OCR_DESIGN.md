# Hybrid OCR Approach Design

## Overview

This document outlines the design for a hybrid OCR system that combines:
1. **Fast traditional OCR** (PP-OCRv5, PaddleOCR) for simple text extraction
2. **VLM refinement** (Nanonets-OCR2-3B) for complex documents

**Expected Performance:** 5-10x faster than VLM-only approach while maintaining quality.

## Architecture

```
┌─────────────────┐
│  Input Document │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  Phase 1: Fast OCR Pass     │
│  (PP-OCRv5 / PaddleOCR)     │
│  • 1-3 sec/page             │
│  • Text + layout detection  │
│  • Confidence scores        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Complexity Analysis        │
│  • Check confidence scores  │
│  • Detect tables/equations  │
│  • Assess layout complexity │
└────────┬────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────────┐
│ Simple  │ │ Complex          │
│ (80%)   │ │ (20%)            │
└────┬────┘ └────┬─────────────┘
     │           │
     │           ▼
     │      ┌─────────────────────────┐
     │      │ Phase 2: VLM Refinement │
     │      │ (Nanonets-OCR2-3B)      │
     │      │ • Quality preset        │
     │      │ • Full semantic extract │
     │      └────┬────────────────────┘
     │           │
     ▼           ▼
┌─────────────────────────────┐
│  Merged Results             │
│  • Semantic regions         │
│  • Structured markdown      │
└─────────────────────────────┘
```

## Components

### 1. Fast OCR Engine (Phase 1)

**Technology:** PaddleOCR with PP-OCRv5

**Installation:**
```bash
pip install paddleocr paddlepaddle
```

**Performance:**
- Speed: 1-3 sec/page
- Accuracy: 90-95% for clean text
- Output: Text + bounding boxes + confidence

**Limitations:**
- No semantic understanding
- Limited table structure extraction
- No equation recognition
- May miss complex layouts

### 2. Complexity Analyzer

Determines if document needs VLM refinement based on:

```python
class ComplexityAnalyzer:
    """Analyze document complexity to route to appropriate processor."""

    def __init__(
        self,
        confidence_threshold=0.85,
        table_detection_threshold=3,
        equation_detection_patterns=[r'\$', r'\\frac', r'\\sum'],
    ):
        self.confidence_threshold = confidence_threshold
        self.table_threshold = table_detection_threshold
        self.equation_patterns = equation_detection_patterns

    def is_complex(self, ocr_result) -> bool:
        """Determine if document requires VLM refinement."""
        # Low confidence in OCR
        avg_confidence = self._calculate_confidence(ocr_result)
        if avg_confidence < self.confidence_threshold:
            return True

        # Contains tables
        if self._detect_tables(ocr_result) >= self.table_threshold:
            return True

        # Contains equations
        if self._detect_equations(ocr_result):
            return True

        # Complex layout (multiple columns, overlapping text)
        if self._detect_complex_layout(ocr_result):
            return True

        return False

    def _calculate_confidence(self, ocr_result):
        """Calculate average confidence from OCR results."""
        confidences = [item['confidence'] for item in ocr_result]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _detect_tables(self, ocr_result):
        """Count table-like structures in OCR output."""
        # Look for aligned rows/columns
        # Check for grid patterns
        # Count cells
        pass

    def _detect_equations(self, ocr_result):
        """Detect mathematical equations."""
        text = ' '.join(item['text'] for item in ocr_result)
        return any(re.search(pattern, text) for pattern in self.equation_patterns)

    def _detect_complex_layout(self, ocr_result):
        """Detect complex document layouts."""
        # Check for multiple columns
        # Detect overlapping bounding boxes
        # Identify non-standard reading order
        pass
```

### 3. VLM Refiner (Phase 2)

**Technology:** Nanonets-OCR2-3B with MPS optimizations

**Quality Preset Selection:**
```python
def select_vlm_preset(complexity_score):
    """Choose appropriate VLM quality based on complexity."""
    if complexity_score < 0.3:
        return "fast"      # Minor issues
    elif complexity_score < 0.7:
        return "balanced"  # Moderate complexity
    else:
        return "high"      # Highly complex
```

### 4. Result Merger

Combines fast OCR and VLM results:

```python
class ResultMerger:
    """Merge results from fast OCR and VLM refinement."""

    def merge(self, fast_result, vlm_result=None):
        """Merge OCR results intelligently."""
        if vlm_result is None:
            # Simple document - convert fast OCR to semantic regions
            return self._convert_fast_ocr(fast_result)
        else:
            # Complex document - use VLM result with fast OCR metadata
            return self._enhance_vlm_with_metadata(vlm_result, fast_result)
```

## Implementation

### Phase 1: Core Hybrid System

```python
"""
Hybrid OCR analyzer combining fast OCR and VLM refinement.
"""

from paddleocr import PaddleOCR
from src.jina_rag_pipeline.ingestion.nanonets_layout import NanonetsLayoutAnalyzer

class HybridOCRAnalyzer:
    """
    Hybrid analyzer using fast OCR + selective VLM refinement.

    Provides 5-10x speedup vs VLM-only while maintaining quality.
    """

    def __init__(
        self,
        use_fast_ocr=True,
        complexity_threshold=0.85,
        vlm_quality_preset="balanced"
    ):
        # Fast OCR engine (CPU-based, very fast)
        self.fast_ocr = PaddleOCR(
            use_angle_cls=True,
            lang='en',
            use_gpu=False  # CPU is fast enough
        ) if use_fast_ocr else None

        # VLM for complex documents
        self.vlm_analyzer = NanonetsLayoutAnalyzer(
            device="mps",
            quality_preset=vlm_quality_preset
        )

        # Complexity analyzer
        self.complexity_analyzer = ComplexityAnalyzer(
            confidence_threshold=complexity_threshold
        )

    def analyze_document(self, file_path, page_number=1):
        """
        Analyze document with hybrid approach.

        Returns:
            SemanticRegion list
        """
        # Phase 1: Fast OCR
        if self.fast_ocr:
            ocr_result = self.fast_ocr.ocr(str(file_path))

            # Analyze complexity
            is_complex = self.complexity_analyzer.is_complex(ocr_result)

            if not is_complex:
                # Simple document - use fast OCR only
                logger.info(f"Simple document detected - using fast OCR only")
                return self._convert_fast_ocr_to_regions(ocr_result, page_number)

        # Phase 2: VLM refinement for complex documents
        logger.info(f"Complex document detected - using VLM refinement")
        return self.vlm_analyzer.extract_regions(file_path, page_number)

    def analyze_documents_batch(self, file_paths, page_numbers=None):
        """
        Batch analyze with hybrid approach.

        Strategy:
        1. Fast OCR all documents (parallel)
        2. Filter complex documents
        3. VLM refinement in batch (only complex ones)
        4. Merge results
        """
        if page_numbers is None:
            page_numbers = [1] * len(file_paths)

        # Phase 1: Fast OCR for all
        fast_results = []
        complex_indices = []

        for i, file_path in enumerate(file_paths):
            ocr_result = self.fast_ocr.ocr(str(file_path))
            fast_results.append(ocr_result)

            if self.complexity_analyzer.is_complex(ocr_result):
                complex_indices.append(i)

        logger.info(
            f"Complexity analysis: {len(complex_indices)}/{len(file_paths)} "
            f"documents need VLM refinement"
        )

        # Phase 2: VLM refinement for complex documents only
        all_regions = [None] * len(file_paths)

        if complex_indices:
            complex_paths = [file_paths[i] for i in complex_indices]
            complex_page_nums = [page_numbers[i] for i in complex_indices]

            vlm_results = self.vlm_analyzer.extract_regions_batch(
                complex_paths,
                page_numbers=complex_page_nums
            )

            # Place VLM results
            for idx, regions in zip(complex_indices, vlm_results):
                all_regions[idx] = regions

        # Convert simple documents
        for i, (file_path, page_num, ocr_result) in enumerate(
            zip(file_paths, page_numbers, fast_results)
        ):
            if all_regions[i] is None:
                all_regions[i] = self._convert_fast_ocr_to_regions(
                    ocr_result, page_num
                )

        return all_regions

    def _convert_fast_ocr_to_regions(self, ocr_result, page_number):
        """Convert PaddleOCR output to SemanticRegion list."""
        # Simple conversion: group by lines, create text regions
        regions = []
        for i, line in enumerate(ocr_result):
            bbox, (text, confidence) = line
            region = SemanticRegion(
                region_id=f"fast_ocr_{page_number}_{i}",
                region_type="text",
                region_sequence=i,
                page_number=page_number,
                content=text,
                raw_markdown=text,
                # Could add bounding box info here
            )
            regions.append(region)
        return regions
```

### Phase 2: Adaptive Quality Selection

```python
class AdaptiveHybridAnalyzer(HybridOCRAnalyzer):
    """Hybrid analyzer with adaptive quality selection."""

    def analyze_document(self, file_path, page_number=1):
        """Analyze with adaptive quality based on complexity score."""
        # Fast OCR
        ocr_result = self.fast_ocr.ocr(str(file_path))

        # Calculate complexity score (0-1)
        complexity_score = self.complexity_analyzer.calculate_score(ocr_result)

        if complexity_score < 0.2:
            # Very simple - fast OCR only
            return self._convert_fast_ocr_to_regions(ocr_result, page_number)

        # Complex - choose VLM quality
        quality_preset = self._select_quality(complexity_score)

        # Reinitialize analyzer with appropriate quality
        self.vlm_analyzer = NanonetsLayoutAnalyzer(
            device="mps",
            quality_preset=quality_preset
        )

        return self.vlm_analyzer.extract_regions(file_path, page_number)

    def _select_quality(self, complexity_score):
        """Select VLM quality based on complexity."""
        if complexity_score < 0.4:
            return "fast"
        elif complexity_score < 0.7:
            return "balanced"
        else:
            return "high"
```

## Performance Projections

### Current Baseline (VLM only)

- 96 pages with FAST preset: ~3-4 hours
- 96 pages with BALANCED preset: ~4-5 hours

### With Hybrid Approach

Assuming 80% simple, 20% complex documents:

```
Simple pages (80% × 96 = 77 pages):
  77 pages × 2 sec = 154 sec = 2.6 min

Complex pages (20% × 96 = 19 pages):
  19 pages × 180 sec (BALANCED) = 3420 sec = 57 min

Total: 2.6 + 57 = ~60 minutes

Speedup: 4-5 hours → 1 hour = 4-5x faster
```

### Best Case (90% simple)

```
Simple: 86 pages × 2 sec = 172 sec = 2.9 min
Complex: 10 pages × 180 sec = 1800 sec = 30 min

Total: ~33 minutes
Speedup: 4-5 hours → 33 min = 7-9x faster
```

## Testing Strategy

### 1. Benchmark Fast OCR

```bash
python benchmark_fast_ocr.py --input tests/fixtures/classroom_music_5pages.pdf
```

### 2. Measure Complexity Distribution

```python
# Analyze your document set
analyzer = HybridOCRAnalyzer()
total = 0
complex = 0

for doc in document_set:
    result = analyzer.fast_ocr.ocr(doc)
    if analyzer.complexity_analyzer.is_complex(result):
        complex += 1
    total += 1

print(f"Complexity: {complex/total*100:.1f}% complex documents")
```

### 3. Compare Quality

```python
# Compare outputs
vlm_only_result = vlm_analyzer.analyze_document("test.png")
hybrid_result = hybrid_analyzer.analyze_document("test.png")

# Manual review or automated similarity check
```

## Implementation Roadmap

1. **Week 1: Core Implementation**
   - Integrate PaddleOCR
   - Build ComplexityAnalyzer
   - Create HybridOCRAnalyzer
   - Basic testing

2. **Week 2: Optimization**
   - Tune complexity thresholds
   - Optimize batch processing
   - Add adaptive quality selection
   - Performance benchmarking

3. **Week 3: Integration**
   - Update NanonetsLoader to use hybrid
   - Add configuration options
   - Update documentation
   - E2E testing

4. **Week 4: Deployment**
   - A/B testing vs VLM-only
   - Monitor quality metrics
   - Tune based on production data
   - Full rollout

## Configuration

Add to `OCRConfig`:

```python
@dataclass
class OCRConfig:
    # Existing fields...

    # Hybrid OCR settings
    use_hybrid_ocr: bool = True
    fast_ocr_confidence_threshold: float = 0.85
    vlm_fallback_quality: str = "balanced"
```

## Next Steps

1. Install PaddleOCR: `pip install paddleocr paddlepaddle`
2. Create `hybrid_ocr_analyzer.py` with implementation
3. Test on sample documents
4. Benchmark performance
5. Integrate with existing pipeline

## Expected Benefits

- **5-10x speedup** for typical document mix
- **Maintained quality** for complex documents
- **Lower compute costs** (fewer VLM calls)
- **Faster previews** (fast OCR for quick checks)
- **Scalable** to large document sets

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Fast OCR misses complex pages | Tune complexity thresholds conservatively |
| Quality degradation | A/B testing, quality monitoring |
| Integration complexity | Gradual rollout, feature flags |
| CPU bottleneck | Parallelize fast OCR across pages |

## References

- PP-OCRv5: https://github.com/PaddlePaddle/PaddleOCR
- Research findings: Web search agent results
- MPS optimizations: `MPS_OPTIMIZATION_GUIDE.md`
