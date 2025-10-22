# frontend Capability Specification

## Purpose
Frontend enhancements to display citations, formatted responses, and RAG quality controls.

## ADDED Requirements

### Requirement: Citation Display
The system SHALL render citations and source references in chat responses.

#### Scenario: Display inline citations
- **WHEN** assistant response contains citation markers [1], [2]
- **THEN** renders citations as interactive elements
- **AND** shows citation number with subtle styling
- **AND** makes citations clickable/hoverable
- **AND** preserves markdown formatting of response text

#### Scenario: Show citation details on hover
- **WHEN** user hovers over citation reference [N]
- **THEN** displays tooltip with source details
- **AND** shows source filename or title
- **AND** shows relevance score
- **AND** shows snippet preview if available

#### Scenario: Navigate to source from citation
- **WHEN** user clicks citation reference
- **THEN** scrolls to or highlights corresponding source in context panel
- **AND** provides visual feedback
- **AND** allows easy return to response

### Requirement: Source Attribution Panel
The system SHALL display retrieved sources with metadata.

#### Scenario: Show text sources
- **WHEN** context is retrieved for query
- **THEN** displays text sources in dedicated panel/section
- **AND** shows citation number for each source
- **AND** shows source name and relevance score
- **AND** shows content snippet or full text

#### Scenario: Show image sources
- **WHEN** images are retrieved
- **THEN** displays image sources with thumbnails
- **AND** shows image citation ID [IMG-N]
- **AND** shows image description and metadata
- **AND** allows viewing full image

#### Scenario: Highlight cited sources
- **WHEN** response includes citations
- **THEN** highlights sources that were actually cited
- **AND** dims or grays out uncited sources
- **AND** shows citation count per source

### Requirement: Markdown Rendering
The system SHALL render markdown-formatted responses correctly.

#### Scenario: Render markdown structure
- **WHEN** displaying assistant response
- **THEN** renders headers (##, ###) with appropriate styling
- **AND** renders lists (ordered, unordered) properly
- **AND** renders **bold** and *italic* text
- **AND** renders tables with borders and alignment

#### Scenario: Render code blocks
- **WHEN** response includes code blocks
- **THEN** renders with syntax highlighting
- **AND** shows language identifier
- **AND** provides copy-to-clipboard button
- **AND** uses monospace font

#### Scenario: Render inline code
- **WHEN** response includes `inline code`
- **THEN** renders with monospace font
- **AND** applies subtle background color
- **AND** distinguishes from regular text

### Requirement: RAG Quality Controls
The system SHALL provide UI controls for RAG configuration.

#### Scenario: Display RAG settings panel
- **WHEN** user opens settings or configuration
- **THEN** shows RAG quality options
- **AND** displays enable_hybrid_search toggle
- **AND** displays enable_reranking toggle
- **AND** displays enable_compression toggle

#### Scenario: Adjust retrieval parameters
- **WHEN** user modifies RAG settings
- **THEN** provides slider for reranking_top_n (1-10)
- **AND** provides slider for compression_threshold (0.5-0.9)
- **AND** shows current values and descriptions
- **AND** applies changes to current session

#### Scenario: Show retrieval statistics
- **WHEN** response is generated
- **THEN** optionally displays retrieval metrics
- **AND** shows number of documents retrieved
- **AND** shows reranking time (if enabled)
- **AND** shows total retrieval time

### Requirement: Confidence Indicators
The system SHALL visually communicate response confidence.

#### Scenario: Show high-confidence responses
- **WHEN** response uses strong citations [1][2][3]
- **THEN** displays confidence indicator (green/high)
- **AND** shows number of supporting sources
- **AND** emphasizes citation strength

#### Scenario: Show uncertain responses
- **WHEN** response includes uncertainty language ("suggests", "partially")
- **THEN** displays moderate confidence indicator (yellow/medium)
- **AND** shows that answer is partial or uncertain
- **AND** suggests refining query

#### Scenario: Show no-context responses
- **WHEN** response indicates no relevant context found
- **THEN** displays low confidence indicator (orange/low)
- **AND** suggests uploading more documents
- **AND** offers to search differently

## MODIFIED Requirements

### Requirement: Chat Message Display (existing chat interface)
The system SHALL enhance message display with citations and formatting.

#### Scenario: Render assistant message with citations
- **WHEN** assistant message is received via WebSocket
- **THEN** renders message text with markdown support
- **AND** renders citations as interactive elements
- **AND** links citations to source panel
- **AND** shows timestamp and metadata

#### Scenario: Display message metadata
- **WHEN** message includes retrieval metadata
- **THEN** optionally shows retrieval stats (toggle)
- **AND** shows number of sources retrieved
- **AND** shows whether reranking was used
- **AND** shows response generation time

### Requirement: Context Display
The system SHALL enhance context visualization during generation.

#### Scenario: Show context retrieval progress
- **WHEN** ContextMessage is received
- **THEN** displays "Retrieving context..." indicator
- **AND** shows number of documents found
- **AND** shows number of images found
- **AND** transitions to "Generating response..." when complete

#### Scenario: Preview retrieved sources
- **WHEN** context is retrieved before generation
- **THEN** briefly shows source count and top source
- **AND** makes full source list expandable
- **AND** includes relevance scores in preview

## ADDED Requirements

### Requirement: Citation Export
The system SHALL allow exporting responses with citations.

#### Scenario: Export conversation with citations
- **WHEN** user requests conversation export
- **THEN** exports in markdown format
- **AND** preserves citation numbers
- **AND** includes source bibliography at end
- **AND** maintains all formatting

#### Scenario: Copy response with citations
- **WHEN** user copies assistant response
- **THEN** copies markdown-formatted text
- **AND** preserves citation markers
- **AND** optionally appends source list

## Relationships
- **Uses**: `api` (consumes enhanced chat responses with metadata)
- **Displays**: Citations, sources, and metadata from enhanced RAG pipeline
- **Controls**: RAG quality settings through API configuration endpoints
