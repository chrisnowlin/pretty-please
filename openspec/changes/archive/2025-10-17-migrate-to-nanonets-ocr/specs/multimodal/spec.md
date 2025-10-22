# Spec Delta: Multimodal

## ADDED Requirements

### Requirement: Vision-Language Model Integration
The system SHALL use vision-language models for rich multimodal understanding.

#### Scenario: Load VLM model for document processing
- **GIVEN** layout analysis is enabled
- **WHEN** initializing the document processor
- **THEN** loads Nanonets-OCR2-3B model
- **AND** configures for M4 Max (MPS device)
- **AND** uses BFloat16 precision for memory efficiency
- **AND** enables Flash Attention 2 if available

#### Scenario: Process image with VLM
- **GIVEN** a document image (slide, PDF page)
- **WHEN** VLM processes the image
- **THEN** generates structured markdown output
- **AND** includes semantic understanding of content
- **AND** provides confidence scores where applicable

#### Scenario: Handle VLM inference errors
- **GIVEN** VLM model loaded successfully
- **WHEN** inference fails for an image
- **THEN** logs error with image details
- **AND** falls back to simpler extraction method
- **AND** continues processing remaining images

### Requirement: Image Description Generation
The system SHALL generate natural language descriptions of images using the VLM.

#### Scenario: Describe chart or graph
- **GIVEN** an image containing a chart or graph
- **WHEN** VLM processes the image
- **THEN** generates description of chart type
- **AND** describes key data points and trends
- **AND** includes axis labels and legend information
- **AND** wraps description in <img></img> tags

#### Scenario: Describe diagram or flowchart
- **GIVEN** an image containing a diagram
- **WHEN** VLM processes the image
- **THEN** describes diagram components
- **AND** explains relationships and flow
- **AND** identifies diagram type (flowchart, architecture, etc.)

#### Scenario: Describe logo or branding
- **GIVEN** an image containing a logo
- **WHEN** VLM processes the image
- **THEN** identifies it as a logo
- **AND** describes visual characteristics
- **AND** may include brand name if recognizable

#### Scenario: Handle unclear images
- **GIVEN** an image with low quality or unclear content
- **WHEN** VLM processes the image
- **THEN** generates best-effort description
- **AND** includes confidence qualifier ("appears to be")
- **AND** does not hallucinate unverified details

### Requirement: Multilingual Content Recognition
The system SHALL recognize and extract text in multiple languages.

#### Scenario: Process CJK (Chinese, Japanese, Korean) documents
- **GIVEN** a document with CJK characters
- **WHEN** VLM processes the document
- **THEN** correctly extracts CJK text
- **AND** preserves character encoding
- **AND** maintains reading direction

#### Scenario: Process RTL (Right-to-Left) languages
- **GIVEN** a document with Arabic or Hebrew text
- **WHEN** VLM processes the document
- **THEN** correctly extracts RTL text
- **AND** preserves text direction in metadata
- **AND** maintains bidirectional text handling

#### Scenario: Process mixed-language documents
- **GIVEN** a document with multiple languages
- **WHEN** VLM processes the document
- **THEN** correctly identifies each language segment
- **AND** preserves all language content
- **AND** may include language tags in metadata

### Requirement: Handwriting Recognition
The system SHALL attempt to recognize and extract handwritten text.

#### Scenario: Extract clear handwriting
- **GIVEN** a document with clear, legible handwriting
- **WHEN** VLM processes the document
- **THEN** extracts handwritten text
- **AND** includes confidence scores
- **AND** marks as handwritten in metadata

#### Scenario: Handle illegible handwriting
- **GIVEN** a document with illegible handwriting
- **WHEN** VLM processes the document
- **THEN** marks region as handwritten but unreadable
- **AND** logs low confidence score
- **AND** does not attempt to guess content

## ADDED Requirements

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
