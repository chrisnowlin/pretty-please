# Spec Delta: Ingestion

## ADDED Requirements

### Requirement: PowerPoint Document Loading
The system SHALL load PowerPoint presentations and extract content for embedding.

#### Scenario: Load PPTX file with text only
- **GIVEN** a PowerPoint file with text-only slides
- **WHEN** loading the .pptx file
- **THEN** extracts text from all slides
- **AND** preserves slide boundaries in metadata
- **AND** includes slide numbers with each text block

#### Scenario: Load PPTX with layout analysis enabled
- **GIVEN** a PowerPoint file with mixed text and images
- **AND** layout analysis is enabled for the collection
- **WHEN** loading the .pptx file
- **THEN** extracts both text and image regions
- **AND** preserves spatial relationships in metadata
- **AND** saves extracted images to extracted_images directory

#### Scenario: Load legacy PPT format
- **GIVEN** a legacy .ppt format file
- **WHEN** loading the file
- **THEN** converts to processable format
- **AND** extracts content same as .pptx
- **OR** provides clear error if conversion not supported

#### Scenario: Handle PowerPoint with speaker notes
- **GIVEN** a PowerPoint with speaker notes
- **WHEN** loading with simple mode
- **THEN** extracts slide text only (notes optional)
- **AND** includes notes in metadata if present

### Requirement: Document Layout Analysis
The system SHALL optionally analyze document layout to identify regions (text, images, tables).

#### Scenario: Analyze document layout
- **GIVEN** a document with mixed content
- **AND** layout analysis is enabled
- **WHEN** processing the document
- **THEN** identifies text regions, image regions, and table regions
- **AND** extracts bounding box coordinates for each region
- **AND** assigns confidence scores to detections

#### Scenario: Extract embedded images from PDF
- **GIVEN** a PDF with embedded images
- **AND** layout analysis is enabled
- **WHEN** processing the PDF
- **THEN** extracts images as separate region entities
- **AND** saves extracted images to collection's extracted_images folder
- **AND** generates embeddings using vision encoder

#### Scenario: Preserve region spatial relationships
- **GIVEN** a document with multiple regions on a page
- **WHEN** layout analysis completes
- **THEN** metadata includes region positioning (top-left, center, etc.)
- **AND** includes region sequence/reading order
- **AND** identifies parent-child relationships (e.g., image caption)

#### Scenario: Fall back when layout analysis unavailable
- **GIVEN** deepdoctection is not installed
- **AND** layout analysis is requested
- **WHEN** loading a document
- **THEN** logs warning about missing dependency
- **AND** falls back to simple text extraction
- **AND** continues processing without error

#### Scenario: Disable layout analysis for performance
- **GIVEN** a collection with layout analysis disabled
- **WHEN** loading any document
- **THEN** uses simple text-only extraction
- **AND** completes processing faster than layout mode
- **AND** does not load layout analysis models

### Requirement: Region-Based Metadata
The system SHALL preserve region information in document metadata for retrieval context.

#### Scenario: Store region metadata
- **GIVEN** a document processed with layout analysis
- **WHEN** storing chunks in vector database
- **THEN** each chunk includes region_type field
- **AND** includes page_number and region_sequence
- **AND** includes bounding box coordinates
- **AND** includes confidence score from detection

#### Scenario: Link extracted images to source document
- **GIVEN** an image extracted from a document
- **WHEN** storing the image embedding
- **THEN** metadata includes source document ID
- **AND** includes original page number
- **AND** includes path to extracted image file
- **AND** includes bounding box in source document

## MODIFIED Requirements

### Requirement: Document Loading
The system SHALL load documents from various file formats into processable text.

#### Scenario: Load PowerPoint file
- **GIVEN** a .pptx or .ppt file
- **WHEN** loading the file
- **THEN** extracts text and optionally images based on configuration
- **AND** preserves slide structure in metadata

### Requirement: Metadata Extraction
The system SHALL extract and preserve document metadata throughout processing.

#### Scenario: Extract PowerPoint metadata
- **GIVEN** a PowerPoint file with properties
- **WHEN** processing the file
- **THEN** extracts title, author, creation date
- **AND** includes slide count and presentation metadata
- **AND** includes per-slide metadata (slide number, title)

#### Scenario: Add region metadata
- **GIVEN** a document processed with layout analysis
- **WHEN** creating chunk metadata
- **THEN** includes region information (type, bbox, confidence)
- **AND** merges with existing document metadata
- **AND** validates region metadata schema
