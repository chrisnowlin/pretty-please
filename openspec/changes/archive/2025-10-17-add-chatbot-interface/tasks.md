# Implementation Tasks

This document outlines the ordered implementation tasks for adding chatbot interface capabilities.

## Phase 1: Foundation - Generation Module

### Task 1.1: Add MLX dependencies
- Add `mlx` and `mlx-lm` to project dependencies (pyproject.toml or equivalent)
- Document version requirements (mlx-lm >= 0.24.0)
- Verify installation on Apple Silicon
- **Validation**: Run `python -c "import mlx; import mlx_lm; print('MLX OK')"`
- **Dependencies**: None
- **Parallelizable**: No

### Task 1.2: Create generation module structure
- Create `src/jina_rag_pipeline/generation/` directory
- Create `__init__.py` with module exports
- Create `qwen_generator.py` skeleton class
- Create `prompts.py` with default system prompts (include multimodal instructions)
- Create `reranker.py` skeleton class
- Create `context_formatter.py` for multimodal context formatting (NEW)
- **Validation**: Import module successfully
- **Dependencies**: Task 1.1
- **Parallelizable**: No

### Task 1.3: Implement QwenGenerator class
- Implement `__init__` with lazy loading
- Implement `_load_model()` using mlx-lm
- Implement `apply_chat_template()` with thinking mode support
- Add device detection and error handling
- **Validation**: Unit test model loading and chat template
- **Dependencies**: Task 1.2
- **Parallelizable**: No

### Task 1.4: Implement streaming generation
- Implement `generate_stream()` async method
- Use `mlx_lm.generate()` in thread pool executor
- Yield tokens incrementally
- Handle soft switches (`/think`, `/no_think`)
- **Validation**: Unit test streaming with mock messages
- **Dependencies**: Task 1.3
- **Parallelizable**: No

### Task 1.5: Implement context window management
- Add token counting utility
- Implement history truncation logic
- Add context length validation
- **Validation**: Unit test with long conversations
- **Dependencies**: Task 1.3
- **Parallelizable**: Can start after Task 1.3

### Task 1.6: Implement document re-ranker
- Implement `rerank()` method in reranker.py
- Batch document scoring
- Return ranked documents with scores
- **Only re-rank text documents** (skip images in multimodal results)
- **Validation**: Unit test with sample documents (text only)
- **Dependencies**: Task 1.3
- **Parallelizable**: Can start after Task 1.3

### Task 1.6.1: Implement multimodal context formatter (NEW)
- Implement `ContextFormatter` class in context_formatter.py
- Add `format_text_context()` method
- Add `format_image_context()` method with `[IMAGE]` markers
- Add `format_multimodal_context()` to combine text and images
- Add `extract_image_references()` to extract ImageMetadata mappings
- **Validation**: Unit test with mixed text/image results
- **Dependencies**: Task 1.2
- **Parallelizable**: Can start after Task 1.2

### Task 1.7: Implement memory management
- Add idle model unloading with timer
- Implement `clear_cache()` method
- Add memory monitoring utilities
- **Validation**: Test model unload/reload cycle
- **Dependencies**: Task 1.3
- **Parallelizable**: Can start after Task 1.3

### Task 1.8: Create default RAG system prompts (with multimodal)
- Write default system prompt in prompts.py
- Add multimodal instruction explaining `[IMAGE]` format
- Add context injection template for text and images
- Add citation instruction template
- **Validation**: Review prompts with test generation
- **Dependencies**: Task 1.2
- **Parallelizable**: Can do in parallel with Task 1.3

### Task 1.9: Add generation configuration model
- Create `GenerationConfig` dataclass
- Define temperature, top_p, top_k, max_tokens fields
- **Add mode-specific defaults** (from research):
  - Thinking mode: temp=0.6, top_p=0.95, top_k=20
  - Non-thinking mode: temp=0.7, top_p=0.8, top_k=20
- Add validation logic
- **Validation**: Unit test configuration validation
- **Dependencies**: Task 1.2
- **Parallelizable**: Can do in parallel with Task 1.3

### Task 1.10: Add generation unit tests
- Test model loading and initialization
- Test streaming generation
- Test chat template application
- Test thinking mode switching
- Test re-ranking
- Test error handling
- **Validation**: All tests pass, coverage > 80%
- **Dependencies**: Tasks 1.3-1.9
- **Parallelizable**: No

## Phase 2: Backend - Chat API and Session Management

### Task 2.1: Create session management module (with multimodal support)
- Create `src/jina_rag_pipeline/api/session.py`
- Implement `Session` dataclass with `image_references: Dict[str, ImageMetadata]` field (NEW)
- Implement `SessionManager` class
- Add `track_image_reference()` and `get_image_references()` methods (NEW)
- Add TTL-based cleanup
- **Validation**: Unit test session lifecycle including image tracking
- **Dependencies**: Task 1.9 (for config model)
- **Parallelizable**: Can start after Task 1.2

### Task 2.2: Create chat models
- Add chat models to `api/models.py`
- Create `ChatMessage`, `ChatConfig`, `SessionInfo` models
- Create WebSocket message protocol models with multimodal support:
  - Include `text_results` and `image_results` fields in context messages (NEW)
  - Include `retrieved_images` count in metadata (NEW)
- **Validation**: Models serialize/deserialize correctly with images
- **Dependencies**: None (can start immediately)
- **Parallelizable**: Can do in parallel with Phase 1

### Task 2.3: Create chat endpoint module
- Create `src/jina_rag_pipeline/api/chat.py`
- Implement session CRUD endpoints
- Add session configuration endpoints
- **Validation**: Manual test with curl/Postman
- **Dependencies**: Tasks 2.1, 2.2
- **Parallelizable**: No

### Task 2.4: Implement WebSocket chat handler
- Implement `/ws/chat/{session_id}` endpoint
- Handle connection lifecycle
- Implement message routing
- Add ping/pong health monitoring (30s timeout) - **from research**
- Add error handling
- **Validation**: Test WebSocket connection, message flow, and heartbeat
- **Dependencies**: Task 2.3
- **Parallelizable**: No

### Task 2.5: Integrate multimodal context retrieval
- Add retrieval logic to chat handler
- Use existing embeddings (`encode_text`) and vector store
- Retrieve both text chunks and image results
- Separate results by modality (`result_type` field)
- Use `ContextFormatter` to format as unified context (Task 1.6.1)
- Track image references in session state
- **Validation**: Test retrieval with existing multimodal collections
- **Dependencies**: Tasks 2.4, 1.6.1
- **Parallelizable**: No

### Task 2.6: Integrate re-ranking (text only)
- Add optional re-ranking step for text documents
- **Skip images in re-ranking** (keep sorted by vector similarity)
- Make configurable per session
- Handle re-ranking errors gracefully
- **Validation**: Compare text results with/without re-ranking, verify images unchanged
- **Dependencies**: Tasks 1.6, 2.5
- **Parallelizable**: No

### Task 2.7: Implement streaming response handler
- Connect generator to WebSocket
- Stream tokens as they're generated
- Send metadata messages (context, complete)
- **Validation**: Test streaming with real model
- **Dependencies**: Tasks 1.4, 2.4
- **Parallelizable**: No

### Task 2.8: Add conversation history management
- Store messages in session (text only in history)
- Enforce history window limits (last 10 turns)
- **Optional**: Consider priority-based truncation (from research) - can defer to Phase 4
- Format history for generation context
- Track image references across turns in separate dict
- **Validation**: Test multi-turn conversations with images in context
- **Dependencies**: Tasks 2.1, 2.7
- **Parallelizable**: No

### Task 2.9: Implement rate limiting
- Add rate limiter middleware
- Configure per-session limits
- Add retry-after headers
- **Validation**: Test rate limit enforcement
- **Dependencies**: Task 2.3
- **Parallelizable**: Can start after Task 2.3

### Task 2.10: Extend health and stats endpoints
- Add generator status to /api/health
- Add chat metrics to /api/stats
- Include active sessions count
- **Validation**: Verify new fields in responses
- **Dependencies**: Task 2.1
- **Parallelizable**: Can start after Task 2.1

### Task 2.11: Integrate chat into main app
- Import chat module in app.py
- Initialize generator in startup event
- Initialize session manager
- Mount chat endpoints
- **Validation**: Server starts without errors
- **Dependencies**: Tasks 2.3, 2.4, Phase 1 complete
- **Parallelizable**: No

### Task 2.12: Add chat API unit tests
- Test session management
- Test WebSocket message protocol
- Test context retrieval integration
- Test error handling
- **Validation**: All tests pass, coverage > 80%
- **Dependencies**: Tasks 2.1-2.11
- **Parallelizable**: No

### Task 2.13: Add chat API integration tests
- Test end-to-end chat flow
- Test multi-turn conversation
- Test session persistence
- Test concurrent sessions
- **Validation**: All integration tests pass
- **Dependencies**: Task 2.12
- **Parallelizable**: No

## Phase 3: Frontend - Chat Interface (React/TypeScript)

### Task 3.1: Create chat page component
- Create `frontend/src/pages/Chat.tsx` (React with TypeScript)
- Add basic layout structure
- Add navigation integration
- **Validation**: Page renders without errors
- **Dependencies**: None (can start in parallel)
- **Parallelizable**: Can do in parallel with Phase 2

### Task 3.2: Implement WebSocket client
- Create `frontend/src/lib/websocket.ts`
- Handle connection lifecycle
- Implement message parsing
- Add reconnection logic
- **Validation**: Test connection to mock WebSocket
- **Dependencies**: Task 3.1
- **Parallelizable**: Can start with Task 3.1

### Task 3.3: Create message components
- Create `MessageBubble.tsx` for chat messages (React/TypeScript)
- Create `ThinkingBlock.tsx` for thinking display
- Create `TypingIndicator.tsx`
- **Validation**: Components render correctly
- **Dependencies**: Task 3.1
- **Parallelizable**: Can do in parallel with Task 3.2

### Task 3.4: Create context display components (multimodal)
- Create `ContextPanel.tsx` (React/TypeScript)
- Create `TextResultCard.tsx` for text chunks with source/score (NEW)
- Create `ImageResultCard.tsx` for image thumbnails with click-to-expand (NEW)
- Display both text and image results
- Show relevance scores
- Add expand/collapse functionality
- **Validation**: Component renders with mock multimodal data
- **Dependencies**: Task 3.1
- **Parallelizable**: Can do in parallel with Task 3.2

### Task 3.4.1: Create image preview modal (NEW)
- Create `ImagePreview.tsx` for full-size image viewing (React/TypeScript)
- Add modal overlay with click-to-close
- Add image metadata display (dimensions, filename)
- **Validation**: Modal opens/closes correctly
- **Dependencies**: Task 3.1
- **Parallelizable**: Can do in parallel with Task 3.2

### Task 3.5: Implement message input
- Create `MessageInput.tsx` (React/TypeScript)
- Add send button and keyboard shortcuts
- Implement multiline support
- Add character counter
- **Validation**: Input sends messages correctly
- **Dependencies**: Task 3.1
- **Parallelizable**: Can do in parallel with Task 3.2

### Task 3.6: Implement session controls
- Create `SessionControls.tsx` (React/TypeScript)
- Add "New Chat" button
- Add "Clear History" button
- Add "Export" functionality
- **Validation**: Controls work correctly
- **Dependencies**: Task 3.1
- **Parallelizable**: Can do in parallel with Task 3.2

### Task 3.7: Create configuration panel
- Create `ConfigPanel.tsx` (React/TypeScript)
- Add top_k slider
- Add thinking mode toggle
- Add max history control
- **Validation**: Settings update correctly
- **Dependencies**: Task 3.1
- **Parallelizable**: Can do in parallel with Task 3.2

### Task 3.8: Implement message streaming display
- Add streaming state management
- Update message bubble in real-time
- Auto-scroll to latest message
- Track image references in state (document_id → metadata mapping)
- **Validation**: Streaming displays smoothly with images in context
- **Dependencies**: Tasks 3.2, 3.3, 3.4
- **Parallelizable**: No

### Task 3.9: Implement error handling UI
- Add error message display
- Add retry buttons
- Add connection status banner
- **Validation**: Errors display clearly
- **Dependencies**: Task 3.2
- **Parallelizable**: Can start after Task 3.2

### Task 3.10: Add loading states
- Add loading spinners
- Add progress indicators
- Add "Retrieving..." messages
- **Validation**: Loading states display correctly
- **Dependencies**: Task 3.1
- **Parallelizable**: Can do in parallel with other Task 3.x

### Task 3.11: Implement responsive layout
- Add CSS media queries
- Test desktop layout
- Test tablet layout
- Test mobile layout
- **Validation**: Layout adapts correctly
- **Dependencies**: Tasks 3.1-3.10
- **Parallelizable**: No

### Task 3.12: Add navigation updates
- Update navigation bar to include "Chat" link
- Add route highlighting
- Ensure search page preserved
- **Validation**: Navigation works correctly
- **Dependencies**: Task 3.1
- **Parallelizable**: Can start after Task 3.1

### Task 3.13: Style chat interface
- Apply consistent design system
- Match existing frontend style
- Add animations and transitions
- Ensure accessibility (ARIA labels, keyboard nav)
- **Validation**: Visual review and accessibility audit
- **Dependencies**: Tasks 3.1-3.12
- **Parallelizable**: No

### Task 3.14: Add frontend unit tests
- Test WebSocket client
- Test message components
- Test session controls
- Test state management
- **Validation**: All tests pass, coverage > 70%
- **Dependencies**: Tasks 3.1-3.13
- **Parallelizable**: No

### Task 3.15: Add frontend integration tests
- Test complete chat flow
- Test WebSocket reconnection
- Test error scenarios
- Test responsive behavior
- **Validation**: All integration tests pass
- **Dependencies**: Task 3.14
- **Parallelizable**: No

## Phase 4: Integration and Testing

### Task 4.1: End-to-end chat test (multimodal)
- Test complete flow: session creation → chat → retrieval → generation
- Verify context integration with text and images
- Verify multi-turn conversation with image references
- Test with real multimodal documents (50/50 text/image split)
- **Validation**: E2E test passes consistently with multimodal collections
- **Dependencies**: Phase 1, 2, 3 complete
- **Parallelizable**: No

### Task 4.2: Performance testing
- Measure first token latency
- Measure token throughput
- Test with concurrent sessions
- Verify memory usage within budget
- **Validation**: Meets performance targets in design
- **Dependencies**: Task 4.1
- **Parallelizable**: No

### Task 4.3: Re-ranking quality evaluation
- Compare search results with/without re-ranking
- Subjective evaluation with test queries
- Measure relevance improvement
- **Validation**: Re-ranking improves results for >80% of queries
- **Dependencies**: Task 4.1
- **Parallelizable**: Can start after Task 4.1

### Task 4.4: Thinking mode evaluation
- Test complex reasoning queries
- Compare thinking vs non-thinking responses
- Measure quality and latency trade-offs
- **Validation**: Document findings and recommendations
- **Dependencies**: Task 4.1
- **Parallelizable**: Can do in parallel with Task 4.3

### Task 4.5: Error scenario testing
- Test model load failures
- Test generation errors
- Test WebSocket disconnections
- Test rate limiting
- **Validation**: All error scenarios handled gracefully
- **Dependencies**: Task 4.1
- **Parallelizable**: Can start after Task 4.1

### Task 4.6: Cross-browser testing
- Test on Chrome/Edge
- Test on Firefox
- Test on Safari
- **Validation**: Works correctly on all browsers
- **Dependencies**: Phase 3 complete
- **Parallelizable**: Can do in parallel with Phase 1-2

### Task 4.7: Memory leak testing
- Run extended chat sessions
- Monitor memory usage over time
- Verify session cleanup
- **Validation**: No memory leaks detected
- **Dependencies**: Task 4.2
- **Parallelizable**: No

### Task 4.8: Documentation
- Document API endpoints (including multimodal message protocol)
- Document WebSocket protocol with image metadata format
- Document frontend components (React/TypeScript)
- Add usage examples with multimodal collections
- **Add performance expectations from research** (token generation: 20-30 tokens/s, first token: 3-5s)
- **Validation**: Documentation complete and accurate
- **Dependencies**: All implementation complete
- **Parallelizable**: Can start earlier and update

### Task 4.9: Update README
- Add chatbot feature description
- Update installation instructions for MLX
- Add usage examples
- Update architecture diagram
- **Validation**: README accurate and helpful
- **Dependencies**: Task 4.8
- **Parallelizable**: Can do with Task 4.8

### Task 4.10: Final integration verification
- Verify all requirements met
- Run full test suite
- Verify no regressions in existing features
- Performance benchmarks pass
- **Validation**: All acceptance criteria met
- **Dependencies**: Tasks 4.1-4.9
- **Parallelizable**: No

## Summary

**Total Tasks**: 48 (updated from 46 to include multimodal tasks)
**New Tasks**:
- Task 1.6.1: Multimodal context formatter
- Task 3.4.1: Image preview modal

**Phases**: 4
**Estimated Parallelization**: ~30% of tasks can run in parallel
**Critical Path**: Phase 1 → Phase 2 (Tasks 2.3-2.11) → Phase 4 (Task 4.1-4.10)

**Key Milestones**:
1. Generator working locally with multimodal context formatting (End of Phase 1)
2. Chat API functional with image reference tracking (End of Phase 2, Task 2.11)
3. Frontend chat interface working with React/TypeScript and image display (End of Phase 3, Task 3.13)
4. Full system validated with multimodal collections (End of Phase 4, Task 4.10)

**Multimodal Updates**:
- Frontend changed from Svelte to React/TypeScript (based on codebase review)
- Added image reference tracking throughout session lifecycle
- Added multimodal context formatting with `[IMAGE]` markers
- Re-ranking applies to text only (images sorted by vector similarity)
- Research recommendations incorporated (mode-specific parameters, ping/pong heartbeat)
