# Frontend Specification Deltas for Image Support

## ADDED Requirements

### Requirement: Image Upload Interface
The system SHALL provide visual interface for uploading images with preview.

#### Scenario: Display image preview on selection
- **WHEN** user selects image files for upload
- **THEN** displays thumbnail previews in upload queue
- **AND** shows filename, size, and format

#### Scenario: Drag and drop images
- **WHEN** user drags image files to upload zone
- **THEN** highlights drop zone with visual feedback
- **AND** shows image previews after drop

#### Scenario: Validate image before upload
- **WHEN** user selects invalid image file
- **THEN** displays error message with reason
- **AND** prevents upload to backend

#### Scenario: Show image upload progress
- **WHEN** images are being uploaded
- **THEN** displays progress bar for each image
- **AND** shows thumbnail with processing status overlay

### Requirement: Image Search Interface
The system SHALL enable users to search using images as queries.

#### Scenario: Upload image for query
- **WHEN** user clicks "Search by Image" button
- **THEN** opens file picker for image selection
- **AND** encodes and sends image to search endpoint

#### Scenario: Paste image from clipboard
- **WHEN** user pastes image into search box
- **THEN** displays pasted image thumbnail
- **AND** enables "Search" action with image query

#### Scenario: Query by example
- **WHEN** user clicks "Find Similar" on image result
- **THEN** uses that image as new search query
- **AND** returns visually similar results

### Requirement: Image Results Display
The system SHALL display image search results with visual previews and metadata.

#### Scenario: Display image thumbnail in results
- **WHEN** search returns image results
- **THEN** shows thumbnail with hover zoom
- **AND** displays relevance score and metadata overlay

#### Scenario: Full-size image preview
- **WHEN** user clicks on image thumbnail
- **THEN** opens modal with full-size image
- **AND** shows complete metadata (dimensions, format, score)
- **AND** provides "Find Similar" and "Download" actions

#### Scenario: Mixed results presentation
- **WHEN** search returns both text and images
- **THEN** displays unified list with clear type indicators
- **AND** uses distinct card styles (text vs image)
- **AND** allows filtering by result type

#### Scenario: Image grid view
- **WHEN** user switches to grid view mode
- **THEN** displays image results in responsive grid
- **AND** shows text results in list below
- **AND** enables masonry layout for varying image sizes

### Requirement: Image Metadata Display
The system SHALL present image properties and technical details to users.

#### Scenario: Show image properties in result card
- **WHEN** displaying image result
- **THEN** shows dimensions, format, file size
- **AND** displays semantic relevance score

#### Scenario: Display color information
- **WHEN** user hovers over image result
- **THEN** shows dominant colors as palette
- **AND** displays RGB statistics in tooltip

### Requirement: Image Query Visualization
The system SHALL provide visual feedback for image-based searches.

#### Scenario: Show query image in search bar
- **WHEN** performing image-based search
- **THEN** displays query image thumbnail in search bar
- **AND** allows user to clear or replace query image

#### Scenario: Compare query to results
- **WHEN** viewing image search results
- **THEN** keeps query image visible for comparison
- **AND** highlights visual similarities with annotations

## MODIFIED Requirements

### Requirement: Upload Zone Display
The system SHALL provide visual interface for uploading documents AND images with appropriate previews.

#### Scenario: Display file type icons (MODIFIED)
- **WHEN** user adds files to upload queue
- **THEN** shows appropriate icon for file type (document icon for text, thumbnail for images)
- **AND** indicates processing requirements

### Requirement: Progress Tracker Display
The system SHALL display real-time processing status for documents AND images.

#### Scenario: Show processing stages (MODIFIED)
- **WHEN** tracking ingestion progress
- **THEN** shows stage-specific status (for images: validation → embedding → thumbnail → complete)
- **AND** estimates remaining time per file type

### Requirement: Search Results Display
The system SHALL display search results for ALL content types with appropriate formatting.

#### Scenario: Result type indicators (ADDED)
- **WHEN** displaying mixed search results
- **THEN** shows clear visual indicator for each type (text icon, image icon)
- **AND** uses color-coding or backgrounds to distinguish types
