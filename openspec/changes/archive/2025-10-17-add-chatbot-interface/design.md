# Design: Chatbot Interface Architecture

## Overview
This document captures architectural decisions for integrating Qwen3-14B-4bit conversational AI into the multimodal RAG pipeline, focusing on the interaction between retrieval, generation, and user interface layers. The chatbot integrates with existing image and text processing capabilities to provide context-aware conversational search.

## Architecture

### System Components

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Frontend (React/TypeScript)                   │
│  ┌──────────────┐              ┌─────────────────────────────┐      │
│  │ Search Page  │              │   Chat Page (New)            │      │
│  │ (Existing)   │              │  - Message interface         │      │
│  │ - Text/Image │              │  - Context panel             │      │
│  │   search     │              │  - Image thumbnails          │      │
│  └──────────────┘              └─────────────────────────────┘      │
│         │                                     │                       │
└─────────┼─────────────────────────────────────┼───────────────────────┘
          │                                     │
          │ HTTP POST                           │ WebSocket
          │ /api/search                         │ /ws/chat/{session_id}
          │ /api/search/image                   │
          ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                               │
│  ┌──────────────┐              ┌─────────────────────────────┐      │
│  │ Search       │              │  Chat Endpoints (New)        │      │
│  │ Endpoints    │              │  - Session management        │      │
│  │ (Existing)   │              │  - WebSocket handler         │      │
│  └──────────────┘              │  - Context retrieval         │      │
│         │                      └─────────────────────────────┘      │
│         │                                     │                       │
│  ┌──────▼─────────────────────────────────────▼──────────┐          │
│  │         Session Manager (New)                          │          │
│  │  - Conversation history (text)                         │          │
│  │  - Image reference tracking                            │          │
│  │  - Context caching                                     │          │
│  │  - Message buffering                                   │          │
│  └────────────────────────────────────────────────────────┘          │
│         │                              │                              │
└─────────┼──────────────────────────────┼──────────────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────┐          ┌────────────────────┐
│  Jina Embeddings v4 │          │  Qwen3 Generator   │
│  (Existing)         │          │  (New - MLX)       │
│  - encode_text()    │          │  - Chat generation │
│  - encode_image()   │          │  - Re-ranking      │
│  (Multimodal)       │          │  - Thinking modes  │
└─────────────────────┘          │  (Text-only LLM)   │
          │                      └────────────────────┘
          │                              │
          ▼                              │
┌─────────────────────┐                 │
│   ChromaDB          │                 │
│   Vector Store      │◄────────────────┘
│   (Existing)        │   Retrieved Context
│  - Text chunks      │   (text + images)
│  - Image embeddings │
│  - Metadata         │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│  Image Storage      │
│  (Existing)         │
│  ./uploads/         │
│   └─{collection}/   │
│      ├─images/      │
│      └─thumbnails/  │
└─────────────────────┘
```

### Data Flow

#### Chat Request Flow (Multimodal)
1. **User Input** → Frontend chat interface (text message)
2. **WebSocket Connection** → Establish persistent connection to `/ws/chat/{session_id}`
3. **Message Reception** → Backend receives user message
4. **Context Retrieval** (Multimodal):
   - Encode query using Jina Embeddings (`encode_text()`)
   - Perform vector search in ChromaDB across both text and image embeddings
   - Retrieve top-k results (default k=5), may include:
     - Text chunks with metadata
     - Image results with `ImageMetadata` (thumbnail_url, full_image_url, dimensions, etc.)
5. **Optional Re-ranking**:
   - Pass retrieved **text documents** to Qwen3 for relevance scoring
   - Re-order text documents by LLM-assessed relevance
   - **Images remain sorted by vector similarity** (Qwen3 is text-only)
6. **Multimodal Context Formatting**:
   - Format text chunks as context strings
   - Format images as text descriptions with metadata:
     ```
     [IMAGE] {document_id}
     Description: {image description from metadata}
     Dimensions: {width}x{height}
     Path: {thumbnail_path for frontend}
     ```
   - Track image references in session state (`image_references` dict)
7. **Context Injection**:
   - Build chat messages array with:
     - System prompt with multimodal instruction
     - Formatted context (text + image descriptions)
     - Conversation history (last 10 turns)
   - Apply Qwen3 chat template
8. **Generation**:
   - Stream tokens from Qwen3-14B via MLX
   - LLM references images by description (text-only model)
   - Send tokens incrementally via WebSocket
   - Update session history with text response
9. **Response Completion**:
   - Send context metadata (including image references) to frontend
   - Frontend renders images as thumbnails in context panel
   - Maintain WebSocket for next turn

## Key Design Decisions

### 1. MLX Framework Choice
**Decision**: Use MLX exclusively for Qwen3-14B inference, no PyTorch fallback.

**Rationale**:
- Optimized for Apple Silicon with superior memory efficiency
- 4-bit quantization support reduces model footprint to ~8GB
- Native Metal integration provides better performance than PyTorch MPS
- Simplified dependency management (no mixed framework complexity)

**Trade-offs**:
- Apple Silicon only (acceptable for local-first design)
- Less mature ecosystem than PyTorch
- No cross-platform compatibility

**Alternatives Considered**:
- PyTorch with MPS: Higher memory usage, slower inference
- llama.cpp: Better portability, but less Python-native

### 2. WebSocket for Chat Communication
**Decision**: Use WebSocket for real-time streaming instead of HTTP SSE or polling.

**Rationale**:
- Full-duplex communication enables streaming responses and control messages
- Lower latency than polling
- Better browser compatibility than SSE
- Easier session management with persistent connection

**Trade-offs**:
- More complex error handling than HTTP
- Requires connection state management
- May face firewall/proxy issues (mitigated by existing CORS setup)

**Alternatives Considered**:
- Server-Sent Events: Simpler, but one-way only
- HTTP polling: Higher latency and overhead
- HTTP long polling: Complex state management

### 3. Session-Based History Management
**Decision**: In-memory session store with TTL-based cleanup, keyed by session_id.

**Rationale**:
- Fast access for conversation history
- Simple implementation without external dependencies
- Acceptable for single-user local deployment
- TTL cleanup prevents memory leaks

**Trade-offs**:
- Lost on server restart (acceptable for local use)
- Not suitable for multi-user production (out of scope)
- Memory grows with concurrent sessions (mitigated by TTL)

**Alternatives Considered**:
- Redis/external store: Over-engineered for local use
- SQLite: I/O overhead for frequent reads
- Stateless with client-side history: Security and context validation concerns

### 4. Context Retrieval Strategy
**Decision**: Retrieve top-k documents, apply LLM re-ranking, inject into system message.

**Rationale**:
- Vector search provides initial relevance filtering
- LLM re-ranking improves precision using semantic understanding
- System message injection keeps context separate from user dialogue
- Top-k configurable per request for flexibility

**Trade-offs**:
- Re-ranking adds latency (1-2s per query)
- Increased token usage in generation context
- May retrieve irrelevant documents if collection is poor quality

**Alternatives Considered**:
- No re-ranking: Faster but lower precision
- Late interaction (ColBERT): More accurate but higher complexity
- Chunk-level retrieval with summarization: Additional generation overhead

### 5. Thinking Mode Configuration
**Decision**: Default to non-thinking mode (`enable_thinking=False`), allow per-session override.

**Rationale**:
- Non-thinking mode sufficient for most conversational queries
- Faster responses (1-2s vs 5-10s)
- Lower token consumption
- Users can opt-in to thinking mode for complex reasoning

**Trade-offs**:
- May miss nuanced reasoning in complex queries
- Additional configuration complexity
- Users need to understand mode differences

**Alternatives Considered**:
- Always thinking mode: Too slow for simple queries
- Automatic mode detection: Complex heuristics, unpredictable behavior
- No thinking mode at all: Loses key Qwen3 capability

### 6. Conversation History Window
**Decision**: Maintain last 10 turns (20 messages) in context, configurable per session.

**Rationale**:
- Balances context preservation with token limits
- 10 turns typically sufficient for coherent conversation
- Configurable for power users
- Prevents context length overflow (32k token limit)

**Trade-offs**:
- May lose relevant earlier context
- Fixed window may not suit all conversation patterns
- Token counting overhead for dynamic window

**Alternatives Considered**:
- Sliding window with token-based truncation: More accurate, higher complexity
- Summary-based compression: Requires additional generation, potential information loss
- Unlimited history: Context overflow, performance degradation

### 7. Multimodal Context Handling
**Decision**: Format images as text descriptions for text-only LLM, track image metadata in session state, render images in frontend context panel.

**Rationale**:
- Qwen3-14B is text-only, cannot process images directly
- Text descriptions allow LLM to reference visual content meaningfully
- Session-level image tracking enables consistent references across turns
- Frontend image display provides visual context to user
- Leverages existing multimodal infrastructure (Jina v4, image storage)

**Trade-offs**:
- LLM cannot "see" images, relies on metadata descriptions
- Text descriptions may not capture all visual details
- Additional complexity in context formatting
- Increased context token usage for image descriptions

**Alternatives Considered**:
- Vision-enabled LLM (Qwen2-VL): Not yet available in MLX, much larger model
- Skip images in chat context: Loses valuable multimodal information
- Separate image-only chat mode: Fragmented user experience
- Hybrid approach with image captioning: Additional model overhead

**Implementation Approach**:
```python
# Image formatted as:
[IMAGE] abc123-def456
Description: System architecture diagram showing FastAPI backend
Dimensions: 1920x1080
File: architecture.png
Relevance Score: 0.92

# LLM can reference: "Based on the architecture diagram, the FastAPI backend..."
# Frontend renders actual thumbnail using document_id
```

## Component Design

### Generation Module (`src/jina_rag_pipeline/generation/`)

**Files**:
- `qwen_generator.py`: Core MLX-based generator class
- `prompts.py`: System prompts and templates (with multimodal instructions)
- `reranker.py`: LLM-based re-ranking logic (text-focused)
- `context_formatter.py`: Multimodal context formatting utilities (NEW)

**QwenGenerator Class**:
```python
class QwenGenerator:
    def __init__(self, model_name: str, device: str = "mps")
    async def generate_stream(self, messages: List[Dict], max_tokens: int, ...) -> AsyncGenerator[str]
    async def rerank(self, query: str, documents: List[str], top_k: int) -> List[Tuple[str, float]]
    def apply_chat_template(self, messages: List[Dict], enable_thinking: bool) -> str
    def clear_cache(self)
```

**ContextFormatter Class** (NEW):
```python
class ContextFormatter:
    def format_text_context(self, text_results: List[SearchResult]) -> str
    def format_image_context(self, image_results: List[SearchResult]) -> str
    def format_multimodal_context(self, text_results: List, image_results: List) -> str
    def extract_image_references(self, formatted_context: str) -> Dict[str, ImageMetadata]
```

**Key Behaviors**:
- Lazy model loading (on first generation call)
- Async streaming with `mlx_lm.generate` in thread pool
- Auto-detection of thinking mode triggers (`/think`, `/no_think`)
- Memory-efficient token streaming
- **Multimodal context formatting**: Text + image descriptions in unified format

### Chat API Module (`src/jina_rag_pipeline/api/chat.py`)

**Endpoints**:
- `POST /api/chat/session`: Create new session, return session_id
- `GET /api/chat/session/{session_id}`: Retrieve session history
- `DELETE /api/chat/session/{session_id}`: Delete session
- `WebSocket /ws/chat/{session_id}`: Real-time chat with streaming

**Session Manager** (with Multimodal Support):
```python
class SessionManager:
    def create_session(self, collection_name: str, config: ChatConfig) -> Session
    def get_session(self, session_id: str) -> Optional[Session]
    def update_history(self, session_id: str, user_msg: str, assistant_msg: str)
    def track_image_reference(self, session_id: str, document_id: str, metadata: ImageMetadata)
    def get_image_references(self, session_id: str) -> Dict[str, ImageMetadata]
    def cleanup_expired_sessions(self)
```

**Session State** (Extended for Multimodal):
```python
class Session:
    session_id: str
    collection_name: str
    conversation_history: List[Dict[str, str]]  # Text messages
    image_references: Dict[str, ImageMetadata]  # Track images across turns
    created_at: datetime
    last_accessed: datetime
    config: ChatConfig
```

**Message Protocol** (with Multimodal Support):
```json
{
  "type": "user_message" | "assistant_chunk" | "context" | "error" | "complete",
  "content": "...",
  "metadata": {
    "thinking_mode": true,
    "retrieved_docs": 5,
    "retrieved_images": 2,
    "tokens_generated": 150
  },
  "context": {
    "text_results": [
      {"content": "...", "source": "doc.pdf", "score": 0.89}
    ],
    "image_results": [
      {
        "document_id": "abc123-def456",
        "description": "System architecture diagram",
        "thumbnail_url": "/api/images/thumbnail/my-collection/abc123-def456_thumb.jpg",
        "full_image_url": "/api/images/full/my-collection/abc123-def456.png",
        "width": 1920,
        "height": 1080,
        "score": 0.92
      }
    ]
  }
}
```

### Frontend Chat Page (`frontend/src/pages/Chat.tsx`)

**Framework**: React with TypeScript (extends existing frontend architecture)

**Components**:
- `ChatInterface`: Main container with message list and input
- `MessageBubble`: Renders user/assistant messages with metadata
- `ContextPanel`: Collapsible panel showing retrieved documents and images
  - `TextResultCard`: Display text chunk with source and score
  - `ImageResultCard`: Display thumbnail with click-to-expand
- `ImagePreview`: Modal for full-size image viewing
- `SessionControls`: New session, clear history, export conversation

**State Management**:
- WebSocket connection state
- Message history array
- Loading/streaming states
- Retrieved context display (text + images)
- Image references tracking (document_id → thumbnail/full URLs)
- Error handling and retry logic

## Integration Points

### 1. With Existing Embeddings (Multimodal)
- Chat uses same `JinaEmbeddingsV4` instance for query encoding
- Supports both `encode_text()` and `encode_image()` methods
- Shared model reduces memory footprint (~8GB)
- Consistent embedding space enables cross-modal retrieval
- Text queries retrieve both text chunks and relevant images

### 2. With Existing Storage (Multimodal)
- Chat queries same ChromaDB collections as search
- Retrieves text chunks with metadata (`modality: "text"`)
- Retrieves image embeddings with `ImageMetadata` (`modality: "image"`)
- Accesses image storage at `./uploads/{collection}/images/` and `./uploads/{collection}/thumbnails/`
- No schema changes required
- Reuses existing collection management

### 3. With Existing API
- Chat endpoints added to existing FastAPI app
- Reuses image serving endpoints:
  - `GET /api/images/thumbnail/{collection_name}/{filename}`
  - `GET /api/images/full/{collection_name}/{filename}`
- Shared CORS and middleware configuration
- Consistent error response format

### 4. With Existing Frontend (React/TypeScript)
- New route `/chat` added to existing React app
- Shared UI components (navigation, collections dropdown)
- Reuses image display components from search page
- Consistent styling with existing pages
- Separate build outputs for modularity

## Performance Considerations

### Memory Budget
| Component | Memory Usage | Notes |
|-----------|-------------|--------|
| Jina Embeddings v4 | ~8GB | Shared with search |
| Qwen3-14B-4bit | ~8GB | Lazy loaded, unloadable |
| ChromaDB | ~2-4GB | Depends on collection size |
| Session History | ~100MB | 100 concurrent sessions estimate |
| **Total** | **~18-20GB** | Well within 48GB unified memory |

### Latency Budget
| Operation | Target Latency | Notes |
|-----------|---------------|--------|
| Context retrieval | <500ms | Vector search + embedding |
| Re-ranking (optional) | 1-2s | LLM scoring, parallel when possible |
| First token | <5s total | Includes all above + generation start |
| Token streaming | ~20-30 tokens/s | MLX on M4 Max |
| Full response (200 tokens) | ~10-15s | Depends on thinking mode |

### Concurrency
- FastAPI async handlers prevent blocking
- MLX generation runs in thread pool executor
- Session manager thread-safe with locks
- WebSocket manager handles up to 50 concurrent connections

## Error Handling

### Model Loading Failures
- Detect MLX availability on startup
- Return 503 Service Unavailable if model load fails
- Log detailed error for debugging
- Provide user-friendly error message

### Generation Failures
- Catch MLX errors during streaming
- Send error message via WebSocket
- Maintain session state (don't corrupt history)
- Allow retry without reconnection

### Context Overflow
- Monitor token count before generation
- Truncate history if approaching 32k limit
- Notify user of truncation
- Preserve recent messages priority

### WebSocket Disconnections
- Detect connection loss via ping/pong
- Buffer messages if connection temporarily lost
- Allow reconnection to existing session
- Cleanup session after prolonged disconnection (30min TTL)

## Testing Strategy

### Unit Tests
- Generator class with mocked MLX model
- Session manager with mock sessions
- Re-ranker with fixed test documents
- Chat template application

### Integration Tests
- End-to-end chat flow with test collection
- WebSocket message protocol
- Session persistence across requests
- Context retrieval and injection

### Performance Tests
- Token generation throughput
- Memory usage under load
- Concurrent session handling
- Context retrieval latency

### User Acceptance Tests
- Conversation coherence over 10+ turns
- Relevance of retrieved context
- Re-ranking quality improvement
- Thinking mode effectiveness

## Security Considerations

### Input Validation
- Sanitize user messages (no code injection)
- Limit message length (max 4096 chars)
- Validate session_id format
- Rate limit requests per session

### Context Injection Safety
- Escape special characters in retrieved documents
- Prevent prompt injection via document metadata
- Limit context size to prevent DoS
- Validate collection access permissions (future work)

### WebSocket Security
- Require valid session_id for connection
- Implement connection timeout
- Sanitize streamed content
- CORS validation on WebSocket upgrade

## Future Enhancements (Out of Scope)

1. **Full Vision-Enabled Chat**:
   - **Partial Support (MVP)**: Retrieved images displayed as context with text descriptions
   - **Future**: Direct image upload in chat, vision-enabled LLM (e.g., Qwen2-VL)
2. **Citation Tracking**: Link generated text to specific source documents/images
3. **Conversation Branching**: Tree-based history with alternate paths
4. **Custom System Prompts**: User-defined behavior profiles per session
5. **Export/Import**: Save and restore conversations with context
6. **Analytics**: Track query patterns, popular topics, response quality
7. **Fine-tuning**: Adapt Qwen3 to domain-specific knowledge
8. **Multi-user Support**: Persistent sessions with authentication
9. **Image Generation**: Generate images based on conversation context
10. **Advanced Re-ranking**: Hybrid cross-encoder + LLM re-ranking for images

## References
- [Qwen3 Model Card](https://huggingface.co/Qwen/Qwen3-14B)
- [MLX Documentation](https://ml-explore.github.io/mlx/build/html/index.html)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Jina Embeddings v4](https://huggingface.co/jinaai/jina-embeddings-v4)
