# Scripts Directory

This directory contains various utility, test, demo, and debug scripts for the Pretty Please RAG pipeline.

## Directory Structure

```
scripts/
├── tests/          # Integration and feature tests
├── utils/          # Utility scripts for maintenance
├── demos/          # Demo and example scripts
├── debug/          # Debugging and troubleshooting scripts
├── quick_test.py   # Quick smoke test
├── run_backend.py  # Backend runner script
├── batch_test_rag.py          # Batch RAG quality testing
└── test_rag_interactive.py    # Interactive RAG testing
```

## Quick Reference

### Essential Scripts

| Script | Description |
|--------|-------------|
| `quick_test.py` | Quick smoke test for basic functionality |
| `run_backend.py` | Start the backend API server |
| `batch_test_rag.py` | Batch RAG quality testing |
| `test_rag_interactive.py` | Interactive RAG testing with detailed output |

## RAG Testing

### Interactive Testing

Test individual queries and see detailed output:

```bash
python scripts/test_rag_interactive.py
```

Features:
- Test queries interactively
- View full retrieval pipeline output (sources, scores, reranking)
- See formatted context with citations
- View generated responses with metrics
- Compare baseline vs enhanced retrieval
- Save examples for analysis
- Toggle reranking on/off

### Batch Testing

Run automated tests on multiple queries:

```bash
# Test all queries in the test dataset
python scripts/batch_test_rag.py \
  --queries-file tests/fixtures/rag_test_queries.json \
  --collection default

# Test a specific category
python scripts/batch_test_rag.py \
  --queries-file tests/fixtures/rag_test_queries.json \
  --collection default \
  --category simple_factual

# Test without reranking (baseline)
python scripts/batch_test_rag.py \
  --queries-file tests/fixtures/rag_test_queries.json \
  --collection default \
  --no-reranking
```

Results are saved to `tests/fixtures/batch_results/` with timestamps.

## Test Scripts (`tests/`)

### Integration Tests

| Script | Description |
|--------|-------------|
| `test_integration.py` | Comprehensive integration test (Phases 1-5) |
| `test_full_rag_pipeline.py` | Full RAG pipeline with Qwen and reranker |
| `test_vector_store_basic.py` | Basic vector store operations |

### Feature Tests

| Script | Description |
|--------|-------------|
| `test_citations.py` | Citation rendering and linking |
| `test_document_storage.py` | Document persistence and retrieval |
| `test_websocket.py` | WebSocket chat endpoint |
| `test_image_workflow.py` | Image upload and processing |

### Upload & Processing Tests

| Script | Description |
|--------|-------------|
| `test_5page_pdf.py` | 5-page PDF via Nanonets |
| `test_large_pdf.py` | Large PDF processing |
| `test_powerpoint_layout.py` | PowerPoint layout analysis |
| `test_batch_processing.py` | Batch processing for multiple documents |

### Async Processing Tests

| Script | Description |
|--------|-------------|
| `test_async_offloading.py` | Async offloading with ThreadPool |
| `test_async_offloading_simple.py` | Simplified async test |

### Model Tests

| Script | Description |
|--------|-------------|
| `test_nanonets_model.py` | Nanonets OCR model |
| `test_jina_basic.py` | Jina Embeddings v4 |
| `test_jina_reranker.py` | JinaAI reranker |
| `test_jina_m0_reranker.py` | JinaAI M0 reranker native API |
| `test_generation_truncation.py` | Response truncation with token limits |

### UI/Frontend Tests

| Script | Description |
|--------|-------------|
| `test_frontend.py` | Frontend functionality |
| `test_upload_ui.py` | Upload UI components |
| `test_user_flow.py` | End-to-end user flow |
| `test_dark_mode.py` | Dark mode functionality |
| `test_browser_devtools.py` | Browser DevTools integration |
| `test_visual_inspection.py` | Visual inspection workflow |

## Utility Scripts (`utils/`)

### Collection Management

| Script | Description |
|--------|-------------|
| `check_collection.py` | Check collection document counts |
| `check_collections.py` | List all collections and documents |
| `check_chroma_data.py` | Inspect ChromaDB storage |
| `cleanup_all_data.py` | Clean all database and upload data |

### System Verification

| Script | Description |
|--------|-------------|
| `verify_install.py` | Verify installation and dependencies |
| `verify_mps.py` | Verify MPS (Apple Silicon GPU) availability |

### Test Data

| Script | Description |
|--------|-------------|
| `create_test_pdf.py` | Generate multi-page test PDFs |

## Demo Scripts (`demos/`)

| Script | Description |
|--------|-------------|
| `demo_markdown_parser.py` | Showcase MarkdownParser capabilities |
| `simple_rag_test.py` | Simple synchronous RAG test |

## Debug Scripts (`debug/`)

| Script | Description |
|--------|-------------|
| `debug_context.py` | Debug context formatting for LLM |
| `debug_pdf_upload.py` | Debug PDF upload issues |
| `delete_old_pdf.py` | Clean up old PDF chunks without document_id |

---

## Usage Examples

### Run Quick Test

```bash
# From project root
python scripts/quick_test.py
```

### Start Backend

```bash
python scripts/run_backend.py
```

### Run Integration Tests

```bash
# Comprehensive test
python scripts/tests/test_integration.py

# Full RAG pipeline
python scripts/tests/test_full_rag_pipeline.py
```

### Check Collection Status

```bash
python scripts/utils/check_collections.py
```

### Clean Database

```bash
python scripts/utils/cleanup_all_data.py
```

### Demo Markdown Parser

```bash
python scripts/demos/demo_markdown_parser.py
```

---

## RAG Testing Workflow

### 1. Interactive Exploration

Start with interactive testing to understand query behavior:

```bash
python scripts/test_rag_interactive.py
```

Try different queries and observe:
- Which documents are retrieved
- How reranking changes the order
- Whether citations are used correctly
- Response quality and formatting

Save good and bad examples using the built-in save feature.

### 2. Baseline Comparison

Compare baseline (no reranking) vs enhanced (with reranking):

```bash
# In interactive mode, choose option 2
# Or run batch tests with and without --no-reranking
```

### 3. Batch Evaluation

Run systematic tests across categories:

```bash
# Test each category
for category in simple_factual comparison multi_hop technical_detail; do
  python scripts/batch_test_rag.py \
    --queries-file tests/fixtures/rag_test_queries.json \
    --category $category \
    --collection default
done
```

### 4. Analyze Results

Review saved results in `tests/fixtures/batch_results/` and `tests/fixtures/good|bad|other/`

Look for:
- Citation accuracy (are sources cited?)
- Markdown formatting quality
- Confidence expression appropriateness
- Retrieval relevance improvements from reranking
- Performance metrics (latency, throughput)

---

## Writing New Scripts

### Best Practices

1. **Location**: Choose the appropriate subdirectory
   - `tests/` - Integration and feature tests
   - `utils/` - Maintenance and utility scripts
   - `demos/` - Example and demonstration scripts
   - `debug/` - Debugging and troubleshooting scripts

2. **Naming**: Use descriptive names with prefixes
   - `test_*` for tests
   - `check_*`, `verify_*` for utilities
   - `demo_*` for demos
   - `debug_*` for debug scripts

3. **Documentation**: Include docstring at top
   ```python
   #!/usr/bin/env python3
   """Brief description of what this script does."""
   ```

4. **Imports**: Add project root to path if needed
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent))
   ```

5. **Main Guard**: Use `if __name__ == "__main__":` for scripts

---

## Migration Notes

All scripts were previously in the project root and have been reorganized into this structure. If you have scripts that reference old paths, update them to:

- `scripts/tests/` for test scripts
- `scripts/utils/` for utilities
- `scripts/demos/` for demos
- `scripts/debug/` for debug scripts

---

## Related Documentation

- [Getting Started Guide](../docs/guides/getting-started.md)
- [System Architecture](../docs/architecture/system-overview.md)
- [Testing Documentation](../tests/README.md)
