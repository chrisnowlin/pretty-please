# OCR Backends Guide

This document explains how to use and switch between the DeepseekOCR and PaddleOCR backends for document processing.

## Overview

The project now supports two modern OCR backends that replace the legacy Nanonets implementation:

1. **DeepseekOCR** - High-quality OCR with multiple resolution modes and advanced features
2. **PaddleOCR-VL** - Fast and efficient OCR with vision-language model capabilities

Both backends can be used interchangeably through the `UnifiedOCRLoader` interface.

## Quick Start

### Using Environment Variables (Recommended)

```bash
# Set the backend via environment variable
export OCR_BACKEND=deepseek  # or 'paddleocr'

# Then use in Python
from src.jina_rag_pipeline.ingestion import create_ocr_loader

loader = create_ocr_loader()
document = loader.load(file_path)
```

### Direct Backend Selection

```python
from src.jina_rag_pipeline.ingestion import UnifiedOCRLoader, OCRConfig

# Using DeepseekOCR
deepseek_loader = UnifiedOCRLoader(backend='deepseek')

# Using PaddleOCR
paddle_loader = UnifiedOCRLoader(backend='paddleocr')

# With custom configuration
loader = UnifiedOCRLoader(
    backend='deepseek',
    config=OCRConfig.deepseek_gundam()  # High-quality mode
)
```

## Backend Comparison

### DeepseekOCR

**Strengths:**
- Multiple resolution modes (tiny, small, base, large, gundam)
- Advanced grounding and compression features
- Excellent for complex documents with tables and equations
- Configurable quality vs. speed trade-offs

**Configuration Options:**
```python
from src.jina_rag_pipeline.ingestion import OCRConfig

# Quality presets
config_fast = OCRConfig.deepseek_tiny()      # Fastest, lowest quality
config_small = OCRConfig.deepseek_small()    # Fast, good quality
config_balanced = OCRConfig.deepseek_balanced()  # Default, balanced
config_large = OCRConfig.deepseek_large()    # Slower, high quality
config_best = OCRConfig.deepseek_gundam()    # Slowest, best quality
```

### PaddleOCR-VL

**Strengths:**
- Fast inference speed
- Efficient memory usage
- Good for standard documents
- Supports both local and server-based processing

**Configuration Options:**
```python
from src.jina_rag_pipeline.ingestion import OCRConfig

# Standard configuration
config = OCRConfig.balanced()  # Recommended for PaddleOCR

# Memory-constrained environments
config = OCRConfig.memory_constrained()
```

### PaddleOCR Optimization Profiles

```python
from src.jina_rag_pipeline.ingestion import create_ocr_loader

# Default (balanced) profile keeps layout detection enabled
paddle_balanced = create_ocr_loader(backend='paddleocr')

# Fast profile cuts runtime on CPU-only hosts (~40% faster, text-only regions)
paddle_fast = create_ocr_loader(
    backend='paddleocr',
    analyzer_kwargs={'optimization_level': 'fast'}
)
```

- `optimization_level="balanced"` (default): full layout detection, best recall (≈10 min / 10 GB on the 2-page sample).
- `optimization_level="fast"`: disables layout detection, lowers render scale, enables MKL-DNN hints (≈5.5 min / 9 GB on the same sample).
- Analyzer kwargs can also be supplied via `PADDLE_ANALYZER_KWARGS='{"optimization_level": "fast"}'` or the shorthand `PADDLE_OPT_LEVEL=fast` when running `ocr_comparison_test.py`.

## Side-by-Side Testing

To compare both OCR backends on the same document:

```python
from src.jina_rag_pipeline.ingestion import create_ocr_loader
from pathlib import Path
import time

test_file = Path("test_document.pdf")

# Test DeepseekOCR
start = time.time()
deepseek_loader = create_ocr_loader(backend='deepseek')
deepseek_doc = deepseek_loader.load(test_file)
deepseek_time = time.time() - start
print(f"DeepseekOCR: {deepseek_time:.2f}s")

# Test PaddleOCR
start = time.time()
paddle_loader = create_ocr_loader(backend='paddleocr')
paddle_doc = paddle_loader.load(test_file)
paddle_time = time.time() - start
print(f"PaddleOCR: {paddle_time:.2f}s")

# Compare results
print(f"\nDeepseek extracted: {len(deepseek_doc.content)} characters")
print(f"PaddleOCR extracted: {len(paddle_doc.content)} characters")
```

## Advanced Configuration

### Custom OCR Configuration

```python
from src.jina_rag_pipeline.ingestion import UnifiedOCRLoader, OCRConfig

# Create custom config
config = OCRConfig(
    batch_size=50,
    render_workers=10,
    analysis_workers=4,
    checkpoint_enabled=True
)

# Use with either backend
loader = UnifiedOCRLoader(
    backend='deepseek',  # or 'paddleocr'
    config=config
)
```

### Backend-Specific Features

#### DeepseekOCR Specific
```python
from src.jina_rag_pipeline.ingestion import DeepseekLoader, OCRConfig

# Direct usage with Deepseek-specific config
config = OCRConfig.deepseek_balanced()
config.enable_grounding = True  # Enable grounding features
config.enable_compression = True  # Enable compression
config.resolution_mode = "large"  # Set resolution

loader = DeepseekLoader(config=config)
```

#### PaddleOCR Specific
```python
from src.jina_rag_pipeline.ingestion import PaddleOCRVLAnalyzer

# Direct analyzer usage
analyzer = PaddleOCRVLAnalyzer()

# Can be used with OCRLoader
from src.jina_rag_pipeline.ingestion import OCRLoader
loader = OCRLoader(analyzer=analyzer)
```

## Performance Considerations

### DeepseekOCR
- Use `deepseek_tiny()` for speed-critical applications
- Use `deepseek_gundam()` for highest quality requirements
- Default `deepseek_balanced()` works well for most cases

### PaddleOCR
- Balanced profile preserves layout fidelity (≈10 min / 10 GB per 2-page sample)
- Fast profile disables layout detection to save ~40% runtime (≈5.5 min / 9 GB)
- Both profiles remain CPU-only; consider a dedicated inference server for sustained throughput

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```python
   # If you get import errors, ensure dependencies are installed
   pip install torch transformers pillow  # For DeepseekOCR
   pip install paddlepaddle paddlex  # For PaddleOCR
   ```

2. **Backend Not Found**
   ```python
   # Check available backends
   from src.jina_rag_pipeline.ingestion import UnifiedOCRLoader

   try:
       loader = UnifiedOCRLoader(backend='deepseek')
       print("DeepseekOCR available")
   except:
       print("DeepseekOCR not available")

   try:
       loader = UnifiedOCRLoader(backend='paddleocr')
       print("PaddleOCR available")
   except:
       print("PaddleOCR not available")
   ```

3. **Memory Issues**
   ```python
   # Use memory-constrained configuration
   from src.jina_rag_pipeline.ingestion import OCRConfig

   config = OCRConfig.memory_constrained()
   loader = create_ocr_loader(config=config)
   ```

## Migration from Nanonets

If you have existing code using Nanonets, update it as follows:

```python
# Old (Nanonets)
from src.jina_rag_pipeline.ingestion import NanonetsFirstLoader
loader = NanonetsFirstLoader()

# New (Unified)
from src.jina_rag_pipeline.ingestion import create_ocr_loader
loader = create_ocr_loader()  # Uses default backend (deepseek)
```

## Testing Script

A test script is provided to verify both backends are working:

```bash
python test_ocr_backends.py
```

This will test:
- Direct initialization of both backends
- UnifiedOCRLoader with both backends
- Environment variable configuration
- Backend switching

## Recommendations

- **For general use**: Start with DeepseekOCR (default) using `deepseek_balanced()` config
- **For speed**: Use PaddleOCR or DeepseekOCR with `deepseek_tiny()` config
- **For quality**: Use DeepseekOCR with `deepseek_gundam()` config
- **For production**: Test both backends with your specific documents and choose based on your requirements

## Environment Variables

- `OCR_BACKEND`: Set to 'deepseek' or 'paddleocr' to select default backend
- `OCR_SERVER_URL`: (PaddleOCR only) URL of PaddleOCR server if using server mode

## Next Steps

1. Test both backends with your document types
2. Measure performance and quality metrics
3. Choose the appropriate backend for your use case
4. Configure optimization settings as needed

For more details on specific configurations, see:
- DeepseekOCR: `docs/guides/deepseek-ocr-configuration.md`
- PaddleOCR: `PADDLEOCR_DEBUG_FINDINGS.md`
