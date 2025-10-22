# API Specification

## MODIFIED Requirements

### Requirement: API Server
The system SHALL provide a FastAPI-based REST API server for query operations.

#### Scenario: Serve static frontend files
- **WHEN** accessing root path /
- **THEN** serves frontend application
- **AND** handles client-side routing

## ADDED Requirements

### Requirement: Document Ingestion Endpoints
The system SHALL expose endpoints for document upload and processing.

#### Scenario: Upload single document
- **WHEN** POST /api/ingest/upload with file
- **THEN** validates file type and size
- **AND** returns task ID for tracking

#### Scenario: Upload multiple documents
- **WHEN** POST /api/ingest/upload with multiple files
- **THEN** queues all files for processing
- **AND** returns task ID with file list

#### Scenario: Check ingestion status
- **WHEN** GET /api/ingest/status/{task_id}
- **THEN** returns current processing status
- **AND** includes progress percentage

#### Scenario: List supported formats
- **WHEN** GET /api/ingest/supported-formats
- **THEN** returns list of accepted file types
- **AND** includes size limits

### Requirement: WebSocket Support
The system SHALL provide WebSocket connections for real-time updates.

#### Scenario: Establish progress connection
- **WHEN** connecting to /ws/progress/{task_id}
- **THEN** establishes WebSocket connection
- **AND** sends initial status message

#### Scenario: Send progress updates
- **WHEN** document processing progresses
- **THEN** sends progress messages
- **AND** includes current file and percentage

#### Scenario: Handle disconnection
- **WHEN** WebSocket connection drops
- **THEN** cleans up resources
- **AND** allows reconnection

### Requirement: Async Task Processing
The system SHALL process document ingestion asynchronously.

#### Scenario: Queue ingestion task
- **WHEN** documents are uploaded
- **THEN** adds to background task queue
- **AND** returns immediately with task ID

#### Scenario: Process task in background
- **WHEN** task reaches front of queue
- **THEN** processes documents sequentially
- **AND** updates progress in real-time

#### Scenario: Handle task failure
- **WHEN** processing error occurs
- **THEN** marks task as failed
- **AND** preserves error details

### Requirement: File Validation
The system SHALL validate uploaded files before processing.

#### Scenario: Validate file type
- **WHEN** file is uploaded
- **THEN** checks against supported formats
- **AND** rejects unsupported types

#### Scenario: Validate file size
- **WHEN** file exceeds size limit
- **THEN** returns 413 error
- **AND** suggests file size limit

#### Scenario: Validate file content
- **WHEN** file appears corrupted
- **THEN** returns validation error
- **AND** suggests re-upload