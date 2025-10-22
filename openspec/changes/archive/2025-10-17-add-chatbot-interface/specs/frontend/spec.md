# frontend Specification Delta

## Purpose
Add chat interface to frontend while preserving existing search functionality.

## ADDED Requirements

### Requirement: Chat Page
The system SHALL provide a dedicated chat interface page.

#### Scenario: Navigate to chat page
- **WHEN** user clicks "Chat" navigation link
- **THEN** displays chat interface at /chat route
- **AND** preserves existing search page at root

#### Scenario: Initial page load
- **WHEN** chat page loads
- **THEN** displays collection selector
- **AND** shows "Start Chat" button

#### Scenario: Select collection for chat
- **WHEN** user selects collection
- **THEN** enables chat interface
- **AND** creates new session

### Requirement: Chat Message Interface
The system SHALL display conversation with message bubbles.

#### Scenario: Display user messages
- **WHEN** user sends message
- **THEN** displays in right-aligned bubble
- **AND** shows timestamp

#### Scenario: Display assistant messages
- **WHEN** assistant responds
- **THEN** displays in left-aligned bubble
- **AND** shows streaming progress

#### Scenario: Display thinking blocks
- **WHEN** thinking mode enabled
- **THEN** displays collapsible thinking section
- **AND** separates from final response

#### Scenario: Display context sources
- **WHEN** response includes retrieved documents
- **THEN** displays expandable context panel
- **AND** shows document titles and scores

### Requirement: Message Input
The system SHALL provide message input with controls.

#### Scenario: Type message
- **WHEN** user types in input field
- **THEN** enables send button
- **AND** supports multiline input

#### Scenario: Send message
- **WHEN** user clicks send or presses Enter
- **THEN** sends message via WebSocket
- **AND** clears input field

#### Scenario: Disable during generation
- **WHEN** assistant generating response
- **THEN** disables input and send button
- **AND** shows generation indicator

#### Scenario: Stop generation
- **WHEN** user clicks stop button
- **THEN** cancels in-progress generation
- **AND** preserves partial response

### Requirement: Session Controls
The system SHALL provide session management controls.

#### Scenario: Create new session
- **WHEN** user clicks "New Chat"
- **THEN** creates fresh session
- **AND** clears message history

#### Scenario: Clear history
- **WHEN** user clicks "Clear History"
- **THEN** removes messages from display
- **AND** resets session history

#### Scenario: Export conversation
- **WHEN** user clicks "Export"
- **THEN** downloads conversation as JSON or Markdown
- **AND** includes metadata

#### Scenario: Configure session settings
- **WHEN** user opens settings panel
- **THEN** displays configurable parameters
- **AND** applies changes immediately

### Requirement: WebSocket Connection Management
The system SHALL manage WebSocket connection state.

#### Scenario: Establish connection
- **WHEN** session created
- **THEN** connects to WebSocket endpoint
- **AND** displays connection status

#### Scenario: Handle connection loss
- **WHEN** WebSocket disconnects
- **THEN** attempts automatic reconnection
- **AND** displays reconnection status

#### Scenario: Connection error
- **WHEN** connection fails
- **THEN** displays error message
- **AND** provides retry button

### Requirement: Real-time Message Streaming
The system SHALL display assistant responses in real-time.

#### Scenario: Stream tokens
- **WHEN** receiving assistant chunks
- **THEN** appends tokens to message bubble
- **AND** auto-scrolls to latest content

#### Scenario: Display typing indicator
- **WHEN** generation started
- **THEN** shows typing indicator
- **AND** removes when complete

#### Scenario: Handle stream completion
- **WHEN** receives complete message
- **THEN** finalizes message bubble
- **AND** re-enables input

### Requirement: Context Display
The system SHALL show retrieved documents used for responses.

#### Scenario: Display context panel
- **WHEN** documents retrieved
- **THEN** shows collapsible context section
- **AND** lists document titles

#### Scenario: Show relevance scores
- **WHEN** displaying documents
- **THEN** includes relevance score
- **AND** orders by descending score

#### Scenario: Expand document preview
- **WHEN** user clicks document
- **THEN** shows document excerpt
- **AND** highlights relevant portions

#### Scenario: Navigate to source
- **WHEN** user clicks "View Full Document"
- **THEN** opens search page with document
- **AND** preserves chat session

### Requirement: Configuration Panel
The system SHALL provide session configuration interface.

#### Scenario: Display current settings
- **WHEN** settings panel opened
- **THEN** shows current top_k, thinking_mode, max_history
- **AND** displays as editable controls

#### Scenario: Update top_k
- **WHEN** user changes top_k slider
- **THEN** updates session configuration
- **AND** applies to next retrieval

#### Scenario: Toggle thinking mode
- **WHEN** user toggles thinking mode switch
- **THEN** updates session configuration
- **AND** affects next generation

#### Scenario: Configure max history
- **WHEN** user changes max history turns
- **THEN** updates session limit
- **AND** truncates existing history if needed

### Requirement: Error Display
The system SHALL display errors clearly to users.

#### Scenario: Display generation error
- **WHEN** generation fails
- **THEN** shows error message in chat
- **AND** provides retry option

#### Scenario: Display retrieval error
- **WHEN** document retrieval fails
- **THEN** shows warning message
- **AND** allows proceeding without context

#### Scenario: Display connection error
- **WHEN** WebSocket fails
- **THEN** shows connection status banner
- **AND** provides reconnect action

### Requirement: Loading States
The system SHALL indicate loading states clearly.

#### Scenario: Loading initial session
- **WHEN** creating session
- **THEN** displays loading spinner
- **AND** disables interface controls

#### Scenario: Retrieving context
- **WHEN** searching for documents
- **THEN** shows "Finding relevant documents..." message
- **AND** displays progress indicator

#### Scenario: Generating response
- **WHEN** LLM generating
- **THEN** shows streaming text
- **AND** displays token count

### Requirement: Responsive Layout
The system SHALL adapt layout to different screen sizes.

#### Scenario: Desktop layout
- **WHEN** viewed on desktop
- **THEN** displays three-column layout
- **AND** shows chat, context, and settings

#### Scenario: Mobile layout
- **WHEN** viewed on mobile
- **THEN** stacks components vertically
- **AND** collapses context and settings

#### Scenario: Tablet layout
- **WHEN** viewed on tablet
- **THEN** displays two-column layout
- **AND** shows chat and collapsible sidebar

## MODIFIED Requirements

### Requirement: Navigation
The system SHALL provide navigation between search and chat interfaces.

#### Scenario: Navigation bar
- **WHEN** any page loaded
- **THEN** displays navigation with "Search" and "Chat" links
- **AND** highlights current page

#### Scenario: Switch between interfaces
- **WHEN** user clicks navigation link
- **THEN** navigates to selected page
- **AND** preserves page state
