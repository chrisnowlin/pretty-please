# embeddings Specification

## Purpose
TBD - created by archiving change add-jina-embeddings-core. Update Purpose after archive.
## Requirements
### Requirement: Model Initialization
The system SHALL initialize Jina Embeddings v4 with configuration-based defaults.

#### Scenario: Initialize with default configuration
- **GIVEN** no explicit configuration provided
- **WHEN** creating JinaEmbeddingsV4 instance
- **THEN** uses `EmbeddingConfig.for_documents()` preset
- **AND** enables late chunking by default
- **AND** uses dimension=1024 for storage efficiency
- **AND** selects optimal device (MPS > CUDA > CPU)

#### Scenario: Initialize with custom configuration
- **GIVEN** custom EmbeddingConfig
- **WHEN** creating JinaEmbeddingsV4(config=custom_config)
- **THEN** uses provided configuration
- **AND** validates configuration parameters
- **AND** logs selected settings

### Requirement: Text Embedding Generation
The system SHALL generate embeddings with task-specific optimization and format control.

#### Scenario: Generate embeddings with configuration
- **GIVEN** texts and EmbeddingConfig
- **WHEN** calling embed_with_config(texts, config)
- **THEN** applies task-specific optimization
- **AND** uses late chunking if enabled
- **AND** returns embeddings in specified format
- **AND** batches intelligently based on tokens

#### Scenario: Backward compatible embedding generation
- **GIVEN** existing code using old embed() method
- **WHEN** calling embed(texts, task="retrieval.passage")
- **THEN** continues working without changes
- **AND** shows deprecation warning
- **AND** uses default configuration with overrides

### Requirement: Dimension Flexibility
The system SHALL support Matryoshka dimension truncation with optimal defaults.

#### Scenario: Use optimal default dimension
- **GIVEN** no explicit dimension specified
- **WHEN** generating embeddings
- **THEN** defaults to dimension=1024
- **AND** balances quality and storage
- **AND** achieves 50% storage reduction vs. 2048

#### Scenario: Dimension truncation
- **GIVEN** full 2048-dimensional embeddings
- **WHEN** truncating to dimension=512
- **THEN** uses first 512 dimensions (Matryoshka property)
- **AND** maintains quality appropriate for use case
- **AND** reduces storage proportionally

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

### Requirement: Late Chunking Support
The system SHALL support late chunking to preserve context across chunk boundaries.

#### Scenario: Enable late chunking for document embeddings
- **GIVEN** a long document split into multiple chunks
- **WHEN** generating embeddings with `late_chunking=True`
- **THEN** chunks are concatenated before tokenization
- **AND** context is preserved across chunk boundaries
- **AND** retrieval quality improves by 5-10% (MRR@10)

#### Scenario: Disable late chunking for queries
- **GIVEN** a short search query
- **WHEN** generating embeddings with `late_chunking=False` (query default)
- **THEN** query is processed as single unit
- **AND** embedding generation is faster
- **AND** matches expected query representation

### Requirement: Task-Specific Optimization
The system SHALL provide task-specific embedding optimization for different use cases.

#### Scenario: Optimize for search queries
- **GIVEN** user search queries for retrieval
- **WHEN** using `EmbeddingConfig.for_query()`
- **THEN** uses task="retrieval.query"
- **AND** disables late chunking
- **AND** optimizes for query representation

#### Scenario: Optimize for document storage
- **GIVEN** documents to be indexed for retrieval
- **WHEN** using `EmbeddingConfig.for_documents()`
- **THEN** uses task="retrieval.passage"
- **AND** enables late chunking
- **AND** optimizes for passage representation

#### Scenario: Optimize for code search
- **GIVEN** code snippets for search or indexing
- **WHEN** using `EmbeddingConfig.for_code(is_query=True/False)`
- **THEN** uses task="code.query" or "code.passage"
- **AND** applies code-specific optimizations
- **AND** improves code retrieval quality

### Requirement: Multi-Vector Embeddings
The system SHALL support multi-vector (token-level) embeddings for advanced retrieval.

#### Scenario: Generate multi-vector embeddings
- **GIVEN** documents requiring high-accuracy retrieval
- **WHEN** using `return_multivector=True`
- **THEN** generates token-level embeddings (one per token)
- **AND** returns List[List[np.ndarray]] shape [docs, tokens, dim]
- **AND** enables ColBERT-style late interaction retrieval

#### Scenario: MaxSim retrieval with multi-vector
- **GIVEN** query and document multi-vector embeddings
- **WHEN** computing relevance score
- **THEN** uses MaxSim: max(dot(query_token, doc_token))
- **AND** achieves higher accuracy than single-vector
- **AND** maintains reasonable performance

### Requirement: Storage-Efficient Formats
The system SHALL support binary and ubinary embedding formats to reduce storage costs.

#### Scenario: Convert embeddings to ubinary format
- **GIVEN** float32 embeddings (4KB per 1024-dim)
- **WHEN** converting to ubinary format
- **THEN** reduces size to 128 bytes (8× reduction)
- **AND** maintains <2% quality loss (MRR@10)
- **AND** enables hamming distance similarity

#### Scenario: Convert embeddings to binary format
- **GIVEN** float32 embeddings with threshold
- **WHEN** converting to binary format with threshold=0.0
- **THEN** reduces size to 128 bytes (8× reduction)
- **AND** maintains <1% quality loss (MRR@10)
- **AND** preserves retrieval effectiveness

#### Scenario: Round-trip format conversion
- **GIVEN** original float embeddings
- **WHEN** converting to binary and back
- **THEN** approximation is consistent
- **AND** similarity rankings are preserved
- **AND** conversion is deterministic

### Requirement: Intelligent Batching
The system SHALL implement token-aware batching for optimal throughput and memory usage.

#### Scenario: Token-aware batch creation
- **GIVEN** documents with varying lengths
- **WHEN** creating batches with max_tokens_per_batch=8192
- **THEN** batches are created based on total token count
- **AND** maximizes GPU utilization
- **AND** prevents OOM from long documents

#### Scenario: Adaptive batch sizing
- **GIVEN** system with 16GB available memory
- **WHEN** computing optimal batch size
- **THEN** automatically scales to batch_size=16
- **AND** prevents memory exhaustion
- **AND** maintains stable processing

#### Scenario: Memory-aware batch processing
- **GIVEN** large document collection for embedding
- **WHEN** memory usage exceeds 80% threshold
- **THEN** dynamically reduces batch size
- **AND** continues processing without OOM
- **AND** logs adjustment for visibility

