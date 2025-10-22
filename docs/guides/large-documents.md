# Processing Large Documents

**Guide for processing textbook-sized documents (300-1000+ pages) with Pretty Please RAG**

---

## Overview

Pretty Please RAG now supports efficient processing of large documents through:

- **Parallel Processing**: Utilizes all CPU cores for rendering and GPU for analysis
- **Checkpoint/Resume**: Automatic crash recovery with page-level checkpoints
- **Aggressive Configuration**: Auto-optimized for M4 Max with 48GB RAM
- **Semantic Chunking**: Preserves tables, equations, and document structure
- **Memory Management**: Intelligent memory utilization up to 40GB

### Expected Performance (M4 Max, 48GB RAM)

| Document Size | Processing Time | Memory Usage |
|---------------|-----------------|--------------|
| 100 pages (~10MB) | ~7 minutes | ~20GB |
| 500 pages (~100MB) | ~35 minutes | ~30GB |
| 1000 pages (~200MB) | ~70 minutes | ~35GB |

**That's a 2-3× speedup compared to sequential processing!**

---

## Quick Start

### Basic Usage

```python
from jina_rag_pipeline.ingestion import NanonetsFirstLoader
from pathlib import Path

# Auto-detects hardware and uses optimal settings
loader = NanonetsFirstLoader()

# Process large PDF with automatic checkpoint/resume
document = loader.load(
    file_path=Path("large_textbook.pdf"),
    collection_name="textbooks",
    resume=True  # Enable automatic resume (default)
)

print(f"Processed {document.metadata.get('page_count')} pages")
```

That's it! The system automatically:
- ✅ Detects your M4 Max and enables aggressive mode
- ✅ Uses 50-page batches for optimal throughput
- ✅ Leverages 12 render workers + 6 analysis workers
- ✅ Creates checkpoints every 50 pages
- ✅ Resumes automatically if interrupted

---

## Processing Profiles

### Auto-Detection

The system automatically detects your hardware and selects the best profile:

- **Aggressive** (M4 Max, 48GB+ RAM): 50-page batches, 12+6 workers, 40GB memory
- **Balanced** (32GB RAM, 8+ cores): 20-page batches, 6+3 workers, 32GB memory
- **Conservative** (16-24GB RAM): 10-page batches, 4+2 workers, 24GB memory

### Check Current Profile

```python
from jina_rag_pipeline.config import get_profile, get_profile_summary

profile = get_profile()
print(f"Using profile: {profile.name}")
print(get_profile_summary(profile))
```

Output:
```
Using profile: aggressive
Processing Profile: aggressive
Maximum speed for 48GB+ systems (M4 Max optimized)

Batch Sizes:
  - Rendering: 50 pages
  - Embedding: 256 chunks

Worker Pools:
  - Render workers: 12
  - Analysis workers: 6

Memory Configuration:
  - Max usage: 40GB
  - Target usage: 35GB
  - Pressure threshold: 85%

Pipeline:
  - Pre-render batches: 2
  - Checkpoint interval: 50 pages
  - Aggressive mode: True
  - Model caching: True
```

### Override Profile

```bash
# Set environment variable before starting
export PROCESSING_PROFILE=balanced

# Or in Python
import os
os.environ["PROCESSING_PROFILE"] = "balanced"
```

---

## Checkpoint and Resume

### How It Works

Checkpoints are automatically saved after each batch (50 pages in aggressive mode):

```
./checkpoints/
  └── textbooks/
      └── a1b2c3d4e5f6.../  # File hash
          └── checkpoint.json
```

### Resume After Crash

If processing is interrupted, simply run the same command again:

```python
# Processing interrupted at page 250/500
loader = NanonetsFirstLoader()

# Automatically resumes from page 250
document = loader.load(
    file_path=Path("large_textbook.pdf"),
    collection_name="textbooks",
    resume=True  # Automatic resume
)
```

The system:
1. Loads checkpoint from `./checkpoints/textbooks/{file_hash}/`
2. Skips pages 0-249 (already processed)
3. Continues from page 250
4. Cleans up checkpoint on successful completion

### Disable Resume

```python
# Start from scratch, ignoring any checkpoints
document = loader.load(
    file_path=Path("large_textbook.pdf"),
    collection_name="textbooks",
    resume=False
)
```

### Manual Checkpoint Management

```python
from jina_rag_pipeline.ingestion import CheckpointManager

manager = CheckpointManager()

# List active checkpoints
checkpoints = manager.list_checkpoints()
for cp in checkpoints:
    print(f"{cp['checkpoint_id']}: {cp['progress']}")

# Cleanup expired checkpoints (>7 days old)
cleaned = manager.cleanup_expired(days=7)
print(f"Cleaned up {cleaned} checkpoints")
```

---

## Parallel Processing

### How It Works

Processing happens in parallel stages:

```
Batch 1 (pages 0-49):
  ├─ Render [12 workers] ──> 12 pages at once
  └─ Analyze [6 workers] ──> 6 pages at once

Batch 2 (pages 50-99):
  ├─ Render [12 workers]
  └─ Analyze [6 workers]
  ...
```

### Worker Configuration

Workers are auto-configured based on your profile:

```python
from jina_rag_pipeline.config import get_profile

profile = get_profile()
print(f"Render workers: {profile.max_render_workers}")
print(f"Analysis workers: {profile.max_analysis_workers}")
print(f"Embedding batch size: {profile.embedding_batch_size}")
```

### Custom Worker Counts

```python
loader = NanonetsFirstLoader(
    batch_size=30,              # Override batch size
    max_render_workers=8,       # Override render workers
    max_analysis_workers=4      # Override analysis workers
)
```

---

## Semantic Chunking

### Structure-Preserving Chunks

Semantic chunking preserves document structure:

- **Tables**: Never split, kept as single chunks
- **Equations**: Kept intact with LaTeX
- **Figures**: Single chunks with descriptions
- **Sections**: Headings start new chunks
- **Text**: Grouped until max size

### Usage

```python
from jina_rag_pipeline.ingestion import SemanticRegionChunker

chunker = SemanticRegionChunker(
    max_chunk_size=1000,        # Max chars for text regions
    preserve_tables=True,        # Keep tables intact
    preserve_equations=True,     # Keep equations intact
    preserve_images=True         # Keep images intact
)

chunks = chunker.chunk(document)

# Inspect chunk types
for chunk in chunks:
    region_type = chunk.metadata.get("region_type", "text")
    atomic = chunk.metadata.get("atomic", False)
    print(f"{region_type}: {len(chunk.content)} chars (atomic: {atomic})")
```

Output:
```
title: 45 chars (atomic: False)
text: 856 chars (atomic: False)
table: 324 chars (atomic: True)
equation: 12 chars (atomic: True)
text: 1024 chars (atomic: False)
```

### Fallback Behavior

If semantic regions aren't available, automatically falls back to character-based chunking:

```python
chunker = SemanticRegionChunker(
    max_chunk_size=1000,
    fallback_to_character=True  # Default
)

chunks = chunker.chunk(document_without_regions)
# Uses FixedSizeChunker automatically
```

---

## Memory Management

### Memory Monitoring

The system monitors memory in real-time and adapts:

```python
from jina_rag_pipeline.batch.memory import MemoryMonitor, MemoryConfig

config = MemoryConfig(
    aggressive_mode=True,           # Enable for M4 Max
    aggressive_max_memory_gb=40,    # Max memory to use
    aggressive_target_gb=35         # Target sustained usage
)

monitor = MemoryMonitor(config)

# Check current status
under_pressure, msg = monitor.check_memory_pressure()
print(msg)  # "Memory usage normal: 62.3%"

# Get detailed stats
stats = monitor.get_memory_stats()
print(f"Available: {stats['available_gb']:.1f}GB")
print(f"Used: {stats['used_gb']:.1f}GB")
```

### Thresholds by Profile

| Profile | Warning | Error | Safety Buffer |
|---------|---------|-------|---------------|
| Aggressive | 85% | 95% | 4GB |
| Balanced | 80% | 95% | 2GB |
| Conservative | 75% | 95% | 2GB |

### Memory Pressure Response

If memory usage is high:
1. **Warning (85%)**: Logged, processing continues
2. **High (90%)**: Batch size reduced automatically
3. **Critical (95%)**: Processing pauses briefly

---

## Best Practices

### 1. For Very Large Documents (1000+ pages)

```python
# Use conservative profile for safety
import os
os.environ["PROCESSING_PROFILE"] = "balanced"

# Process in smaller chunks if needed
loader = NanonetsFirstLoader(batch_size=20)
```

### 2. For Maximum Speed (M4 Max)

```python
# Ensure aggressive mode is enabled
os.environ["PROCESSING_PROFILE"] = "aggressive"

loader = NanonetsFirstLoader()
# Uses 50-page batches, 12+6 workers, 256 chunk embeddings
```

### 3. For Reliability

```python
# Checkpoints enabled by default, but you can adjust interval
loader = NanonetsFirstLoader(
    enable_checkpoints=True,
    checkpoint_dir=Path("./my_checkpoints")
)

# Checkpoint every 25 pages instead of 50
loader.batch_size = 25
```

### 4. Monitor Progress

```python
def progress_callback(page_num, total_pages, message):
    percent = (page_num / total_pages) * 100
    print(f"Progress: {percent:.1f}% ({page_num}/{total_pages}) - {message}")

document = loader.load(
    file_path=Path("large_textbook.pdf"),
    progress_callback=progress_callback
)
```

Output:
```
Progress: 10.0% (50/500) - Processed page 50
Progress: 20.0% (100/500) - Processed page 100
Progress: 30.0% (150/500) - Processed page 150
...
```

---

## Troubleshooting

### Out of Memory Errors

**Solution 1: Use Conservative Profile**
```bash
export PROCESSING_PROFILE=conservative
```

**Solution 2: Reduce Batch Size**
```python
loader = NanonetsFirstLoader(batch_size=10)
```

**Solution 3: Reduce Workers**
```python
loader = NanonetsFirstLoader(
    max_render_workers=4,
    max_analysis_workers=2
)
```

### Slow Processing

**Check Profile**
```python
from jina_rag_pipeline.config import get_profile

profile = get_profile()
if profile.name != "aggressive":
    print(f"Consider switching to aggressive mode")
    print(f"Current: {profile.name}")
```

**Enable Aggressive Mode**
```bash
export PROCESSING_PROFILE=aggressive
```

### Checkpoint Issues

**Check Checkpoint Status**
```python
from jina_rag_pipeline.ingestion import CheckpointManager

manager = CheckpointManager()
checkpoints = manager.list_checkpoints()
print(f"Found {len(checkpoints)} active checkpoints")
```

**Manually Delete Checkpoint**
```python
# Start fresh
manager.cleanup_expired(days=0)  # Delete all
```

### GPU Not Utilized

The Nanonets model should automatically use MPS (Metal Performance Shaders) on M4 Max.

**Check GPU Usage**
```bash
# In another terminal while processing
sudo powermetrics --samplers gpu_power -i 1000 -n 1
```

---

## API Integration

### Using with FastAPI

```python
from fastapi import FastAPI, UploadFile, BackgroundTasks
from jina_rag_pipeline.ingestion import NanonetsFirstLoader

app = FastAPI()

@app.post("/process-large-document")
async def process_document(
    file: UploadFile,
    collection: str,
    background_tasks: BackgroundTasks
):
    # Save uploaded file
    file_path = Path(f"./uploads/{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Process in background with checkpoint support
    def process():
        loader = NanonetsFirstLoader()
        document = loader.load(
            file_path,
            collection_name=collection,
            resume=True
        )
        # Add to vector database...

    background_tasks.add_task(process)

    return {"message": "Processing started", "checkpoints_enabled": True}
```

### Admin Endpoints

```python
# Mount admin router
from jina_rag_pipeline.api.endpoints_admin import router as admin_router

app.include_router(admin_router)
```

Access at:
- `GET /api/admin/profile` - View current profile
- `GET /api/admin/checkpoints` - List checkpoints
- `POST /api/admin/checkpoints/cleanup` - Clean expired checkpoints
- `GET /api/admin/statistics` - System statistics

---

## Performance Optimization

### Tune for Your Hardware

**For 32GB RAM systems:**
```bash
export PROCESSING_PROFILE=balanced
```

**For 16GB RAM systems:**
```bash
export PROCESSING_PROFILE=conservative
```

### Monitor Resource Usage

```python
from jina_rag_pipeline.batch.memory import MemoryMonitor

monitor = MemoryMonitor()

while processing:
    stats = monitor.get_memory_stats()
    print(f"Memory: {stats['percent_used']:.1f}%")
    print(f"Process: {stats['process_used_gb']:.1f}GB")
    time.sleep(5)
```

### Benchmark Your System

```python
import time
from pathlib import Path

# Time a known document
start = time.time()
document = loader.load(Path("test_100_pages.pdf"))
elapsed = time.time() - start

pages_per_minute = 100 / (elapsed / 60)
print(f"Processing speed: {pages_per_minute:.1f} pages/minute")
```

---

## Advanced Configuration

### Custom Checkpoint Directory

```python
loader = NanonetsFirstLoader(
    enable_checkpoints=True,
    checkpoint_dir=Path("/data/checkpoints")
)
```

### Disable Checkpoints (Not Recommended)

```python
loader = NanonetsFirstLoader(
    enable_checkpoints=False
)
```

### Profile-Specific Settings

```python
from jina_rag_pipeline.config import ProcessingProfile

custom_profile = ProcessingProfile(
    name="custom",
    description="My custom settings",
    render_batch_size=30,
    embedding_batch_size=128,
    max_render_workers=8,
    max_analysis_workers=4,
    max_memory_gb=32,
    memory_target_gb=28,
    memory_pressure_threshold=0.80,
    pre_render_batches=1,
    checkpoint_interval_pages=30,
    aggressive_mode=False
)

# Use custom profile
loader = NanonetsFirstLoader(
    batch_size=custom_profile.render_batch_size,
    max_render_workers=custom_profile.max_render_workers,
    max_analysis_workers=custom_profile.max_analysis_workers
)
```

---

## Examples

### Example 1: Process Textbook with Progress

```python
from jina_rag_pipeline.ingestion import NanonetsFirstLoader
from pathlib import Path
import time

def progress_cb(page, total, msg):
    print(f"[{page}/{total}] {msg}")

start = time.time()
loader = NanonetsFirstLoader()

document = loader.load(
    file_path=Path("calculus_textbook.pdf"),
    collection_name="math_textbooks",
    progress_callback=progress_cb,
    resume=True
)

elapsed = time.time() - start
pages = document.metadata.get("page_count")

print(f"\nCompleted in {elapsed/60:.1f} minutes")
print(f"Speed: {pages/(elapsed/60):.1f} pages/minute")
```

### Example 2: Process with Semantic Chunking

```python
from jina_rag_pipeline.ingestion import (
    NanonetsFirstLoader,
    SemanticRegionChunker
)

# Load document
loader = NanonetsFirstLoader()
document = loader.load(
    Path("physics_textbook.pdf"),
    collection_name="physics"
)

# Chunk with semantic awareness
chunker = SemanticRegionChunker(
    max_chunk_size=1200,
    preserve_tables=True,
    preserve_equations=True
)

chunks = chunker.chunk(document)

# Analyze chunks
table_chunks = [c for c in chunks if c.metadata.get("region_type") == "table"]
equation_chunks = [c for c in chunks if c.metadata.get("region_type") == "equation"]

print(f"Total chunks: {len(chunks)}")
print(f"Tables: {len(table_chunks)}")
print(f"Equations: {len(equation_chunks)}")
```

### Example 3: Resume After Interruption

```python
# Initial attempt (interrupted at page 300)
try:
    loader = NanonetsFirstLoader()
    document = loader.load(
        Path("large_textbook.pdf"),
        collection_name="textbooks"
    )
except KeyboardInterrupt:
    print("Processing interrupted!")

# Resume (automatically continues from page 300)
loader = NanonetsFirstLoader()
document = loader.load(
    Path("large_textbook.pdf"),
    collection_name="textbooks",
    resume=True  # Auto-resumes
)

print("Processing completed!")
```

---

## Support

### Common Issues

1. **Memory errors**: Switch to conservative profile
2. **Slow performance**: Verify aggressive mode is enabled
3. **Checkpoint not resuming**: Check file hasn't changed (uses MD5 hash)
4. **Quality issues**: Ensure Nanonets model is loaded correctly

### Get Help

- GitHub Issues: https://github.com/chrisnowlin/pretty-please/issues
- Documentation: https://docs.your-site.com
- Discord: https://discord.gg/your-server

---

## Summary

✅ **Auto-configured for M4 Max**: Just call `NanonetsFirstLoader()`
✅ **Checkpoint/Resume**: Automatic crash recovery
✅ **2-3× Speedup**: Parallel processing on all cores
✅ **Structure-Preserving**: Tables and equations stay intact
✅ **Production-Ready**: Process 1000-page books in ~1 hour

Start processing large documents today with minimal configuration!
