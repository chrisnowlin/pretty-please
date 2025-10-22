#!/bin/bash
#
# Clean up experimental files from OCR optimization work
# Moves experimental code to docs/archive/ocr-experiments/
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}OCR Experimentation Cleanup${NC}"
echo -e "${BLUE}========================================${NC}"

# Create archive directory
ARCHIVE_DIR="docs/archive/ocr-experiments"
mkdir -p "$ARCHIVE_DIR"
echo -e "${GREEN}✓${NC} Created archive directory: $ARCHIVE_DIR"

# Files to KEEP (production-ready)
echo -e "\n${BLUE}Production files (keeping in root):${NC}"
echo "  - README.md"
echo "  - CLAUDE.md"
echo "  - Makefile"
echo "  - src/jina_rag_pipeline/ingestion/nanonets_hybrid.py (NEW)"

# Files to ARCHIVE (experimental/research)
echo -e "\n${YELLOW}Archiving experimental files...${NC}"

# PaddleOCR hybrid experiments (superseded by Nanonets two-tier)
mv HYBRID_OCR_DESIGN.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ HYBRID_OCR_DESIGN.md"
mv HYBRID_OCR_IMPLEMENTATION.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ HYBRID_OCR_IMPLEMENTATION.md"
mv HYBRID_OCR_SUMMARY.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ HYBRID_OCR_SUMMARY.md"
mv HYBRID_OCR_TEST_RESULTS.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ HYBRID_OCR_TEST_RESULTS.md"
mv test_hybrid_ocr.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_hybrid_ocr.py"
mv test_paddle_ocr_output.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_paddle_ocr_output.py"
mv test_paddle_quick.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_paddle_quick.py"

# Model research & benchmarking
mv NANONETS_MODEL_ANALYSIS.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ NANONETS_MODEL_ANALYSIS.md"
mv OCR_STRATEGY_OPTIONS.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ OCR_STRATEGY_OPTIONS.md"
mv test_nanonets_fast_preset.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_nanonets_fast_preset.py"
mv test_music_ncscos.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_music_ncscos.py"

# MLX optimization experiments
mv MLX_OPTIMIZATION_GUIDE.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ MLX_OPTIMIZATION_GUIDE.md"
mv MLX_KNOWN_ISSUES.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ MLX_KNOWN_ISSUES.md"
mv MPS_OPTIMIZATION_GUIDE.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ MPS_OPTIMIZATION_GUIDE.md"
mv MULTIPROCESS_MLX_FAILURE.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ MULTIPROCESS_MLX_FAILURE.md"
mv THREADING_FIX_SUMMARY.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ THREADING_FIX_SUMMARY.md"

# Benchmark scripts and results
mv benchmark_mlx_inference.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ benchmark_mlx_inference.py"
mv benchmark_mlx_workers.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ benchmark_mlx_workers.py"
mv benchmark_4bit_vs_8bit.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ benchmark_4bit_vs_8bit.py"
mv mlx_benchmark_results.json "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ mlx_benchmark_results.json"
mv 4bit_8bit_benchmark_results.json "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ 4bit_8bit_benchmark_results.json"
mv BENCHMARK_FINDINGS.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ BENCHMARK_FINDINGS.md"

# Test scripts (various experiments)
mv test_mlx_inference.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_mlx_inference.py"
mv test_nanonets_mlx.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_nanonets_mlx.py"
mv test_single_page_mlx.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_single_page_mlx.py"
mv test_mps_optimizations.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_mps_optimizations.py"
mv test_mps_quality.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_mps_quality.py"
mv test_large_doc.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_large_doc.py"
mv test_enhancement_e2e.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_enhancement_e2e.py"
mv test_enhancement_quick.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_enhancement_quick.py"
mv test_fixed.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_fixed.py"
mv test_simple.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_simple.py"
mv test_integration.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ test_integration.py"

# Processing scripts (experimental)
mv process_mlx_turbo.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ process_mlx_turbo.py"
mv process_multiprocess_mlx.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ process_multiprocess_mlx.py"
mv process_full_document.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ process_full_document.py"
mv process_sequential_checkpoint.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ process_sequential_checkpoint.py"
mv profile_sequential.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ profile_sequential.py"

# Utility scripts
mv compare_backends.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ compare_backends.py"
mv compare_quality.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ compare_quality.py"
mv inspect_test_pdf.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ inspect_test_pdf.py"
mv monitor_progress.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ monitor_progress.py"
mv quick_test.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ quick_test.py"
mv search_database.py "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ search_database.py"

# Analysis documents (superseded)
mv 10_MINUTE_TARGET_ANALYSIS.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ 10_MINUTE_TARGET_ANALYSIS.md"
mv 4BIT_PROTOTYPE_GUIDE.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ 4BIT_PROTOTYPE_GUIDE.md"
mv 4BIT_QUANTIZATION_RESULTS.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ 4BIT_QUANTIZATION_RESULTS.md"
mv PROCESSING_TIME_ESTIMATE.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ PROCESSING_TIME_ESTIMATE.md"
mv DATABASE_PERSISTENCE.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ DATABASE_PERSISTENCE.md"
mv CODE_REVIEW_FINDINGS.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ CODE_REVIEW_FINDINGS.md"
mv TEST_RESULTS.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ TEST_RESULTS.md"

# Phase completion docs (from development)
mv PHASE_1_COMPLETE.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ PHASE_1_COMPLETE.md"
mv PHASE_2_EXPORT_COMPLETE.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ PHASE_2_EXPORT_COMPLETE.md"
mv PHASE_3_SIMPLE.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ PHASE_3_SIMPLE.md"
mv IMPLEMENTATION_COMPLETE.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ IMPLEMENTATION_COMPLETE.md"
mv IMPLEMENTATION_SUMMARY.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ IMPLEMENTATION_SUMMARY.md"
mv BATCH_INFERENCE_SUMMARY.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ BATCH_INFERENCE_SUMMARY.md"
mv QUICK_START.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ QUICK_START.md"

# AGENTS.md (not needed in root)
mv AGENTS.md "$ARCHIVE_DIR/" 2>/dev/null && echo "  ✓ AGENTS.md"

echo -e "\n${GREEN}✓${NC} Experimental files archived to: $ARCHIVE_DIR"

# Create archive README
cat > "$ARCHIVE_DIR/README.md" << 'EOF'
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
EOF

echo -e "${GREEN}✓${NC} Created archive README: $ARCHIVE_DIR/README.md"

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Cleanup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\n${GREEN}Production files remain in root:${NC}"
echo "  - README.md, CLAUDE.md, Makefile"
echo "  - src/jina_rag_pipeline/ingestion/nanonets_hybrid.py"
echo "  - test_nanonets_hybrid.py"
echo "  - NANONETS_TWO_TIER_SYSTEM.md"
echo ""
echo -e "${YELLOW}Experimental files archived to:${NC}"
echo "  - $ARCHIVE_DIR/"
echo ""
echo -e "${GREEN}✓${NC} Codebase is now in a clean, production-ready state"
