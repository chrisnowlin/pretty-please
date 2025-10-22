# api Specification

## Purpose
TBD - created by archiving change add-query-interface. Update Purpose after archive.
## Requirements
### Requirement: API Server
The system SHALL provide a FastAPI-based REST API server for query operations.

#### Scenario: Serve static frontend files
- **WHEN** accessing root path /
- **THEN** serves frontend application
- **AND** handles client-side routing

### Requirement: Search Endpoint
The system SHALL expose a search endpoint for semantic queries.

#### Scenario: Execute basic search
- **WHEN** POST /search with query text
- **THEN** returns top-k similar documents
- **AND** includes relevance scores

#### Scenario: Search with filters
- **WHEN** search includes metadata filters
- **THEN** returns only matching documents
- **AND** maintains relevance ordering

#### Scenario: Handle empty results
- **WHEN** no documents match query
- **THEN** returns empty result array
- **AND** includes search metadata

### Requirement: Response Format
The system SHALL return structured responses with appropriate metadata.

#### Scenario: Search response includes region metadata
- **GIVEN** a successful search with results from layout-analyzed documents
- **WHEN** returning search results
- **THEN** each result includes region metadata when available
- **AND** preserves all region fields (type, bbox, confidence)
- **AND** includes image_path for extracted images

#### Scenario: Ingestion status includes region statistics
- **GIVEN** checking status of layout-analyzed document
- **WHEN** GET /api/ingest/status/{task_id}
- **THEN** includes regions_extracted count
- **AND** includes breakdown by region type
- **AND** includes processing mode (simple vs layout)

### Requirement: Health Monitoring
The system SHALL provide health and monitoring endpoints.

#### Scenario: Health check
- **WHEN** GET /health is called
- **THEN** returns service status
- **AND** includes component health states

#### Scenario: Statistics endpoint
- **WHEN** GET /stats is called
- **THEN** returns system statistics
- **AND** includes collection counts and sizes

### Requirement: Query Caching
The system SHALL cache frequently accessed query results.

#### Scenario: Cache hit
- **WHEN** identical query is repeated
- **THEN** returns cached results
- **AND** reduces response time significantly

#### Scenario: Cache invalidation
- **WHEN** underlying data changes
- **THEN** invalidates affected cache entries
- **AND** ensures fresh results on next query

### Requirement: Rate Limiting
The system SHALL implement rate limiting to prevent abuse.

#### Scenario: Within rate limit
- **WHEN** requests are within limit
- **THEN** processes normally
- **AND** returns results without delay

#### Scenario: Exceed rate limit
- **WHEN** client exceeds rate limit
- **THEN** returns 429 status code
- **AND** includes retry-after header

### Requirement: Document Ingestion Endpoints
The system SHALL provide endpoints for uploading and processing documents.

#### Scenario: Upload PowerPoint file
- **GIVEN** a valid .pptx or .ppt file
- **WHEN** POST /api/ingest/upload with PowerPoint file
- **THEN** accepts the file for processing
- **AND** returns task ID for status tracking
- **AND** processes based on collection's layout analysis settings

#### Scenario: List supported formats includes PowerPoint
- **GIVEN** API is running
- **WHEN** GET /api/ingest/formats
- **THEN** returns list including .pptx and .ppt
- **AND** indicates whether layout analysis is available
- **AND** shows format-specific capabilities

### Requirement: WebSocket Support
The system SHALL provide WebSocket connections for real-time updates **and citation source metadata**.

#### Scenario: Send progress updates
- **WHEN** document processing progresses
- **THEN** sends progress messages
- **AND** includes current file and percentage

#### Scenario: Handle disconnection
- **WHEN** WebSocket connection drops
- **THEN** cleans up resources
- **AND** allows reconnection

#### Scenario: Include citation map in context messages
- **WHEN** sending context message via WebSocket
- **THEN** includes citation_map field with citation ID to source metadata mapping
- **AND** citation IDs match those used in formatted context text
- **AND** each citation includes source, type (text/image), score, and metadata

**Rationale**: Enables frontend to render citations as interactive links to source material. Citation map provides necessary metadata to display source documents and images when users click citation markers.

#### Scenario: Provide complete source metadata for text citations
- **WHEN** citation_map includes text citation (e.g., "[1]")
- **THEN** metadata includes source document name
- **AND** includes relevance score
- **AND** includes document content from search results
- **AND** includes any additional metadata (page numbers, timestamps, etc.)

**Rationale**: Text citations need complete document information to display in source viewer, including the actual content and contextual metadata.

#### Scenario: Provide complete source metadata for image citations
- **WHEN** citation_map includes image citation (e.g., "[IMG-1]")
- **THEN** metadata includes document_id for reference
- **AND** includes thumbnail_url and full_image_url
- **AND** includes image dimensions (width, height)
- **AND** includes file metadata (filename, format, file_size)
- **AND** includes description and mean RGB values

**Rationale**: Image citations require URLs and metadata to display images in source viewer with proper attribution and preview capabilities.

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

### Requirement: Document File Serving
The system SHALL provide secure endpoints to retrieve stored document files for citation viewing.

#### Scenario: Serve text document by ID
- **WHEN** GET /api/documents/{collection}/{filename}
- **THEN** validates collection name and filename
- **AND** prevents path traversal attacks using `safe_filename()`
- **AND** restricts access to `./uploads/{collection}/documents/` only
- **AND** returns document with correct Content-Type header
- **AND** includes Cache-Control and ETag headers for efficiency

**Rationale**: Citation links need to retrieve original documents. Security validation prevents directory traversal. Caching headers improve performance for repeated access.

#### Scenario: Handle missing document gracefully
- **WHEN** requested document file not found
- **THEN** returns 404 Not Found with clear message
- **AND** suggests document may have been uploaded before persistence feature
- **AND** includes document_id in error for debugging

**Rationale**: Documents uploaded before this feature won't have stored files. Clear error enables frontend to fall back to chunk text display.

#### Scenario: Determine Content-Type from extension
- **WHEN** serving document file
- **THEN** sets Content-Type based on file extension
- **Example**: `.pdf` → `application/pdf`, `.txt` → `text/plain`, `.md` → `text/markdown`
- **AND** defaults to `application/octet-stream` for unknown types
- **AND** includes `Content-Disposition: inline` for browser preview

**Rationale**: Correct MIME types enable browser to display PDFs inline, syntax highlight code files, and render markdown. Inline disposition previews documents without downloading.

#### Scenario: Implement range requests for large PDFs
- **WHEN** client requests byte range (Range header)
- **THEN** returns 206 Partial Content with requested bytes
- **AND** includes Content-Range header
- **AND** supports PDF streaming for large files

**Rationale**: Range requests enable efficient PDF viewing without downloading entire file. Critical for multi-megabyte documents.

#### Scenario: Apply rate limiting to document endpoint
- **WHEN** client exceeds request limit for document downloads
- **THEN** returns 429 Too Many Requests
- **AND** includes Retry-After header
- **AND** logs suspicious activity

**Rationale**: Prevents abuse, DoS attacks, and excessive bandwidth usage from automated scraping.

### Requirement: Collection Configuration Management
The system SHALL provide endpoints to manage collection-specific configuration.

#### Scenario: Get collection configuration
- **GIVEN** a collection exists
- **WHEN** GET /api/collections/{name}/config
- **THEN** returns current configuration including layout_analysis settings
- **AND** includes enable_layout_analysis boolean
- **AND** includes layout_ocr_enabled boolean
- **AND** includes layout_table_extraction boolean

#### Scenario: Update collection configuration
- **GIVEN** a collection exists
- **WHEN** PUT /api/collections/{name}/config with new settings
- **THEN** validates configuration schema
- **AND** saves configuration to collection's config.json file
- **AND** returns updated configuration
- **AND** applies settings to future document processing

#### Scenario: Create collection with configuration
- **GIVEN** creating a new collection
- **WHEN** POST /api/collections with config parameter
- **THEN** creates collection with specified configuration
- **AND** validates config before creation
- **AND** saves config to collection directory

#### Scenario: Invalid configuration
- **GIVEN** invalid configuration values
- **WHEN** updating collection config
- **THEN** returns 400 Bad Request
- **AND** provides clear validation error messages
- **AND** does not modify existing configuration

### Requirement: Layout Analysis Status
The system SHALL provide information about layout analysis capabilities.

#### Scenario: Check layout analysis availability
- **GIVEN** API server is running
- **WHEN** GET /api/capabilities
- **THEN** returns whether deepdoctection is installed
- **AND** indicates layout analysis availability
- **AND** lists available layout models

#### Scenario: Processing with layout analysis status
- **GIVEN** a document being processed with layout analysis
- **WHEN** GET /api/ingest/status/{task_id}
- **THEN** includes layout_analysis_enabled in response
- **AND** includes count of regions extracted
- **AND** reports region types detected (text/image/table)

### Requirement: Region Metadata in Search Results
The system SHALL include region information in search responses when available.

#### Scenario: Search results include region metadata
- **GIVEN** searching a collection with layout-analyzed documents
- **WHEN** performing search
- **THEN** results include region_type field when available
- **AND** includes page_number and bbox when available
- **AND** includes image_path for image regions
- **AND** distinguishes standalone vs extracted images

#### Scenario: Filter results by region type
- **GIVEN** a search query
- **WHEN** including region_type filter parameter
- **THEN** returns only results matching specified region type
- **AND** supports values: text, image, table, title, list
- **AND** returns 400 for invalid region types

