# Configuration UI Guide

## Overview

The configuration dashboard exposes global presets for embeddings and OCR. Users can adjust presets, review performance guidance, and synchronize settings across environments using JSON export/import.

## Hardware-Aware Recommendations

The backend inspects host hardware (operating system, CPU architecture, total RAM) and surfaces recommended presets via `/api/config/recommendations`. The UI displays these suggestions in both the Embedding and OCR panels:

- **Apple Silicon (arm64)** → MLX Optimized OCR preset (~2.2 GB vs ~8 GB for Balanced) with a fast path for Metal acceleration.
- **Low-memory hosts (≤16 GB)** → Memory Constrained presets to prevent OOM conditions.
- **High-memory hosts (≥48 GB)** → Fast embedding preset for higher throughput.

Click **Apply Recommendation** to merge the suggestion into the form; you can still fine-tune advanced parameters afterward.

## Exporting Configuration

Use **Export Configuration** in the Settings toolbar to download `global-config-YYYY-MM-DD.json`. The payload contains both embedding and OCR models and can be committed to version control or shared with teammates.

Example JSON structure:

```json
{
  "embeddings": {
    "task": "retrieval.passage",
    "dimensions": 1024,
    "late_chunking": true,
    "return_multivector": false,
    "embedding_format": "float",
    "batch_size": 32,
    "max_tokens_per_batch": 8192
  },
  "ocr": {
    "batch_size": 20,
    "render_workers": 4,
    "analysis_workers": 2,
    "pre_render_batches": 3,
    "checkpoint_enabled": true,
    "use_two_tier": false,
    "complexity_table_threshold": 1,
    "complexity_equation_threshold": 1,
    "complexity_image_threshold": 2,
    "complexity_min_text_length": 100
  }
}
```

## Importing Configuration

Select **Import Configuration** and choose a previously exported JSON file. The payload is validated via Pydantic before being written to disk. Successful imports automatically refresh the active embedding and OCR panels.

## Performance Expectations

Integration tests enforce that `/api/config/embeddings`, `/api/config/ocr`, and `/api/config/recommendations` respond in under 100 ms when served locally. UI components have been smoke-tested at a 768 px viewport to verify responsive layout.
