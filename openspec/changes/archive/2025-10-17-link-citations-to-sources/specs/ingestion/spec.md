# Ingestion Specification Delta: Document Persistence During Processing

## MODIFIED Requirements

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

## ADDED Requirements

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
