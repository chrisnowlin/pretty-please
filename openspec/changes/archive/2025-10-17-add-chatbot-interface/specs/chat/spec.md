# chat Specification Delta

## Purpose
Enable conversational interactions with multimodal document collections (text + images) through session-based chat with real-time streaming.

## ADDED Requirements

### Requirement: Session Management
The system SHALL manage chat sessions with conversation history tracking.

#### Scenario: Create new session
- **WHEN** POST /api/chat/session with collection name
- **THEN** generates unique session_id
- **AND** returns session metadata

#### Scenario: Configure session parameters
- **WHEN** creating session
- **THEN** accepts top_k, thinking_mode, max_history
- **AND** applies defaults for unspecified parameters

#### Scenario: Retrieve session history
- **WHEN** GET /api/chat/session/{session_id}
- **THEN** returns message history
- **AND** includes session configuration

#### Scenario: Delete session
- **WHEN** DELETE /api/chat/session/{session_id}
- **THEN** removes session from storage
- **AND** returns confirmation

#### Scenario: Session expiration
- **WHEN** session inactive for 30 minutes
- **THEN** automatically deleted
- **AND** cleanup occurs in background

#### Scenario: Track image references in session
- **WHEN** session created
- **THEN** initializes empty image_references dict
- **AND** maintains across conversation turns

### Requirement: WebSocket Chat Interface
The system SHALL provide real-time chat via WebSocket connections.

#### Scenario: Establish WebSocket connection
- **WHEN** connecting to /ws/chat/{session_id}
- **THEN** establishes persistent connection
- **AND** sends initial session state

#### Scenario: Receive user message
- **WHEN** client sends message via WebSocket
- **THEN** validates message format
- **AND** triggers RAG pipeline

#### Scenario: Stream assistant response
- **WHEN** generation produces tokens
- **THEN** sends chunks incrementally
- **AND** includes chunk metadata

#### Scenario: Handle connection interruption
- **WHEN** WebSocket connection drops
- **THEN** preserves session state
- **AND** allows reconnection

#### Scenario: Close connection gracefully
- **WHEN** client or server closes WebSocket
- **THEN** completes in-progress generation
- **AND** cleans up connection resources

### Requirement: Message Protocol
The system SHALL use structured message format for WebSocket communication.

#### Scenario: User message format
- **WHEN** client sends user message
- **THEN** includes type, content, and optional metadata
- **AND** validates required fields

#### Scenario: Assistant chunk format
- **WHEN** sending generated tokens
- **THEN** includes type=assistant_chunk and content
- **AND** includes token count and timing

#### Scenario: Context message format (multimodal)
- **WHEN** sending retrieved documents
- **THEN** includes type=context with text_results and image_results arrays
- **AND** includes relevance scores for all results

#### Scenario: Image result format
- **WHEN** context includes images
- **THEN** includes ImageMetadata (document_id, thumbnail_url, full_image_url, dimensions)
- **AND** includes image description and relevance score

#### Scenario: Error message format
- **WHEN** error occurs
- **THEN** includes type=error, message, and code
- **AND** preserves session state

#### Scenario: Complete message format
- **WHEN** response generation finishes
- **THEN** includes type=complete and metadata
- **AND** includes total tokens and duration

### Requirement: Conversation History
The system SHALL maintain conversation history within sessions.

#### Scenario: Append user message
- **WHEN** user message received
- **THEN** adds to session history
- **AND** timestamps message

#### Scenario: Append assistant response
- **WHEN** generation completes
- **THEN** adds full response to history
- **AND** preserves thinking blocks if present

#### Scenario: Enforce history limit
- **WHEN** history exceeds max_history turns
- **THEN** removes oldest messages
- **AND** notifies client of truncation

#### Scenario: Export history
- **WHEN** client requests history export
- **THEN** returns formatted conversation
- **AND** includes metadata and timestamps

### Requirement: Context Retrieval Integration (Multimodal)
The system SHALL retrieve relevant documents (text and images) for each user message.

#### Scenario: Retrieve on user message
- **WHEN** user message received
- **THEN** encodes query with embeddings (encode_text)
- **AND** performs vector search across text and image embeddings

#### Scenario: Handle mixed modality results
- **WHEN** retrieval returns both text and images
- **THEN** separates into text_results and image_results
- **AND** preserves modality information

#### Scenario: Apply session top_k
- **WHEN** retrieving documents
- **THEN** uses session configured top_k
- **AND** returns top-k results (combined text + images)

#### Scenario: Re-rank text documents only
- **WHEN** re-ranking enabled
- **THEN** scores only text documents with generator
- **AND** reorders text by relevance, keeps images sorted by vector similarity

#### Scenario: Track retrieved images
- **WHEN** images in results
- **THEN** adds to session image_references dict
- **AND** maintains across conversation turns

#### Scenario: Send context to client
- **WHEN** documents retrieved
- **THEN** sends context message with text_results and image_results
- **AND** includes document IDs, scores, and ImageMetadata for images

#### Scenario: Format multimodal context for LLM
- **WHEN** building generation prompt
- **THEN** formats text as blocks and images as text descriptions
- **AND** includes in system message with `[IMAGE]` markers

### Requirement: Image Reference Management
The system SHALL track and manage image references across conversation turns.

#### Scenario: Store image metadata in session
- **WHEN** image retrieved in context
- **THEN** stores ImageMetadata keyed by document_id
- **AND** available for subsequent turns

#### Scenario: Retrieve image metadata from session
- **WHEN** LLM references image in response
- **THEN** frontend can fetch metadata by document_id
- **AND** renders thumbnail from session data

#### Scenario: Accumulate images across turns
- **WHEN** multiple turns retrieve different images
- **THEN** session maintains all referenced images
- **AND** provides complete image context

#### Scenario: Clean up expired image references
- **WHEN** session expires
- **THEN** removes image_references from memory
- **AND** no orphaned metadata

### Requirement: Session Configuration
The system SHALL support per-session chat configuration.

#### Scenario: Configure retrieval parameters
- **WHEN** creating session
- **THEN** accepts top_k, distance_metric, rerank_enabled
- **AND** validates parameter values

#### Scenario: Configure generation parameters
- **WHEN** creating session
- **THEN** accepts max_tokens, temperature, thinking_mode
- **AND** applies to all turns in session

#### Scenario: Configure history settings
- **WHEN** creating session
- **THEN** accepts max_history_turns
- **AND** truncates history accordingly

#### Scenario: Update session configuration
- **WHEN** PUT /api/chat/session/{session_id}/config
- **THEN** updates specified parameters
- **AND** applies to subsequent turns

### Requirement: Multi-turn Context Awareness
The system SHALL maintain context awareness across conversation turns.

#### Scenario: Reference previous messages
- **WHEN** user refers to earlier conversation
- **THEN** includes relevant history in context
- **AND** generates coherent response

#### Scenario: Track conversation topic
- **WHEN** conversation evolves
- **THEN** retrieves documents relevant to current topic
- **AND** adapts context retrieval

#### Scenario: Handle clarification requests
- **WHEN** user asks for clarification
- **THEN** references specific prior response
- **AND** expands explanation

### Requirement: Error Resilience
The system SHALL handle errors gracefully without corrupting session state.

#### Scenario: Handle retrieval errors
- **WHEN** vector search fails
- **THEN** sends error message to client
- **AND** preserves session history

#### Scenario: Handle generation errors
- **WHEN** generation fails mid-stream
- **THEN** sends error with partial response
- **AND** allows retry

#### Scenario: Handle model unavailable
- **WHEN** generator not loaded
- **THEN** returns 503 Service Unavailable
- **AND** includes model loading status

#### Scenario: Handle session not found
- **WHEN** session_id invalid or expired
- **THEN** returns 404 error
- **AND** suggests creating new session

### Requirement: Performance Monitoring
The system SHALL track and report chat performance metrics.

#### Scenario: Track response latency
- **WHEN** processing user message
- **THEN** measures retrieval, rerank, and generation time
- **AND** includes in completion metadata

#### Scenario: Track token throughput
- **WHEN** streaming response
- **THEN** calculates tokens per second
- **AND** logs performance metrics

#### Scenario: Track session statistics
- **WHEN** session active
- **THEN** maintains turn count, total tokens, avg latency
- **AND** returns in session metadata

### Requirement: Rate Limiting
The system SHALL prevent abuse through rate limiting.

#### Scenario: Limit messages per session
- **WHEN** session exceeds 100 messages per hour
- **THEN** returns 429 rate limit error
- **AND** includes retry-after header

#### Scenario: Limit concurrent sessions per client
- **WHEN** client creates excessive sessions
- **THEN** rejects new session creation
- **AND** suggests deleting old sessions

#### Scenario: Limit token generation
- **WHEN** single response approaches max_tokens
- **THEN** truncates generation gracefully
- **AND** notifies client of truncation
