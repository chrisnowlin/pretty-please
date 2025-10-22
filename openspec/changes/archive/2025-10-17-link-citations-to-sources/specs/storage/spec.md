# Storage Specification Delta: Document File Persistence

## ADDED Requirements

### Requirement: Persistent Document File Storage
The system SHALL store uploaded document files permanently on disk for citation linking and source verification.

#### Scenario: Store uploaded text document
- **WHEN** text document is uploaded and processed
- **THEN** saves original file to `./uploads/{collection}/documents/` directory
- **AND** uses UUID-based filename to prevent conflicts
- **AND** preserves original file extension
- **AND** stores `document_path` in chunk metadata

**Rationale**: Citations reference source documents. To display original content when users click citations, we must preserve the uploaded files, not just their embeddings. UUID-based naming prevents filename collisions and path traversal attacks.

#### Scenario: Store document path in metadata
- **WHEN** adding document chunks to vector store
- **THEN** includes `document_path` field in metadata
- **AND** includes `source` field with original filename
- **AND** includes `document_id` for correlation
- **AND** includes `upload_timestamp` for tracking

**Rationale**: Metadata linking enables retrieving the original document from disk when rendering citations. The `source` field provides user-friendly names while `document_path` provides the actual storage location.

#### Scenario: Handle duplicate document uploads
- **WHEN** same document uploaded multiple times
- **THEN** stores as separate files with unique UUIDs
- **AND** each upload gets distinct `document_id`
- **AND** deduplication handled at ingestion pipeline level (existing fingerprinting)

**Rationale**: Multiple uploads should create separate instances to support different collections or contexts. Existing fingerprinting in DocumentProcessor prevents redundant processing.

#### Scenario: Create collection-specific storage directories
- **WHEN** first document uploaded to collection
- **THEN** creates `./uploads/{collection}/documents/` directory
- **AND** creates `./uploads/{collection}/images/` directory (already implemented)
- **AND** creates `./uploads/{collection}/thumbnails/` directory (already implemented)
- **AND** sets appropriate file permissions

**Rationale**: Collection-scoped storage enables easy cleanup when collections deleted and isolates data between collections for access control.

### Requirement: Document Storage Directory Structure
The system SHALL organize stored documents in a consistent, secure directory hierarchy.

#### Scenario: Structure for text documents
- **WHEN** storing text documents
- **THEN** follows structure: `./uploads/{collection}/documents/{document_id}{extension}`
- **Example**: `./uploads/papers/documents/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf`
- **AND** mirrors structure of existing image storage
- **AND** uses same UUID scheme as `document_id` in metadata

**Rationale**: Consistent structure with existing image storage simplifies implementation and maintenance. UUID-based filenames prevent path traversal while maintaining extension for MIME type detection.

#### Scenario: Validate storage paths
- **WHEN** building document storage paths
- **THEN** validates collection name contains no path separators (`/`, `\`, `..`)
- **AND** validates filename is UUID with valid extension
- **AND** restricts access to `./uploads/` directory tree only
- **AND** returns error for invalid paths

**Rationale**: Path validation prevents directory traversal attacks and ensures documents stored only in intended locations.

### Requirement: Disk Space Management
The system SHALL provide visibility into storage utilization and support cleanup operations.

#### Scenario: Calculate collection storage size
- **WHEN** querying collection statistics
- **THEN** includes total disk usage for documents and images
- **AND** reports number of stored files
- **AND** reports largest files for cleanup decisions

**Rationale**: Administrators need visibility into disk usage to manage capacity and identify collections consuming excessive space.

#### Scenario: Clean up deleted collections
- **WHEN** collection is deleted from vector store
- **THEN** removes associated `./uploads/{collection}/` directory
- **AND** recursively deletes all documents, images, and thumbnails
- **AND** logs deletion for audit trail
- **AND** requires confirmation for non-empty collections

**Rationale**: Automatic cleanup prevents orphaned files and reclaims disk space. Confirmation prevents accidental data loss.

#### Scenario: Handle disk full conditions
- **WHEN** disk space exhausted during upload
- **THEN** returns clear error message
- **AND** suggests cleanup actions
- **AND** prevents partial writes
- **AND** maintains data consistency

**Rationale**: Graceful handling of disk full prevents corruption and provides actionable feedback to users.
