# OCR Configuration Guide

## Overview

This guide covers the streamlined OCR configuration system introduced in the OCR pipeline optimization. The new system uses `OCRConfig` presets and the simplified `NanonetsLoader` to provide smart defaults that work well for 80% of use cases while allowing customization when needed.

## Key Concepts

### OCRConfig

`OCRConfig` is a simple configuration dataclass with 5 core parameters that control OCR processing:

1. **batch_size**: Number of pages to process in each batch (impacts memory usage)
2. **render_workers**: Number of parallel workers for PDF/PPT rendering (impacts rendering speed)
3. **analysis_workers**: Number of parallel workers for OCR analysis (limited to 1 for MLX)
4. **pre_render_batches**: Number of batches to pre-render ahead of analysis (pipeline depth)
5. **checkpoint_enabled**: Whether to enable checkpoint/resume functionality

### NanonetsLoader

`NanonetsLoader` is a streamlined document loader that uses `OCRConfig` presets and automatically selects the best configuration based on your hardware.

## Quick Start

### Using Default Configuration

The simplest way to use the new system is to let it auto-detect the best configuration:

```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader

# Auto-selects mlx_optimized on Apple Silicon, balanced on other platforms
loader = NanonetsLoader()

# Load and process a document
documents = loader.load("path/to/document.pdf")
```

**What happens:**
- On Apple Silicon (M1/M2/M3/M4): Uses `OCRConfig.mlx_optimized()`
- On other platforms: Uses `OCRConfig.balanced()`
- Automatically configures optimal settings for your hardware

### Using Configuration Presets

For more control, you can explicitly choose a preset:

```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig

# MLX-optimized preset (recommended for Apple Silicon)
loader = NanonetsLoader(config=OCRConfig.mlx_optimized())

# Balanced preset (good for most systems)
loader = NanonetsLoader(config=OCRConfig.balanced())

# Memory-constrained preset (scales based on available RAM)
loader = NanonetsLoader(config=OCRConfig.memory_constrained())
```

### Custom Configuration

For advanced use cases, create a custom configuration:

```python
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader

# Custom configuration
config = OCRConfig(
    batch_size=25,           # Process 25 pages per batch
    render_workers=15,       # Use 15 workers for rendering
    analysis_workers=1,      # Single worker for MLX
    pre_render_batches=5,    # Pre-render 5 batches ahead
    checkpoint_enabled=True  # Enable checkpointing
)

loader = NanonetsLoader(config=config)
```

## Configuration Presets

### mlx_optimized()

**Best for:** Apple Silicon Macs (M1/M2/M3/M4) with 16GB+ RAM

**Settings:**
```python
OCRConfig(
    batch_size=30,              # Large batches for efficiency
    render_workers=auto,        # 80% of logical cores
    analysis_workers=1,         # MLX thread-safety constraint
    pre_render_batches=4,       # Deep pipeline for constant work
    checkpoint_enabled=True
)
```

**Performance:**
- 96-page document: ~60-75 minutes
- Memory usage: ~3GB (2.2GB model + inference)
- Optimized for MLX backend with 2.2GB quantized model

**When to use:**
- You have an Apple Silicon Mac
- You want optimal performance with low memory usage
- Processing large documents (50+ pages)

### balanced()

**Best for:** General-purpose processing on any platform

**Settings:**
```python
OCRConfig(
    batch_size=20,              # Moderate batch size
    render_workers=auto,        # 80% of logical cores
    analysis_workers=2,         # Parallel analysis (PyTorch)
    pre_render_batches=3,       # Balanced pipeline depth
    checkpoint_enabled=True
)
```

**Performance:**
- Good balance of speed and memory usage
- Works well on systems with 16GB+ RAM
- Suitable for medium documents (10-50 pages)

**When to use:**
- You're not on Apple Silicon
- You have 16GB+ RAM
- Processing medium-sized documents

### memory_constrained()

**Best for:** Systems with limited RAM or processing very large documents

**Settings (auto-scales based on available memory):**

**8GB or less:**
```python
OCRConfig(
    batch_size=8,               # Small batches
    render_workers=2-4,         # Minimal workers
    analysis_workers=1,         # Single worker
    pre_render_batches=2,       # Shallow pipeline
    checkpoint_enabled=True
)
```

**16GB:**
```python
OCRConfig(
    batch_size=10,
    render_workers=4-8,
    analysis_workers=1,
    pre_render_batches=3,
    checkpoint_enabled=True
)
```

**32GB+:**
```python
OCRConfig(
    batch_size=20,
    render_workers=auto,
    analysis_workers=2,
    pre_render_batches=3,
    checkpoint_enabled=True
)
```

**When to use:**
- You have 8-16GB RAM
- Processing very large documents (100+ pages)
- You're experiencing out-of-memory errors

## Configuration Parameters Explained

### batch_size

Controls how many pages are processed together in a single batch.

**Impact:**
- **Higher values (20-30)**: Faster processing, higher memory usage
- **Lower values (8-15)**: Slower processing, lower memory usage

**Memory calculation:**
```
Memory per batch = (batch_size × ~200MB per page) + model_memory
```

**Recommendations:**
- MLX (2.2GB model): 20-30 pages
- PyTorch (14GB model): 10-20 pages
- Low memory (<16GB): 8-10 pages

### render_workers

Number of parallel workers for rendering PDF/PowerPoint to images.

**Impact:**
- **Higher values (15-20)**: Faster rendering, higher CPU usage
- **Lower values (4-8)**: Slower rendering, lower CPU usage

**Recommendations:**
- Auto-detect: 80% of logical CPU cores (recommended)
- Manual override: Set based on CPU cores and workload

**Example:**
```python
# Auto-detect (recommended)
config = OCRConfig.mlx_optimized()  # Automatically sets to ~80% of cores

# Manual override
config = OCRConfig(render_workers=12)  # Force 12 workers
```

### analysis_workers

Number of parallel workers for OCR analysis.

**Impact:**
- **MLX backend**: MUST be 1 (thread-safety constraint)
- **PyTorch backend**: Can be 2-4 for parallelism

**Important:**
- The system automatically enforces `analysis_workers=1` for MLX
- Do not set higher than 1 for MLX (will be ignored)
- For PyTorch, values of 2-4 can improve throughput

**Recommendations:**
- MLX: Always 1
- PyTorch on GPU: 2-4
- PyTorch on CPU: 1-2

### pre_render_batches

Number of batches to pre-render ahead of OCR analysis (pipeline depth).

**Impact:**
- **Higher values (4-5)**: OCR never waits for rendering, higher memory
- **Lower values (2-3)**: OCR may wait for rendering, lower memory

**Memory calculation:**
```
Pipeline memory = pre_render_batches × batch_size × 200MB
```

**Recommendations:**
- MLX with 16GB+ RAM: 4-5 batches
- Balanced systems: 3 batches
- Memory constrained: 2 batches

**Example:**
```python
# Deep pipeline (recommended for MLX)
config = OCRConfig(pre_render_batches=4)

# Shallow pipeline (lower memory)
config = OCRConfig(pre_render_batches=2)
```

### checkpoint_enabled

Whether to save progress checkpoints for resume capability.

**Impact:**
- **True**: Can resume if interrupted, slight overhead
- **False**: No resume capability, slightly faster

**Recommendations:**
- Always `True` for large documents (50+ pages)
- Can be `False` for small documents (<10 pages)

## Performance Tuning

### Target Performance

Based on M4 Max benchmarks with mlx_optimized preset:

| Document Size | Processing Time | Pages/Second |
|--------------|-----------------|--------------|
| 10 pages | ~8-12 minutes | 0.8-1.25 |
| 50 pages | ~40-60 minutes | 0.8-1.25 |
| 96 pages | ~60-75 minutes | 1.2-1.6 |

### Optimization Strategy

The system uses **pipeline parallelism** to maximize throughput:

```
[Render Batch 1] → [Analyze Page 1] → [Store Results]
[Render Batch 2] ↘    ↓
[Render Batch 3]   [Analyze Page 2]
[Render Batch 4]       ↓
    ↓              [Analyze Page 3]
[Continue...]          ↓
                  [Continue...]
```

**Key principles:**
1. **Maximize rendering parallelism**: Use 80% of CPU cores
2. **Deep pipeline**: Pre-render multiple batches ahead
3. **Optimal batch size**: Balance memory and efficiency
4. **Single-worker MLX**: Thread-safety enforced automatically

### Tuning for Your Hardware

#### M1/M2 MacBook Air (8GB RAM)

```python
config = OCRConfig(
    batch_size=8,        # Small batches for limited memory
    render_workers=4,    # Conservative CPU usage
    analysis_workers=1,  # MLX single-worker
    pre_render_batches=2 # Shallow pipeline
)
```

**Expected performance:** ~90-120 minutes for 96 pages

#### M1/M2 MacBook Pro (16GB RAM)

```python
config = OCRConfig.mlx_optimized()  # Default works great
```

**Expected performance:** ~70-90 minutes for 96 pages

#### M3/M4 MacBook Pro (32GB+ RAM)

```python
config = OCRConfig(
    batch_size=30,       # Large batches
    render_workers=20,   # Maximum parallelism
    analysis_workers=1,  # MLX single-worker
    pre_render_batches=5 # Very deep pipeline
)
```

**Expected performance:** ~60-75 minutes for 96 pages

#### Linux/Windows with NVIDIA GPU

```python
config = OCRConfig(
    batch_size=15,       # Moderate for 14GB PyTorch model
    render_workers=16,   # Based on CPU cores
    analysis_workers=2,  # Parallel PyTorch inference
    pre_render_batches=3
)
```

**Expected performance:** ~80-100 minutes for 96 pages

## Memory Management

### Memory Usage Calculation

```python
total_memory = (
    model_memory +
    (batch_size × pages_per_batch × page_memory) +
    (pre_render_batches × batch_size × rendered_page_memory)
)
```

**Typical values:**
- MLX model: 2.2GB
- PyTorch model: 14GB
- Rendered page: ~5-10MB
- In-memory page: ~200MB during processing

### Memory Limits by Configuration

| Preset | Batch Size | Pre-render | Total Memory |
|--------|-----------|-----------|--------------|
| mlx_optimized | 30 | 4 | ~8-10GB |
| balanced | 20 | 3 | ~10-14GB (PyTorch) |
| memory_constrained (8GB) | 8 | 2 | ~4-6GB |
| memory_constrained (16GB) | 10 | 3 | ~6-8GB |

### Handling Out-of-Memory Errors

If you encounter OOM errors:

1. **Use memory_constrained preset:**
   ```python
   config = OCRConfig.memory_constrained()
   ```

2. **Reduce batch size:**
   ```python
   config = OCRConfig(batch_size=8)
   ```

3. **Reduce pipeline depth:**
   ```python
   config = OCRConfig(pre_render_batches=2)
   ```

4. **Process documents in chunks:**
   ```python
   # Split large PDF into smaller chunks first
   from PyPDF2 import PdfReader, PdfWriter

   # Process first 50 pages
   loader.load("document.pdf", page_range=(0, 50))

   # Process next 50 pages
   loader.load("document.pdf", page_range=(50, 100))
   ```

## Checkpointing

### How Checkpoints Work

Checkpoints save progress periodically so processing can resume if interrupted:

```python
loader = NanonetsLoader()  # checkpoint_enabled=True by default

# Process a large document
documents = loader.load("large_document.pdf")

# If interrupted, run again to resume:
documents = loader.load("large_document.pdf")  # Resumes from checkpoint
```

### Checkpoint Files

Checkpoints are saved to `./checkpoints/` by default:

```
checkpoints/
  ├── large_document_pdf_checkpoint.json      # Progress state
  └── large_document_pdf_regions/             # Cached OCR results
      ├── page_001.json
      ├── page_002.json
      └── ...
```

### Checkpoint Configuration

```python
from pathlib import Path

config = OCRConfig(
    checkpoint_enabled=True,  # Enable checkpointing
    checkpoint_dir=Path("./custom_checkpoints")  # Custom directory
)

loader = NanonetsLoader(config=config)
```

### Managing Checkpoints

```python
# Clear checkpoints for a document
from jina_rag_pipeline.ingestion.checkpoint import CheckpointManager

manager = CheckpointManager(checkpoint_dir=Path("./checkpoints"))
manager.clear_checkpoint("large_document.pdf")

# Or delete checkpoint files manually
import shutil
shutil.rmtree("./checkpoints/large_document_pdf_checkpoint")
```

## Examples

### Example 1: Simple Document Processing

```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader

# Use defaults (auto-selects best configuration)
loader = NanonetsLoader()

# Load a PDF
documents = loader.load("report.pdf")

print(f"Processed {len(documents)} pages")
```

### Example 2: Large Document with Custom Settings

```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig

# Custom configuration for large document
config = OCRConfig(
    batch_size=25,
    render_workers=18,
    analysis_workers=1,
    pre_render_batches=4,
    checkpoint_enabled=True
)

loader = NanonetsLoader(config=config)

# Process 150-page document
documents = loader.load("large_report.pdf")
```

### Example 3: Memory-Constrained Processing

```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig

# Use memory-constrained preset
loader = NanonetsLoader(config=OCRConfig.memory_constrained())

# Process with minimal memory usage
documents = loader.load("document.pdf")
```

### Example 4: PowerPoint Presentation

```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig

# Optimized for presentations
config = OCRConfig(
    batch_size=10,       # Smaller batches for slides
    render_workers=12,   # Parallel rendering
    analysis_workers=1,
    pre_render_batches=3
)

loader = NanonetsLoader(config=config)
documents = loader.load("presentation.pptx")
```

### Example 5: Batch Processing Multiple Documents

```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from pathlib import Path

loader = NanonetsLoader()

# Process multiple documents
document_paths = Path("./documents").glob("*.pdf")

for doc_path in document_paths:
    print(f"Processing {doc_path.name}...")
    documents = loader.load(str(doc_path))
    print(f"  → Extracted {len(documents)} pages")
```

## Troubleshooting

### Performance Issues

**Problem:** Processing is too slow

**Solutions:**
1. Increase batch_size: `config = OCRConfig(batch_size=30)`
2. Increase pre_render_batches: `config = OCRConfig(pre_render_batches=5)`
3. Verify MLX is being used (Apple Silicon only)
4. Check CPU usage - should be high during rendering

**Problem:** System feels sluggish during processing

**Solutions:**
1. Reduce render_workers: `config = OCRConfig(render_workers=8)`
2. Process in background or off-hours
3. Close other applications

### Memory Issues

**Problem:** Out of memory errors

**Solutions:**
1. Use memory_constrained preset: `OCRConfig.memory_constrained()`
2. Reduce batch_size: `config = OCRConfig(batch_size=8)`
3. Reduce pre_render_batches: `config = OCRConfig(pre_render_batches=2)`
4. Close other applications
5. Process document in chunks

**Problem:** System swap/paging excessively

**Solutions:**
1. Reduce batch_size by 50%
2. Reduce pre_render_batches to 2
3. Monitor memory: `htop` or Activity Monitor

### Quality Issues

**Problem:** OCR quality is poor

**Solutions:**
1. This is not a configuration issue - quality is determined by the model
2. Check input document quality (resolution, clarity)
3. Consider pre-processing images for better contrast

**Problem:** Some pages are skipped

**Solutions:**
1. Check logs for errors
2. Verify checkpoint is not stale (clear and retry)
3. Ensure document is not corrupted

## Migration Guide

See [OCR Migration Guide](ocr-migration.md) for migrating from the old profile-based system.

## Related Documentation

- [OCR Migration Guide](ocr-migration.md) - Migrate from old profile system
- [Getting Started](getting-started.md) - Basic setup and usage
- [Nanonets Migration Guide](nanonets-migration.md) - Nanonets analyzer features
- [System Architecture](../architecture/system-overview.md) - System internals
