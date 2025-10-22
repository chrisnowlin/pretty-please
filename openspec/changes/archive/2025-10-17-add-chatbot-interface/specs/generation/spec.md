# generation Specification Delta

## Purpose
Provide LLM-based text generation capabilities using Qwen3-14B-4bit via MLX framework for conversational responses and document re-ranking.

## ADDED Requirements

### Requirement: MLX Generator Initialization
The system SHALL provide a generator class for Qwen3-14B-4bit model initialization and management.

#### Scenario: Load model on first use
- **WHEN** generator is created
- **THEN** model is not immediately loaded
- **AND** lazy loading occurs on first generation call

#### Scenario: Detect MLX availability
- **WHEN** generator is initialized
- **THEN** verifies MLX framework is installed
- **AND** raises clear error if unavailable

#### Scenario: Configure model parameters
- **WHEN** initializing generator
- **THEN** accepts model name, max tokens, temperature, and top_p
- **AND** validates parameter ranges

### Requirement: Streaming Text Generation
The system SHALL generate text responses asynchronously with token streaming.

#### Scenario: Generate with conversation history
- **WHEN** provided with messages array
- **THEN** applies chat template with history
- **AND** generates coherent response

#### Scenario: Stream tokens in real-time
- **WHEN** generation begins
- **THEN** yields tokens as they are generated
- **AND** provides consistent streaming rate

#### Scenario: Handle generation errors
- **WHEN** generation fails
- **THEN** raises descriptive exception
- **AND** preserves model state for retry

### Requirement: Chat Template Support
The system SHALL apply Qwen3 chat templates to message arrays.

#### Scenario: Format multi-turn conversation
- **WHEN** messages contain user and assistant roles
- **THEN** formats with proper role markers
- **AND** includes generation prompt

#### Scenario: Apply thinking mode configuration
- **WHEN** enable_thinking is True
- **THEN** template allows thinking blocks
- **AND** model may generate `<think>` tags

#### Scenario: Apply non-thinking mode
- **WHEN** enable_thinking is False
- **THEN** template disables thinking
- **AND** model generates direct responses

### Requirement: Thinking Mode Control
The system SHALL support both thinking and non-thinking generation modes.

#### Scenario: Default to non-thinking mode
- **WHEN** no mode specified
- **THEN** uses non-thinking configuration
- **AND** applies temperature 0.7, top_p 0.8

#### Scenario: Enable thinking mode
- **WHEN** thinking mode requested
- **THEN** uses thinking configuration
- **AND** applies temperature 0.6, top_p 0.95

#### Scenario: Detect soft switches
- **WHEN** user message contains `/think`
- **THEN** enables thinking for that turn
- **AND** maintains setting until changed

#### Scenario: Detect no-think switches
- **WHEN** user message contains `/no_think`
- **THEN** disables thinking for that turn
- **AND** applies non-thinking parameters

### Requirement: Document Re-ranking
The system SHALL re-rank search results using LLM-based relevance assessment.

#### Scenario: Score document relevance
- **WHEN** provided query and document list
- **THEN** generates relevance scores 0-1
- **AND** returns ranked documents

#### Scenario: Parallel re-ranking
- **WHEN** multiple documents provided
- **THEN** batches scoring requests
- **AND** completes within 2 seconds

#### Scenario: Handle re-ranking errors
- **WHEN** scoring fails for document
- **THEN** assigns neutral score 0.5
- **AND** logs error without failing request

#### Scenario: Re-rank text documents only
- **WHEN** mixed text and image results provided
- **THEN** re-ranks only text documents
- **AND** preserves image sorting by vector similarity

### Requirement: Multimodal Context Formatting
The system SHALL format multimodal context (text + images) for text-only LLM consumption.

#### Scenario: Format text context
- **WHEN** text search results provided
- **THEN** formats as delimited text blocks
- **AND** includes source metadata

#### Scenario: Format image context as text
- **WHEN** image search results provided
- **THEN** formats as text descriptions with metadata
- **AND** includes `[IMAGE]` marker, document_id, dimensions, and description

#### Scenario: Combine multimodal context
- **WHEN** both text and image results provided
- **THEN** merges into unified context string
- **AND** maintains result ordering (text first, then images)

#### Scenario: Extract image references
- **WHEN** formatted context includes images
- **THEN** extracts document_id to ImageMetadata mapping
- **AND** returns for session tracking

#### Scenario: Handle missing image metadata
- **WHEN** image result lacks description
- **THEN** generates basic description from filename and dimensions
- **AND** logs warning

### Requirement: Context Window Management
The system SHALL manage context length within 32,768 token limit.

#### Scenario: Truncate long history
- **WHEN** conversation history exceeds token limit
- **THEN** removes oldest messages
- **AND** preserves system prompt and recent context

#### Scenario: Estimate token count
- **WHEN** building prompt
- **THEN** estimates token usage
- **AND** warns if approaching limit

### Requirement: Memory Management
The system SHALL efficiently manage model memory usage.

#### Scenario: Unload model when idle
- **WHEN** no generation for 10 minutes
- **THEN** unloads model from memory
- **AND** reloads on next request

#### Scenario: Clear generation cache
- **WHEN** explicit clear requested
- **THEN** releases model memory
- **AND** clears KV cache

#### Scenario: Monitor memory usage
- **WHEN** generation active
- **THEN** tracks current memory consumption
- **AND** logs warnings if approaching limit

### Requirement: System Prompts
The system SHALL provide configurable system prompts for RAG chat with multimodal awareness.

#### Scenario: Default RAG system prompt
- **WHEN** no custom prompt provided
- **THEN** uses default RAG-optimized prompt
- **AND** instructs model to use provided context

#### Scenario: Multimodal instruction in prompt
- **WHEN** context includes images
- **THEN** system prompt explains image format (`[IMAGE]` markers)
- **AND** instructs model to reference images by description

#### Scenario: Custom system prompt
- **WHEN** session specifies custom prompt
- **THEN** applies custom prompt
- **AND** validates prompt structure

#### Scenario: Inject context into system message
- **WHEN** retrieved documents available
- **THEN** formats context with document boundaries (text and images)
- **AND** instructs model to cite sources

### Requirement: Generation Configuration
The system SHALL allow per-request generation configuration.

#### Scenario: Configure max tokens
- **WHEN** max_tokens specified
- **THEN** limits generation to specified length
- **AND** stops generation at limit

#### Scenario: Configure sampling parameters
- **WHEN** temperature and top_p provided
- **THEN** applies custom sampling
- **AND** overrides mode defaults

#### Scenario: Configure stop sequences
- **WHEN** stop sequences specified
- **THEN** halts generation on match
- **AND** excludes stop sequence from output
