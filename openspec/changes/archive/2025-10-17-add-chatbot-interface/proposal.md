# Add Chatbot Interface

## Summary
Add conversational RAG capabilities using Qwen3-14B-4bit via MLX framework to enable a chatbot-like user experience. This enhancement provides real-time conversational responses that combine semantic search with natural language generation, supporting both response generation and search result re-ranking. The chatbot integrates with the existing multimodal capabilities, handling both text and image context in conversations.

## Motivation
The current system supports semantic search and document retrieval but lacks conversational capabilities. Users need to:
- Engage in natural dialogue about their document collections
- Receive generated summaries and insights from retrieved context
- Have multi-turn conversations with session-based history
- Get improved search results through LLM-based re-ranking

Adding Qwen3-14B-4bit (14.8B parameters, 4-bit quantized) via MLX provides:
- Efficient inference on Apple Silicon (M4 Max) with minimal memory footprint
- 32,768 token context window for extensive document context
- Thinking mode for complex reasoning and non-thinking mode for efficiency
- Built-in chat template support with conversation history
- Multilingual conversation support (100+ languages)

## Scope
This change introduces conversational AI capabilities while preserving the existing search interface.

### In Scope
- **Generation Capability**: New MLX-based LLM generation system with Qwen3-14B-4bit
- **Chat Capability**: Real-time conversational interface with WebSocket streaming
- **API Modifications**: New chat endpoints and session management
- **Frontend Addition**: New chat page (React/TypeScript) alongside existing search interface
- **Session Management**: Conversation history and context tracking
- **Context Integration**: Automatic retrieval and injection of relevant documents (text and images)
- **Multimodal Context Handling**: Display and reference images in chat context
- **Re-ranking**: LLM-based result re-ranking for improved relevance (text-focused)
- **Image Reference Tracking**: Track images mentioned across conversation turns

### Out of Scope
- Modifications to existing search page UI/UX
- Changes to embedding models or vector search algorithms
- Fine-tuning or customization of the Qwen3 model
- Multi-user authentication or user-specific sessions (deferred to future work)
- Voice input/output capabilities
- Document summarization as standalone feature (only within chat context)
- Vision-enabled LLM (Qwen3-14B is text-only, works with image descriptions)
- Image generation or manipulation
- Image upload directly in chat (deferred to Phase 2/3)

## Dependencies
- Requires MLX framework (`mlx` and `mlx-lm` packages)
- Depends on existing embeddings and storage capabilities (including Jina v4 `encode_image`)
- Depends on existing multimodal infrastructure (image ingestion, storage, serving)
- Requires ~8GB additional memory for model during inference
- Frontend build tooling (Bun) for new chat page (React/TypeScript)

## Risks and Mitigations
1. **Memory Constraints**: 4-bit quantized model + embeddings may stress 48GB unified memory
   - *Mitigation*: Lazy loading, careful batch size management, model unloading when idle

2. **Latency**: Generation may be slower than pure search
   - *Mitigation*: Streaming responses via WebSocket, non-thinking mode for simple queries

3. **Context Quality**: Retrieved documents may not always be relevant
   - *Mitigation*: Re-ranking step, configurable top-k, expose confidence scores

4. **MLX Compatibility**: MLX is Apple Silicon specific
   - *Mitigation*: Clear error messages, graceful degradation to search-only mode

## Success Criteria
- Chat endpoint responds with streaming generation in <5 seconds for first token
- Session history maintained across multiple turns (minimum 10 turns)
- Re-ranking improves relevance for at least 80% of queries (subjective evaluation)
- Memory usage stays below 40GB during concurrent chat + search operations
- Frontend chat interface provides clear visual distinction between retrieved context and generated responses
- **Multimodal context properly displayed**: Images shown as thumbnails in context panel
- **Image references work correctly**: LLM mentions images by description, frontend renders them
- **Mixed modality retrieval**: Handle collections with 50/50 text/image split without degradation

## Related Changes
- **add-multimodal-support** (archived): Provides image ingestion, encoding, and search infrastructure that chat depends on
- **add-frontend-ui** (archived): Provides React/TypeScript frontend that chat page extends

## Approval
- [ ] Reviewed by technical lead
- [ ] Architecture approved
- [ ] Implementation plan validated
