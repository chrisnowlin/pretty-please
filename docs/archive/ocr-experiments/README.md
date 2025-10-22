# OCR Experimentation Archive

This directory contains experimental code, benchmarks, and research from the OCR optimization work (2025-10).

## What's Here

### PaddleOCR Hybrid Experiments
Explored using PaddleOCR for fast initial pass + Nanonets for complex documents.
**Result**: Abandoned due to PaddleOCR crashes on music notation.
**Files**: `HYBRID_OCR_*.md`, `test_paddle_*.py`, `test_hybrid_ocr.py`

### Nanonets Two-Tier System (Final Choice)
Research and implementation of FAST + BALANCED preset approach.
**Result**: Implemented as production solution in `src/jina_rag_pipeline/ingestion/nanonets_hybrid.py`
**Files**: `NANONETS_MODEL_ANALYSIS.md`, `OCR_STRATEGY_OPTIONS.md`, `NANONETS_TWO_TIER_SYSTEM.md`

### MLX Optimization Research
Apple Silicon Metal optimizations, threading issues, quantization experiments.
**Files**: `MLX_*.md`, `benchmark_mlx_*.py`, `test_mlx_*.py`

### MPS Optimization Research
PyTorch MPS backend optimizations, quality presets, resolution tuning.
**Files**: `MPS_*.md`, `test_mps_*.py`

### Benchmark Results
Performance measurements across different configurations.
**Files**: `*_benchmark_results.json`, `BENCHMARK_FINDINGS.md`

## Production Code

The final production implementation is:
- **`src/jina_rag_pipeline/ingestion/nanonets_hybrid.py`** - Nanonets two-tier system
- **`docs/NANONETS_TWO_TIER_SYSTEM.md`** - Production documentation

## Key Findings

1. **PaddleOCR Hybrid**: Fast but unstable (crashes on complex documents)
2. **Nanonets Two-Tier**: Stable, 2x faster than BALANCED-only
3. **FAST Preset**: ~177 seconds/page (not much faster than BALANCED ~199s for complex docs)
4. **Decision**: Use Nanonets two-tier for stability, accept moderate speed improvement

## Date
2025-10-20
