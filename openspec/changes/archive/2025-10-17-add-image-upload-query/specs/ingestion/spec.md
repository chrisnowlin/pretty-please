# Ingestion Specification Deltas for Image Support

## ADDED Requirements

### Requirement: Image Loading
The system SHALL load images from various image formats into processable Image objects.

#### Scenario: Load PNG image
- **WHEN** loading a .png file
- **THEN** creates PIL Image object
- **AND** converts to RGB if needed

#### Scenario: Load JPEG image
- **WHEN** loading a .jpg or .jpeg file
- **THEN** handles EXIF orientation
- **AND** preserves color profile metadata

#### Scenario: Load WebP image
- **WHEN** loading a .webp file
- **THEN** extracts image data
- **AND** converts to standard RGB format

#### Scenario: Validate image integrity
- **WHEN** loading corrupted image file
- **THEN** raises clear error message
- **AND** suggests file re-upload

### Requirement: Image Processing Pipeline
The system SHALL process images through a complete ingestion workflow.

#### Scenario: Process single image
- **WHEN** ingesting a new image file
- **THEN** loads, validates, generates embeddings
- **AND** stores in vector database with image metadata
- **AND** generates thumbnail for UI display

#### Scenario: Batch process image directory
- **WHEN** processing directory of images
- **THEN** processes all supported image files
- **AND** reports progress with preview thumbnails

#### Scenario: Handle image processing errors
- **WHEN** error occurs during image embedding
- **THEN** logs error with image identifier
- **AND** continues processing remaining images

### Requirement: Image Metadata Extraction
The system SHALL extract and preserve image-specific metadata throughout processing.

#### Scenario: Extract image dimensions
- **WHEN** processing any image
- **THEN** captures width, height, aspect_ratio
- **AND** attaches to embeddings metadata

#### Scenario: Extract EXIF metadata
- **WHEN** image contains EXIF data
- **THEN** extracts camera, timestamp, location (if present)
- **AND** includes in chunk metadata
- **AND** respects privacy settings for location data

#### Scenario: Compute image statistics
- **WHEN** processing image for embedding
- **THEN** calculates mean RGB values, color distribution
- **AND** stores in metadata for filtering/analysis

### Requirement: Thumbnail Generation
The system SHALL create optimized thumbnails for efficient UI display.

#### Scenario: Generate standard thumbnail
- **WHEN** ingesting any image
- **THEN** creates 256x256 thumbnail
- **AND** maintains aspect ratio with letterboxing/pillarboxing
- **AND** compresses with quality=85 for file size

#### Scenario: Cache thumbnail efficiently
- **WHEN** thumbnail is generated
- **THEN** stores in collection-specific cache directory
- **AND** uses content-addressed naming (hash-based)
- **AND** sets appropriate cache expiration

#### Scenario: Regenerate missing thumbnail
- **WHEN** thumbnail requested but not found
- **THEN** regenerates from original image
- **AND** updates cache atomically

### Requirement: Image File Management
The system SHALL manage image files with efficient storage and retrieval.

#### Scenario: Store original image
- **WHEN** image is ingested
- **THEN** saves to collection-specific directory
- **AND** uses UUID-based filename to avoid conflicts
- **AND** preserves original format and quality

#### Scenario: Link image to embeddings
- **WHEN** storing image embeddings
- **THEN** includes file path in metadata
- **AND** creates bidirectional reference (embedding ← → file)
- **AND** enables efficient retrieval by ID

## MODIFIED Requirements

### Requirement: Document Loading
The system SHALL load documents AND images from various file formats into processable objects.

#### Scenario: Handle unsupported format (MODIFIED)
- **WHEN** loading unsupported file type
- **THEN** raises clear error message
- **AND** suggests supported formats (including image formats)

### Requirement: Document Processing Pipeline
The system SHALL process documents AND images through a complete ingestion workflow.

#### Scenario: Process mixed content batch (ADDED)
- **WHEN** processing directory with text files and images
- **THEN** routes each file to appropriate loader (text vs image)
- **AND** generates embeddings using correct encoder
- **AND** reports unified progress across all file types
