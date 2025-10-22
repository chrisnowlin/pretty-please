# api Capability Specification

## Purpose
API enhancements to support configurable RAG quality settings and expose retrieval metadata in responses.

## ADDED Requirements

### Requirement: RAG Configuration Endpoint
The system SHALL provide endpoints to manage RAG quality configuration.

#### Scenario: Get current RAG configuration
- **WHEN** GET /api/config/rag is called
- **THEN** returns current RAG configuration as JSON
- **AND** includes hybrid_search, reranking, compression settings
- **AND** includes model names and parameter values

#### Scenario: Update RAG configuration
- **WHEN** POST /api/config/rag with new settings
- **THEN** validates configuration parameters
- **AND** updates active configuration
- **AND** returns updated configuration
- **AND** applies changes to subsequent queries without restart

#### Scenario: Reset to default configuration
- **WHEN** POST /api/config/rag/reset is called
- **THEN** restores default RAG configuration
- **AND** returns default configuration
- **AND** logs configuration reset action

### Requirement: Enhanced Session Configuration
The system SHALL support per-session RAG configuration.

#### Scenario: Create session with custom RAG config
- **WHEN** POST /api/chat/session with rag_config parameter
- **THEN** creates session with specified RAG settings
- **AND** validates configuration parameters
- **AND** stores config with session
- **AND** applies config to all queries in that session

#### Scenario: Update session RAG config
- **WHEN** PATCH /api/chat/session/{session_id}/config with rag_config
- **THEN** updates session's RAG configuration
- **AND** validates new parameters
- **AND** applies to subsequent queries in session
- **AND** doesn't affect other sessions

### Requirement: Retrieval Metadata in Responses
The system SHALL include retrieval metadata in chat responses.

#### Scenario: Include citation metadata
- **WHEN** chat response is generated with citations
- **THEN** includes "citations" array in response
- **AND** each citation includes ID, source, relevance score
- **AND** each citation includes original and reranked scores (if reranking enabled)
- **AND** citations map to [N] references in response text

#### Scenario: Include retrieval metrics
- **WHEN** chat response is generated
- **THEN** includes retrieval_metadata object
- **AND** includes retrieval_time_ms
- **AND** includes documents_retrieved count
- **AND** includes documents_after_rerank count (if applicable)
- **AND** includes hybrid_search_used boolean

#### Scenario: Expose reranking details
- **WHEN** reranking is enabled for query
- **THEN** includes reranker_model name in metadata
- **AND** includes reranking_time_ms
- **AND** includes score_before and score_after for each source
- **AND** shows ranking change for each document

## MODIFIED Requirements

### Requirement: WebSocket Chat Messages (from existing api spec)
The system SHALL enhance WebSocket messages with citation and metadata.

#### Scenario: Send context message with citations
- **WHEN** sending ContextMessage to client
- **THEN** includes numbered citation IDs for each text result
- **AND** includes image citation IDs for each image result
- **AND** includes relevance scores
- **AND** includes original_score and reranked_score if reranking used

#### Scenario: Send complete message with retrieval stats
- **WHEN** sending CompleteMessage after generation
- **THEN** includes existing fields (tokens_generated, duration_ms)
- **AND** adds retrieval_stats with retrieval time and document counts
- **AND** adds citation_count for total citations in response
- **AND** adds reranking_enabled boolean

### Requirement: Chat Configuration Model (from existing models.py)
The system SHALL extend ChatConfig to support RAG quality parameters.

#### Scenario: Accept RAG quality config in session creation
- **WHEN** CreateSessionRequest is submitted
- **THEN** accepts optional rag_config field
- **AND** validates enable_hybrid_search boolean
- **AND** validates enable_reranking boolean
- **AND** validates enable_compression boolean
- **AND** validates reranking_top_n (1-20 range)

## ADDED Requirements

### Requirement: Health Check Enhancement
The system SHALL include RAG component health in health check.

#### Scenario: Check reranker model health
- **WHEN** GET /health is called
- **THEN** includes reranker_status field
- **AND** reports "loaded", "unloaded", or "error"
- **AND** includes model name and load time if loaded

#### Scenario: Report configuration health
- **WHEN** GET /health is called
- **THEN** includes rag_config_status field
- **AND** validates configuration is consistent
- **AND** reports any invalid settings

### Requirement: Debug Endpoint
The system SHALL provide debug endpoint for RAG pipeline inspection.

#### Scenario: Get retrieval debug info
- **WHEN** POST /api/debug/retrieval with query
- **THEN** returns full retrieval pipeline details
- **AND** includes vector search results with scores
- **AND** includes keyword search results (if hybrid enabled)
- **AND** includes reranked results with score changes
- **AND** includes compressed chunks (if compression enabled)

#### Scenario: Test reranker performance
- **WHEN** POST /api/debug/reranker with query and documents
- **THEN** runs reranker on provided documents
- **AND** returns scores and rankings
- **AND** includes model name and inference time
- **AND** compares to vector similarity scores

## Relationships
- **Uses**: `retrieval` (calls enhanced retrieval pipeline)
- **Uses**: `generation` (uses enhanced prompts and formatting)
- **Provides**: Configuration interface for RAG quality features
- **Consumed by**: `frontend` (UI uses new metadata for display)
