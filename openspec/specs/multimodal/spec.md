# multimodal Specification

## Purpose
TBD - created by archiving change add-multimodal-support. Update Purpose after archive.
## Requirements
### Requirement: Image Embedding Generation
The system SHALL generate embeddings for images using Jina v4's visual encoder.

#### Scenario: Encode single image
- **WHEN** encoding an image file
- **THEN** generates embedding vector
- **AND** maintains visual semantic information

#### Scenario: Handle various image formats
- **WHEN** processing PNG, JPG, or WEBP images
- **THEN** successfully generates embeddings
- **AND** normalizes format differences internally

#### Scenario: Respect memory constraints
- **WHEN** processing large images
- **THEN** resizes within max_pixels limit
- **AND** preserves aspect ratio

### Requirement: Visual Document Processing
The system SHALL process documents containing visual elements.

#### Scenario: Process PDF with embedded images
- **GIVEN** a PDF with embedded images
- **AND** layout analysis is enabled
- **WHEN** ingesting the PDF
- **THEN** extracts both text and image regions separately
- **AND** generates text embeddings for text regions
- **AND** generates vision embeddings for image regions
- **AND** maintains document structure in metadata

#### Scenario: Handle mixed content documents
- **GIVEN** a document containing text and images
- **WHEN** processing with layout analysis
- **THEN** generates appropriate embeddings for each region type
- **AND** preserves spatial relationships between regions
- **AND** links regions to source document and page

### Requirement: Cross-Modal Search
The system SHALL support searching across different modalities.

#### Scenario: Text-to-image search
- **WHEN** searching with text query for images
- **THEN** returns relevant images
- **AND** ranks by semantic similarity

#### Scenario: Image-to-text search
- **WHEN** searching with image for text documents
- **THEN** returns semantically related texts
- **AND** bridges visual-textual gap

#### Scenario: Image-to-image similarity
- **WHEN** searching with image query
- **THEN** finds visually similar images
- **AND** captures semantic similarity beyond pixels

### Requirement: Multi-Vector Embeddings
The system SHALL support multi-vector representations for complex documents.

#### Scenario: Generate multi-vector embeddings
- **WHEN** return_multivector=True
- **THEN** returns multiple 128-dim vectors
- **AND** captures fine-grained semantics

#### Scenario: Late-interaction retrieval
- **WHEN** searching with multi-vector query
- **THEN** performs token-level matching
- **AND** achieves higher precision

### Requirement: Unified Search Interface
The system SHALL provide consistent search regardless of modality.

#### Scenario: Automatic modality detection
- **WHEN** receiving search query
- **THEN** detects input type automatically
- **AND** routes to appropriate encoder

#### Scenario: Mixed results presentation
- **WHEN** search returns multiple modalities
- **THEN** presents unified ranking
- **AND** indicates result type in metadata

### Requirement: Region-Based Multimodal Processing
The system SHALL process document regions with modality-appropriate encoders.

#### Scenario: Process text region with text encoder
- **GIVEN** a document region identified as text
- **WHEN** processing the region
- **THEN** uses Jina text encoder for embedding generation
- **AND** preserves region metadata (bbox, page, type)
- **AND** stores as text modality in vector database

#### Scenario: Process image region with vision encoder
- **GIVEN** a document region identified as image
- **WHEN** processing the region
- **THEN** uses Jina vision encoder for embedding generation
- **AND** saves extracted image to extracted_images folder
- **AND** stores as image modality with path reference

#### Scenario: Process table region with structured encoding
- **GIVEN** a document region identified as table
- **WHEN** processing the region
- **THEN** extracts table as HTML or structured format
- **AND** uses text encoder on structured representation
- **AND** preserves table structure in metadata

#### Scenario: Handle mixed regions on same page
- **GIVEN** a document page with text, image, and table regions
- **WHEN** processing the page
- **THEN** generates separate embeddings for each region
- **AND** maintains reading order/sequence in metadata
- **AND** links all regions to same source document and page

### Requirement: Embedded Image Extraction
The system SHALL extract images embedded within documents for separate encoding.

#### Scenario: Extract image from PDF page
- **GIVEN** a PDF page containing an embedded chart image
- **WHEN** processing with layout analysis enabled
- **THEN** detects image region boundaries
- **AND** extracts image to file in extracted_images folder
- **AND** generates embedding using vision encoder
- **AND** stores with reference to source document

#### Scenario: Extract multiple images from single page
- **GIVEN** a document page with multiple images
- **WHEN** processing the page
- **THEN** extracts each image separately
- **AND** assigns unique region sequence numbers
- **AND** preserves spatial relationships in metadata

#### Scenario: Skip image extraction when layout analysis disabled
- **GIVEN** layout analysis is disabled for collection
- **WHEN** processing document with embedded images
- **THEN** does not extract images
- **AND** processes only text content
- **AND** completes faster than layout mode

### Requirement: Cross-Modal Search with Regions
The system SHALL support searching for content within document regions.

#### Scenario: Search for image within documents
- **GIVEN** a text query describing visual content
- **WHEN** searching across collections
- **THEN** returns both standalone images and extracted document regions
- **AND** indicates whether result is standalone or extracted
- **AND** provides source document context for extracted regions

#### Scenario: Filter search by region type
- **GIVEN** a search query with region_type filter
- **WHEN** executing search
- **THEN** returns only results matching the specified region type
- **AND** supports filtering by "text", "image", "table", "title"

### Requirement: Vision Encoder Routing
The system SHALL route image content to appropriate models for embedding generation.

#### Scenario: Route semantic image regions
- **GIVEN** an image region with generated description
- **WHEN** generating embeddings
- **THEN** uses Jina v4 vision encoder for image
- **AND** uses text encoder for description
- **AND** stores both embeddings for multimodal retrieval
- **AND** links image and description in metadata

#### Scenario: Handle image without description
- **GIVEN** an extracted image without description
- **WHEN** generating embeddings
- **THEN** uses vision encoder only
- **AND** includes placeholder description in metadata
- **AND** marks as "description_unavailable"

