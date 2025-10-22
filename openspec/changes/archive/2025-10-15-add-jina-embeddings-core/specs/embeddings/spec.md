## ADDED Requirements

### Requirement: Model Initialization
The system SHALL provide a JinaEmbeddingsV4 class that initializes the model with MPS backend support for Apple Silicon acceleration.

#### Scenario: Successful initialization with MPS
- **WHEN** JinaEmbeddingsV4 is instantiated on Apple Silicon
- **THEN** the model loads with MPS backend enabled
- **AND** reports successful initialization

#### Scenario: Fallback to CPU when MPS unavailable
- **WHEN** MPS backend is not available
- **THEN** the model falls back to CPU execution
- **AND** logs a warning about reduced performance

### Requirement: Text Embedding Generation
The system SHALL generate embeddings for text input using task-specific adapters.

#### Scenario: Generate retrieval embeddings
- **WHEN** encoding text with task="retrieval"
- **THEN** returns embeddings optimized for semantic search
- **AND** supports both query and passage prompt types

#### Scenario: Generate text-matching embeddings
- **WHEN** encoding text with task="text-matching"
- **THEN** returns embeddings optimized for similarity comparison
- **AND** handles multilingual text correctly

#### Scenario: Generate code embeddings
- **WHEN** encoding text with task="code"
- **THEN** returns embeddings optimized for code understanding
- **AND** preserves code syntax semantics

### Requirement: Dimension Flexibility
The system SHALL support flexible embedding dimensions through Matryoshka truncation.

#### Scenario: Truncate to smaller dimension
- **WHEN** user specifies truncate_dim=512
- **THEN** embeddings are truncated from 2048 to 512 dimensions
- **AND** maintains semantic quality

#### Scenario: Use default dimensions
- **WHEN** no truncate_dim is specified
- **THEN** returns full 2048-dimensional embeddings

### Requirement: Memory Management
The system SHALL implement lazy loading and caching for efficient memory usage.

#### Scenario: Lazy load model
- **WHEN** model is first accessed for encoding
- **THEN** loads model weights into memory
- **AND** caches for subsequent use

#### Scenario: Model caching
- **WHEN** model has been downloaded once
- **THEN** subsequent initializations use cached weights
- **AND** skip downloading from Hugging Face