# frontend Specification - Chat UX Redesign

## MODIFIED Requirements

### Requirement: Chat Message Display
The system SHALL render chat messages with modern visual hierarchy and clear role distinction.

#### Scenario: Display user message
- **WHEN** user sends a message
- **THEN** renders right-aligned message bubble
- **AND** applies user-specific styling (blue background, white text)
- **AND** shows timestamp on hover or when complete
- **AND** limits width to 70% of container for readability

#### Scenario: Display assistant message
- **WHEN** assistant responds
- **THEN** renders left-aligned message bubble
- **AND** applies assistant-specific styling (light gray background)
- **AND** includes AI avatar icon
- **AND** renders markdown content with proper formatting

#### Scenario: Render markdown content
- **WHEN** message contains markdown formatting
- **THEN** renders bold, italic, lists, and links correctly
- **AND** syntax-highlights code blocks
- **AND** provides copy button on code blocks
- **AND** sanitizes HTML to prevent XSS

#### Scenario: Display message timestamp
- **WHEN** message is completed
- **THEN** shows formatted timestamp
- **AND** uses relative time for recent messages ("2 minutes ago")
- **AND** uses absolute time for older messages ("Jan 15, 3:24 PM")

### Requirement: Typing Indicator
The system SHALL provide clear visual feedback during message generation.

#### Scenario: Show typing indicator
- **WHEN** assistant begins generating response
- **THEN** displays animated typing indicator
- **AND** positions indicator as assistant message
- **AND** shows three dots bouncing in sequence
- **AND** announces "Assistant is typing" to screen readers

#### Scenario: Transition to message
- **WHEN** first token arrives from stream
- **THEN** replaces typing indicator with message bubble
- **AND** shows streaming cursor at end of text
- **AND** smoothly animates transition

#### Scenario: Complete generation
- **WHEN** generation completes
- **THEN** removes streaming cursor
- **AND** adds timestamp
- **AND** enables message actions

### Requirement: Message Input
The system SHALL provide an enhanced input experience with auto-resize and clear feedback.

#### Scenario: Auto-resize textarea
- **WHEN** user types multi-line message
- **THEN** textarea grows to fit content
- **AND** maintains minimum height of 2 rows
- **AND** caps maximum height at 8 rows
- **AND** scrolls content when max height reached

#### Scenario: Keyboard shortcuts
- **WHEN** user presses Enter without Shift
- **THEN** sends message and clears input
- **WHEN** user presses Shift+Enter
- **THEN** inserts new line without sending
- **WHEN** user presses Escape
- **THEN** clears input or cancels generation if active

#### Scenario: Input disabled state
- **WHEN** assistant is generating
- **THEN** disables textarea
- **AND** shows visual disabled state
- **AND** displays "Generating..." placeholder
- **WHEN** WebSocket disconnected
- **THEN** disables textarea
- **AND** shows "Reconnecting..." placeholder

#### Scenario: Focus management
- **WHEN** user sends message
- **THEN** automatically returns focus to input
- **WHEN** page loads with active session
- **THEN** focuses input for immediate typing

## ADDED Requirements

### Requirement: Prompt Suggestions
The system SHALL guide users with example prompts when chat is empty.

#### Scenario: Display suggestions
- **WHEN** chat session active with no messages
- **THEN** displays 4 example prompts
- **AND** formats as clickable cards or pills
- **AND** includes relevant emoji or icon per suggestion
- **AND** hides suggestions once first message sent

#### Scenario: Use suggestion
- **WHEN** user clicks prompt suggestion
- **THEN** fills input with suggestion text
- **AND** automatically sends message
- **AND** adds user message to history
- **AND** triggers assistant response

#### Scenario: Contextual suggestions
- **WHEN** collection metadata available
- **THEN** includes collection-specific suggestions
- **AND** references collection topic if known
- **AND** falls back to generic suggestions if no metadata

### Requirement: Connection Status Indicator
The system SHALL clearly display WebSocket connection status at all times.

#### Scenario: Connected state
- **WHEN** WebSocket connected
- **THEN** shows green badge with "Connected" text
- **AND** includes checkmark or dot icon
- **AND** positions prominently in header

#### Scenario: Connecting state
- **WHEN** WebSocket connecting
- **THEN** shows yellow badge with "Connecting..." text
- **AND** displays loading spinner
- **AND** indicates progress if reconnecting

#### Scenario: Disconnected state
- **WHEN** WebSocket disconnects
- **THEN** shows red badge with "Disconnected" text
- **AND** includes warning icon
- **AND** displays auto-retry countdown if applicable
- **AND** provides manual "Reconnect" button

#### Scenario: Connection error notification
- **WHEN** connection fails unexpectedly
- **THEN** shows toast notification
- **AND** explains reason for disconnection
- **AND** provides recovery actions

### Requirement: Message Actions
The system SHALL provide actions for interacting with individual messages.

#### Scenario: Show message actions
- **WHEN** user hovers over message (desktop)
- **THEN** displays action buttons
- **AND** includes "Copy" button for all messages
- **AND** includes "Regenerate" button for assistant messages
- **WHEN** user focuses message via keyboard
- **THEN** makes actions keyboard-accessible

#### Scenario: Copy message
- **WHEN** user clicks copy button
- **THEN** copies message text to clipboard
- **AND** shows "Copied!" confirmation feedback
- **AND** announces copy action to screen readers

#### Scenario: Regenerate response
- **WHEN** user clicks regenerate on assistant message
- **THEN** removes current assistant message
- **AND** re-sends previous user message
- **AND** generates new response
- **AND** maintains conversation context

### Requirement: Error Handling
The system SHALL display errors contextually with recovery options.

#### Scenario: Display inline error
- **WHEN** generation error occurs
- **THEN** shows error as system message in chat flow
- **AND** applies error styling (red border, yellow background)
- **AND** explains error in user-friendly language
- **AND** hides technical details (logs to console)

#### Scenario: Provide error recovery
- **WHEN** transient error occurs
- **THEN** displays "Retry" button
- **WHEN** user clicks retry
- **THEN** re-attempts failed operation
- **WHEN** session error occurs
- **THEN** displays "Start New Session" button

#### Scenario: Rate limit error
- **WHEN** rate limit reached
- **THEN** shows rate limit message
- **AND** displays countdown to retry availability
- **AND** disables input until retry available

### Requirement: Accessibility
The system SHALL be fully accessible via keyboard and screen reader.

#### Scenario: Keyboard navigation
- **WHEN** user presses Tab
- **THEN** moves focus to next interactive element
- **AND** shows visible focus indicator
- **WHEN** user navigates to message actions
- **THEN** makes actions accessible via Enter/Space
- **WHEN** user presses Escape
- **THEN** closes open menus or cancels operations

#### Scenario: Screen reader support
- **WHEN** new message added
- **THEN** announces message with role prefix
- **AND** uses polite ARIA live region
- **WHEN** typing indicator appears
- **THEN** announces "Assistant is typing"
- **WHEN** connection status changes
- **THEN** announces status change assertively

#### Scenario: ARIA labels
- **WHEN** interactive elements render
- **THEN** includes descriptive aria-label
- **AND** uses aria-describedby for additional context
- **AND** marks message list with role="log"
- **AND** uses semantic HTML where possible

### Requirement: Responsive Design
The system SHALL adapt chat layout for mobile, tablet, and desktop.

#### Scenario: Mobile layout
- **WHEN** viewport width below 640px
- **THEN** reduces message padding
- **AND** increases tap target sizes (min 44x44px)
- **AND** shows message actions always visible (not hover)
- **AND** stacks header elements vertically if needed

#### Scenario: Tablet layout
- **WHEN** viewport width 640px-1024px
- **THEN** uses medium spacing
- **AND** maintains 70% max message width
- **AND** supports both touch and hover interactions

#### Scenario: Desktop layout
- **WHEN** viewport width above 1024px
- **THEN** uses comfortable spacing
- **AND** shows message actions on hover
- **AND** optimizes for keyboard+mouse workflows

### Requirement: Animation & Transitions
The system SHALL use smooth animations to enhance UX without hindering performance.

#### Scenario: Message enter animation
- **WHEN** new message added to list
- **THEN** fades in from bottom
- **AND** completes animation in 200ms
- **AND** uses ease-out timing function

#### Scenario: Typing indicator animation
- **WHEN** typing indicator visible
- **THEN** bounces three dots in sequence
- **AND** loops animation infinitely
- **AND** maintains 60fps performance

#### Scenario: Streaming cursor
- **WHEN** message streaming
- **THEN** shows pulsing cursor at text end
- **AND** pulses every 1 second
- **AND** removes cursor when streaming completes

#### Scenario: Respect motion preferences
- **WHEN** user prefers reduced motion
- **THEN** disables all animations
- **AND** uses instant transitions instead
- **AND** maintains functionality without animation

### Requirement: Performance
The system SHALL maintain responsive performance with large conversation histories.

#### Scenario: Handle long conversations
- **WHEN** conversation contains 100+ messages
- **THEN** maintains smooth scrolling
- **AND** renders in under 100ms on user action
- **AND** uses efficient re-render strategy (React.memo)

#### Scenario: Streaming performance
- **WHEN** receiving token stream
- **THEN** updates UI within 16ms per token
- **AND** batches rapid updates if needed
- **AND** maintains scroll position correctly

#### Scenario: Bundle size
- **WHEN** chat page loads
- **THEN** initial bundle under 200KB (gzipped)
- **AND** lazy loads markdown renderer
- **AND** lazy loads syntax highlighter
- **AND** increases total bundle by max 50KB

## REMOVED Requirements
None. This change is additive to the existing frontend specification.
