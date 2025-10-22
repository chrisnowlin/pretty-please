# frontend Specification

## Purpose
TBD - created by archiving change add-frontend-ui. Update Purpose after archive.
## Requirements
### Requirement: Web Application
The system SHALL provide a single-page web application for user interactions.

#### Scenario: Access web interface
- **WHEN** user navigates to application URL
- **THEN** loads responsive web interface
- **AND** displays search and upload options

#### Scenario: Responsive design
- **WHEN** accessing from different devices
- **THEN** adapts layout for desktop/tablet/mobile
- **AND** maintains full functionality

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

### Requirement: Document Upload
The system SHALL enable document upload through the web interface.

#### Scenario: Upload via drag-and-drop
- **WHEN** user drags files onto upload zone
- **THEN** validates file types and sizes
- **AND** shows file preview with status

#### Scenario: Upload via file selection
- **WHEN** user clicks to select files
- **THEN** opens file browser dialog
- **AND** allows multiple file selection

#### Scenario: Upload validation
- **WHEN** unsupported file is selected
- **THEN** shows clear error message
- **AND** lists supported formats

### Requirement: Ingestion Progress
The system SHALL provide real-time feedback on document processing.

#### Scenario: Show processing progress
- **WHEN** documents are being ingested
- **THEN** displays progress bar with percentage
- **AND** shows current file being processed

#### Scenario: Handle processing errors
- **WHEN** ingestion error occurs
- **THEN** displays error notification
- **AND** allows retry or skip options

#### Scenario: Complete ingestion
- **WHEN** all documents processed
- **THEN** shows success notification
- **AND** updates collection statistics

### Requirement: Collection Management View
The system SHALL display collection information and statistics.

#### Scenario: View collection list
- **WHEN** accessing collections page
- **THEN** displays all available collections
- **AND** shows document count for each

#### Scenario: Select active collection
- **WHEN** user selects a collection
- **THEN** sets as active for search/upload
- **AND** updates UI to reflect selection

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

### Requirement: Interactive Citations
The system SHALL render citation markers in chat responses as interactive links to source material.

#### Scenario: Render text citations as links
- **WHEN** assistant response contains text citation marker (e.g., "[1]", "[2]")
- **THEN** renders citation as clickable link
- **AND** preserves citation formatting and numbering
- **AND** applies distinct styling (color, hover state)
- **AND** includes ARIA label describing the citation source

**Rationale**: Makes citations discoverable and actionable, allowing users to verify information sources. Accessibility labels ensure screen reader users understand the purpose of citation links.

#### Scenario: Render image citations as links
- **WHEN** assistant response contains image citation marker (e.g., "[IMG-1]")
- **THEN** renders citation as clickable link
- **AND** preserves citation formatting
- **AND** applies distinct styling to indicate image source
- **AND** includes ARIA label describing the image source

**Rationale**: Image citations should be clearly distinguished from text citations while maintaining consistent interaction patterns.

#### Scenario: Handle missing citation metadata
- **WHEN** citation marker appears but no metadata exists in citation map
- **THEN** renders citation as plain text (non-interactive)
- **AND** logs warning for debugging
- **AND** does not break message rendering

**Rationale**: Graceful degradation ensures robust behavior when citation data is incomplete or missing, preventing UI failures.

### Requirement: Source Viewer
The system SHALL provide a viewer component to display citation source material.

#### Scenario: Display text source content
- **WHEN** user clicks text citation link
- **THEN** opens source viewer with document content
- **AND** displays source name and relevance score
- **AND** highlights or formats content for readability
- **AND** includes metadata (timestamps, page numbers if available)

**Rationale**: Users need to see the original source text to verify information and explore context beyond the summary provided in the response.

#### Scenario: Display image source content
- **WHEN** user clicks image citation link
- **THEN** opens source viewer with full-size image
- **AND** displays image filename and metadata
- **AND** provides zoom or pan capability for large images
- **AND** shows image dimensions and format

**Rationale**: Users need to see full-resolution images to understand visual content referenced in responses, with sufficient detail for verification.

#### Scenario: Close source viewer
- **WHEN** user clicks close button, presses ESC, or clicks outside viewer
- **THEN** closes source viewer
- **AND** returns keyboard focus to citation link
- **AND** restores previous UI state

**Rationale**: Multiple exit methods ensure accessibility and user preference. Returning focus prevents keyboard navigation confusion.

#### Scenario: Switch between sources
- **WHEN** user clicks different citation while viewer is open
- **THEN** updates viewer content to new source
- **AND** maintains viewer state (open/closed, position)
- **AND** updates metadata display

**Rationale**: Allows efficient source comparison without repeatedly opening and closing the viewer.

### Requirement: Citation Navigation Accessibility
The system SHALL ensure citation links are fully accessible via keyboard and assistive technologies.

#### Scenario: Keyboard navigation to citations
- **WHEN** user presses Tab key in chat message
- **THEN** focuses on next citation link in document order
- **AND** displays visible focus indicator
- **AND** skips non-interactive text

**Rationale**: Keyboard users must be able to discover and activate citations without a mouse. Clear focus indicators show current position.

#### Scenario: Activate citation with keyboard
- **WHEN** citation link has focus and user presses Enter or Space
- **THEN** opens source viewer for that citation
- **AND** same behavior as mouse click
- **AND** focus moves to viewer close button

**Rationale**: Standard keyboard activation patterns (Enter/Space) ensure consistent behavior. Moving focus to viewer allows immediate interaction or dismissal.

#### Scenario: Screen reader announces citations
- **WHEN** screen reader encounters citation link
- **THEN** announces citation number and source type
- **AND** announces link role
- **AND** announces source name if available
- **Example**: "Link, citation 1, source Python documentation, relevance 0.95"

**Rationale**: Screen reader users need sufficient context to understand what each citation represents before activating it.

### Requirement: Citation Styling
The system SHALL visually distinguish citations from regular text while maintaining readability.

#### Scenario: Style text citations
- **WHEN** rendering text citation link (e.g., "[1]")
- **THEN** applies blue or accent color
- **AND** maintains original font size and weight
- **AND** shows underline on hover
- **AND** changes cursor to pointer on hover

**Rationale**: Visual distinction helps users identify interactive elements. Consistent styling with other links maintains UI coherence.

#### Scenario: Style image citations
- **WHEN** rendering image citation link (e.g., "[IMG-1]")
- **THEN** applies distinct color (e.g., purple or green)
- **AND** optionally includes image icon
- **AND** shows underline on hover
- **AND** changes cursor to pointer on hover

**Rationale**: Different color helps users distinguish image sources from text sources at a glance, improving scannability.

#### Scenario: Maintain responsive design
- **WHEN** viewing citations on mobile or small screens
- **THEN** citation links remain tappable with sufficient touch target size (44x44px minimum)
- **AND** source viewer adapts to screen size
- **AND** maintains readability of source content

**Rationale**: Mobile users need appropriately sized touch targets. Responsive viewer ensures usability across devices.

### Requirement: Theme System
The system SHALL provide a theme system that manages light and dark color schemes for the user interface.

#### Scenario: Initialize theme from system preference
- **WHEN** application loads for the first time
- **THEN** detects user's system color scheme preference
- **AND** applies the matching theme (light or dark)

#### Scenario: Persist theme preference
- **WHEN** user changes theme
- **THEN** stores preference in browser local storage
- **AND** applies saved theme on next visit

#### Scenario: Apply consistent theme colors
- **WHEN** theme is active
- **THEN** all UI components use appropriate colors from theme
- **AND** colors provide sufficient contrast for accessibility

### Requirement: Theme Toggle Control
The system SHALL provide a user interface control for switching between themes.

#### Scenario: Access theme toggle
- **WHEN** viewing the application
- **THEN** displays theme toggle in navigation or settings area
- **AND** clearly indicates current active theme

#### Scenario: Switch to light mode
- **WHEN** user selects light theme
- **THEN** immediately applies light color scheme
- **AND** saves preference for future sessions

#### Scenario: Switch to dark mode
- **WHEN** user selects dark theme
- **THEN** immediately applies dark color scheme
- **AND** saves preference for future sessions

#### Scenario: Follow system preference
- **WHEN** user selects "system" or "auto" option
- **THEN** detects current system preference
- **AND** applies matching theme automatically

#### Scenario: Update when system preference changes
- **WHEN** system theme preference changes (user changes OS theme)
- **AND** app is set to follow system preference
- **THEN** automatically updates app theme to match

### Requirement: Dark Mode Colors
The system SHALL define a comprehensive dark color palette for dark mode.

#### Scenario: Dark background colors
- **WHEN** dark theme is active
- **THEN** primary background is dark (e.g., #1a1a1a or similar)
- **AND** secondary backgrounds provide visual hierarchy

#### Scenario: Dark text colors
- **WHEN** dark theme is active
- **THEN** text colors have sufficient contrast against dark backgrounds
- **AND** primary text is light (e.g., #e0e0e0 or white)

#### Scenario: Dark component styling
- **WHEN** dark theme is active
- **THEN** all interactive elements (buttons, inputs, cards) use dark-appropriate colors
- **AND** borders and shadows adapt for dark visibility

### Requirement: Light Mode Colors
The system SHALL define a comprehensive light color palette for light mode.

#### Scenario: Light background colors
- **WHEN** light theme is active
- **THEN** primary background is light (e.g., #ffffff or #f9f9f9)
- **AND** secondary backgrounds provide visual hierarchy

#### Scenario: Light text colors
- **WHEN** light theme is active
- **THEN** text colors have sufficient contrast against light backgrounds
- **AND** primary text is dark (e.g., #333333 or similar)

#### Scenario: Light component styling
- **WHEN** light theme is active
- **THEN** all interactive elements use light-appropriate colors
- **AND** borders and shadows adapt for light visibility

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

