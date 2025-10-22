# API Specification Delta: Citation Source Linking

## MODIFIED Requirements

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

## ADDED Requirements

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
