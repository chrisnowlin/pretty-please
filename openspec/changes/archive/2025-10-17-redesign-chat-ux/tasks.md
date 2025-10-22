# Implementation Tasks - Detailed

## Phase 1: Component Refactoring (No Visual Changes)
**Goal**: Extract existing chat code into reusable components without changing appearance or behavior.

### Task 1.1: Extract ChatMessage component

**File**: `frontend/src/components/chat/ChatMessage.tsx`

**Implementation Steps**:
1. Create new file `frontend/src/components/chat/ChatMessage.tsx`
2. Define TypeScript interface for props:
   ```typescript
   interface ChatMessageProps {
     message: Message;
     isStreaming?: boolean;
     showTimestamp?: boolean;
   }

   interface Message {
     role: 'user' | 'assistant';
     content: string;
     timestamp: Date | null;
   }
   ```

3. Extract message rendering JSX from ChatPage.tsx (lines 218-236):
   ```typescript
   export function ChatMessage({ message, isStreaming = false, showTimestamp = true }: ChatMessageProps) {
     return (
       <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
         <div className={`max-w-[70%] rounded-lg p-3 ${
           message.role === 'user'
             ? 'bg-blue-500 text-white'
             : 'bg-gray-100 text-gray-900'
         }`}>
           <p className="whitespace-pre-wrap">{message.content}</p>
           {showTimestamp && message.timestamp && (
             <p className="text-xs mt-1 opacity-70">
               {message.timestamp.toLocaleTimeString()}
             </p>
           )}
         </div>
       </div>
     );
   }
   ```

4. Create barrel export in `frontend/src/components/chat/index.ts`:
   ```typescript
   export { ChatMessage } from './ChatMessage';
   export type { ChatMessageProps } from './ChatMessage';
   ```

**Technical Considerations**:
- Keep exact same className strings to preserve visual appearance
- Don't add any new styling in this phase
- Ensure TypeScript types are strict (no `any`)
- Export both component and types for reusability

**Edge Cases**:
- Handle `null` timestamp gracefully
- Handle empty content string
- Handle very long content (truncation handled by parent)

**Validation**:
- [ ] Component renders identically to inline version
- [ ] User messages right-aligned with blue background
- [ ] Assistant messages left-aligned with gray background
- [ ] Timestamps display correctly when present
- [ ] No TypeScript errors
- [ ] Visual regression test passes (screenshot comparison)

**Testing**:
```typescript
// ChatMessage.test.tsx
describe('ChatMessage', () => {
  it('renders user message with correct styling', () => {
    const message = { role: 'user', content: 'Test', timestamp: new Date() };
    const { container } = render(<ChatMessage message={message} />);
    expect(container.querySelector('.justify-end')).toBeInTheDocument();
    expect(container.querySelector('.bg-blue-500')).toBeInTheDocument();
  });

  it('renders assistant message with correct styling', () => {
    const message = { role: 'assistant', content: 'Response', timestamp: new Date() };
    const { container } = render(<ChatMessage message={message} />);
    expect(container.querySelector('.justify-start')).toBeInTheDocument();
    expect(container.querySelector('.bg-gray-100')).toBeInTheDocument();
  });

  it('hides timestamp when showTimestamp is false', () => {
    const message = { role: 'user', content: 'Test', timestamp: new Date() };
    const { container } = render(<ChatMessage message={message} showTimestamp={false} />);
    expect(container.querySelector('.text-xs')).not.toBeInTheDocument();
  });
});
```

**Estimated Time**: 1-1.5 hours

---

### Task 1.2: Extract MessageList component

**File**: `frontend/src/components/chat/MessageList.tsx`

**Implementation Steps**:
1. Create `frontend/src/components/chat/MessageList.tsx`
2. Define interface:
   ```typescript
   interface MessageListProps {
     messages: Message[];
     isGenerating: boolean;
     messagesEndRef: React.RefObject<HTMLDivElement>;
   }
   ```

3. Extract message list container from ChatPage.tsx (lines 211-250):
   ```typescript
   import { ChatMessage } from './ChatMessage';

   export function MessageList({ messages, isGenerating, messagesEndRef }: MessageListProps) {
     return (
       <div className="h-96 overflow-y-auto p-4 space-y-4">
         {messages.length === 0 && (
           <p className="text-center text-gray-500 mt-8">
             Start a conversation by typing a message below
           </p>
         )}

         {messages.map((msg, idx) => (
           <ChatMessage
             key={`${msg.role}-${idx}`}
             message={msg}
             showTimestamp={!!msg.timestamp}
           />
         ))}

         {isGenerating && (
           <div className="flex justify-start">
             <div className="bg-gray-100 rounded-lg p-3">
               <div className="flex space-x-2">
                 <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                 <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                 <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
               </div>
             </div>
           </div>
         )}

         <div ref={messagesEndRef} />
       </div>
     );
   }
   ```

4. Add to barrel export in `frontend/src/components/chat/index.ts`

**Technical Considerations**:
- Use stable keys for messages (consider message.id if available, fallback to index)
- Preserve scroll behavior with messagesEndRef
- Keep exact spacing and sizing (`h-96`, `space-y-4`)
- Don't change loading indicator yet (will be improved in Phase 3)

**Auto-scroll Implementation**:
```typescript
// In parent component (ChatPage)
const messagesEndRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [messages]);
```

**Edge Cases**:
- Empty message list (show placeholder text)
- Very long message list (scroll performance)
- Rapid message updates (debounce scroll)
- Message added while user is scrolled up (preserve position)

**Validation**:
- [ ] Messages render in correct order
- [ ] Auto-scroll to bottom on new message
- [ ] Empty state shows placeholder text
- [ ] Loading indicator displays when generating
- [ ] Scroll container correct height (`h-96`)
- [ ] No layout shift on message addition

**Testing**:
```typescript
describe('MessageList', () => {
  it('renders empty state when no messages', () => {
    const ref = createRef<HTMLDivElement>();
    const { getByText } = render(
      <MessageList messages={[]} isGenerating={false} messagesEndRef={ref} />
    );
    expect(getByText(/Start a conversation/i)).toBeInTheDocument();
  });

  it('renders all messages in order', () => {
    const messages = [
      { role: 'user', content: 'First', timestamp: new Date() },
      { role: 'assistant', content: 'Second', timestamp: new Date() },
    ];
    const ref = createRef<HTMLDivElement>();
    const { getAllByText } = render(
      <MessageList messages={messages} isGenerating={false} messagesEndRef={ref} />
    );
    const elements = getAllByText(/First|Second/);
    expect(elements).toHaveLength(2);
  });

  it('shows loading indicator when generating', () => {
    const ref = createRef<HTMLDivElement>();
    const { container } = render(
      <MessageList messages={[]} isGenerating={true} messagesEndRef={ref} />
    );
    expect(container.querySelectorAll('.animate-bounce')).toHaveLength(3);
  });
});
```

**Estimated Time**: 1-1.5 hours

---

### Task 1.3: Extract MessageInput component

**File**: `frontend/src/components/chat/MessageInput.tsx`

**Implementation Steps**:
1. Create `frontend/src/components/chat/MessageInput.tsx`
2. Define comprehensive interface:
   ```typescript
   interface MessageInputProps {
     value: string;
     onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
     onSubmit: () => void;
     disabled: boolean;
     isGenerating: boolean;
     placeholder?: string;
   }
   ```

3. Extract input area from ChatPage.tsx (lines 253-273):
   ```typescript
   export function MessageInput({
     value,
     onChange,
     onSubmit,
     disabled,
     isGenerating,
     placeholder = "Type your message... (Enter to send, Shift+Enter for new line)"
   }: MessageInputProps) {
     const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
       if (e.key === 'Enter' && !e.shiftKey) {
         e.preventDefault();
         if (value.trim() && !disabled && !isGenerating) {
           onSubmit();
         }
       }
     };

     return (
       <div className="border-t p-4">
         <div className="flex space-x-2">
           <textarea
             value={value}
             onChange={onChange}
             onKeyPress={handleKeyPress}
             placeholder={placeholder}
             className="flex-1 p-2 border rounded resize-none"
             rows={2}
             disabled={disabled || isGenerating}
           />
           <button
             onClick={onSubmit}
             disabled={!value.trim() || disabled || isGenerating}
             className="bg-blue-500 text-white px-6 rounded hover:bg-blue-600 disabled:bg-gray-300"
           >
             Send
           </button>
         </div>
       </div>
     );
   }
   ```

**Technical Considerations**:
- Keyboard handling must match current behavior exactly
- Enter sends, Shift+Enter adds newline
- Prevent default on Enter to avoid adding newline before send
- Disable input when `disabled` OR `isGenerating`
- Button disabled when input empty, disabled, or generating

**Edge Cases**:
- Empty message (trim whitespace before sending)
- Message with only whitespace (don't send)
- Pressing Enter while disabled (no-op)
- Shift+Enter at end of text (adds newline correctly)
- Long messages (textarea scrolls, doesn't resize yet)

**Validation**:
- [ ] Enter key sends message
- [ ] Shift+Enter adds newline without sending
- [ ] Send button disabled when input empty
- [ ] Send button disabled when generating
- [ ] Textarea disabled when disconnected
- [ ] Placeholder text displays correctly
- [ ] No visual changes from current implementation

**Testing**:
```typescript
describe('MessageInput', () => {
  it('calls onSubmit when Enter pressed', () => {
    const onSubmit = jest.fn();
    const onChange = jest.fn();
    const { getByRole } = render(
      <MessageInput
        value="Test message"
        onChange={onChange}
        onSubmit={onSubmit}
        disabled={false}
        isGenerating={false}
      />
    );
    const textarea = getByRole('textbox');
    fireEvent.keyPress(textarea, { key: 'Enter', shiftKey: false });
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('does not submit when Shift+Enter pressed', () => {
    const onSubmit = jest.fn();
    const onChange = jest.fn();
    const { getByRole } = render(
      <MessageInput
        value="Test"
        onChange={onChange}
        onSubmit={onSubmit}
        disabled={false}
        isGenerating={false}
      />
    );
    const textarea = getByRole('textbox');
    fireEvent.keyPress(textarea, { key: 'Enter', shiftKey: true });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('disables textarea when generating', () => {
    const { getByRole } = render(
      <MessageInput
        value=""
        onChange={() => {}}
        onSubmit={() => {}}
        disabled={false}
        isGenerating={true}
      />
    );
    expect(getByRole('textbox')).toBeDisabled();
  });

  it('disables send button when input empty', () => {
    const { getByText } = render(
      <MessageInput
        value=""
        onChange={() => {}}
        onSubmit={() => {}}
        disabled={false}
        isGenerating={false}
      />
    );
    expect(getByText('Send')).toBeDisabled();
  });
});
```

**Estimated Time**: 1.5-2 hours

---

### Task 1.4: Extract SessionSetup component

**File**: `frontend/src/components/chat/SessionSetup.tsx`

**Implementation Steps**:
1. Create `frontend/src/components/chat/SessionSetup.tsx`
2. Define interface with collection type:
   ```typescript
   interface Collection {
     name: string;
     count: number;
   }

   interface SessionSetupProps {
     collections: Collection[] | undefined;
     selectedCollection: string;
     onCollectionChange: (collectionName: string) => void;
     onCreateSession: () => void;
   }
   ```

3. Extract session setup UI from ChatPage.tsx (lines 156-183):
   ```typescript
   export function SessionSetup({
     collections,
     selectedCollection,
     onCollectionChange,
     onCreateSession
   }: SessionSetupProps) {
     return (
       <div className="bg-white rounded-lg shadow p-6">
         <h2 className="text-xl font-semibold mb-4">Start a Chat Session</h2>
         <div className="space-y-4">
           <div>
             <label className="block text-sm font-medium mb-2">
               Select Collection
             </label>
             <select
               value={selectedCollection}
               onChange={(e) => onCollectionChange(e.target.value)}
               className="w-full p-2 border rounded"
             >
               <option value="">Choose a collection...</option>
               {collections?.map((col) => (
                 <option key={col.name} value={col.name}>
                   {col.name} ({col.count} documents)
                 </option>
               ))}
             </select>
           </div>
           <button
             onClick={onCreateSession}
             disabled={!selectedCollection}
             className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-300"
           >
             Start Chat
           </button>
         </div>
       </div>
     );
   }
   ```

**Technical Considerations**:
- Collections data comes from TanStack Query (may be undefined during load)
- Handle undefined/null collections gracefully
- Preserve dropdown default option "Choose a collection..."
- Button disabled when no collection selected
- Keep exact styling to match current appearance

**Edge Cases**:
- Collections loading (undefined state)
- Empty collections array
- Collection with 0 documents (still selectable)
- Very long collection names (CSS truncation)

**Validation**:
- [ ] Collections populate dropdown correctly
- [ ] Default "Choose a collection..." option shows
- [ ] Selection updates state
- [ ] Start button disabled when no selection
- [ ] Button triggers session creation
- [ ] Document counts display correctly
- [ ] No visual changes

**Testing**:
```typescript
describe('SessionSetup', () => {
  const mockCollections = [
    { name: 'test-collection', count: 42 },
    { name: 'another-collection', count: 10 },
  ];

  it('renders collection options', () => {
    const { getByText } = render(
      <SessionSetup
        collections={mockCollections}
        selectedCollection=""
        onCollectionChange={() => {}}
        onCreateSession={() => {}}
      />
    );
    expect(getByText(/test-collection \(42 documents\)/)).toBeInTheDocument();
    expect(getByText(/another-collection \(10 documents\)/)).toBeInTheDocument();
  });

  it('disables start button when no collection selected', () => {
    const { getByText } = render(
      <SessionSetup
        collections={mockCollections}
        selectedCollection=""
        onCollectionChange={() => {}}
        onCreateSession={() => {}}
      />
    );
    expect(getByText('Start Chat')).toBeDisabled();
  });

  it('enables start button when collection selected', () => {
    const { getByText } = render(
      <SessionSetup
        collections={mockCollections}
        selectedCollection="test-collection"
        onCollectionChange={() => {}}
        onCreateSession={() => {}}
      />
    );
    expect(getByText('Start Chat')).not.toBeDisabled();
  });

  it('calls onCreateSession when button clicked', () => {
    const onCreateSession = jest.fn();
    const { getByText } = render(
      <SessionSetup
        collections={mockCollections}
        selectedCollection="test-collection"
        onCollectionChange={() => {}}
        onCreateSession={onCreateSession}
      />
    );
    fireEvent.click(getByText('Start Chat'));
    expect(onCreateSession).toHaveBeenCalledTimes(1);
  });
});
```

**Estimated Time**: 1 hour

---

### Task 1.5: Update ChatPage to use new components

**File**: `frontend/src/pages/ChatPage.tsx`

**Implementation Steps**:
1. Import new components:
   ```typescript
   import {
     ChatMessage,
     MessageList,
     MessageInput,
     SessionSetup
   } from '@/components/chat';
   ```

2. Replace inline JSX with component usage:
   ```typescript
   // Before (lines 156-183):
   {!session ? (
     <div className="bg-white rounded-lg shadow p-6">
       {/* ... inline session setup ... */}
     </div>
   ) : /* ... */}

   // After:
   {!session ? (
     <SessionSetup
       collections={collections?.collections}
       selectedCollection={selectedCollection}
       onCollectionChange={setSelectedCollection}
       onCreateSession={createSession}
     />
   ) : /* ... */}
   ```

3. Replace message list section:
   ```typescript
   // Before (lines 211-250):
   <div className="h-96 overflow-y-auto p-4 space-y-4">
     {/* ... inline message rendering ... */}
   </div>

   // After:
   <MessageList
     messages={messages}
     isGenerating={isGenerating}
     messagesEndRef={messagesEndRef}
   />
   ```

4. Replace input section:
   ```typescript
   // Before (lines 253-273):
   <div className="border-t p-4">
     {/* ... inline input ... */}
   </div>

   // After:
   <MessageInput
     value={input}
     onChange={(e) => setInput(e.target.value)}
     onSubmit={sendMessage}
     disabled={!isConnected}
     isGenerating={isGenerating}
   />
   ```

5. Clean up removed code (delete inline JSX)

6. Verify reduced line count (should drop from ~277 to ~180-200 lines)

**Technical Considerations**:
- Maintain all state management in ChatPage (don't lift state into components)
- Keep WebSocket logic in ChatPage
- Preserve useEffect hooks (auto-scroll, session creation)
- Don't change any business logic

**Refactoring Checklist**:
- [ ] Remove inline session setup JSX
- [ ] Remove inline message list JSX
- [ ] Remove inline input JSX
- [ ] Remove handleKeyPress function (moved to MessageInput)
- [ ] Keep all state hooks (useState, useRef)
- [ ] Keep all WebSocket logic
- [ ] Keep createSession and sendMessage functions
- [ ] Update imports
- [ ] Remove unused code

**Validation**:
- [ ] Page compiles without TypeScript errors
- [ ] All existing functionality works:
  - [ ] Session creation flow
  - [ ] Message sending (Enter key)
  - [ ] Message streaming display
  - [ ] Auto-scroll to bottom
  - [ ] Connection status display
  - [ ] End session button
- [ ] No visual changes (screenshot comparison)
- [ ] Reduced component complexity (line count down)
- [ ] Existing integration tests pass

**Testing**:
```bash
# Run existing tests
bun test frontend/src/pages/ChatPage.test.tsx

# Visual regression test
npm run test:visual -- --update-snapshots

# Integration test
npm run test:e2e -- chat-flow.spec.ts
```

**Estimated Time**: 1-1.5 hours

---

**Phase 1 Summary**:
- **Total Tasks**: 5
- **Estimated Effort**: 6-7.5 hours
- **Parallelization**: Tasks 1.1-1.4 can be done concurrently (4 devs can work simultaneously)
- **Critical Path**: All tasks → Task 1.5 (refactoring depends on component creation)
- **Output**: 4 new reusable components, cleaner ChatPage component

---

## Phase 2: Visual Design Polish
**Goal**: Apply modern chat UI patterns with improved visual hierarchy.

### Task 2.1: Update message bubble styling

**File**: `frontend/src/components/chat/ChatMessage.tsx`

**Implementation Steps**:
1. Update user message styling:
   ```typescript
   // Before:
   className={`max-w-[70%] rounded-lg p-3 ${
     message.role === 'user'
       ? 'bg-blue-500 text-white'
       : 'bg-gray-100 text-gray-900'
   }`}

   // After:
   className={`max-w-[70%] rounded-2xl p-3 md:p-4 shadow-sm ${
     message.role === 'user'
       ? 'bg-blue-600 text-white'
       : 'bg-gray-100 text-gray-900 border border-gray-200'
   }`}
   ```

2. Add gradient for user messages (optional modern touch):
   ```typescript
   // User message with gradient:
   'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-md'
   ```

3. Improve message container alignment:
   ```typescript
   <div className={`flex ${
     message.role === 'user' ? 'justify-end' : 'justify-start'
   } animate-fade-in-up`}>
   ```

4. Add hover effect for interactivity:
   ```typescript
   className={`... transition-all duration-150 hover:shadow-md`}
   ```

5. Responsive padding:
   ```typescript
   // Mobile: p-3, Desktop: p-4
   className={`... p-3 md:p-4`}
   ```

**Design Tokens**:
```typescript
// Create design tokens file: frontend/src/styles/chat-tokens.ts
export const chatTokens = {
  message: {
    user: {
      bg: 'bg-blue-600',
      text: 'text-white',
      border: '',
      shadow: 'shadow-md',
    },
    assistant: {
      bg: 'bg-gray-100',
      text: 'text-gray-900',
      border: 'border border-gray-200',
      shadow: 'shadow-sm',
    },
    maxWidth: 'max-w-[70%]',
    borderRadius: 'rounded-2xl',
    padding: 'p-3 md:p-4',
  },
  timestamp: {
    text: 'text-xs',
    color: 'text-gray-500',
    spacing: 'mt-1',
  },
};
```

**Before/After Comparison**:
| Aspect | Before | After |
|--------|--------|-------|
| Background | blue-500 | blue-600 (darker, better contrast) |
| Border Radius | rounded-lg (8px) | rounded-2xl (16px, more modern) |
| Padding | p-3 (12px) | p-3 md:p-4 (responsive) |
| Shadow | none | shadow-sm/md (depth) |
| Assistant Border | none | border-gray-200 (definition) |

**Technical Considerations**:
- Use Tailwind arbitrary values carefully (prefer predefined scales)
- Test color contrast (WCAG AA: 4.5:1 for normal text)
- Ensure touch targets remain >44x44px
- Test on different screen sizes (mobile, tablet, desktop)

**Color Contrast Testing**:
```bash
# Install contrast checker
npm install --save-dev wcag-contrast

# Test contrast ratios
node scripts/check-contrast.js
# blue-600 (#2563eb) on white: 8.59:1 ✓ AAA
# gray-900 (#111827) on gray-100 (#f3f4f6): 16.24:1 ✓ AAA
```

**Edge Cases**:
- Very short messages (single word) - still readable with new padding
- Very long messages - max-width prevents excessive width
- Code blocks in messages - handled by markdown renderer (Phase 4)
- RTL languages - test text-align with dir="rtl"

**Validation**:
- [ ] User messages darker blue (blue-600)
- [ ] Messages have rounded corners (16px radius)
- [ ] Responsive padding (12px mobile, 16px desktop)
- [ ] Subtle shadow on messages
- [ ] Assistant messages have light border
- [ ] Max width 70% maintained
- [ ] Hover effect smooth (150ms transition)
- [ ] Color contrast meets WCAG AA minimum
- [ ] Readable on all screen sizes

**Visual Regression**:
```typescript
// frontend/src/components/chat/__tests__/ChatMessage.visual.test.tsx
import { toMatchImageSnapshot } from 'jest-image-snapshot';

expect.extend({ toMatchImageSnapshot });

describe('ChatMessage Visual', () => {
  it('matches user message snapshot', async () => {
    const image = await captureComponent(
      <ChatMessage message={{ role: 'user', content: 'Test', timestamp: new Date() }} />
    );
    expect(image).toMatchImageSnapshot();
  });

  it('matches assistant message snapshot', async () => {
    const image = await captureComponent(
      <ChatMessage message={{ role: 'assistant', content: 'Response', timestamp: new Date() }} />
    );
    expect(image).toMatchImageSnapshot();
  });
});
```

**Estimated Time**: 2-2.5 hours

---

### Task 2.2: Add message avatars

**File**: `frontend/src/components/chat/ChatMessage.tsx`

**Implementation Steps**:
1. Create avatar component file:
   ```typescript
   // frontend/src/components/chat/MessageAvatar.tsx
   interface MessageAvatarProps {
     role: 'user' | 'assistant';
   }

   export function MessageAvatar({ role }: MessageAvatarProps) {
     if (role === 'user') {
       return (
         <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
           <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
             <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
           </svg>
         </div>
       );
     }

     return (
       <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white flex-shrink-0">
         <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
           <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
           <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
         </svg>
       </div>
     );
   }
   ```

2. Update ChatMessage to include avatar:
   ```typescript
   export function ChatMessage({ message, isStreaming, showTimestamp }: ChatMessageProps) {
     return (
       <div className={`flex items-start gap-2 ${
         message.role === 'user' ? 'justify-end flex-row-reverse' : 'justify-start'
       }`}>
         <MessageAvatar role={message.role} />

         <div className={`max-w-[70%] rounded-2xl p-3 md:p-4 shadow-sm ${
           message.role === 'user'
             ? 'bg-blue-600 text-white'
             : 'bg-gray-100 text-gray-900 border border-gray-200'
         }`}>
           <p className="whitespace-pre-wrap text-base leading-relaxed">
             {message.content}
           </p>
           {showTimestamp && message.timestamp && (
             <p className="text-xs mt-1 opacity-70">
               {formatTimestamp(message.timestamp)}
             </p>
           )}
         </div>
       </div>
     );
   }
   ```

3. Add timestamp formatting utility:
   ```typescript
   // frontend/src/utils/formatTimestamp.ts
   export function formatTimestamp(date: Date): string {
     const now = new Date();
     const diffMs = now.getTime() - date.getTime();
     const diffMins = Math.floor(diffMs / 60000);

     if (diffMins < 1) return 'Just now';
     if (diffMins < 60) return `${diffMins}m ago`;
     if (diffMins < 1440) return date.toLocaleTimeString('en-US', {
       hour: 'numeric',
       minute: '2-digit'
     });

     return date.toLocaleString('en-US', {
       month: 'short',
       day: 'numeric',
       hour: 'numeric',
       minute: '2-digit'
     });
   }
   ```

**Design Considerations**:
- Avatar size: 32px (w-8 h-8) - visible but not overwhelming
- User avatar: User icon in blue
- Assistant avatar: Chat bubbles in purple gradient
- Position: Left of message for assistant, right for user (using flex-row-reverse)
- Spacing: 8px gap between avatar and message (gap-2)

**Alternative Avatar Approaches**:
```typescript
// Option 1: Text initials
<div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
  U
</div>

// Option 2: Custom image (if user photos added later)
<img
  src={message.userAvatar || '/default-avatar.png'}
  alt={message.role}
  className="w-8 h-8 rounded-full object-cover"
/>

// Option 3: Emoji avatars
<div className="w-8 h-8 flex items-center justify-center text-xl">
  {message.role === 'user' ? '👤' : '🤖'}
</div>
```

**Technical Considerations**:
- Use `flex-shrink-0` on avatar to prevent squishing
- Use `items-start` to align avatar with top of message
- `flex-row-reverse` for user messages puts avatar on right
- SVG icons embedded inline (no external file dependencies)
- Icons from Heroicons (MIT licensed)

**Edge Cases**:
- Very long messages - avatar stays at top (items-start)
- Single-line messages - avatar vertically centered looks odd (stick with top align)
- Mobile screens - avatar size appropriate for touch targets

**Validation**:
- [ ] User avatar displays on right side
- [ ] Assistant avatar displays on left side
- [ ] Avatars 32px circular
- [ ] User avatar has user icon (blue background)
- [ ] Assistant avatar has chat icon (purple gradient)
- [ ] Gap between avatar and message (8px)
- [ ] Avatar aligned to top of message
- [ ] Avatar doesn't shrink on long messages
- [ ] Accessible alt text (implicit in SVG)

**Testing**:
```typescript
describe('MessageAvatar', () => {
  it('renders user avatar with correct icon', () => {
    const { container } = render(<MessageAvatar role="user" />);
    expect(container.querySelector('.bg-blue-600')).toBeInTheDocument();
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('renders assistant avatar with correct icon', () => {
    const { container } = render(<MessageAvatar role="assistant" />);
    expect(container.querySelector('.from-purple-500')).toBeInTheDocument();
  });

  it('has correct size classes', () => {
    const { container } = render(<MessageAvatar role="user" />);
    const avatar = container.firstChild;
    expect(avatar).toHaveClass('w-8', 'h-8', 'rounded-full');
  });
});
```

**Estimated Time**: 1.5-2 hours

---

### Task 2.3: Improve typography

**File**: `frontend/src/components/chat/ChatMessage.tsx` and global styles

**Implementation Steps**:
1. Update message text styling:
   ```typescript
   <p className="whitespace-pre-wrap text-base leading-relaxed font-normal">
     {message.content}
   </p>
   ```

2. Update timestamp styling:
   ```typescript
   <p className="text-xs leading-tight font-medium opacity-70 mt-1.5">
     {formatTimestamp(message.timestamp)}
   </p>
   ```

3. Update header typography in ChatPage:
   ```typescript
   // Session header
   <h2 className="text-lg font-semibold leading-snug text-gray-900">
     {session.collection_name}
   </h2>

   // Page title
   <h1 className="text-3xl font-bold leading-tight text-gray-900 mb-6">
     Chat
   </h1>
   ```

4. Create typography system:
   ```typescript
   // frontend/src/styles/typography.ts
   export const typography = {
     heading: {
       h1: 'text-3xl font-bold leading-tight',
       h2: 'text-xl font-semibold leading-snug',
       h3: 'text-lg font-semibold leading-normal',
     },
     body: {
       base: 'text-base leading-relaxed font-normal',
       small: 'text-sm leading-normal font-normal',
       tiny: 'text-xs leading-tight font-medium',
     },
     message: {
       content: 'text-base leading-relaxed whitespace-pre-wrap',
       timestamp: 'text-xs leading-tight opacity-70 mt-1.5',
     },
   };
   ```

5. Apply system font stack (if not already set):
   ```css
   /* frontend/src/index.css or global styles */
   body {
     font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto',
                  'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans',
                  'Helvetica Neue', sans-serif;
     -webkit-font-smoothing: antialiased;
     -moz-osx-font-smoothing: grayscale;
   }
   ```

**Typography Scale**:
| Element | Size | Line Height | Weight | Use Case |
|---------|------|-------------|--------|----------|
| h1 | 30px (text-3xl) | 36px (tight) | 700 (bold) | Page title |
| h2 | 20px (text-xl) | 28px (snug) | 600 (semibold) | Section headers |
| h3 | 18px (text-lg) | 28px (normal) | 600 (semibold) | Subsections |
| Body | 16px (text-base) | 24px (relaxed) | 400 (normal) | Message content |
| Small | 14px (text-sm) | 20px (normal) | 400 (normal) | Helper text |
| Tiny | 12px (text-xs) | 16px (tight) | 500 (medium) | Timestamps, labels |

**Line Height Rationale**:
- **Tight (1.25)**: Headings - compact for visual impact
- **Snug (1.375)**: Subheadings - slightly more breathing room
- **Normal (1.5)**: Small body text - standard readable
- **Relaxed (1.625)**: Message content - extra space for long-form reading

**Technical Considerations**:
- Use system font stack for best performance (no web font loading)
- `leading-relaxed` improves readability for longer messages
- `whitespace-pre-wrap` preserves user formatting (newlines)
- Font weights: 400 (normal), 500 (medium), 600 (semibold), 700 (bold)
- Test on Windows/Mac/Linux for font rendering differences

**Accessibility**:
- Minimum font size 12px (text-xs) - meets accessibility guidelines
- Line height 1.5+ for body text - improves readability for dyslexic users
- Sufficient contrast maintained with new typography

**Edge Cases**:
- Very long words (URLs) - handled by word-break utilities if needed
- Mixed languages - system fonts support most scripts
- Emoji in text - rendered at same size as text

**Validation**:
- [ ] Message content uses text-base (16px)
- [ ] Message content has relaxed leading (1.625)
- [ ] Timestamps use text-xs (12px)
- [ ] Timestamps have tight leading (1.25)
- [ ] Headings use appropriate font weights
- [ ] Text renders smoothly (antialiasing)
- [ ] Hierarchy clear (size differences obvious)
- [ ] Readable on all screen sizes

**Visual Comparison**:
```typescript
// Before:
<p className="whitespace-pre-wrap">{msg.content}</p>
<p className="text-xs mt-1 opacity-70">{timestamp}</p>

// After:
<p className="whitespace-pre-wrap text-base leading-relaxed">
  {msg.content}
</p>
<p className="text-xs leading-tight font-medium opacity-70 mt-1.5">
  {timestamp}
</p>
```

**Estimated Time**: 1-1.5 hours

---

### Task 2.4: Enhance connection status display

**File**: `frontend/src/pages/ChatPage.tsx` (create new component later)

**Implementation Steps**:
1. Create ConnectionStatus component:
   ```typescript
   // frontend/src/components/chat/ConnectionStatus.tsx
   interface ConnectionStatusProps {
     isConnected: boolean;
     isConnecting?: boolean;
   }

   export function ConnectionStatus({ isConnected, isConnecting = false }: ConnectionStatusProps) {
     if (isConnecting) {
       return (
         <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-50 border border-yellow-200">
           <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
           <span className="text-sm font-medium text-yellow-800">
             Connecting...
           </span>
         </div>
       );
     }

     if (isConnected) {
       return (
         <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 border border-green-200">
           <div className="w-2 h-2 rounded-full bg-green-500" />
           <span className="text-sm font-medium text-green-800">
             Connected
           </span>
         </div>
       );
     }

     return (
       <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-50 border border-red-200">
         <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
           <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
         </svg>
         <span className="text-sm font-medium text-red-800">
           Disconnected
         </span>
       </div>
     );
   }
   ```

2. Update ChatPage header to use component:
   ```typescript
   // Replace lines 187-196
   <div className="border-b p-4 flex items-center justify-between bg-white">
     <div className="flex items-center gap-4">
       <div>
         <h2 className="text-lg font-semibold leading-snug text-gray-900">
           {session.collection_name}
         </h2>
       </div>
       <ConnectionStatus isConnected={isConnected} />
     </div>
     <button
       onClick={() => {
         wsRef.current?.close();
         setSession(null);
         setMessages([]);
       }}
       className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
     >
       End Session
     </button>
   </div>
   ```

3. Add connection state management (if not exists):
   ```typescript
   const [isConnecting, setIsConnecting] = useState(false);

   // In createSession function:
   setIsConnecting(true);
   const ws = new WebSocket(wsUrl);

   ws.onopen = () => {
     setIsConnected(true);
     setIsConnecting(false);
   };

   ws.onerror = () => {
     setIsConnected(false);
     setIsConnecting(false);
   };
   ```

**Design Tokens**:
```typescript
const statusStyles = {
  connected: {
    container: 'bg-green-50 border-green-200',
    dot: 'bg-green-500',
    text: 'text-green-800',
    icon: null,
  },
  connecting: {
    container: 'bg-yellow-50 border-yellow-200',
    dot: 'bg-yellow-500 animate-pulse',
    text: 'text-yellow-800',
    icon: null,
  },
  disconnected: {
    container: 'bg-red-50 border-red-200',
    dot: null,
    text: 'text-red-800',
    icon: 'text-red-500',
  },
};
```

**Color Accessibility**:
- Green: Sufficient contrast on light background
- Yellow: Warning color, pulsing animation adds emphasis
- Red: Error color with icon for redundancy (not just color)

**Technical Considerations**:
- Use semantic colors (green=success, yellow=warning, red=error)
- Include icon for disconnected state (not just color-dependent)
- Pulsing animation for connecting state shows activity
- `inline-flex` allows badge to size to content
- Position prominently in header (not small text)

**Edge Cases**:
- Rapid connect/disconnect cycles - debounce state changes
- Long connection time - show "Connecting..." with timeout warning
- Never connects - show error message after timeout

**Validation**:
- [ ] Connected badge shows green with checkmark dot
- [ ] Connecting badge shows yellow with pulsing dot
- [ ] Disconnected badge shows red with warning icon
- [ ] Badge positioned prominently in header
- [ ] Text clearly readable (contrast)
- [ ] Animation smooth (60fps)
- [ ] Badge updates in real-time with connection state
- [ ] Color-blind friendly (icons + color)

**Testing**:
```typescript
describe('ConnectionStatus', () => {
  it('renders connected state', () => {
    const { getByText, container } = render(
      <ConnectionStatus isConnected={true} />
    );
    expect(getByText('Connected')).toBeInTheDocument();
    expect(container.querySelector('.bg-green-50')).toBeInTheDocument();
  });

  it('renders connecting state', () => {
    const { getByText, container } = render(
      <ConnectionStatus isConnected={false} isConnecting={true} />
    );
    expect(getByText('Connecting...')).toBeInTheDocument();
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders disconnected state', () => {
    const { getByText, container } = render(
      <ConnectionStatus isConnected={false} />
    );
    expect(getByText('Disconnected')).toBeInTheDocument();
    expect(container.querySelector('.bg-red-50')).toBeInTheDocument();
    expect(container.querySelector('svg')).toBeInTheDocument();
  });
});
```

**Estimated Time**: 1.5-2 hours

---

### Task 2.5: Responsive layout improvements

**Files**: All chat components

**Implementation Steps**:

1. **Mobile optimizations (< 640px)**:
   ```typescript
   // MessageList.tsx - Reduce height on mobile
   <div className="h-80 sm:h-96 overflow-y-auto p-2 sm:p-4 space-y-3 sm:space-y-4">

   // ChatMessage.tsx - Adjust padding
   <div className="p-2.5 sm:p-3 md:p-4 ...">

   // MessageInput.tsx - Full width on mobile
   <div className="border-t p-2 sm:p-4">
     <div className="flex flex-col sm:flex-row gap-2">
       <textarea className="w-full sm:flex-1 ..." />
       <button className="w-full sm:w-auto min-h-[44px] ...">
         Send
       </button>
     </div>
   </div>
   ```

2. **Tablet optimizations (640px - 1024px)**:
   ```typescript
   // ChatPage.tsx - Adjust container width
   <div className="w-full sm:max-w-3xl lg:max-w-5xl mx-auto p-2 sm:p-4">

   // ChatMessage.tsx - Responsive max-width
   <div className="max-w-[85%] sm:max-w-[75%] lg:max-w-[70%] ...">
   ```

3. **Desktop optimizations (> 1024px)**:
   ```typescript
   // Use comfortable spacing
   <div className="p-4 lg:p-6 space-y-4 lg:space-y-6">

   // Larger avatars on desktop
   <MessageAvatar className="w-8 h-8 lg:w-10 lg:h-10" />
   ```

4. **Touch target improvements**:
   ```typescript
   // Ensure all interactive elements ≥ 44x44px on mobile
   <button className="min-h-[44px] min-w-[44px] px-4 ...">

   // Prompt suggestions
   <button className="min-h-[44px] px-4 py-2 ...">

   // Message actions (Phase 5)
   <button className="p-2 min-w-[44px] min-h-[44px] ...">
   ```

5. **Create responsive breakpoint constants**:
   ```typescript
   // frontend/src/utils/breakpoints.ts
   export const breakpoints = {
     sm: 640,   // Small devices (phones)
     md: 768,   // Medium devices (tablets)
     lg: 1024,  // Large devices (desktops)
     xl: 1280,  // Extra large devices
   };

   export const useBreakpoint = () => {
     const [breakpoint, setBreakpoint] = useState('sm');

     useEffect(() => {
       const handleResize = () => {
         const width = window.innerWidth;
         if (width >= breakpoints.lg) setBreakpoint('lg');
         else if (width >= breakpoints.md) setBreakpoint('md');
         else setBreakpoint('sm');
       };

       handleResize();
       window.addEventListener('resize', handleResize);
       return () => window.removeEventListener('resize', handleResize);
     }, []);

     return breakpoint;
   };
   ```

6. **Mobile-specific interaction patterns**:
   ```typescript
   // Show message actions always on mobile (not hover)
   const breakpoint = useBreakpoint();
   const showActionsAlways = breakpoint === 'sm';

   <MessageActions
     visible={showActionsAlways || isHovered}
   />
   ```

**Responsive Testing Matrix**:
| Device | Width | Layout | Touch Targets | Spacing |
|--------|-------|--------|---------------|---------|
| iPhone SE | 375px | Single column | 44x44px min | Compact (p-2) |
| iPhone 12/13 | 390px | Single column | 44x44px min | Compact |
| iPad Mini | 768px | Wide column | 44x44px min | Medium (p-3) |
| iPad Pro | 1024px | Wide column | Hover OK | Comfortable (p-4) |
| Desktop | 1440px+ | Max-width container | Hover OK | Spacious (p-6) |

**Touch Target Guidelines** (iOS/Android HIG):
- Minimum: 44x44px (44dp Android, 44pt iOS)
- Comfortable: 48x48px
- Spacing between targets: 8px minimum

**Technical Considerations**:
- Use Tailwind responsive prefixes: `sm:`, `md:`, `lg:`, `xl:`
- Mobile-first approach: base styles for mobile, add modifiers for larger screens
- Test with Chrome DevTools device emulator
- Test on real devices when possible
- Consider notch/safe areas on newer phones

**Viewport Meta Tag** (verify exists):
```html
<!-- frontend/public/index.html -->
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
```

**Edge Cases**:
- Landscape mode on phones (reduce vertical padding)
- Split-screen mode on tablets (test at 512px width)
- Browser zoom (test at 150%, 200%)
- Very small phones (320px width - iPhone 5)
- Foldable devices (unusual aspect ratios)

**Validation**:
- [ ] Layout works at 320px (iPhone 5)
- [ ] Layout works at 375px (iPhone SE/8)
- [ ] Layout works at 768px (iPad)
- [ ] Layout works at 1024px (iPad Pro)
- [ ] Layout works at 1440px+ (Desktop)
- [ ] All touch targets ≥ 44x44px on mobile
- [ ] Buttons stack vertically on mobile (MessageInput)
- [ ] Comfortable spacing on all screen sizes
- [ ] No horizontal scroll on any device
- [ ] Message actions visible on mobile (not hover-only)
- [ ] Text readable at all sizes (no truncation)

**Testing Checklist**:
```bash
# Chrome DevTools
- iPhone SE (375x667)
- iPhone 12 Pro (390x844)
- iPad Air (820x1180)
- iPad Pro 12.9" (1024x1366)
- Desktop (1920x1080)

# Test interactions:
- Tap targets on mobile
- Hover states on desktop
- Scroll performance
- Input focus states
- Orientation change (portrait/landscape)
```

**Playwright E2E Test**:
```typescript
// frontend/tests/e2e/responsive.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Responsive Layout', () => {
  test('mobile layout works correctly', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/chat');

    // Touch targets should be large enough
    const sendButton = page.locator('button:has-text("Send")');
    const box = await sendButton.boundingBox();
    expect(box?.height).toBeGreaterThanOrEqual(44);
    expect(box?.width).toBeGreaterThanOrEqual(44);
  });

  test('tablet layout works correctly', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/chat');

    // Container should have max-width
    const container = page.locator('.max-w-3xl');
    expect(await container.count()).toBe(1);
  });

  test('desktop layout works correctly', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/chat');

    // Message actions should appear on hover
    await page.hover('.ChatMessage');
    const actions = page.locator('.MessageActions');
    await expect(actions).toBeVisible();
  });
});
```

**Estimated Time**: 2-3 hours

---

**Phase 2 Summary**:
- **Total Tasks**: 5
- **Estimated Effort**: 8.5-11 hours
- **Parallelization**: Tasks 2.1-2.3 can be done concurrently
- **Output**: Modern visual design, improved hierarchy, responsive layout

---

## Phase 3: Enhanced Interaction Features
**Goal**: Add typing indicators, prompt suggestions, and improved input.

### Task 3.1: Implement TypingIndicator component

**File**: `frontend/src/components/chat/TypingIndicator.tsx`

**Implementation Steps**:

1. Create TypingIndicator component:
   ```typescript
   export function TypingIndicator() {
     return (
       <div
         className="flex justify-start"
         role="status"
         aria-live="polite"
         aria-label="Assistant is typing"
       >
         <div className="flex items-start gap-2">
           {/* Avatar matching assistant style */}
           <MessageAvatar role="assistant" />

           {/* Typing bubble */}
           <div className="bg-gray-100 border border-gray-200 rounded-2xl p-4 shadow-sm">
             <div className="flex items-center gap-1" aria-hidden="true">
               <div className="w-2 h-2 bg-gray-400 rounded-full animate-typing-dot-bounce" />
               <div className="w-2 h-2 bg-gray-400 rounded-full animate-typing-dot-bounce animation-delay-200" />
               <div className="w-2 h-2 bg-gray-400 rounded-full animate-typing-dot-bounce animation-delay-400" />
             </div>
             <span className="sr-only">Assistant is typing</span>
           </div>
         </div>
       </div>
     );
   }
   ```

2. Add Tailwind animation config:
   ```javascript
   // frontend/tailwind.config.js
   module.exports = {
     theme: {
       extend: {
         keyframes: {
           'typing-dot-bounce': {
             '0%, 60%, 100%': {
               transform: 'translateY(0)',
             },
             '30%': {
               transform: 'translateY(-8px)',
             },
           },
         },
         animation: {
           'typing-dot-bounce': 'typing-dot-bounce 1.4s infinite ease-in-out',
         },
       },
     },
     plugins: [
       function ({ addUtilities }) {
         const newUtilities = {
           '.animation-delay-200': {
             'animation-delay': '0.2s',
           },
           '.animation-delay-400': {
             'animation-delay': '0.4s',
           },
         };
         addUtilities(newUtilities);
       },
     ],
   };
   ```

3. Integrate into MessageList:
   ```typescript
   // MessageList.tsx
   export function MessageList({ messages, isGenerating, messagesEndRef }: MessageListProps) {
     return (
       <div className="h-96 overflow-y-auto p-4 space-y-4">
         {messages.length === 0 && !isGenerating && (
           <p className="text-center text-gray-500 mt-8">
             Start a conversation by typing a message below
           </p>
         )}

         {messages.map((msg, idx) => (
           <ChatMessage
             key={msg.id || `${msg.role}-${idx}`}
             message={msg}
             showTimestamp={!!msg.timestamp}
           />
         ))}

         {isGenerating && <TypingIndicator />}

         <div ref={messagesEndRef} />
       </div>
     );
   }
   ```

**Animation Timing**:
- Duration: 1.4s (industry standard for typing indicator)
- Stagger: 0.2s between dots (200ms, 400ms delays)
- Motion: Bounce up 8px, ease-in-out
- Infinite loop

**Accessibility**:
- `role="status"`: Announces as status update
- `aria-live="polite"`: Waits for pause before announcing
- `aria-label="Assistant is typing"`: Descriptive label
- `aria-hidden="true"` on visual dots: Hide decorative elements
- `sr-only` text: Provides context for screen readers

**Performance Optimization**:
```typescript
// Memoize to prevent re-renders
export const TypingIndicator = React.memo(function TypingIndicator() {
  // ... component code
});
```

**Alternative Implementations**:
```typescript
// Option 1: Pulse animation (simpler)
<div className="flex gap-1">
  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
</div>

// Option 2: Ellipsis text (no animation)
<div className="text-gray-400 font-medium">
  Typing<span className="animate-pulse">...</span>
</div>

// Option 3: Custom SVG animation
<svg width="40" height="10" viewBox="0 0 40 10">
  <circle cx="5" cy="5" r="3" className="typing-dot">
    <animate attributeName="opacity" values="0.4;1;0.4" dur="1.4s" repeatCount="indefinite" />
  </circle>
  {/* ... more dots */}
</svg>
```

**Technical Considerations**:
- Use CSS animations (more performant than JS)
- Infinite loop with `animate-typing-dot-bounce`
- GPU-accelerated (transform property)
- Maintains 60fps
- Respects `prefers-reduced-motion` (will add in Phase 6)

**Edge Cases**:
- Very fast generation (indicator briefly visible) - acceptable
- Multiple generations in sequence - indicator shows/hides correctly
- Generation error before completion - hide indicator, show error

**Validation**:
- [ ] Three dots bounce in sequence
- [ ] Animation smooth (60fps)
- [ ] Stagger timing correct (200ms, 400ms)
- [ ] Bubble matches assistant message style
- [ ] Avatar displays (assistant style)
- [ ] Announces to screen reader "Assistant is typing"
- [ ] Shows/hides correctly with isGenerating state
- [ ] Positioned as assistant message (left-aligned)
- [ ] Auto-scrolls into view when appears

**Testing**:
```typescript
describe('TypingIndicator', () => {
  it('renders with correct ARIA attributes', () => {
    const { container } = render(<TypingIndicator />);
    const status = container.querySelector('[role="status"]');
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).toHaveAttribute('aria-label', 'Assistant is typing');
  });

  it('renders three dots', () => {
    const { container } = render(<TypingIndicator />);
    const dots = container.querySelectorAll('.animate-typing-dot-bounce');
    expect(dots).toHaveLength(3);
  });

  it('includes screen reader text', () => {
    const { container } = render(<TypingIndicator />);
    const srText = container.querySelector('.sr-only');
    expect(srText).toHaveTextContent('Assistant is typing');
  });

  it('has correct stagger delays', () => {
    const { container } = render(<TypingIndicator />);
    const dots = container.querySelectorAll('.animate-typing-dot-bounce');
    expect(dots[1]).toHaveClass('animation-delay-200');
    expect(dots[2]).toHaveClass('animation-delay-400');
  });
});
```

**Visual Regression**:
```typescript
test('TypingIndicator animation renders correctly', async ({ page }) => {
  await page.goto('/chat-storybook/typing-indicator');

  // Wait for animation to start
  await page.waitForTimeout(100);

  // Capture at different points in animation
  await page.screenshot({ path: 'typing-0ms.png' });
  await page.waitForTimeout(300);
  await page.screenshot({ path: 'typing-300ms.png' });
  await page.waitForTimeout(300);
  await page.screenshot({ path: 'typing-600ms.png' });
});
```

**Estimated Time**: 2-2.5 hours

---

### Task 3.2: Add streaming cursor to messages

**File**: `frontend/src/components/chat/ChatMessage.tsx`

**Implementation Steps**:

1. Add cursor element to streaming messages:
   ```typescript
   export function ChatMessage({ message, isStreaming, showTimestamp }: ChatMessageProps) {
     return (
       <div className={`flex items-start gap-2 ${...}`}>
         <MessageAvatar role={message.role} />

         <div className={`max-w-[70%] rounded-2xl p-3 md:p-4 ${...}`}>
           <div className="whitespace-pre-wrap text-base leading-relaxed inline">
             {message.content}
             {isStreaming && message.role === 'assistant' && (
               <span
                 className="inline-block w-0.5 h-5 bg-current ml-0.5 animate-pulse"
                 aria-hidden="true"
               />
             )}
           </div>

           {showTimestamp && message.timestamp && !isStreaming && (
             <p className="text-xs leading-tight font-medium opacity-70 mt-1.5">
               {formatTimestamp(message.timestamp)}
             </p>
           )}
         </div>
       </div>
     );
   }
   ```

2. Create custom pulse animation (optional):
   ```javascript
   // tailwind.config.js
   keyframes: {
     'cursor-blink': {
       '0%, 49%': { opacity: '1' },
       '50%, 100%': { opacity: '0' },
     },
   },
   animation: {
     'cursor-blink': 'cursor-blink 1s infinite',
   },
   ```

3. Update ChatMessage prop interface:
   ```typescript
   interface ChatMessageProps {
     message: Message;
     isStreaming?: boolean;  // Already exists
     showTimestamp?: boolean;
   }
   ```

4. Update parent component to pass isStreaming:
   ```typescript
   // MessageList.tsx
   {messages.map((msg, idx) => {
     const isLastMessage = idx === messages.length - 1;
     const streamingThisMessage = isGenerating &&
                                   isLastMessage &&
                                   msg.role === 'assistant' &&
                                   !msg.timestamp;

     return (
       <ChatMessage
         key={msg.id || `${msg.role}-${idx}`}
         message={msg}
         isStreaming={streamingThisMessage}
         showTimestamp={!!msg.timestamp}
       />
     );
   })}
   ```

**Cursor Design Options**:
```typescript
// Option 1: Thin vertical line (minimal)
<span className="w-0.5 h-5 bg-current ml-0.5 animate-pulse" />

// Option 2: Thicker block cursor (like terminal)
<span className="w-2 h-5 bg-current ml-1 animate-pulse" />

// Option 3: Blinking cursor (classic)
<span className="w-0.5 h-5 bg-current ml-0.5 animate-cursor-blink" />

// Option 4: Pulsing dot (subtle)
<span className="w-1.5 h-1.5 rounded-full bg-current ml-1 align-middle animate-pulse" />
```

**Recommended**: Option 1 (thin vertical line with pulse) - modern, subtle, doesn't distract

**Technical Considerations**:
- Use `inline-block` for cursor to flow with text
- Match cursor color to text (`bg-current`)
- Height matches text line-height (`h-5` ≈ 20px)
- Small left margin (`ml-0.5`) for spacing
- Only show for assistant messages (not user)
- Only show while streaming (not after completion)
- Hide timestamp while streaming

**Animation Behavior**:
- Tailwind `animate-pulse`: 2s fade in/out
- Custom `cursor-blink`: 1s hard on/off (more noticeable)
- Matches typing cursor in text editors

**Edge Cases**:
- Empty content (cursor at start of message)
- Very long content (cursor at end, scrolled into view)
- Multi-line content (cursor on last line)
- Content with trailing newline (cursor placement)

**Validation**:
- [ ] Cursor displays during streaming (assistant messages only)
- [ ] Cursor pulses smoothly
- [ ] Cursor positioned at end of text
- [ ] Cursor height matches text line-height
- [ ] Cursor color matches text color
- [ ] Cursor hidden when streaming completes
- [ ] Timestamp shows after streaming completes
- [ ] Cursor flows inline with text (no line break)

**Testing**:
```typescript
describe('ChatMessage streaming cursor', () => {
  it('shows cursor when streaming assistant message', () => {
    const message = {
      role: 'assistant',
      content: 'Streaming text',
      timestamp: null,
    };
    const { container } = render(
      <ChatMessage message={message} isStreaming={true} />
    );
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('hides cursor when not streaming', () => {
    const message = {
      role: 'assistant',
      content: 'Complete text',
      timestamp: new Date(),
    };
    const { container } = render(
      <ChatMessage message={message} isStreaming={false} />
    );
    expect(container.querySelector('.animate-pulse')).not.toBeInTheDocument();
  });

  it('never shows cursor for user messages', () => {
    const message = {
      role: 'user',
      content: 'User message',
      timestamp: null,
    };
    const { container } = render(
      <ChatMessage message={message} isStreaming={true} />
    );
    expect(container.querySelector('.animate-pulse')).not.toBeInTheDocument();
  });

  it('hides timestamp while streaming', () => {
    const message = {
      role: 'assistant',
      content: 'Streaming',
      timestamp: null,
    };
    const { container } = render(
      <ChatMessage message={message} isStreaming={true} showTimestamp={true} />
    );
    expect(container.querySelector('.text-xs')).not.toBeInTheDocument();
  });
});
```

**Estimated Time**: 1-1.5 hours

---

### Task 3.3: Create PromptSuggestions component

**File**: `frontend/src/components/chat/PromptSuggestions.tsx`

**Implementation Steps**:

1. Create PromptSuggestions component:
   ```typescript
   interface PromptSuggestionsProps {
     suggestions: string[];
     onSelect: (suggestion: string) => void;
     label?: string;
   }

   export function PromptSuggestions({
     suggestions,
     onSelect,
     label = "Try asking:"
   }: PromptSuggestionsProps) {
     return (
       <div className="flex flex-col items-center justify-center py-8 px-4">
         {/* Header */}
         <div className="mb-6 text-center">
           <h3 className="text-lg font-semibold text-gray-900 mb-2">
             {label}
           </h3>
           <p className="text-sm text-gray-500">
             Select a suggestion below or type your own question
           </p>
         </div>

         {/* Suggestions Grid */}
         <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
           {suggestions.map((suggestion, idx) => (
             <button
               key={idx}
               onClick={() => onSelect(suggestion)}
               className="group flex items-start gap-3 p-4 text-left border border-gray-200 rounded-xl bg-white hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 shadow-sm hover:shadow-md"
             >
               {/* Icon */}
               <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-100 group-hover:bg-blue-200 flex items-center justify-center transition-colors">
                 <svg
                   className="w-5 h-5 text-blue-600"
                   fill="none"
                   viewBox="0 0 24 24"
                   stroke="currentColor"
                 >
                   <path
                     strokeLinecap="round"
                     strokeLinejoin="round"
                     strokeWidth={2}
                     d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                   />
                 </svg>
               </div>

               {/* Text */}
               <div className="flex-1 min-w-0">
                 <p className="text-sm font-medium text-gray-900 group-hover:text-blue-900 transition-colors">
                   {suggestion}
                 </p>
               </div>

               {/* Arrow */}
               <svg
                 className="flex-shrink-0 w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors"
                 fill="none"
                 viewBox="0 0 24 24"
                 stroke="currentColor"
               >
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
               </svg>
             </button>
           ))}
         </div>
       </div>
     );
   }
   ```

2. Integrate into MessageList:
   ```typescript
   export function MessageList({ messages, isGenerating, messagesEndRef, onSelectSuggestion }: MessageListProps) {
     const isEmpty = messages.length === 0 && !isGenerating;

     return (
       <div className="h-96 overflow-y-auto p-4">
         {isEmpty ? (
           <PromptSuggestions
             suggestions={DEFAULT_SUGGESTIONS}
             onSelect={onSelectSuggestion}
           />
         ) : (
           <div className="space-y-4">
             {messages.map((msg, idx) => (
               <ChatMessage
                 key={msg.id || `${msg.role}-${idx}`}
                 message={msg}
                 isStreaming={isGenerating && idx === messages.length - 1}
                 showTimestamp={!!msg.timestamp}
               />
             ))}

             {isGenerating && <TypingIndicator />}
           </div>
         )}

         <div ref={messagesEndRef} />
       </div>
     );
   }
   ```

3. Wire up in ChatPage:
   ```typescript
   const handleSuggestionSelect = (suggestion: string) => {
     setInput(suggestion);
     // Auto-send
     if (wsRef.current && isConnected) {
       const userMessage: Message = {
         role: 'user',
         content: suggestion,
         timestamp: new Date(),
       };
       setMessages((prev) => [...prev, userMessage]);
       setIsGenerating(true);
       wsRef.current.send(JSON.stringify({
         type: 'user_message',
         content: suggestion,
       }));
     }
   };

   <MessageList
     messages={messages}
     isGenerating={isGenerating}
     messagesEndRef={messagesEndRef}
     onSelectSuggestion={handleSuggestionSelect}
   />
   ```

**Design Rationale**:
- **Grid Layout**: 2 columns on desktop, 1 on mobile
- **Card Style**: Rounded corners, shadow, hover effects
- **Icons**: Question mark icon (universal "ask" symbol)
- **Hover**: Border changes blue, background tints blue, shadow increases
- **Arrow**: Right-pointing arrow indicates action/navigation

**Alternative Layouts**:
```typescript
// Option 1: Pill/tag style (compact)
<div className="flex flex-wrap gap-2 justify-center">
  {suggestions.map((suggestion) => (
    <button className="px-4 py-2 rounded-full bg-gray-100 hover:bg-blue-100 text-sm">
      {suggestion}
    </button>
  ))}
</div>

// Option 2: List style (simple)
<div className="space-y-2">
  {suggestions.map((suggestion) => (
    <button className="w-full text-left p-3 rounded-lg hover:bg-gray-50">
      {suggestion}
    </button>
  ))}
</div>

// Option 3: Icon grid (visual)
<div className="grid grid-cols-2 gap-4">
  {suggestions.map(({ text, emoji }) => (
    <button className="flex flex-col items-center p-4 border rounded-lg">
      <span className="text-3xl mb-2">{emoji}</span>
      <span className="text-sm">{text}</span>
    </button>
  ))}
</div>
```

**Recommended**: Card/button hybrid (as shown) - best balance of visual appeal and usability

**Accessibility**:
- Buttons are keyboard-navigable (Tab)
- Enter/Space activates suggestion
- Clear hover/focus states
- Descriptive button text (full suggestion as label)
- Semantic HTML (button elements)

**Technical Considerations**:
- Suggestions hidden once first message sent
- Auto-send on click (don't just fill input)
- Clear visual feedback on hover/click
- Responsive grid (1 col mobile, 2 col desktop)
- Touch-friendly on mobile (large tap targets)

**Edge Cases**:
- Long suggestion text (wrap to multiple lines)
- Very short suggestion (still looks good)
- 3 suggestions (grid adjusts)
- 6+ suggestions (add scroll or limit to 4-6)

**Validation**:
- [ ] Displays when message list empty
- [ ] Hides after first message sent
- [ ] 2-column grid on desktop
- [ ] 1-column on mobile
- [ ] Hover effects smooth (border, background, shadow)
- [ ] Click auto-sends message
- [ ] Keyboard accessible (Tab, Enter)
- [ ] Icons display correctly
- [ ] Text wraps for long suggestions
- [ ] Touch-friendly on mobile

**Testing**:
```typescript
describe('PromptSuggestions', () => {
  const mockSuggestions = [
    'Summarize the key findings',
    'What are the main themes?',
  ];

  it('renders all suggestions', () => {
    const { getByText } = render(
      <PromptSuggestions
        suggestions={mockSuggestions}
        onSelect={() => {}}
      />
    );
    expect(getByText('Summarize the key findings')).toBeInTheDocument();
    expect(getByText('What are the main themes?')).toBeInTheDocument();
  });

  it('calls onSelect when suggestion clicked', () => {
    const onSelect = jest.fn();
    const { getByText } = render(
      <PromptSuggestions
        suggestions={mockSuggestions}
        onSelect={onSelect}
      />
    );
    fireEvent.click(getByText('Summarize the key findings'));
    expect(onSelect).toHaveBeenCalledWith('Summarize the key findings');
  });

  it('renders custom label', () => {
    const { getByText } = render(
      <PromptSuggestions
        suggestions={mockSuggestions}
        onSelect={() => {}}
        label="Custom label:"
      />
    );
    expect(getByText('Custom label:')).toBeInTheDocument();
  });

  it('has keyboard accessible buttons', () => {
    const { getAllByRole } = render(
      <PromptSuggestions
        suggestions={mockSuggestions}
        onSelect={() => {}}
      />
    );
    const buttons = getAllByRole('button');
    expect(buttons).toHaveLength(2);
    buttons.forEach(button => {
      expect(button).toHaveAttribute('type', 'button');
    });
  });
});
```

**Estimated Time**: 2.5-3 hours

---

### Task 3.4: Define prompt suggestion content

**File**: `frontend/src/constants/suggestions.ts`

**Implementation Steps**:
1. Create default suggestions array:
   ```typescript
   export const DEFAULT_SUGGESTIONS = [
     "Summarize the key findings from recent documents",
     "What are the main themes across these documents?",
     "Find information about [specific topic in collection]",
     "How do these documents relate to each other?",
   ];
   ```

2. Create collection-aware suggestion generator:
   ```typescript
   export function getCollectionSuggestions(collectionName: string, metadata?: Record<string, any>): string[] {
     // If metadata includes topic/domain
     if (metadata?.topic) {
       return [
         `Summarize key points about ${metadata.topic}`,
         `What are recent developments in ${metadata.topic}?`,
         `Compare different approaches to ${metadata.topic}`,
         `What questions remain unanswered about ${metadata.topic}?`,
       ];
     }

     // Use collection name as context
     return [
       `Summarize the ${collectionName} collection`,
       `What are the key insights from ${collectionName}?`,
       `Find patterns in ${collectionName} documents`,
       `What's missing from ${collectionName}?`,
     ];
   }
   ```

3. Add suggestion categories:
   ```typescript
   export const SUGGESTION_CATEGORIES = {
     summary: ["Summarize...", "What are the key findings..."],
     analysis: ["Compare...", "What patterns exist..."],
     search: ["Find information about...", "Show me documents related to..."],
     insights: ["What insights can you provide...", "What's the relationship between..."],
   };
   ```

**Validation**:
- [ ] Suggestions are clear and actionable
- [ ] Suggestions relevant to RAG use case
- [ ] Collection-aware suggestions use metadata
- [ ] Fallback to generic suggestions works

**Estimated Time**: 30-45 minutes

---

### Task 3.5: Implement auto-resizing textarea

**File**: `frontend/src/components/chat/MessageInput.tsx`

**Implementation Steps**:
1. Add auto-resize hook:
   ```typescript
   function useAutoResizeTextarea(value: string, minRows = 2, maxRows = 8) {
     const textareaRef = useRef<HTMLTextAreaElement>(null);

     useEffect(() => {
       const textarea = textareaRef.current;
       if (!textarea) return;

       // Reset height to auto to get the correct scrollHeight
       textarea.style.height = 'auto';

       // Calculate new height
       const lineHeight = 24; // text-base line height
       const minHeight = lineHeight * minRows;
       const maxHeight = lineHeight * maxRows;
       const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);

       textarea.style.height = `${newHeight}px`;
     }, [value, minRows, maxRows]);

     return textareaRef;
   }
   ```

2. Update MessageInput component:
   ```typescript
   export function MessageInput({ value, onChange, ... }: MessageInputProps) {
     const textareaRef = useAutoResizeTextarea(value, 2, 8);

     return (
       <textarea
         ref={textareaRef}
         value={value}
         onChange={onChange}
         className="flex-1 p-2 border rounded resize-none overflow-y-auto"
         style={{ minHeight: '48px', maxHeight: '192px' }}
         rows={2}
         ...
       />
     );
   }
   ```

**Technical Notes**:
- Reset height to 'auto' before measuring scrollHeight
- Use `overflow-y-auto` when maxHeight reached
- Preserve `resize-none` to prevent manual resize

**Validation**:
- [ ] Textarea grows with content (2-8 rows)
- [ ] Scrolls when max height reached
- [ ] No jumping or flickering during resize
- [ ] Works on paste and keyboard input

**Estimated Time**: 1 hour

---

### Task 3.6: Improve focus management

**File**: `frontend/src/pages/ChatPage.tsx` and `frontend/src/components/chat/MessageInput.tsx`

**Implementation Steps**:
1. Focus input after sending message:
   ```typescript
   const inputRef = useRef<HTMLTextAreaElement>(null);

   const sendMessage = () => {
     // ... existing send logic
     setInput('');

     // Focus input after sending
     setTimeout(() => inputRef.current?.focus(), 0);
   };
   ```

2. Focus input on page load (if session active):
   ```typescript
   useEffect(() => {
     if (session && isConnected) {
       inputRef.current?.focus();
     }
   }, [session, isConnected]);
   ```

3. Focus first suggestion on Tab from input:
   ```typescript
   const handleKeyDown = (e: React.KeyboardEvent) => {
     if (e.key === 'Tab' && messages.length === 0) {
       // Let Tab navigate to first suggestion
       // Default browser behavior handles this
     }
   };
   ```

**Validation**:
- [ ] Input focused after sending message
- [ ] Input focused on session start
- [ ] Tab navigation works smoothly
- [ ] Focus visible (focus ring)

**Estimated Time**: 30-45 minutes

---

**Phase 3 Summary**:
- **Total Tasks**: 6
- **Estimated Effort**: 8.5-11.5 hours
- **Output**: Typing indicators, prompt suggestions, auto-resize input, focus management

---

## Phase 4: Markdown & Code Rendering
**Goal**: Properly render markdown with syntax-highlighted code blocks.

### Task 4.1: Add markdown dependencies

**Implementation Steps**:
1. Install packages:
   ```bash
   cd frontend
   bun add react-markdown remark-gfm
   bun add -D @types/react-markdown
   ```

2. Update package.json (verify):
   ```json
   {
     "dependencies": {
       "react-markdown": "^9.0.1",
       "remark-gfm": "^4.0.0"
     }
   }
   ```

3. Check bundle size impact:
   ```bash
   bun run build
   # Verify bundle increase < 50KB gzipped
   ```

**Validation**:
- [ ] Dependencies installed successfully
- [ ] TypeScript types available
- [ ] Bundle size acceptable (<50KB increase)

**Estimated Time**: 15-30 minutes

---

### Task 4.2: Create MarkdownRenderer component

**File**: `frontend/src/components/chat/MarkdownRenderer.tsx`

**Implementation Steps**:
```typescript
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CodeBlock } from './CodeBlock';

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <CodeBlock language={match[1]} code={String(children).replace(/\n$/, '')} />
          ) : (
            <code className="px-1.5 py-0.5 bg-gray-100 rounded text-sm font-mono" {...props}>
              {children}
            </code>
          );
        },
        p({ children }) {
          return <p className="mb-2 last:mb-0">{children}</p>;
        },
        ul({ children }) {
          return <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>;
        },
        ol({ children }) {
          return <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>;
        },
        a({ href, children }) {
          return (
            <a href={href} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
```

**Validation**:
- [ ] Bold/italic renders correctly
- [ ] Lists formatted properly
- [ ] Links open in new tab
- [ ] Inline code has background
- [ ] Block code uses CodeBlock component

**Estimated Time**: 1-1.5 hours

---

### Task 4.3: Add syntax highlighting

**Files**: `frontend/src/components/chat/CodeBlock.tsx`

**Implementation Steps**:
1. Install Prism.js:
   ```bash
   bun add prismjs
   bun add -D @types/prismjs
   ```

2. Create CodeBlock component:
   ```typescript
   import { useEffect, useRef } from 'react';
   import Prism from 'prismjs';
   import 'prismjs/themes/prism-tomorrow.css'; // Dark theme

   // Import languages
   import 'prismjs/components/prism-javascript';
   import 'prismjs/components/prism-typescript';
   import 'prismjs/components/prism-python';
   import 'prismjs/components/prism-bash';
   import 'prismjs/components/prism-json';

   interface CodeBlockProps {
     language: string;
     code: string;
   }

   export function CodeBlock({ language, code }: CodeBlockProps) {
     const codeRef = useRef<HTMLElement>(null);

     useEffect(() => {
       if (codeRef.current) {
         Prism.highlightElement(codeRef.current);
       }
     }, [code]);

     return (
       <div className="relative my-2 rounded-lg overflow-hidden">
         <div className="bg-gray-800 px-4 py-2 text-xs text-gray-300 font-mono">
           {language}
         </div>
         <pre className="!m-0 !rounded-t-none">
           <code ref={codeRef} className={`language-${language}`}>
             {code}
           </code>
         </pre>
       </div>
     );
   }
   ```

**Validation**:
- [ ] Syntax highlighting works for JS/TS/Python/Bash/JSON
- [ ] Language label displays above code
- [ ] Dark theme matches chat aesthetic
- [ ] Code scrolls horizontally if too wide

**Estimated Time**: 1.5-2 hours

---

### Task 4.4: Add copy-to-clipboard for code blocks

**File**: Update `CodeBlock.tsx`

**Implementation Steps**:
```typescript
export function CodeBlock({ language, code }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-2 rounded-lg overflow-hidden group">
      <div className="bg-gray-800 px-4 py-2 text-xs text-gray-300 font-mono flex justify-between items-center">
        <span>{language}</span>
        <button
          onClick={handleCopy}
          className="px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 transition-colors text-white"
          aria-label="Copy code"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      {/* ... rest of component */}
    </div>
  );
}
```

**Validation**:
- [ ] Copy button visible in code header
- [ ] Clicking copies code to clipboard
- [ ] "Copied!" feedback shows for 2 seconds
- [ ] Works on all supported code blocks

**Estimated Time**: 45 minutes - 1 hour

---

### Task 4.5: Integrate MarkdownRenderer into ChatMessage

**File**: `frontend/src/components/chat/ChatMessage.tsx`

**Implementation Steps**:
```typescript
import { MarkdownRenderer } from './MarkdownRenderer';

export function ChatMessage({ message, isStreaming, showTimestamp }: ChatMessageProps) {
  return (
    <div className={`flex items-start gap-2 ${...}`}>
      <MessageAvatar role={message.role} />

      <div className={`max-w-[70%] rounded-2xl p-3 md:p-4 shadow-sm ${...}`}>
        {message.role === 'assistant' ? (
          <div className="prose prose-sm max-w-none">
            <MarkdownRenderer content={message.content} />
            {isStreaming && (
              <span className="inline-block w-0.5 h-5 bg-current ml-0.5 animate-pulse" />
            )}
          </div>
        ) : (
          <p className="whitespace-pre-wrap text-base leading-relaxed">
            {message.content}
          </p>
        )}

        {showTimestamp && message.timestamp && !isStreaming && (
          <p className="text-xs leading-tight font-medium opacity-70 mt-1.5">
            {formatTimestamp(message.timestamp)}
          </p>
        )}
      </div>
    </div>
  );
}
```

**Validation**:
- [ ] Assistant messages render markdown
- [ ] User messages remain plain text
- [ ] Streaming cursor still works with markdown
- [ ] Markdown styles don't break layout

**Estimated Time**: 30-45 minutes

---

**Phase 4 Summary**:
- **Total Tasks**: 5
- **Estimated Effort**: 5-6.5 hours
- **Output**: Markdown rendering with syntax-highlighted code blocks and copy functionality

---

## Phase 5: Message Actions & Error Handling
**Goal**: Add interactive message actions and improved error displays.

### Task 5.1: Create MessageActions component

**File**: `frontend/src/components/chat/MessageActions.tsx`

**Implementation Steps**:
```typescript
interface MessageActionsProps {
  messageId: string;
  messageContent: string;
  isAssistant: boolean;
  onCopy: () => void;
  onRegenerate?: () => void;
}

export function MessageActions({
  messageContent,
  isAssistant,
  onCopy,
  onRegenerate
}: MessageActionsProps) {
  return (
    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
      <button
        onClick={onCopy}
        className="p-1.5 rounded bg-white border border-gray-200 hover:bg-gray-50 shadow-sm"
        aria-label="Copy message"
        title="Copy message"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      </button>

      {isAssistant && onRegenerate && (
        <button
          onClick={onRegenerate}
          className="p-1.5 rounded bg-white border border-gray-200 hover:bg-gray-50 shadow-sm"
          aria-label="Regenerate response"
          title="Regenerate response"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      )}
    </div>
  );
}
```

**Integration into ChatMessage**:
```typescript
<div className={`relative group max-w-[70%] rounded-2xl ...`}>
  <MessageActions
    messageContent={message.content}
    isAssistant={message.role === 'assistant'}
    onCopy={handleCopy}
    onRegenerate={message.role === 'assistant' ? handleRegenerate : undefined}
  />
  {/* ... message content */}
</div>
```

**Validation**:
- [ ] Actions appear on hover (desktop)
- [ ] Actions always visible on mobile
- [ ] Copy button works for all messages
- [ ] Regenerate button only for assistant messages

**Estimated Time**: 1.5-2 hours

---

### Task 5.2: Implement copy message action

**Implementation**:
```typescript
const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

const handleCopy = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content);
    setCopyFeedback('Copied!');
    setTimeout(() => setCopyFeedback(null), 2000);
  } catch (err) {
    console.error('Failed to copy:', err);
    setCopyFeedback('Failed to copy');
  }
};
```

**Validation**:
- [ ] Copies message to clipboard
- [ ] Shows "Copied!" feedback
- [ ] Announces to screen reader
- [ ] Handles clipboard API errors

**Estimated Time**: 30-45 minutes

---

### Task 5.3: Implement regenerate action

**Implementation**:
```typescript
const handleRegenerate = (messageIndex: number) => {
  // Find the user message before this assistant message
  const userMessageIndex = messageIndex - 1;
  if (userMessageIndex < 0) return;

  const userMessage = messages[userMessageIndex];

  // Remove messages from this assistant message onward
  setMessages(messages.slice(0, messageIndex));

  // Re-send the user message
  if (wsRef.current && isConnected) {
    setIsGenerating(true);
    wsRef.current.send(JSON.stringify({
      type: 'user_message',
      content: userMessage.content,
    }));
  }
};
```

**Validation**:
- [ ] Removes current assistant response
- [ ] Re-sends previous user message
- [ ] Generates new response
- [ ] Updates UI correctly

**Estimated Time**: 1 hour

---

### Task 5.4: Create ErrorMessage component

**File**: `frontend/src/components/chat/ErrorMessage.tsx`

**Implementation**:
```typescript
interface ErrorMessageProps {
  error: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorMessage({ error, onRetry, onDismiss }: ErrorMessageProps) {
  return (
    <div className="flex justify-center my-4">
      <div className="max-w-md bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800">{error}</p>
            <div className="flex gap-2 mt-2">
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="text-sm font-medium text-red-600 hover:text-red-700"
                >
                  Retry
                </button>
              )}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="text-sm font-medium text-red-600 hover:text-red-700"
                >
                  Dismiss
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

**Estimated Time**: 45 minutes - 1 hour

---

### Task 5.5: Add error recovery actions

**Implementation in ChatPage**:
```typescript
const [error, setError] = useState<string | null>(null);

// In WebSocket handlers:
ws.onerror = (event) => {
  setError('Connection error. Please check your network.');
  setIsConnected(false);
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'error') {
    setError(message.content);
    setIsGenerating(false);
  }
};

const handleRetry = () => {
  setError(null);
  // Retry last action
  if (!isConnected) {
    createSession(); // Reconnect
  } else if (messages.length > 0) {
    // Resend last user message
    const lastUserMsg = messages.filter(m => m.role === 'user').pop();
    if (lastUserMsg) {
      // Resend logic
    }
  }
};
```

**Validation**:
- [ ] Network errors show retry button
- [ ] Generation errors show retry button
- [ ] Session errors show "Start New Session"
- [ ] Rate limit errors show countdown

**Estimated Time**: 1.5-2 hours

---

### Task 5.6: Improve error messaging

**Implementation**:
```typescript
const ERROR_MESSAGES: Record<string, string> = {
  'network_error': 'Unable to connect. Please check your internet connection.',
  'session_expired': 'Your session has expired. Please start a new chat.',
  'rate_limit': 'Too many requests. Please wait a moment before trying again.',
  'generation_failed': 'Failed to generate response. Please try again.',
  'invalid_input': 'Invalid message. Please check your input and try again.',
};

function getFriendlyErrorMessage(errorCode: string, fallback: string): string {
  return ERROR_MESSAGES[errorCode] || fallback;
}
```

**Validation**:
- [ ] User-friendly error messages
- [ ] Technical details in console
- [ ] Actionable guidance provided

**Estimated Time**: 30-45 minutes

---

**Phase 5 Summary**:
- **Total Tasks**: 6
- **Estimated Effort**: 6-8 hours
- **Output**: Message actions (copy, regenerate) and robust error handling

---

## Phase 6: Accessibility & Polish
**Goal**: Ensure full keyboard and screen reader accessibility, add final polish.

### Task 6.1: Add ARIA labels to all interactive elements

**Implementation across components**:
```typescript
// MessageInput
<textarea aria-label="Message input" ... />
<button aria-label="Send message" ... />

// MessageActions
<button aria-label="Copy message" title="Copy" ... />
<button aria-label="Regenerate response" title="Regenerate" ... />

// PromptSuggestions
<button aria-label={`Try suggestion: ${suggestion}`} ... />

// ConnectionStatus
<div aria-live="assertive" aria-label={`Connection status: ${status}`} ... />
```

**Validation**:
- [ ] All buttons have aria-label
- [ ] All inputs have aria-label
- [ ] Screen reader announces all elements
- [ ] Labels are descriptive and concise

**Estimated Time**: 1 hour

---

### Task 6.2: Implement ARIA live regions

**Implementation**:
```typescript
// MessageList
<div role="log" aria-live="polite" aria-relevant="additions">
  {messages.map(...)}
</div>

// TypingIndicator
<div role="status" aria-live="polite" aria-atomic="true">
  <span className="sr-only">Assistant is typing</span>
</div>

// ConnectionStatus
<div aria-live="assertive">
  {isConnected ? 'Connected' : 'Disconnected'}
</div>
```

**Validation**:
- [ ] New messages announced
- [ ] Typing status announced
- [ ] Connection changes announced immediately
- [ ] No excessive announcements

**Estimated Time**: 1 hour

---

### Task 6.3: Add keyboard navigation

**Implementation**:
```typescript
// ChatPage keyboard shortcuts
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    // Escape: Cancel generation or close dialogs
    if (e.key === 'Escape' && isGenerating) {
      stopGeneration();
    }

    // Ctrl/Cmd + K: Focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      inputRef.current?.focus();
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [isGenerating]);
```

**Validation**:
- [ ] Tab navigates through all elements
- [ ] Enter/Space activates buttons
- [ ] Escape cancels operations
- [ ] Keyboard shortcuts work

**Estimated Time**: 1-1.5 hours

---

### Task 6.4: Add visible focus indicators

**Implementation in global styles**:
```css
/* frontend/src/index.css */
*:focus-visible {
  @apply outline-none ring-2 ring-blue-500 ring-offset-2;
}

button:focus-visible {
  @apply ring-2 ring-blue-500 ring-offset-1;
}

textarea:focus-visible,
input:focus-visible {
  @apply ring-2 ring-blue-500;
}
```

**Validation**:
- [ ] Focus ring visible on all interactive elements
- [ ] Contrast ratio meets WCAG AA (3:1 minimum)
- [ ] Ring doesn't break layout
- [ ] Mouse clicks don't show ring (only keyboard focus)

**Estimated Time**: 30-45 minutes

---

### Task 6.5: Test with screen readers

**Testing checklist**:
```
VoiceOver (macOS):
- [ ] Navigate through chat with VO+arrow keys
- [ ] Messages announced with role (user/assistant)
- [ ] Typing indicator announced
- [ ] Connection status changes announced
- [ ] Message actions accessible and announced

NVDA (Windows):
- [ ] Same tests as VoiceOver
- [ ] Verify ARIA live regions work
- [ ] Check button labels are clear
```

**Estimated Time**: 1.5-2 hours (includes fixing issues found)

---

### Task 6.6: Add reduced motion support

**Implementation**:
```typescript
// Detect motion preference
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Conditional animation classes
<div className={prefersReducedMotion ? '' : 'animate-fade-in-up'}>

// Or in Tailwind config:
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Validation**:
- [ ] Animations disabled when preference set
- [ ] Functionality works without animations
- [ ] No jarring instant transitions

**Estimated Time**: 45 minutes - 1 hour

---

### Task 6.7: Animation polish

**Refinements**:
```javascript
// tailwind.config.js - Add fade-in-up animation
keyframes: {
  'fade-in-up': {
    '0%': { opacity: '0', transform: 'translateY(10px)' },
    '100%': { opacity: '1', transform: 'translateY(0)' },
  },
},
animation: {
  'fade-in-up': 'fade-in-up 0.2s ease-out',
},
```

**Validation**:
- [ ] Message enter animations smooth
- [ ] Typing indicator maintains 60fps
- [ ] No animation jank or stutter
- [ ] Transitions feel natural

**Estimated Time**: 1 hour

---

### Task 6.8: Performance testing

**Testing steps**:
1. Generate 100+ message conversation
2. Measure with Chrome DevTools:
   - Initial render time
   - Re-render on new message
   - Scroll performance (60fps?)
   - Memory usage

3. Check bundle size:
   ```bash
   bun run build
   ls -lh dist/*.js
   ```

4. Optimize if needed:
   - Add React.memo to components
   - Use useCallback for handlers
   - Implement virtualization if needed

**Validation**:
- [ ] Renders <100ms on new message
- [ ] Maintains 60fps scrolling
- [ ] Bundle increase <50KB gzipped
- [ ] Memory stable (no leaks)

**Estimated Time**: 2-3 hours

---

**Phase 6 Summary**:
- **Total Tasks**: 8
- **Estimated Effort**: 9-12 hours
- **Output**: Fully accessible chat with polished animations and performance

---

## Phase 7: Testing & Documentation
**Goal**: Comprehensive testing and documentation of new UX.

### Task 7.1: Write unit tests for new components

**Files**: `frontend/src/components/chat/__tests__/`

Create test files for:
- `ChatMessage.test.tsx` (already shown in detail)
- `MessageList.test.tsx`
- `MessageInput.test.tsx`
- `TypingIndicator.test.tsx`
- `PromptSuggestions.test.tsx`
- `MessageActions.test.tsx`
- `ErrorMessage.test.tsx`

**Testing approach**:
- Component rendering
- Props handling
- Event handlers
- Edge cases
- Accessibility (ARIA attributes)

**Target**: >80% code coverage

**Estimated Time**: 3-4 hours

---

### Task 7.2: Write integration tests

**File**: `frontend/src/__tests__/chat-integration.test.tsx`

**Test scenarios**:
```typescript
describe('Chat Integration', () => {
  it('complete chat flow: session → message → response', async () => {
    // Create session
    // Send message
    // Verify response appears
    // Verify auto-scroll
  });

  it('handles streaming messages', async () => {
    // Mock WebSocket streaming
    // Verify progressive updates
    // Verify cursor appears/disappears
  });

  it('handles errors gracefully', async () => {
    // Trigger error
    // Verify error message
    // Click retry
    // Verify recovery
  });
});
```

**Estimated Time**: 2-3 hours

---

### Task 7.3: E2E tests with Playwright

**File**: `frontend/tests/e2e/chat.spec.ts`

**Test coverage**:
```typescript
test('user can complete chat flow', async ({ page }) => {
  // Select collection
  // Start session
  // Send message
  // Verify response
  // Test regenerate
  // End session
});

test('keyboard navigation works', async ({ page }) => {
  // Tab through elements
  // Use Enter to activate
  // Test Escape key
});

test('works on mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  // Test mobile interactions
});
```

**Estimated Time**: 2-3 hours

---

### Task 7.4: Accessibility audit

**Tools and process**:
1. Run axe-core:
   ```bash
   npm install -D @axe-core/playwright
   ```

2. Automated testing:
   ```typescript
   test('chat page has no accessibility violations', async ({ page }) => {
     await page.goto('/chat');
     const results = await new AxeBuilder({ page }).analyze();
     expect(results.violations).toEqual([]);
   });
   ```

3. Manual testing:
   - Keyboard-only navigation
   - Screen reader testing
   - Color contrast validation
   - Focus indicator visibility

**Estimated Time**: 2-3 hours

---

### Task 7.5: Visual regression testing

**Setup**:
```bash
npm install -D @playwright/test
```

**Capture screenshots**:
```typescript
test('chat UI matches baseline', async ({ page }) => {
  await page.goto('/chat');
  await expect(page).toHaveScreenshot('chat-empty.png');

  // Create session
  await expect(page).toHaveScreenshot('chat-with-session.png');

  // Send message
  await expect(page).toHaveScreenshot('chat-with-messages.png');
});
```

**Estimated Time**: 1.5-2 hours

---

### Task 7.6: Update documentation

**Files to create/update**:

1. **Component documentation** (JSDoc):
   ```typescript
   /**
    * ChatMessage component displays a single message in the conversation.
    *
    * @param message - The message object containing role, content, and timestamp
    * @param isStreaming - Whether this message is currently being streamed
    * @param showTimestamp - Whether to display the message timestamp
    *
    * @example
    * <ChatMessage
    *   message={{ role: 'user', content: 'Hello', timestamp: new Date() }}
    *   showTimestamp={true}
    * />
    */
   ```

2. **README updates** (`frontend/README.md`):
   - Chat features section
   - Keyboard shortcuts
   - Accessibility features
   - Component overview

3. **User guide** (`docs/CHAT_GUIDE.md`):
   - How to start a chat session
   - Using prompt suggestions
   - Message actions (copy, regenerate)
   - Keyboard shortcuts reference

**Estimated Time**: 2-3 hours

---

### Task 7.7: Performance benchmarking

**Benchmarking script**:
```typescript
// scripts/benchmark-chat.ts
const results = {
  pageLoad: 0,
  firstMessage: 0,
  streamingLatency: 0,
  hundredMessages: 0,
};

// Measure page load
const start = performance.now();
await page.goto('/chat');
results.pageLoad = performance.now() - start;

// Measure streaming
// Measure long conversation
// Document results
```

**Document results in**: `docs/PERFORMANCE.md`

**Estimated Time**: 1.5-2 hours

---

**Phase 7 Summary**:
- **Total Tasks**: 7
- **Estimated Effort**: 14.5-20 hours
- **Output**: Comprehensive test coverage, documentation, and performance benchmarks

---

## Final Summary

### Total Implementation Effort
- **Phase 1**: 6-7.5 hours (Component refactoring)
- **Phase 2**: 8.5-11 hours (Visual design)
- **Phase 3**: 8.5-11.5 hours (Interactions)
- **Phase 4**: 5-6.5 hours (Markdown rendering)
- **Phase 5**: 6-8 hours (Actions & errors)
- **Phase 6**: 9-12 hours (Accessibility)
- **Phase 7**: 14.5-20 hours (Testing & docs)

**Total**: 58-76.5 hours (~8-10 working days for one developer)

### Parallelization Opportunities
- Phase 1: Tasks 1.1-1.4 (4 developers)
- Phase 2: Tasks 2.1-2.3 (3 developers)
- Phase 3: Tasks 3.1-3.2 with 3.3-3.4 (2 pairs)
- Phase 4: Tasks 4.1-4.3 with 4.4 (2 developers)
- Phase 7: All testing tasks (4-5 developers)

**With 3-4 developers**: ~3-4 weeks calendar time

### Success Metrics
- [ ] All 42 tasks completed
- [ ] Visual regression tests pass
- [ ] Accessibility audit clean (0 violations)
- [ ] Performance targets met (<100ms renders, <50KB bundle increase)
- [ ] >80% test coverage
- [ ] All existing functionality preserved
- [ ] User testing shows improved satisfaction