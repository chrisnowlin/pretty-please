# Frontend Specification Delta: Citation Source Linking

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Real-time Updates
The system SHALL provide real-time updates for long-running operations **and citation metadata**.

#### Scenario: WebSocket connection
- **WHEN** starting long operation
- **THEN** establishes WebSocket connection
- **AND** receives progress updates

#### Scenario: Connection recovery
- **WHEN** WebSocket disconnects
- **THEN** attempts automatic reconnection
- **AND** resumes progress tracking

#### Scenario: Receive and store citation metadata
- **WHEN** receiving context message with citation_map via WebSocket
- **THEN** parses and stores citation metadata
- **AND** associates citation map with current conversation turn
- **AND** makes citation data available during message rendering

**Rationale**: Citation metadata must be received and stored before rendering assistant responses to enable interactive citations. Association with conversation turn ensures correct citation display in multi-turn conversations.
