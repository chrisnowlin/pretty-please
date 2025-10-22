# Spec Delta: Multimodal

## ADDED Requirements

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

## MODIFIED Requirements

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
