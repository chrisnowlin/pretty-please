# Spec Delta: API

## ADDED Requirements

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

## MODIFIED Requirements

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
