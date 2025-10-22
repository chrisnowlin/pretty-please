# Implementation Tasks

## Phase 1: Memory Optimization (Week 1, Priority: Critical)

### Task 1.1: Enable Progressive Rendering by Default
- [x] Change `NanonetsFirstLoader.__init__` default: `progressive=True` (loaders.py:422)
- [x] Update `batch_size` to auto-detect from processing profile (50 pages for aggressive mode)
- [x] Add configuration via processing profiles (`ProcessingProfile`)
- [x] Add checkpoint/resume support with parallel processing
- [ ] Update API endpoint to accept `progressive` and `batch_size` parameters
- [ ] Test with 50-page and 200-page PDFs
- [ ] Update documentation to explain progressive mode

**Files**: `src/jina_rag_pipeline/ingestion/loaders.py`, `src/jina_rag_pipeline/api/app.py`

**Implementation Notes**: Implemented with aggressive configuration support, auto-detecting M4 Max for optimal settings.

### Task 1.2: Implement Memory Monitoring
- [x] Enhanced `MemoryMonitor` class in `batch/memory.py` with aggressive mode support
- [x] Track current memory usage using `psutil`
- [x] Implement adaptive batch size calculation based on available memory
- [x] Add memory pressure detection (adjustable thresholds for aggressive mode: 85% warning, 95% error)
- [x] Configured for aggressive memory utilization (40GB max, 35GB target for M4 Max)
- [ ] Log memory stats at each phase (render, analyze, embed)
- [ ] Add `/api/metrics/memory` endpoint

**Files**: `src/jina_rag_pipeline/batch/memory.py`, `src/jina_rag_pipeline/api/app.py`

**Implementation Notes**: Implemented with aggressive mode configuration that adjusts thresholds for M4 Max systems.

### Task 1.3: Improve Temporary File Cleanup
- [ ] Add temp file tracking per page/batch
- [ ] Cleanup temp images immediately after Nanonets analysis
- [ ] Add automatic cleanup on exception/crash
- [ ] Verify no temp file leaks in tests
- [ ] Add `/tmp` cleanup job in API shutdown handler

**Files**: `src/jina_rag_pipeline/ingestion/loaders.py`

### Task 1.4: Document Memory Requirements
- [ ] Add memory requirements to README
- [ ] Create operator guide for large documents
- [ ] Document environment variables
- [ ] Add troubleshooting section

**Files**: `README.md`, `docs/guides/large-documents.md`

---

## Phase 2: Checkpointing (Week 1-2, Priority: High)

### Task 2.1: Create CheckpointManager
- [x] Create `CheckpointManager` class in `ingestion/checkpoint.py`
- [x] Implement checkpoint schema (JSON format with Checkpoint dataclass)
- [x] Add save/load checkpoint methods with atomic writes
- [x] Add checkpoint validation and corruption detection via file hash
- [x] Implement checkpoint expiration (7 days default, configurable)
- [x] Add cleanup methods for expired checkpoints
- [x] Add checkpoint listing functionality

**Files**: `src/jina_rag_pipeline/ingestion/checkpoint.py`

**Implementation Notes**: Fully implemented with file hash validation, atomic writes, and automatic cleanup.

**Checkpoint Schema**:
```python
{
    "checkpoint_id": str,
    "file_path": str,
    "file_hash": str,
    "collection_name": str,
    "total_pages": int,
    "processed_pages": int,
    "last_page_completed": int,
    "page_results": [
        {
            "page_num": int,
            "content_hash": str,
            "chunk_ids": List[str]
        }
    ],
    "created_at": str,
    "updated_at": str
}
```

### Task 2.2: Integrate Checkpoints into Document Processing
- [x] Modified `NanonetsFirstLoader.load()` to use checkpoints with new `_load_pdf_with_checkpoints` method
- [x] Save checkpoint after each batch (configurable: 50 pages for aggressive mode)
- [x] Load checkpoint on start, skip completed pages automatically
- [x] Add `resume` parameter to load() method (default: True)
- [ ] Add `--resume` flag to API ingestion endpoint
- [ ] Test resume after simulated crash at page 50/100

**Files**: `src/jina_rag_pipeline/ingestion/loaders.py`, `src/jina_rag_pipeline/api/app.py`

**Implementation Notes**: Integrated into NanonetsFirstLoader with automatic resume capability.

### Task 2.3: Checkpoint Directory Management
- [ ] Create checkpoint directory structure: `./checkpoints/{collection}/{task_id}/`
- [ ] Add configuration via `CHECKPOINT_DIR` env var
- [ ] Implement automatic cleanup after successful completion
- [ ] Add manual cleanup endpoint: `/api/checkpoints/{task_id}/cleanup`
- [ ] Add checkpoint listing: `/api/checkpoints`

**Files**: `src/jina_rag_pipeline/api/app.py`, `src/jina_rag_pipeline/ingestion/checkpoint.py`

### Task 2.4: Test Crash Recovery
- [ ] Create test: process 50 pages, crash at page 25, resume
- [ ] Create test: corrupt checkpoint, verify fallback
- [ ] Create test: multiple concurrent checkpoints
- [ ] Verify checkpoint cleanup after success
- [ ] Benchmark checkpoint overhead (should be <5%)

**Files**: `tests/test_checkpoint.py`

---

## Phase 3: Parallel Processing (Week 2, Priority: High)

### Task 3.1: Refactor Page Processing for Parallelization
- [ ] Extract `_process_single_page()` method from main loop
- [ ] Ensure page processing is stateless and thread-safe
- [ ] Add page ordering preservation mechanism
- [ ] Test single-threaded path still works

**Files**: `src/jina_rag_pipeline/ingestion/loaders.py`

### Task 3.2: Implement Parallel Page Rendering
- [x] Add ThreadPoolExecutor for PDF page rendering via `_render_pages_parallel` method
- [x] Configure max workers via processing profile (default: 12 for aggressive/M4 Max)
- [x] Implement result ordering by page number in returned dict
- [x] Add error handling per worker with proper exception propagation
- [ ] Test with 100-page PDF

**Files**: `src/jina_rag_pipeline/ingestion/loaders.py`

**Implementation Notes**: Implemented with 12 workers for M4 Max, properly ordered results.

### Task 3.3: Implement Parallel Nanonets Analysis
- [x] Add ThreadPoolExecutor for analysis via `_analyze_pages_parallel` method (max 6 workers for aggressive)
- [x] Configure via processing profile (default: 6 for aggressive/M4 Max)
- [ ] Implement GPU memory monitoring to avoid OOM
- [ ] Ensure Nanonets model thread-safety
- [ ] Test analysis quality matches sequential

**Files**: `src/jina_rag_pipeline/ingestion/loaders.py`, `src/jina_rag_pipeline/ingestion/nanonets_layout.py`

**Implementation Notes**: Implemented with 6 concurrent workers for M4 Max GPU utilization.

### Task 3.4: Optimize Batch Embedding
- [ ] Increase embedding batch size to 64 chunks
- [ ] Implement batched encoding in pipeline
- [ ] Add configuration via `EMBEDDING_BATCH_SIZE`
- [ ] Measure speedup vs sequential
- [ ] Verify embedding quality unchanged

**Files**: `src/jina_rag_pipeline/ingestion/pipeline.py`, `src/jina_rag_pipeline/embeddings/jina_v4.py`

### Task 3.5: Worker Pool Configuration
- [ ] Auto-detect optimal worker counts based on CPU/RAM
- [ ] Add manual override via environment variables
- [ ] Log worker pool configuration at startup
- [ ] Add worker utilization metrics
- [ ] Test on M4 Max with various worker counts

**Files**: `src/jina_rag_pipeline/ingestion/loaders.py`

---

## Phase 4: Semantic Chunking (Week 3, Priority: Medium)

### Task 4.1: Create SemanticRegionChunker
- [x] Create `SemanticRegionChunker` class in `ingestion/semantic_chunking.py`
- [x] Implement region-aware chunking algorithm
- [x] Preserve tables as single chunks (atomic regions)
- [x] Keep equations intact (atomic regions)
- [x] Detect and preserve chapter/section boundaries (headings start new chunks)
- [x] Add fallback to character chunking if no regions
- [x] Export from ingestion module

**Files**: `src/jina_rag_pipeline/ingestion/semantic_chunking.py`, `src/jina_rag_pipeline/ingestion/__init__.py`

**Implementation Notes**: Fully implemented with atomic region support and intelligent section merging.

**Algorithm**:
```python
def chunk_by_semantic_regions(regions: List[SemanticRegion]) -> List[Chunk]:
    - Group consecutive text regions until max size
    - Keep tables/equations/figures as single chunks
    - Start new chunk at heading/title boundaries
    - Add region metadata to each chunk
```

### Task 4.2: Update Pipeline to Use Semantic Chunking
- [ ] Add `use_semantic_chunking` configuration option
- [ ] Integrate `SemanticRegionChunker` into pipeline
- [ ] Extract semantic regions from Nanonets metadata
- [ ] Handle documents without semantic regions
- [ ] Test chunking quality with sample textbook

**Files**: `src/jina_rag_pipeline/ingestion/pipeline.py`

### Task 4.3: Chunk Quality Validation
- [ ] Verify tables not split across chunks
- [ ] Verify equations preserved with LaTeX
- [ ] Check chapter boundaries respected
- [ ] Measure chunk size distribution
- [ ] Compare retrieval quality vs character chunking

**Files**: `tests/test_semantic_chunking.py`

### Task 4.4: Update API for Chunking Configuration
- [ ] Add `/api/collections/{name}/chunking` endpoint
- [ ] Allow per-collection chunking strategy
- [ ] Store chunking config in collection metadata
- [ ] Update collection config schema
- [ ] Document chunking options

**Files**: `src/jina_rag_pipeline/api/app.py`, `src/jina_rag_pipeline/api/models.py`

---

## Phase 5: Task Persistence (Week 3, Priority: Medium)

### Task 5.1: Create Task Database Schema
- [ ] Create SQLite schema for task persistence
- [ ] Add tables: `tasks`, `task_files`, `task_progress`
- [ ] Enable WAL mode for concurrent access
- [ ] Add database migrations support
- [ ] Create database initialization script

**Files**: `src/jina_rag_pipeline/api/task_db.py`

**Schema**:
```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    collection_name TEXT NOT NULL,
    status TEXT NOT NULL,
    progress REAL DEFAULT 0,
    total_files INTEGER,
    processed_files INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE task_files (
    id INTEGER PRIMARY KEY,
    task_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    status TEXT NOT NULL,
    size INTEGER,
    error TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);
```

### Task 5.2: Integrate Database with TaskManager
- [ ] Modify `TaskManager` to use SQLite backend
- [ ] Persist task state on creation/update
- [ ] Load active tasks on server startup
- [ ] Implement task expiration (7 days)
- [ ] Add database cleanup job

**Files**: `src/jina_rag_pipeline/api/tasks.py`

### Task 5.3: Test Task Persistence
- [ ] Test task survives server restart
- [ ] Test task expiration cleanup
- [ ] Test concurrent task access
- [ ] Verify WebSocket still works with DB backend
- [ ] Test database corruption recovery

**Files**: `tests/test_task_persistence.py`

---

## Phase 6: Testing & Documentation (Week 3, Priority: High)

### Task 6.1: Create Test Documents
- [ ] Generate synthetic 100-page PDF
- [ ] Generate synthetic 500-page PDF with varied content
- [ ] Include tables, equations, figures in test PDFs
- [ ] Add test fixtures to repository
- [ ] Document test document structure

**Files**: `tests/fixtures/`, `scripts/utils/create_test_documents.py`

### Task 6.2: Integration Tests
- [ ] Test 100-page PDF end-to-end
- [ ] Test 500-page PDF with checkpointing
- [ ] Test parallel processing correctness
- [ ] Test semantic chunking quality
- [ ] Test memory usage stays below 32GB
- [ ] Test resume after crash at various points

**Files**: `tests/test_large_documents.py`

### Task 6.3: Performance Tests
- [ ] Benchmark 100-page processing time
- [ ] Benchmark 500-page processing time
- [ ] Profile memory usage throughout pipeline
- [ ] Measure parallel speedup (1 vs 4 workers)
- [ ] Compare semantic vs character chunking quality

**Files**: `tests/test_large_document_performance.py`

### Task 6.4: Documentation Updates
- [ ] Update README with large document support
- [ ] Create `docs/guides/large-documents.md`
- [ ] Document all new environment variables
- [ ] Add troubleshooting guide
- [ ] Create operator runbook
- [ ] Update API documentation

**Files**: `README.md`, `docs/guides/large-documents.md`

### Task 6.5: User Guide
- [ ] Write "Processing Large Documents" guide
- [ ] Include memory requirements
- [ ] Document checkpoint/resume usage
- [ ] Add configuration examples
- [ ] Include performance tuning tips

**Files**: `docs/guides/large-documents.md`

---

## Verification Checklist

Before marking this change as complete:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] 500-page PDF processes successfully without OOM
- [ ] Checkpoint/resume works correctly
- [ ] Memory stays below 32GB during processing
- [ ] Parallel processing produces correct results
- [ ] Semantic chunking preserves document structure
- [ ] Documentation is complete and accurate
- [ ] API endpoints documented in OpenAPI spec
- [ ] Performance meets success criteria (<2 hours for 500 pages)

---

## UPDATED: Aggressive Configuration Tasks for M4 Max

### Task 1.1b: Implement Aggressive Processing Profile
- [x] Add default `batch_size` of **50 pages** for aggressive profile
- [x] Create configuration profiles module: `aggressive`, `balanced`, `conservative`
- [x] Auto-detect M4 Max (ARM64 + 32GB+ RAM) and enable aggressive profile
- [x] Add `PROCESSING_PROFILE` environment variable support
- [ ] Implement pre-rendering buffer (2 batches ahead in memory)
- [ ] Test profile switching and performance impact

**Files**: `src/jina_rag_pipeline/config/profiles.py`, `src/jina_rag_pipeline/ingestion/loaders.py`, `src/jina_rag_pipeline/config/__init__.py`

**Implementation Notes**: Fully implemented with auto-detection, three profiles (aggressive: 50pg/12+6 workers, balanced: 20pg/6+3 workers, conservative: 10pg/4+2 workers).

### Task 1.2b: Aggressive Memory Configuration
- [x] Update `MAX_MEMORY_GB` to **40GB** for M4 Max in aggressive profile
- [x] Adjust memory pressure thresholds for aggressive mode (warn at 85%, error at 95%)
- [x] Add memory usage target of 35GB for optimal throughput in aggressive profile
- [ ] Implement intelligent memory allocation for large batches
- [ ] Test with multiple 500+ page documents simultaneously

**Implementation Notes**: Memory configuration integrated into ProcessingProfile with aggressive settings.

### Task 3.2b: Maximum Parallelization for Rendering
- [ ] Increase `MAX_RENDER_WORKERS` to **12** (all M4 Max P-cores)
- [ ] Implement pipeline overlapping (render next batch while analyzing current)
- [ ] Add queue-based rendering pipeline with 2-batch lookahead
- [ ] Target: Render 50 pages in under 1 minute
- [ ] Benchmark: Measure render throughput (pages/second)

### Task 3.3b: Aggressive Nanonets Parallelization
- [ ] Increase `MAX_ANALYSIS_WORKERS` to **6** for M4 Max GPU
- [ ] Implement model pre-loading (load once, keep in memory)
- [ ] Add model caching to avoid reload overhead
- [ ] Test GPU memory limits with 6 concurrent workers
- [ ] Add dynamic worker scaling based on GPU memory availability
- [ ] Target: Analyze 50 pages in under 5 minutes

### Task 3.4b: High-Throughput Embedding
- [ ] Increase `EMBEDDING_BATCH_SIZE` to **256 chunks**
- [ ] Implement embedding queue for continuous processing
- [ ] Pre-load and cache Jina v4 model
- [ ] Add pipeline overlapping with analysis stage
- [ ] Target: Embed 1000 chunks in under 2 minutes
- [ ] Test MPS acceleration with large batches

### Task 3.6: NEW - Pipeline Overlapping Implementation
- [ ] Create `OverlappedPipeline` class
- [ ] Implement stage queues: Render → Analysis → Embedding → Storage
- [ ] Add concurrent stage execution with ThreadPoolExecutor
- [ ] Ensure proper backpressure and flow control
- [ ] Add metrics for stage utilization and bottleneck detection
- [ ] Test end-to-end with 1000-page document

**Files**: `src/jina_rag_pipeline/ingestion/pipeline_overlapped.py`

---

## Performance Verification Tasks

### Task 7.1: Aggressive Mode Benchmarking
- [ ] Benchmark 100-page document (target: <7 minutes)
- [ ] Benchmark 500-page document (target: <35 minutes)
- [ ] Benchmark 1000-page document (target: <70 minutes)
- [ ] Measure memory usage at each stage (target: 30-35GB peak)
- [ ] Verify quality matches conservative mode
- [ ] Document actual vs target performance

### Task 7.2: Resource Utilization Analysis
- [ ] Measure CPU utilization during processing (target: >80% on P-cores)
- [ ] Measure GPU utilization (target: >70%)
- [ ] Measure memory utilization (target: 30-35GB sustained)
- [ ] Identify bottlenecks in pipeline
- [ ] Create performance tuning guide based on findings

### Task 7.3: Stress Testing
- [ ] Process three 500-page documents concurrently
- [ ] Process 2000-page synthetic document
- [ ] Test memory recovery after processing
- [ ] Test system stability over 4-hour processing session
- [ ] Verify checkpoint/resume under high load

---

## Updated Environment Variables

```bash
# Aggressive Mode Defaults for M4 Max (48GB)
PROCESSING_PROFILE=aggressive      # Auto-select profile
PROGRESSIVE_RENDERING=true
RENDER_BATCH_SIZE=50              # 5× larger batches
PRE_RENDER_BATCHES=2              # Buffer ahead

# Maximum Parallelization
MAX_RENDER_WORKERS=12             # All P-cores
MAX_ANALYSIS_WORKERS=6            # Push GPU harder
EMBEDDING_BATCH_SIZE=256          # 4× larger

# Aggressive Memory Usage  
MAX_MEMORY_GB=40                  # Use 83% of RAM
MEMORY_TARGET_GB=35               # Aim for 35GB usage
AGGRESSIVE_MODE=true              # Enable all optimizations

# Checkpoint Strategy (larger intervals for speed)
CHECKPOINT_INTERVAL_PAGES=50      # After each batch
```

---

## Success Criteria Updates

With aggressive configuration:

- [ ] **100-page document**: <7 minutes (was 15 min target)
- [ ] **500-page document**: <35 minutes (was 60-120 min target)
- [ ] **1000-page document**: <70 minutes (was 2-4 hours target)
- [ ] **Memory usage**: 30-35GB sustained (was 10GB target)
- [ ] **CPU utilization**: >80% on performance cores
- [ ] **GPU utilization**: >70% during analysis phase
- [ ] **Quality**: No degradation vs sequential processing
- [ ] **Reliability**: Checkpoint/resume works with large batches
