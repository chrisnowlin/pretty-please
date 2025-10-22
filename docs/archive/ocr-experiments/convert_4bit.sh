#!/bin/bash
#
# Convert Nanonets OCR model to 4-bit quantization
#
# This script converts the Nanonets model from 8-bit to 4-bit quantization
# to achieve ~2x faster inference with minimal quality loss.
#

set -e  # Exit on error

echo "=========================================="
echo "4-BIT MODEL CONVERSION"
echo "=========================================="
echo ""

# Configuration
MODEL_NAME="nanonets/nanonets-ocr2-3b"
OUTPUT_DIR="./models/nanonets-ocr2-3b-mlx-4bit"
LOG_FILE="4bit_conversion.log"

echo "Source model: ${MODEL_NAME}"
echo "Output directory: ${OUTPUT_DIR}"
echo "Log file: ${LOG_FILE}"
echo ""

# Check if output directory exists
if [ -d "${OUTPUT_DIR}" ]; then
    echo "⚠️  Output directory already exists: ${OUTPUT_DIR}"
    read -p "Delete and recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing directory..."
        rm -rf "${OUTPUT_DIR}"
    else
        echo "Aborting conversion."
        exit 1
    fi
fi

echo ""
echo "Starting 4-bit conversion..."
echo "This will:"
echo "  1. Download model from HuggingFace (~14 GB)"
echo "  2. Convert to MLX format"
echo "  3. Apply 4-bit quantization"
echo "  4. Save to ${OUTPUT_DIR} (~1.6 GB)"
echo ""
echo "Estimated time: 10-15 minutes"
echo ""

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Run conversion
echo "Running mlx_vlm.convert..."
.venv/bin/python -m mlx_vlm convert \
    --hf-path "${MODEL_NAME}" \
    --mlx-path "${OUTPUT_DIR}" \
    -q \
    --q-bits 4 \
    2>&1 | tee "${LOG_FILE}"

# Check if conversion succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 4-BIT CONVERSION COMPLETE"
    echo "=========================================="
    echo ""

    # Show directory size
    if command -v du &> /dev/null; then
        SIZE=$(du -sh "${OUTPUT_DIR}" | cut -f1)
        echo "Model size: ${SIZE}"
    fi

    # Count files
    FILE_COUNT=$(find "${OUTPUT_DIR}" -type f | wc -l)
    echo "Files created: ${FILE_COUNT}"
    echo ""

    echo "Next steps:"
    echo "  1. Test 4-bit model: ./test_4bit_quality.py"
    echo "  2. Benchmark speed: ./benchmark_4bit_vs_8bit.py"
    echo "  3. Compare quality: ./compare_quality.py"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ CONVERSION FAILED"
    echo "=========================================="
    echo ""
    echo "Check ${LOG_FILE} for details"
    exit 1
fi
