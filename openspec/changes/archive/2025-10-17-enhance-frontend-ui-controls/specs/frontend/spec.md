# frontend Specification Deltas

## ADDED Requirements

### Requirement: RAG Configuration Settings
The system SHALL provide a user interface for viewing and updating global RAG configuration.

#### Scenario: Access RAG configuration settings
- **WHEN** user navigates to settings page
- **THEN** displays RAG configuration tab
- **AND** shows current retrieval, reranking, and citation settings

#### Scenario: Update retrieval batch size
- **WHEN** user changes initial_retrieval_k value
- **THEN** validates value is between 1 and 50
- **AND** sends PUT request to /api/config/rag
- **AND** updates UI optimistically

#### Scenario: Toggle reranking feature
- **WHEN** user toggles enable_reranking checkbox
- **THEN** immediately updates backend configuration
- **AND** shows/hides rerank model selection dropdown
- **AND** displays rerank_top_n slider when enabled

#### Scenario: Configure hybrid search
- **WHEN** user enables hybrid search
- **THEN** displays hybrid_alpha slider (0-1)
- **AND** shows tooltip explaining semantic vs keyword weighting
- **AND** saves configuration on change

#### Scenario: Select citation style
- **WHEN** user selects citation style dropdown
- **THEN** shows options: numbered, inline, footnote
- **AND** updates configuration
- **AND** applies to new chat sessions

#### Scenario: Configuration validation error
- **WHEN** user enters invalid value (e.g., initial_retrieval_k > 50)
- **THEN** shows inline error message
- **AND** disables save button
- **AND** highlights invalid field

#### Scenario: Configuration update failure
- **WHEN** PUT /api/config/rag fails
- **THEN** reverts UI to previous values
- **AND** displays error toast with message
- **AND** provides retry action button

**Rationale**: Global RAG configuration affects retrieval quality across all sessions. Users need UI access to tune parameters without modifying backend config files.

### Requirement: Advanced Session Configuration
The system SHALL allow users to configure advanced generation and RAG parameters when creating chat sessions.

#### Scenario: Expand advanced session options
- **WHEN** user clicks "Advanced Settings" in session setup
- **THEN** displays collapsible section with generation parameters
- **AND** shows temperature slider (0-2)
- **AND** shows top_p slider (0-1)
- **AND** shows top_k input (min 1)
- **AND** shows max_history_turns input (min 1)

#### Scenario: Configure thinking mode
- **WHEN** user toggles thinking mode checkbox
- **THEN** adjusts default temperature and top_p for thinking mode
- **AND** updates max_tokens recommendation
- **AND** shows explanation of thinking mode benefits

#### Scenario: Override RAG settings per session
- **WHEN** user expands "Retrieval Settings" in advanced options
- **THEN** shows "Use global settings" checkbox (checked by default)
- **AND** when unchecked, displays session-specific RAG config fields
- **AND** pre-fills with current global config values

#### Scenario: Create session with custom configuration
- **WHEN** user creates session with advanced settings
- **THEN** merges custom config with defaults
- **THEN** sends POST /api/chat/session with config object
- **AND** creates session with customized GenerationConfig
- **AND** displays active config summary in chat header

#### Scenario: Reset to defaults
- **WHEN** user clicks "Reset to Defaults" in advanced settings
- **THEN** restores all fields to default values
- **AND** checks "Use global settings" for RAG config
- **AND** updates generation params to non-thinking mode defaults

**Rationale**: Advanced users need fine-grained control over generation behavior for experimentation and optimization. Progressive disclosure keeps UI simple for casual users.

### Requirement: Collection Configuration Management
The system SHALL provide UI for managing collection-specific configuration including layout analysis settings.

#### Scenario: View collection configuration
- **WHEN** user navigates to Collections tab in settings
- **THEN** displays list of all collections
- **AND** shows "Configure" button for each collection
- **AND** displays current layout analysis status badge

#### Scenario: Edit layout analysis settings
- **WHEN** user clicks Configure on a collection
- **THEN** opens collection config panel
- **AND** displays enable_layout_analysis toggle
- **AND** shows layout_ocr_enabled toggle (when layout analysis enabled)
- **AND** shows layout_table_extraction toggle (when layout analysis enabled)

#### Scenario: Update collection configuration
- **WHEN** user changes layout analysis settings
- **THEN** validates configuration
- **AND** sends PUT /api/collections/{name}/config
- **AND** updates collection config.json
- **AND** displays success notification
- **AND** shows warning that change affects future uploads only

#### Scenario: Create collection with configuration
- **WHEN** user creates new collection from UI
- **THEN** shows optional "Layout Analysis Settings" section
- **AND** allows enabling layout features during creation
- **AND** sends POST /api/collections/create with config parameter
- **AND** creates collection with specified configuration

#### Scenario: Invalid collection configuration
- **WHEN** PUT /api/collections/{name}/config fails validation
- **THEN** displays error with validation details
- **AND** does not modify collection config
- **AND** allows user to correct and retry

**Rationale**: Collection-level layout analysis configuration determines document processing behavior. UI access enables users to optimize settings per collection type without backend file editing.

### Requirement: Image Search Interface
The system SHALL provide image upload search capability in the search page.

#### Scenario: Toggle to image search mode
- **WHEN** user clicks "Image Search" tab on search page
- **THEN** hides text search input
- **AND** displays image upload zone with drag-and-drop
- **AND** shows modality filter dropdown (All, Images Only, Text Only)
- **AND** preserves selected collection

#### Scenario: Upload image for search
- **WHEN** user drags image file onto upload zone
- **THEN** validates file is image type (.png, .jpg, .jpeg, .webp, .gif, .bmp)
- **AND** displays image preview with filename
- **AND** shows file size
- **AND** enables search button

#### Scenario: Execute image-based search
- **WHEN** user clicks Search with uploaded image
- **THEN** sends POST /api/search/image as FormData
- **AND** includes collection_name, top_k, modality_filter
- **AND** displays loading indicator
- **AND** processes image with Jina V4 vision encoder
- **AND** returns semantic search results

#### Scenario: Display image search results
- **WHEN** image search returns results
- **THEN** renders ResultsList with ImageResultCard and ResultCard
- **AND** shows relevance scores
- **AND** displays modality badges (text/image)
- **AND** allows clicking results to view full content

#### Scenario: Clear image and search again
- **WHEN** user clicks "Clear" on uploaded image
- **THEN** removes image preview
- **AND** resets upload zone
- **AND** disables search button
- **AND** allows uploading different image

#### Scenario: Invalid image file
- **WHEN** user uploads non-image file
- **THEN** shows error message
- **AND** lists supported image formats
- **AND** does not enable search button

**Rationale**: Image-to-image and image-to-text search are key multimodal RAG capabilities. Exposing this feature enables visual document discovery and cross-modal retrieval.

## MODIFIED Requirements

### Requirement: Real-time Updates
**MODIFY** from: The system SHALL provide real-time updates for long-running operations **and citation metadata**.

**TO**: The system SHALL provide real-time updates for long-running operations, **citation metadata, and retrieval performance metrics**.

#### Scenario: Receive and display retrieval metrics
- **WHEN** receiving context message via WebSocket
- **THEN** extracts retrieval_metrics from message
- **AND** displays metrics card in chat
- **AND** shows documents retrieved, images retrieved, total time
- **AND** shows vector search time and reranking time when applicable

#### Scenario: Collapsible metrics display
- **WHEN** metrics card appears in chat
- **THEN** displays summary (e.g., "Retrieved 5 docs in 234ms")
- **AND** auto-collapses detailed breakdown after 3 seconds
- **AND** allows user to expand for full metrics
- **AND** shows reranking status and compression status

**Rationale**: Retrieval metrics help users understand system performance and make informed decisions about RAG configuration tuning.

### Requirement: Search Interface
The system SHALL display region metadata from layout-analyzed documents in search results.

#### Scenario: Display region metadata badges
- **WHEN** search result includes region metadata
- **THEN** displays region_type badge (Text, Image, Table, Title, List)
- **AND** shows page_number when available
- **AND** positions badge in bottom-left corner of ResultCard
- **AND** uses color coding for region types

#### Scenario: Filter results by region type
- **WHEN** user selects region type filter in search controls
- **THEN** adds region_type parameter to search request
- **AND** displays only results matching selected type
- **AND** updates result count
- **AND** allows clearing filter to show all results

**Rationale**: Region metadata from layout analysis provides context about document structure. Displaying this information helps users understand result provenance and refine searches.

## Relationships
- **Depends on**: Existing `api` spec endpoints for `/api/config/rag`, `/api/collections/{name}/config`, `/api/search/image`
- **Extends**: Current `frontend` spec requirements for Search Interface, Collection Management, Real-time Updates
- **Enables**: Future requirements for visual bounding box display, configuration profiles, A/B testing
