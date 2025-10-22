# Spec Delta: Ingestion

## MODIFIED Requirements

### Requirement: Document Layout Analysis
The system SHALL use semantic layout analysis to identify and extract content regions.

#### Scenario: Analyze document layout with semantic understanding
- **GIVEN** a document with mixed content
- **AND** layout analysis is enabled
- **WHEN** processing the document
- **THEN** extracts semantic regions (text, tables, images, equations)
- **AND** preserves content structure in markdown format
- **AND** generates rich metadata for each region type

#### Scenario: Extract tables with full structure
- **GIVEN** a document with tables
- **AND** layout analysis is enabled
- **WHEN** processing the document
- **THEN** extracts tables in both HTML and markdown format
- **AND** preserves cell content, headers, and structure
- **AND** includes row and column counts in metadata

#### Scenario: Recognize mathematical equations
- **GIVEN** a document with mathematical notation
- **AND** layout analysis is enabled
- **WHEN** processing the document
- **THEN** extracts equations in LaTeX format
- **AND** distinguishes inline ($...$) from display ($$...$$) equations
- **AND** creates separate regions for complex equations

#### Scenario: Generate image descriptions
- **GIVEN** a document with embedded images
- **AND** layout analysis is enabled
- **WHEN** processing the document
- **THEN** generates natural language descriptions of images
- **AND** classifies image types (logo, chart, diagram, photo)
- **AND** includes descriptions in region metadata

#### Scenario: Preserve semantic structure
- **GIVEN** a document with hierarchical content
- **WHEN** layout analysis completes
- **THEN** preserves heading levels (H1-H6) in metadata
- **AND** maintains list structure (ordered/unordered)
- **AND** identifies text blocks by semantic role

#### Scenario: Handle multilingual documents
- **GIVEN** a document in non-English language
- **AND** layout analysis is enabled
- **WHEN** processing the document
- **THEN** correctly extracts text in the source language
- **AND** maintains character encoding and diacritics
- **AND** supports 12+ languages including CJK

#### Scenario: Process handwritten content
- **GIVEN** a document with handwritten text
- **AND** layout analysis is enabled
- **WHEN** processing the document
- **THEN** attempts to extract handwritten text
- **AND** includes confidence scores for handwriting recognition
- **OR** gracefully handles unrecognizable handwriting

#### Scenario: Detect special elements
- **GIVEN** a document with checkboxes, signatures, or watermarks
- **WHEN** layout analysis processes the document
- **THEN** identifies checkboxes with state (☐, ☑, ☒)
- **AND** detects signatures and wraps in <signature> tags
- **AND** extracts watermarks and wraps in <watermark> tags

#### Scenario: Fall back when model unavailable
- **GIVEN** Nanonets model is not installed or failed to load
- **AND** layout analysis is requested
- **WHEN** loading a document
- **THEN** logs warning about missing model
- **AND** falls back to simple text extraction
- **AND** continues processing without error

#### Scenario: Use clean dependencies
- **GIVEN** system is configured for layout analysis
- **WHEN** initializing the analyzer
- **THEN** loads model using transformers library only
- **AND** requires no runtime code patching
- **AND** handles all errors gracefully with clear messages

## ADDED Requirements

### Requirement: Semantic Region Metadata
The system SHALL store semantic metadata for content understanding and retrieval.

#### Scenario: Store semantic tags
- **GIVEN** a region extracted with layout analysis
- **WHEN** storing in vector database
- **THEN** includes semantic tags (e.g., "financial", "technical")
- **AND** includes markdown structure level
- **AND** includes content type (markdown/html/latex)

#### Scenario: Store table metadata
- **GIVEN** a table region
- **WHEN** storing in vector database
- **THEN** includes both HTML and markdown representations
- **AND** includes row and column counts
- **AND** includes header row detection flag

#### Scenario: Store image metadata
- **GIVEN** an image region with description
- **WHEN** storing in vector database
- **THEN** includes generated description text
- **AND** includes image type classification
- **AND** links to extracted image file if applicable

#### Scenario: Store equation metadata
- **GIVEN** an equation region
- **WHEN** storing in vector database
- **THEN** includes LaTeX representation
- **AND** includes equation type (inline/display)
- **AND** includes mathematical domain hints if detectable

### Requirement: Markdown-Based Content Parsing
The system SHALL parse structured markdown output into semantic regions.

#### Scenario: Parse markdown structure
- **GIVEN** markdown output from layout analysis
- **WHEN** parsing into regions
- **THEN** identifies major structural elements (headers, tables, images)
- **AND** extracts content while preserving formatting
- **AND** assigns unique IDs to each region

#### Scenario: Handle complex nested structures
- **GIVEN** markdown with nested lists and tables
- **WHEN** parsing into regions
- **THEN** correctly identifies nesting levels
- **AND** preserves parent-child relationships
- **AND** maintains reading order across nesting

#### Scenario: Validate parsed output
- **GIVEN** parsed semantic regions
- **WHEN** validation runs
- **THEN** ensures all regions have required fields
- **AND** validates content format matches region type
- **AND** checks for parsing errors and logs warnings

## MODIFIED Requirements

### Requirement: Region-Based Metadata
The system SHALL preserve region information in document metadata for retrieval context.

#### Scenario: Store semantic region metadata
- **GIVEN** a document processed with layout analysis
- **WHEN** storing chunks in vector database
- **THEN** each chunk includes region_type field
- **AND** includes page_number and region_sequence
- **AND** includes semantic tags and content structure
- **AND** includes extraction timestamp and model info

#### Scenario: Link extracted content to source
- **GIVEN** content extracted from a document
- **WHEN** storing the content embedding
- **THEN** metadata includes source document ID
- **AND** includes original page number
- **AND** includes markdown structure position
- **AND** includes semantic context (heading, section)
