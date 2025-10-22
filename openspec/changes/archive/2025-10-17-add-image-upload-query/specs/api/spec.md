# API Specification Deltas for Image Support

## ADDED Requirements

### Requirement: Image Upload Support
The system SHALL accept image files through the document upload endpoint.

#### Scenario: Upload single image
- **WHEN** POST /api/ingest/upload with .png, .jpg, .jpeg, or .webp file
- **THEN** validates image format and size
- **AND** returns task ID for tracking

#### Scenario: Upload multiple images
- **WHEN** POST /api/ingest/upload with multiple image files
- **THEN** queues all images for processing
- **AND** returns task ID with file list

#### Scenario: Reject unsupported image format
- **WHEN** uploading .tiff or .raw image file
- **THEN** returns 400 error with supported formats list
- **AND** does not create processing task

### Requirement: Image Search Endpoint
The system SHALL provide dedicated endpoint for image-based queries.

#### Scenario: Text-to-image search
- **WHEN** POST /api/search with query text and image_only=true filter
- **THEN** returns only image results
- **AND** ranks by semantic relevance to query text

#### Scenario: Image-to-image search
- **WHEN** POST /api/search/image with uploaded image
- **THEN** encodes query image using vision encoder
- **AND** returns visually similar images

#### Scenario: Image-to-text search
- **WHEN** POST /api/search/image with image and modality_filter="text"
- **THEN** returns text documents semantically related to image
- **AND** includes relevance scores

### Requirement: Image Metadata Response
The system SHALL include image-specific metadata in search results and status responses.

#### Scenario: Image result metadata
- **WHEN** search returns image results
- **THEN** includes width, height, format, file_size
- **AND** includes thumbnail_url for UI display

#### Scenario: Image ingestion status
- **WHEN** GET /api/ingest/status/{task_id} for image task
- **THEN** includes image-specific processing steps
- **AND** reports thumbnail generation status

### Requirement: Thumbnail Access
The system SHALL provide endpoints for accessing image thumbnails.

#### Scenario: Retrieve thumbnail
- **WHEN** GET /api/images/thumbnail/{collection}/{image_id}
- **THEN** returns 256x256 thumbnail image
- **AND** sets appropriate cache headers

#### Scenario: Retrieve full image
- **WHEN** GET /api/images/full/{collection}/{image_id}
- **THEN** returns original image file
- **AND** includes proper content-type header

## MODIFIED Requirements

### Requirement: Document Ingestion Endpoints
The system SHALL expose endpoints for document AND image upload and processing.

#### Scenario: Check supported formats (MODIFIED)
- **WHEN** GET /api/ingest/supported-formats
- **THEN** returns list including .png, .jpg, .jpeg, .webp
- **AND** specifies max image size (e.g., 20MB per image)

### Requirement: Search Endpoint
The system SHALL expose a search endpoint for semantic queries across ALL modalities.

#### Scenario: Mixed modality search (ADDED)
- **WHEN** POST /api/search without modality filter
- **THEN** returns both text and image results
- **AND** ranks by unified relevance score
- **AND** includes result_type field ("text" or "image")
