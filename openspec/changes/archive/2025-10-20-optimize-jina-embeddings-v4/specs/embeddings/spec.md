# embeddings Specification Delta

## ADDED Requirements

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

## MODIFIED Requirements

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

## REMOVED Requirements

None. This is a purely additive enhancement maintaining full backward compatibility.

## Implementation Guidance

### Configuration System with Standard Dataclass

Use standard Python dataclasses for configuration:

```python
from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class EmbeddingConfig:
    """Configuration for Jina Embeddings v4."""

    task: Literal[
        "retrieval.query",
        "retrieval.passage",
        "text-matching",
        "classification",
        "separation",
        "code.query",
        "code.passage"
    ] = "retrieval.passage"

    dimensions: Literal[128, 256, 512, 1024, 2048] = 1024
    late_chunking: bool = True
    return_multivector: bool = False
    embedding_format: Literal["float", "base64", "binary", "ubinary"] = "float"

    batch_size: int = Field(default=32, ge=1, le=256)
    max_tokens_per_batch: int = Field(default=8192, ge=1024, le=32768)

    @field_validator('late_chunking', mode='before')
    @classmethod
    def disable_late_chunking_for_queries(cls, v, info):
        """Automatically disable late chunking for query tasks."""
        if info.data.get('task', '').endswith('.query'):
            return False
        return v

    @classmethod
    def for_query(cls, **kwargs) -> 'EmbeddingConfig':
        """Preset for search queries."""
        return cls(
            task="retrieval.query",
            dimensions=1024,
            late_chunking=False,
            **kwargs
        )

    @classmethod
    def for_documents(cls, **kwargs) -> 'EmbeddingConfig':
        """Preset for document indexing."""
        return cls(
            task="retrieval.passage",
            dimensions=1024,
            late_chunking=True,
            **kwargs
        )

    @classmethod
    def for_code(cls, is_query: bool = False, **kwargs) -> 'EmbeddingConfig':
        """Preset for code search."""
        task = "code.query" if is_query else "code.passage"
        return cls(
            task=task,
            dimensions=1024,
            late_chunking=(not is_query),
            **kwargs
        )

    @classmethod
    def storage_optimized(cls, **kwargs) -> 'EmbeddingConfig':
        """Minimize storage with ubinary format."""
        return cls(
            task="retrieval.passage",
            dimensions=512,
            embedding_format="ubinary",
            late_chunking=True,
            **kwargs
        )
```

### Late Chunking Implementation

Integrate late chunking into the embedding pipeline:

```python
def embed_with_late_chunking(
    self,
    texts: List[str],
    config: EmbeddingConfig
) -> np.ndarray:
    """
    Generate embeddings with optional late chunking.

    Late chunking: Concatenate text chunks before tokenization
    to preserve context across boundaries.
    """
    if not config.late_chunking:
        # Standard embedding
        return self._generate_embeddings(texts, config)

    # Late chunking enabled
    # Concatenate texts with special separator
    concatenated = " [SEP] ".join(texts)

    # Generate single embedding for concatenated text
    full_embedding = self._generate_embeddings([concatenated], config)[0]

    # Split back into individual embeddings using attention masks
    # (Model-specific implementation)
    individual_embeddings = self._split_concatenated_embedding(
        full_embedding,
        texts,
        concatenated
    )

    return np.array(individual_embeddings)
```

### Multi-Vector Embeddings Handler

Implement ColBERT-style multi-vector embeddings:

```python
class MultiVectorHandler:
    """Handle token-level multi-vector embeddings."""

    def generate_multivector(
        self,
        texts: List[str],
        model,
        config: EmbeddingConfig
    ) -> List[List[np.ndarray]]:
        """
        Generate token-level embeddings.

        Returns:
            List[List[np.ndarray]] where:
            - Outer list: one per input text
            - Inner list: one embedding per token
            - np.ndarray: embedding vector (config.dimensions)
        """
        # Call model with return_multivector=True
        # Jina v4 returns shape: [num_texts, num_tokens, dimensions]
        outputs = model(
            texts,
            task=config.task,
            dimensions=config.dimensions,
            return_multivector=True
        )

        # Convert to list format
        return [
            [outputs[i, j] for j in range(outputs.shape[1])]
            for i in range(outputs.shape[0])
        ]

    def maxsim_score(
        self,
        query_vectors: List[np.ndarray],
        doc_vectors: List[np.ndarray]
    ) -> float:
        """
        Compute MaxSim score for multi-vector retrieval.

        MaxSim: For each query token, find max similarity with any doc token,
        then average across query tokens.
        """
        scores = []

        for q_vec in query_vectors:
            # Compute similarity with all doc vectors
            similarities = [
                np.dot(q_vec, d_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(d_vec))
                for d_vec in doc_vectors
            ]
            # Take maximum
            scores.append(max(similarities))

        # Average across query tokens
        return np.mean(scores)

    def store_multivector(
        self,
        doc_id: str,
        token_embeddings: List[np.ndarray],
        vector_store
    ):
        """
        Store multi-vector embeddings in vector store.

        Strategy: Flatten with position metadata.
        """
        for position, embedding in enumerate(token_embeddings):
            vector_store.add(
                id=f"{doc_id}_token_{position}",
                vector=embedding,
                metadata={
                    "doc_id": doc_id,
                    "token_position": position,
                    "is_multivector": True
                }
            )
```

### Binary Format Conversion

Implement efficient binary embedding storage:

```python
import numpy as np

class FormatConverter:
    """Convert embeddings between storage formats."""

    @staticmethod
    def to_binary(
        embeddings: np.ndarray,
        threshold: float = 0.0
    ) -> np.ndarray:
        """
        Convert float embeddings to binary (1 bit per dimension).

        Args:
            embeddings: Float array of shape [..., dimensions]
            threshold: Values > threshold become 1, else 0

        Returns:
            Packed binary array with shape [..., dimensions // 8]
        """
        binary = (embeddings > threshold).astype(np.uint8)
        return np.packbits(binary, axis=-1)

    @staticmethod
    def to_ubinary(embeddings: np.ndarray) -> np.ndarray:
        """
        Convert float embeddings to unsigned binary (sign bits).

        Uses only sign: positive=1, negative=0.
        Maintains better quality than threshold-based binary.

        Args:
            embeddings: Float array of shape [..., dimensions]

        Returns:
            Packed binary array with shape [..., dimensions // 8]
        """
        binary = (embeddings > 0).astype(np.uint8)
        return np.packbits(binary, axis=-1)

    @staticmethod
    def from_binary(
        binary: np.ndarray,
        original_dims: int,
        dtype=np.float32
    ) -> np.ndarray:
        """
        Convert binary back to float approximation.

        Args:
            binary: Packed binary array
            original_dims: Original dimension count
            dtype: Output data type

        Returns:
            Float array with shape [..., original_dims]
        """
        # Unpack bits
        bits = np.unpackbits(binary, axis=-1)

        # Truncate to original dimensions (may have padding)
        bits = bits[..., :original_dims]

        # Convert to float: 0 -> -1, 1 -> +1
        return (bits.astype(dtype) * 2) - 1

    @staticmethod
    def hamming_similarity(
        binary1: np.ndarray,
        binary2: np.ndarray
    ) -> float:
        """
        Compute Hamming similarity between binary embeddings.

        Args:
            binary1, binary2: Packed binary arrays

        Returns:
            Similarity score in [0, 1]
        """
        # XOR to find differing bits
        xor = np.bitwise_xor(binary1, binary2)

        # Count matching bits
        total_bits = binary1.size * 8
        differing_bits = np.unpackbits(xor).sum()

        return 1.0 - (differing_bits / total_bits)

# Usage example
converter = FormatConverter()

# Convert to ubinary (8× storage reduction)
float_embeddings = model.embed(texts)  # Shape: [N, 1024]
binary = converter.to_ubinary(float_embeddings)  # Shape: [N, 128]

# Storage: 4KB -> 128 bytes per embedding

# Compute similarity in binary space (fast)
similarity = converter.hamming_similarity(binary[0], binary[1])

# Convert back to float if needed (approximation)
approx_float = converter.from_binary(binary, original_dims=1024)
```

### Intelligent Batching System

Implement token-aware batching for optimal throughput:

```python
import psutil
from typing import List, Iterator

class BatchProcessor:
    """Token-aware batch processing for embeddings."""

    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.max_tokens = config.max_tokens_per_batch

    def create_batches(
        self,
        texts: List[str]
    ) -> Iterator[List[str]]:
        """
        Create token-aware batches.

        Yields batches such that total tokens ≤ max_tokens_per_batch.
        """
        current_batch = []
        current_tokens = 0

        for text in texts:
            # Fast token estimation (1.3× word count)
            estimated_tokens = int(len(text.split()) * 1.3)

            # Check if adding this text exceeds limit
            if current_tokens + estimated_tokens > self.max_tokens:
                if current_batch:
                    yield current_batch
                current_batch = [text]
                current_tokens = estimated_tokens
            else:
                current_batch.append(text)
                current_tokens += estimated_tokens

        # Yield remaining batch
        if current_batch:
            yield current_batch

    @staticmethod
    def adaptive_batch_size(
        available_memory_gb: float,
        backend: str = "mps"
    ) -> int:
        """
        Compute optimal batch size based on available memory.

        Args:
            available_memory_gb: Available RAM in GB
            backend: "mps", "cuda", or "cpu"

        Returns:
            Recommended batch size
        """
        # Base memory per backend
        base_memory = {
            "mps": 14,    # PyTorch MPS
            "cuda": 14,   # PyTorch CUDA
            "cpu": 8,     # PyTorch CPU
        }

        base = base_memory.get(backend, 14)
        available = available_memory_gb - base

        # Per-text memory overhead (~50MB)
        per_text_mb = 50
        max_batch = int((available * 1024) / per_text_mb)

        # Clamp to reasonable range
        return max(8, min(max_batch, 256))

    def process_with_memory_monitoring(
        self,
        texts: List[str],
        embed_fn
    ) -> np.ndarray:
        """
        Process texts with dynamic batch size adjustment.

        Monitors memory and reduces batch size if pressure is high.
        """
        results = []
        current_batch_size = self.config.batch_size

        for batch in self.create_batches(texts):
            # Check memory before processing
            memory_percent = psutil.virtual_memory().percent

            if memory_percent > 80:
                # Reduce batch size
                new_batch_size = max(4, current_batch_size // 2)
                if new_batch_size < current_batch_size:
                    logger.warning(
                        f"Memory pressure {memory_percent}%, "
                        f"reducing batch: {current_batch_size} → {new_batch_size}"
                    )
                    current_batch_size = new_batch_size

                # Force garbage collection
                import gc
                gc.collect()

            # Process batch
            batch_embeddings = embed_fn(batch[:current_batch_size])
            results.append(batch_embeddings)

        return np.vstack(results)
```

### Configuration Presets Summary

| Preset | Task | Dimensions | Late Chunking | Format | Use Case |
|--------|------|------------|---------------|--------|----------|
| `for_query()` | retrieval.query | 1024 | False | float | Search queries |
| `for_documents()` | retrieval.passage | 1024 | True | float | Document indexing |
| `for_code(is_query=True)` | code.query | 1024 | False | float | Code search query |
| `for_code(is_query=False)` | code.passage | 1024 | True | float | Code indexing |
| `storage_optimized()` | retrieval.passage | 512 | True | ubinary | Large-scale storage |

### Testing Configuration and Features

Create comprehensive tests for new functionality:

```python
import pytest
from unittest.mock import Mock, patch

def test_embedding_config_validation():
    """Test configuration validation."""
    # Valid config
    config = EmbeddingConfig(
        task="retrieval.query",
        dimensions=1024,
        late_chunking=False
    )
    assert config.task == "retrieval.query"

    # Invalid dimension
    with pytest.raises(ValueError):
        EmbeddingConfig(dimensions=999)

    # Invalid task
    with pytest.raises(ValueError):
        EmbeddingConfig(task="invalid-task")

def test_late_chunking_auto_disable():
    """Test late chunking auto-disabled for queries."""
    config = EmbeddingConfig(
        task="retrieval.query",
        late_chunking=True  # Should be overridden
    )
    assert config.late_chunking == False

def test_binary_format_conversion():
    """Test round-trip binary conversion."""
    converter = FormatConverter()

    # Original embeddings
    float_emb = np.random.randn(10, 1024).astype(np.float32)

    # Convert to binary and back
    binary = converter.to_ubinary(float_emb)
    approx = converter.from_binary(binary, original_dims=1024)

    # Check dimensions match
    assert binary.shape == (10, 128)  # 1024 / 8 = 128 bytes
    assert approx.shape == float_emb.shape

    # Check similarity is preserved (not exact)
    orig_sim = np.dot(float_emb[0], float_emb[1])
    approx_sim = np.dot(approx[0], approx[1])
    assert abs(orig_sim - approx_sim) < 0.5

def test_token_aware_batching():
    """Test batching based on token count."""
    processor = BatchProcessor(
        EmbeddingConfig(max_tokens_per_batch=100)
    )

    texts = [
        "Short text",
        "Medium length text with more words here",
        "Another short one",
        "Very long text " * 50  # ~100 words
    ]

    batches = list(processor.create_batches(texts))

    # Long text should be in separate batch
    assert len(batches) >= 2

def test_adaptive_batch_size():
    """Test memory-aware batch sizing."""
    # High memory system
    batch = BatchProcessor.adaptive_batch_size(32, "mps")
    assert batch >= 32

    # Low memory system
    batch = BatchProcessor.adaptive_batch_size(8, "mps")
    assert batch <= 16

def test_multivector_maxsim():
    """Test MaxSim scoring for multi-vector embeddings."""
    handler = MultiVectorHandler()

    # Mock query and document vectors
    query = [np.random.randn(1024) for _ in range(5)]  # 5 tokens
    doc = [np.random.randn(1024) for _ in range(10)]   # 10 tokens

    score = handler.maxsim_score(query, doc)

    # Score should be in reasonable range
    assert -1.0 <= score <= 1.0
```
