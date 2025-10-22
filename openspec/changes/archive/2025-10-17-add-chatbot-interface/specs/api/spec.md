# api Specification Delta

## Purpose
Extend the existing API to support chat sessions and conversational interactions.

## ADDED Requirements

### Requirement: Chat Session Endpoints
The system SHALL expose HTTP endpoints for chat session lifecycle management.

#### Scenario: Create chat session
- **WHEN** POST /api/chat/session with collection_name
- **THEN** returns session_id and configuration
- **AND** initializes empty conversation history

#### Scenario: Get session details
- **WHEN** GET /api/chat/session/{session_id}
- **THEN** returns session metadata and history
- **AND** includes current configuration

#### Scenario: Update session configuration
- **WHEN** PUT /api/chat/session/{session_id}/config
- **THEN** updates specified parameters
- **AND** returns updated configuration

#### Scenario: Delete chat session
- **WHEN** DELETE /api/chat/session/{session_id}
- **THEN** removes session data
- **AND** returns 204 No Content

#### Scenario: List active sessions
- **WHEN** GET /api/chat/sessions
- **THEN** returns array of session summaries
- **AND** includes last activity timestamp

### Requirement: Chat WebSocket Endpoint
The system SHALL provide WebSocket endpoint for real-time chat.

#### Scenario: Connect to chat WebSocket
- **WHEN** WebSocket /ws/chat/{session_id}
- **THEN** establishes persistent connection
- **AND** sends initial state message

#### Scenario: Send user message
- **WHEN** client sends JSON message
- **THEN** validates message structure
- **AND** triggers chat pipeline

#### Scenario: Receive streamed response
- **WHEN** generation produces tokens
- **THEN** receives incremental chunks
- **AND** assembles full response

#### Scenario: Handle WebSocket errors
- **WHEN** WebSocket error occurs
- **THEN** receives error message
- **AND** connection remains open for retry

### Requirement: Health Check Extension
The system SHALL include generator status in health checks.

#### Scenario: Report generator health
- **WHEN** GET /api/health
- **THEN** includes generator_loaded field
- **AND** includes model memory usage

### Requirement: Stats Extension
The system SHALL report chat statistics in stats endpoint.

#### Scenario: Include chat metrics
- **WHEN** GET /api/stats
- **THEN** includes active_sessions count
- **AND** includes total chat turns processed

## MODIFIED Requirements

### Requirement: API Server
The system SHALL provide a FastAPI-based REST API server for query operations and chat interactions.

#### Scenario: Initialize chat components
- **WHEN** server starts
- **THEN** initializes generator and session manager
- **AND** logs initialization status
