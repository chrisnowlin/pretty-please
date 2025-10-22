# Chat UX Redesign - Design Document

## Overview
This document outlines the design decisions, UX patterns, and architectural approach for redesigning the chat interface to follow modern best practices while maintaining full backward compatibility with the existing backend.

## Design Principles

### 1. Familiar Patterns
Follow established chat UX conventions that users know from ChatGPT, Claude, and other modern chat interfaces:
- Right-aligned user messages, left-aligned assistant messages
- Clear visual distinction through color and positioning
- Streaming text appears token-by-token with smooth animation
- System messages (connection, errors) visually distinct from conversation

### 2. Progressive Disclosure
Don't overwhelm users with all features at once:
- Show prompt suggestions only when chat is empty
- Context panel collapsible (show/hide retrieved documents)
- Advanced options (temperature, top-k) behind settings toggle
- Message actions (copy, regenerate) appear on hover

### 3. Responsive Feedback
Provide immediate visual feedback for all user actions:
- Typing indicator during generation
- Connection status with color-coded indicator
- Optimistic UI updates (message appears immediately on send)
- Error states with clear recovery actions

### 4. Accessibility First
Build for keyboard-only and screen reader users from the start:
- Full keyboard navigation (Tab, Enter, Escape)
- ARIA labels on all interactive elements
- Focus indicators clearly visible
- Semantic HTML structure

## Component Architecture

Based on research from Vercel AI SDK and shadcn-chatbot-kit, we'll create a component hierarchy:

```
<ChatPage>
  ├── <ChatContainer>
  │   ├── <ChatHeader>
  │   │   ├── Collection badge
  │   │   ├── Connection status indicator
  │   │   └── Settings menu
  │   ├── <ChatMessages>
  │   │   ├── <PromptSuggestions> (when empty)
  │   │   ├── <MessageList>
  │   │   │   └── <ChatMessage>
  │   │   │       ├── Avatar
  │   │   │       ├── <MarkdownRenderer>
  │   │   │       ├── Timestamp
  │   │   │       └── <MessageActions> (hover)
  │   │   └── <TypingIndicator> (when generating)
  │   ├── <ContextPanel> (optional, collapsible)
  │   │   ├── Retrieved documents
  │   │   └── Image thumbnails
  │   └── <ChatForm>
  │       ├── <MessageInput>
  │       │   └── Auto-resizing textarea
  │       └── Send button with loading state
  └── <SessionSetup> (when no session)
      ├── Collection selector
      └── Configuration options
```

## Key UX Patterns

### Message Display
**Problem**: Current implementation uses basic colored boxes without clear visual hierarchy.

**Solution**: Implement chat bubble pattern with:
- User messages: Right-aligned, solid color background (blue/purple)
- Assistant messages: Left-aligned, subtle background (gray-100)
- Max width: 70% of container to maintain readability
- Rounded corners with tail/pointer optional
- Avatar icons for role clarity (user icon, AI icon)
- Timestamps shown on hover or for completed messages

**Reference**: Vercel AI Chatbot pattern, shadcn ChatMessage component

### Typing Indicator
**Problem**: Current loading indicator is generic bouncing dots, not chat-specific.

**Solution**: Implement animated typing indicator:
- Three dots bouncing in sequence
- Positioned as assistant message
- Appears immediately when generation starts
- Transitions smoothly to actual message content
- ARIA live region announces "Assistant is typing..."

**Reference**: shadcn TypingIndicator component, industry standard pattern

### Message Streaming
**Problem**: Streaming text appends without visual feedback about completion.

**Solution**:
- Cursor/pulse indicator at end of streaming text
- Smooth fade-in of timestamp when complete
- Slight animation when message finalizes
- Clear visual state change: streaming → complete

### Input Experience
**Problem**: Fixed-height textarea with manual enter/shift-enter handling.

**Solution**: Auto-resizing textarea with:
- Grows with content (min 2 rows, max 8 rows)
- Clear placeholder: "Ask about your documents..."
- Disabled state with visual feedback during generation
- Send button shows loading spinner when generating
- Enter sends, Shift+Enter for new line
- Focus returns to input after sending

**Reference**: shadcn MessageInput component, modern textarea patterns

### Prompt Suggestions
**Problem**: Empty chat state doesn't guide users on what they can ask.

**Solution**: Show 3-4 example prompts when chat is empty:
- "Summarize the key findings from recent documents"
- "What are the main themes across these documents?"
- "Find information about [topic from collection]"
- Click suggestion to auto-fill and send
- Suggestions contextual to collection when possible

**Reference**: ChatGPT, Claude pattern; shadcn PromptSuggestions component

### Connection Status
**Problem**: Connection indicator is small text in header, easy to miss.

**Solution**: Prominent connection indicator:
- Badge/pill in header with icon + text
- Green: "Connected", Yellow: "Connecting...", Red: "Disconnected"
- Auto-retry on disconnect with countdown
- Toast notification on unexpected disconnection
- Disable input when not connected

### Error Handling
**Problem**: Errors shown as generic alerts, no recovery options.

**Solution**: Contextual error handling:
- Inline error messages within chat flow (as system message)
- Retry button for transient errors
- "Start New Session" for session errors
- Detailed error info in console, friendly message to user
- Different error states: network, server, rate limit, etc.

### Markdown Rendering
**Problem**: Basic whitespace-pre-wrap doesn't render markdown properly.

**Solution**: Proper markdown rendering:
- Code blocks with syntax highlighting
- Copy-to-clipboard button on code blocks
- Bold, italic, lists, links rendered correctly
- Tables formatted properly
- Safe HTML rendering (no XSS)

**Reference**: react-markdown + remark-gfm, or custom renderer

### Message Actions
**Problem**: No way to copy, regenerate, or rate messages.

**Solution**: Hover action menu on messages:
- Copy message text (icon button)
- Regenerate response (assistant messages only)
- Upvote/downvote (UI only, backend integration future)
- Appears on hover, accessible via keyboard (focus)

## Visual Design Tokens

### Colors
- **User messages**: `bg-blue-600 text-white`
- **Assistant messages**: `bg-gray-100 text-gray-900`
- **System messages**: `bg-yellow-50 border-yellow-200 text-yellow-800`
- **Error messages**: `bg-red-50 border-red-200 text-red-800`
- **Connection green**: `text-green-600`
- **Connection red**: `text-red-600`

### Typography
- **Message text**: `text-base leading-relaxed`
- **Timestamp**: `text-xs text-gray-500`
- **Code**: `font-mono text-sm`
- **Headers**: `font-semibold`

### Spacing
- **Message gap**: `space-y-4`
- **Message padding**: `p-3 md:p-4`
- **Container padding**: `p-4 md:p-6`
- **Max message width**: `max-w-[70%]`

### Animations
- **Message enter**: `fade-in-up` 200ms ease
- **Typing dots**: `bounce` 600ms infinite
- **Streaming cursor**: `pulse` 1s infinite
- **Hover states**: 150ms ease transition

## Accessibility Features

### Keyboard Navigation
- Tab: Navigate between input, send button, message actions
- Enter: Send message (from input)
- Shift+Enter: New line in input
- Escape: Close settings/context panel, cancel generation
- Arrow up/down: Navigate message history (optional)

### Screen Reader Support
- ARIA live regions for:
  - Message list (`role="log" aria-live="polite"`)
  - Connection status (`aria-live="assertive"`)
  - Typing indicator (`aria-live="polite"`)
- ARIA labels on:
  - Send button: "Send message"
  - Stop button: "Stop generating"
  - Message actions: "Copy message", "Regenerate response"
- Message role announcements: "User said: ...", "Assistant replied: ..."

### Focus Management
- Focus input after sending message
- Focus first message action on keyboard navigation
- Focus trap in modals/settings
- Visible focus indicators (ring-2 ring-blue-500)

## Performance Considerations

### Virtualization
For conversations with 100+ messages, consider:
- React Window or TanStack Virtual for message list
- Render only visible messages + buffer
- Defer until performance issue observed

### Code Splitting
- Lazy load markdown renderer
- Lazy load syntax highlighter
- Bundle size target: <50KB increase (gzipped)

### Re-render Optimization
- React.memo on ChatMessage component
- Stable callback references (useCallback)
- Avoid re-rendering entire list on new message
- Use key={message.id} for efficient reconciliation

## Migration Strategy

### Phase 1: Component Refactor (No Visual Changes)
Extract existing code into reusable components without changing appearance:
1. Extract `<ChatMessage>` component
2. Extract `<MessageList>` component
3. Extract `<MessageInput>` component
4. Verify all functionality still works

### Phase 2: Visual Polish
Apply new visual design to components:
1. Update message bubble styling
2. Improve typography and spacing
3. Add connection status badge
4. Test responsive layout

### Phase 3: Enhanced Features
Add new UX features one at a time:
1. Typing indicator
2. Prompt suggestions
3. Markdown rendering
4. Message actions
5. Context panel (optional)

### Phase 4: Accessibility & Polish
Final touches:
1. Add ARIA labels
2. Keyboard navigation testing
3. Screen reader testing
4. Animation tuning
5. Performance testing

## Testing Strategy

### Unit Tests
- Component rendering (snapshot tests)
- Markdown rendering edge cases
- Message formatting logic

### Integration Tests
- WebSocket message handling
- Session creation flow
- Error state handling
- Message streaming

### E2E Tests
- Full conversation flow (Playwright)
- Keyboard-only navigation
- Mobile responsive layout
- Long conversation (100+ messages)

### Accessibility Tests
- axe-core automated testing
- Manual screen reader testing (NVDA/VoiceOver)
- Keyboard navigation testing
- Color contrast validation

## Design References

From Context7 research:
1. **Vercel AI Chatbot** (`/vercel/ai-chatbot`): useChat hook pattern, streaming message display
2. **shadcn-chatbot-kit** (`/blazity/shadcn-chatbot-kit`): Component architecture, accessibility patterns
3. **Industry Best Practices** (2025 chat UI research):
   - Message screen layouts with clear visual hierarchy
   - Typing indicators and loading states
   - Auto-scroll behavior patterns
   - Mobile-first responsive design

## Open Questions
1. Should we add a context panel showing retrieved documents, or keep chat focused?
   - **Recommendation**: Add as optional collapsible panel (default collapsed)

2. How many prompt suggestions to show?
   - **Recommendation**: 4 suggestions, contextual to collection metadata when possible

3. Should message actions be always visible or on hover?
   - **Recommendation**: Hover for desktop, always visible on mobile (touch)

4. Include voice input button for future extensibility?
   - **Recommendation**: No, defer to separate voice feature proposal
