# Ingestion Capability Delta

This delta specifies changes to the ingestion capability for large document support.

## MODIFIED Requirements

### Requirement: Document Processing Pipeline
The system SHALL process documents through a complete ingestion workflow with **checkpoint support for large documents** and **parallel processing capabilities**.

#### ADDED Scenario: Process large PDF with progressive rendering
- **GIVEN** a PDF with 500+ pages
- **WHEN** processing with progressive mode enabled  
- **THEN** renders pages in batches of 10
- **AND** keeps memory usage below 32GB
- **AND** cleans up temporary files after each batch
- **AND** reports progress after each batch

#### ADDED Scenario: Process with checkpointing
- **GIVEN** a large document being processed
- **WHEN** processing completes for each page or batch
- **THEN** saves checkpoint with progress state
- **AND** checkpoint includes page number, results, and metadata
- **AND** checkpoint enables resume from failure point

#### ADDED Scenario: Resume from checkpoint after crash
- **GIVEN** a processing job that crashed at page 250/500
- **WHEN** restarting the processing task
- **THEN** automatically loads checkpoint
- **AND** resumes from page 251
- **AND** reuses previously processed results
- **AND** completes remaining 250 pages
- **AND** deletes checkpoint after successful completion

#### ADDED Scenario: Parallel page processing
- **GIVEN** a document with multiple pages
- **WHEN** processing with parallel mode enabled
- **THEN** processes up to 4 pages simultaneously (configurable)
- **AND** maintains correct page ordering in results
- **AND** respects memory constraints
- **AND** limits GPU-intensive operations appropriately

#### ADDED Scenario: Adaptive batch sizing based on memory
- **GIVEN** system memory usage is high (>80%)
- **WHEN** about to process next batch
- **THEN** reduces batch size to safe level
- **AND** monitors memory throughout processing
- **AND** prevents out-of-memory errors

---

## ADDED Requirements

### Requirement: Large Document Support
The system SHALL reliably process documents with 1000+ pages without memory exhaustion or data loss.

#### Scenario: Process 500-page textbook
- **GIVEN** a 500-page PDF textbook (~100MB)
- **WHEN** uploading for processing
- **THEN** completes processing within 2 hours
- **AND** keeps memory usage below 32GB throughout
- **AND** produces high-quality chunks with preserved structure
- **AND** enables full-text search across all pages

#### Scenario: Memory-efficient progressive processing
- **GIVEN** limited system memory
- **WHEN** processing very large document
- **THEN** renders pages progressively in batches
- **AND** processes rendered batch before rendering next
- **AND** cleans up temporary files immediately after use
- **AND** never loads entire document into memory

#### Scenario: Crash recovery without data loss
- **GIVEN** a processing job interrupted by crash or restart
- **WHEN** system restarts
- **THEN** automatically detects incomplete tasks
- **AND** resumes from last checkpoint
- **AND** notifies user of resumed processing
- **AND** completes without reprocessing completed pages

#### Scenario: Handle processing timeout
- **GIVEN** a processing job taking longer than expected
- **WHEN** job exceeds reasonable time limit (4 hours)
- **THEN** continues processing if making progress
- **AND** saves checkpoint periodically
- **AND** allows manual cancellation with state preservation

---

### Requirement: Semantic Chunking
The system SHALL preserve document structure and semantic units when creating chunks for embedding.

#### Scenario: Preserve table integrity
- **GIVEN** a document containing tables
- **WHEN** creating chunks for embedding
- **THEN** keeps entire table as single chunk
- **AND** never splits table rows across chunks
- **AND** includes table metadata (rows, columns, headers)
- **AND** marks chunk as atomic/indivisible

#### Scenario: Preserve mathematical equations
- **GIVEN** a document with LaTeX equations
- **WHEN** chunking for embeddings
- **THEN** keeps complete equation in single chunk
- **AND** includes LaTeX representation in metadata
- **AND** preserves equation context (surrounding text)
- **AND** marks equation chunk as atomic

#### Scenario: Preserve figures and images
- **GIVEN** a document with embedded figures
- **WHEN** chunking content
- **THEN** keeps figure description as single chunk
- **AND** links to original image metadata
- **AND** includes caption and context
- **AND** does not split figure reference from description

#### Scenario: Respect chapter boundaries
- **GIVEN** a textbook with chapter headings
- **WHEN** detecting heading/title regions
- **THEN** starts new chunk at chapter boundary
- **AND** includes chapter title in chunk metadata
- **AND** groups related sections within chapter
- **AND** preserves hierarchical structure

#### Scenario: Fallback to character chunking
- **GIVEN** a document without semantic region metadata
- **WHEN** attempting semantic chunking
- **THEN** detects absence of semantic regions
- **AND** automatically falls back to character-based chunking
- **AND** logs fallback decision
- **AND** still produces usable chunks

#### Scenario: Configurable semantic chunking
- **GIVEN** per-collection chunking configuration
- **WHEN** processing documents in collection
- **THEN** applies collection-specific chunking strategy
- **AND** respects preservation settings (tables, equations)
- **AND** uses configured maximum chunk size
- **AND** allows override via API parameters

---

### Requirement: Task Persistence
The system SHALL persist task state to survive server restarts and crashes.

#### Scenario: Task survives server restart
- **GIVEN** a long-running processing task in progress
- **WHEN** server is restarted (intentional or crash)
- **THEN** task state is loaded from persistent storage
- **AND** task status is preserved
- **AND** WebSocket clients can reconnect and resume monitoring
- **AND** processing continues from last checkpoint

#### Scenario: Task expiration and cleanup
- **GIVEN** completed or failed tasks in storage
- **WHEN** tasks are older than retention period (7 days)
- **THEN** automatically removes expired task records
- **AND** cleans up associated checkpoints
- **AND** removes temporary files
- **AND** logs cleanup actions

#### Scenario: Query task history
- **GIVEN** persistent task storage
- **WHEN** requesting task list via API
- **THEN** returns all tasks within retention period
- **AND** includes task status and progress
- **AND** shows both active and completed tasks
- **AND** allows filtering by collection or status

---

### Requirement: Memory Monitoring
The system SHALL actively monitor and manage memory usage during large document processing.

#### Scenario: Monitor memory throughout processing
- **GIVEN** a document being processed
- **WHEN** each processing phase executes
- **THEN** tracks current memory usage
- **AND** logs memory stats at key checkpoints
- **AND** warns when usage exceeds 80% of limit
- **AND** provides memory metrics via API

#### Scenario: Adaptive resource allocation
- **GIVEN** available system memory
- **WHEN** calculating safe batch size
- **THEN** dynamically adjusts based on current usage
- **AND** leaves buffer for system and other processes
- **AND** scales down if memory pressure detected
- **AND** scales up when memory available

#### Scenario: Memory pressure handling
- **GIVEN** memory usage approaching limit (>90%)
- **WHEN** about to allocate more memory
- **THEN** triggers garbage collection
- **AND** flushes caches if available
- **AND** reduces batch size
- **AND** logs warning with memory stats
- **AND** fails gracefully if still insufficient

---

## MODIFIED Requirements

### Requirement: Document Loading
The system SHALL load documents from various file formats into processable text **with configurable processing modes**.

#### MODIFIED Scenario: Load PowerPoint file
- **GIVEN** a .pptx or .ppt file
- **WHEN** loading the file
- **THEN** extracts text and optionally images based on configuration
- **AND** preserves slide structure in metadata
- **AND** **supports both batch and progressive rendering modes**
- **AND** **uses progressive mode by default for files >50 slides**

---

## Configuration Schema

### Collection Configuration Extension

```json
{
  "collection_name": "string",
  "processing": {
    "progressive_rendering": true,
    "batch_size": 10,
    "parallel_workers": 4,
    "checkpoint_enabled": true,
    "checkpoint_interval_pages": 10
  },
  "chunking": {
    "strategy": "semantic",
    "max_chunk_size": 1000,
    "preserve_tables": true,
    "preserve_equations": true,
    "preserve_figures": true,
    "fallback_to_character": true
  },
  "memory": {
    "max_memory_gb": 32,
    "enable_monitoring": true,
    "adaptive_batching": true
  }
}
```

### Environment Variables

New environment variables for configuration:

```bash
# Progressive Rendering
PROGRESSIVE_RENDERING=true
RENDER_BATCH_SIZE=10

# Parallel Processing  
MAX_RENDER_WORKERS=4
MAX_ANALYSIS_WORKERS=2

# Memory Management
MAX_MEMORY_GB=32
ENABLE_MEMORY_MONITORING=true

# Checkpointing
CHECKPOINT_DIR=./checkpoints
CHECKPOINT_INTERVAL_PAGES=10
AUTO_RESUME=true

# Task Persistence
TASK_DATABASE=./tasks.db
TASK_RETENTION_DAYS=7

# Semantic Chunking
USE_SEMANTIC_CHUNKING=true
PRESERVE_TABLES=true
PRESERVE_EQUATIONS=true
```

---

## API Extensions

### New Endpoints

#### GET /api/checkpoints
List all active checkpoints.

**Response**:
```json
{
  "checkpoints": [
    {
      "checkpoint_id": "string",
      "collection_name": "string",
      "file_name": "string",
      "total_pages": 500,
      "processed_pages": 250,
      "created_at": "2025-10-18T10:00:00Z",
      "updated_at": "2025-10-18T12:00:00Z"
    }
  ]
}
```

#### DELETE /api/checkpoints/{checkpoint_id}
Manually delete a checkpoint.

#### GET /api/metrics/memory
Get current memory usage statistics.

**Response**:
```json
{
  "current_gb": 12.5,
  "available_gb": 35.5,
  "usage_percent": 26.0,
  "max_configured_gb": 32,
  "batch_size_current": 10,
  "memory_pressure": "normal"
}
```

### Modified Endpoints

#### POST /api/ingest/upload
Add optional parameters:

```json
{
  "files": ["multipart/form-data"],
  "collection_name": "string",
  "progressive": true,
  "batch_size": 10,
  "enable_checkpoint": true,
  "resume": false
}
```

---

## Performance Targets

### Success Criteria

- **100-page document**: <15 minutes, <6GB memory
- **500-page document**: <2 hours, <8GB memory  
- **1000-page document**: <4 hours, <10GB memory
- **Checkpoint overhead**: <5% time increase
- **Resume accuracy**: 100% (no data loss)
- **Memory prediction**: Within 20% of actual

### Quality Metrics

- **Table preservation**: 100% (never split)
- **Equation preservation**: 100% (with LaTeX)
- **Chapter boundary detection**: >95% accuracy
- **Chunk quality**: No degradation vs current
