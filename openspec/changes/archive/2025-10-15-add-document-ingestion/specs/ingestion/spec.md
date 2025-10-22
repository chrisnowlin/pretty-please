## ADDED Requirements

### Requirement: Document Loading
The system SHALL load documents from various file formats into processable text.

#### Scenario: Load text file
- **WHEN** loading a .txt file
- **THEN** extracts full text content
- **AND** preserves encoding (UTF-8)

#### Scenario: Load PDF document
- **WHEN** loading a .pdf file
- **THEN** extracts text from all pages
- **AND** maintains page boundaries in metadata

#### Scenario: Handle unsupported format
- **WHEN** loading unsupported file type
- **THEN** raises clear error message
- **AND** suggests supported formats

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
The system SHALL process documents through a complete ingestion workflow.

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

### Requirement: Metadata Extraction
The system SHALL extract and preserve document metadata throughout processing.

#### Scenario: Extract file metadata
- **WHEN** processing any document
- **THEN** captures filename, path, size, modified date
- **AND** attaches to all chunks from that document

#### Scenario: Extract document properties
- **WHEN** document contains metadata (PDF, DOCX)
- **THEN** extracts title, author, creation date
- **AND** includes in chunk metadata

#### Scenario: Add custom metadata
- **WHEN** user provides additional metadata
- **THEN** merges with extracted metadata
- **AND** validates against schema

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