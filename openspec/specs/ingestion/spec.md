# ingestion Specification

## Purpose
TBD - created by archiving change add-document-ingestion. Update Purpose after archive.
## Requirements
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

### Requirement: Text Chunking
The system SHALL split documents into optimal chunks for embedding generation.

#### Scenario: Chunk with overlap
- **WHEN** chunking text with size=1000 and overlap=200
- **THEN** creates chunks of ~1000 characters
- **AND** overlaps 200 characters between consecutive chunks

#### Scenario: Respect sentence boundaries
- **WHEN** sentence-aware chunking is enabled
- **THEN** chunks end at sentence boundaries
- **AND** prevents mid-sentence splits

#### Scenario: Handle small documents
- **WHEN** document is smaller than chunk size
- **THEN** returns single chunk with full content
- **AND** marks as complete document

### Requirement: Document Processing Pipeline
The system SHALL process documents through a complete ingestion workflow **and preserve original files for citation linking**.

#### Scenario: Process single document
- **WHEN** ingesting a new document
- **THEN** loads, chunks, generates embeddings
- **AND** stores in vector database with metadata

#### Scenario: Batch process directory
- **WHEN** processing directory of documents
- **THEN** processes all supported files
- **AND** reports progress and statistics

#### Scenario: Handle processing errors
- **WHEN** error occurs during processing
- **THEN** logs error with document identifier
- **AND** continues processing remaining documents

#### Scenario: Persist document file during ingestion
- **WHEN** processing text document for embedding
- **THEN** copies file to `./uploads/{collection}/documents/` before processing
- **AND** renames to `{document_id}{extension}` using UUID
- **AND** stores `document_path` in all chunk metadata
- **AND** does NOT delete original file after embedding
- **AND** preserves file in permanent storage

**Rationale**: Currently, text documents are deleted after chunking and embedding (line 240 in tasks.py), making citation linking impossible. Preserving files enables source verification and transparency. Mirroring existing image storage pattern ensures consistency.

#### Scenario: Handle document persistence failure
- **WHEN** document copy/move to storage fails
- **THEN** logs error with details
- **AND** continues with embedding process
- **AND** marks document as "storage_failed" in metadata
- **AND** cleanup removes temporary files

**Rationale**: Storage failures shouldn't block embedding workflow. Metadata flag allows graceful degradation in citation viewer (show chunk text instead).

### Requirement: Metadata Extraction
The system SHALL extract and preserve document metadata throughout processing.

#### Scenario: Extract PowerPoint metadata
- **GIVEN** a PowerPoint file with properties
- **WHEN** processing the file
- **THEN** extracts title, author, creation date
- **AND** includes slide count and presentation metadata
- **AND** includes per-slide metadata (slide number, title)

#### Scenario: Add region metadata
- **GIVEN** a document processed with layout analysis
- **WHEN** creating chunk metadata
- **THEN** includes region information (type, bbox, confidence)
- **AND** merges with existing document metadata
- **AND** validates region metadata schema

### Requirement: Incremental Processing
The system SHALL support efficient reprocessing by tracking document state.

#### Scenario: Skip unchanged documents
- **WHEN** document hash matches previous processing
- **THEN** skips reprocessing
- **AND** reports as already processed

#### Scenario: Detect modified documents
- **WHEN** document modified since last processing
- **THEN** reprocesses entire document
- **AND** updates existing embeddings

#### Scenario: Force reprocessing
- **WHEN** force flag is set
- **THEN** reprocesses all documents
- **AND** replaces existing embeddings

### Requirement: Document File Lifecycle Management
The system SHALL manage the lifecycle of uploaded document files from ingestion through deletion.

#### Scenario: Save document on upload
- **WHEN** document file uploaded via API
- **THEN** saves to temporary directory first
- **AND** moves to permanent storage after validation
- **AND** atomic move prevents partial writes
- **AND** verifies file integrity after move

**Rationale**: Two-phase upload (temp → permanent) ensures atomicity and prevents corrupted files in permanent storage.

#### Scenario: Track document metadata
- **WHEN** saving document to storage
- **THEN** records document_id, source name, storage path
- **AND** includes upload timestamp
- **AND** includes file size and format
- **AND** adds to all chunk metadata for retrieval

**Rationale**: Comprehensive metadata enables document retrieval, audit trail, and storage management.

#### Scenario: Clean up orphaned documents
- **WHEN** document processing fails mid-stream
- **THEN** removes temporary files
- **AND** keeps permanent storage only for successfully processed docs
- **AND** logs cleanup actions

**Rationale**: Failed uploads shouldn't consume disk space. Clean separation between temp and permanent storage simplifies cleanup.

### Requirement: Document Deduplication
The system SHALL leverage existing fingerprinting to avoid redundant storage **while maintaining citation traceability**.

#### Scenario: Detect duplicate document
- **WHEN** document with same content hash uploaded
- **THEN** existing fingerprint mechanism detects duplicate
- **AND** skips re-processing (existing behavior)
- **AND** STILL stores new copy with unique document_id
- **AND** different uploads can cite distinct instances

**Rationale**: Deduplication prevents redundant embedding work, but multiple upload instances should remain independently citable for audit/provenance.

#### Scenario: Link metadata to shared embeddings
- **WHEN** duplicate detected but storage differs
- **THEN** new metadata points to existing embeddings
- **AND** citation map includes upload-specific source name
- **AND** users see their uploaded filename in citations

**Rationale**: Multiple users uploading same document should see their own filename in citations, even if embeddings are shared.

### Requirement: PowerPoint Document Loading
The system SHALL load PowerPoint presentations and extract content for embedding.

#### Scenario: Load PPTX file with text only
- **GIVEN** a PowerPoint file with text-only slides
- **WHEN** loading the .pptx file
- **THEN** extracts text from all slides
- **AND** preserves slide boundaries in metadata
- **AND** includes slide numbers with each text block

#### Scenario: Load PPTX with layout analysis enabled
- **GIVEN** a PowerPoint file with mixed text and images
- **AND** layout analysis is enabled for the collection
- **WHEN** loading the .pptx file
- **THEN** extracts both text and image regions
- **AND** preserves spatial relationships in metadata
- **AND** saves extracted images to extracted_images directory

#### Scenario: Load legacy PPT format
- **GIVEN** a legacy .ppt format file
- **WHEN** loading the file
- **THEN** converts to processable format
- **AND** extracts content same as .pptx
- **OR** provides clear error if conversion not supported

#### Scenario: Handle PowerPoint with speaker notes
- **GIVEN** a PowerPoint with speaker notes
- **WHEN** loading with simple mode
- **THEN** extracts slide text only (notes optional)
- **AND** includes notes in metadata if present

### Requirement: Document Layout Analysis
The system SHALL optionally analyze document layout to identify regions (text, images, tables).

#### Scenario: Analyze document layout
- **GIVEN** a document with mixed content
- **AND** layout analysis is enabled
- **WHEN** processing the document
- **THEN** identifies text regions, image regions, and table regions
- **AND** extracts bounding box coordinates for each region
- **AND** assigns confidence scores to detections

#### Scenario: Extract embedded images from PDF
- **GIVEN** a PDF with embedded images
- **AND** layout analysis is enabled
- **WHEN** processing the PDF
- **THEN** extracts images as separate region entities
- **AND** saves extracted images to collection's extracted_images folder
- **AND** generates embeddings using vision encoder

#### Scenario: Preserve region spatial relationships
- **GIVEN** a document with multiple regions on a page
- **WHEN** layout analysis completes
- **THEN** metadata includes region positioning (top-left, center, etc.)
- **AND** includes region sequence/reading order
- **AND** identifies parent-child relationships (e.g., image caption)

#### Scenario: Fall back when layout analysis unavailable
- **GIVEN** deepdoctection is not installed
- **AND** layout analysis is requested
- **WHEN** loading a document
- **THEN** logs warning about missing dependency
- **AND** falls back to simple text extraction
- **AND** continues processing without error

#### Scenario: Disable layout analysis for performance
- **GIVEN** a collection with layout analysis disabled
- **WHEN** loading any document
- **THEN** uses simple text-only extraction
- **AND** completes processing faster than layout mode
- **AND** does not load layout analysis models

### Requirement: Region-Based Metadata
The system SHALL preserve region information in document metadata for retrieval context.

#### Scenario: Store semantic region metadata
- **GIVEN** a document processed with layout analysis
- **WHEN** storing chunks in vector database
- **THEN** each chunk includes region_type field
- **AND** includes page_number and region_sequence
- **AND** includes semantic tags and content structure
- **AND** includes extraction timestamp and model info

#### Scenario: Link extracted content to source
- **GIVEN** content extracted from a document
- **WHEN** storing the content embedding
- **THEN** metadata includes source document ID
- **AND** includes original page number
- **AND** includes markdown structure position
- **AND** includes semantic context (heading, section)

### Requirement: Semantic Region Metadata
The system SHALL store semantic metadata for content understanding and retrieval.

#### Scenario: Store semantic tags
- **GIVEN** a region extracted with layout analysis
- **WHEN** storing in vector database
- **THEN** includes semantic tags (e.g., "financial", "technical")
- **AND** includes markdown structure level
- **AND** includes content type (markdown/html/latex)

#### Scenario: Store table metadata
- **GIVEN** a table region
- **WHEN** storing in vector database
- **THEN** includes both HTML and markdown representations
- **AND** includes row and column counts
- **AND** includes header row detection flag

#### Scenario: Store image metadata
- **GIVEN** an image region with description
- **WHEN** storing in vector database
- **THEN** includes generated description text
- **AND** includes image type classification
- **AND** links to extracted image file if applicable

#### Scenario: Store equation metadata
- **GIVEN** an equation region
- **WHEN** storing in vector database
- **THEN** includes LaTeX representation
- **AND** includes equation type (inline/display)
- **AND** includes mathematical domain hints if detectable

### Requirement: Markdown-Based Content Parsing
The system SHALL parse structured markdown output into semantic regions.

#### Scenario: Parse markdown structure
- **GIVEN** markdown output from layout analysis
- **WHEN** parsing into regions
- **THEN** identifies major structural elements (headers, tables, images)
- **AND** extracts content while preserving formatting
- **AND** assigns unique IDs to each region

#### Scenario: Handle complex nested structures
- **GIVEN** markdown with nested lists and tables
- **WHEN** parsing into regions
- **THEN** correctly identifies nesting levels
- **AND** preserves parent-child relationships
- **AND** maintains reading order across nesting

#### Scenario: Validate parsed output
- **GIVEN** parsed semantic regions
- **WHEN** validation runs
- **THEN** ensures all regions have required fields
- **AND** validates content format matches region type
- **AND** checks for parsing errors and logs warnings

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

