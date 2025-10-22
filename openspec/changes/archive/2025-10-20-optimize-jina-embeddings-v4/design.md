# Optimize Jina Embeddings v4 - Design

## Architecture Overview

The optimization enhances the existing `JinaEmbeddingsV4` class with advanced capabilities while maintaining backward compatibility. The design follows a layered approach:

```
JinaEmbeddingsV4 (public API)
    ├── EmbeddingConfig (configuration management)
    ├── BatchProcessor (intelligent batching)
    ├── FormatConverter (embedding format conversion)
    └── MultiVectorHandler (ColBERT-style embeddings)
```

## Architectural Alignment with OCR Pipeline

This design follows the **same architectural patterns** established in the OCR pipeline streamlining (`openspec/changes/archive/2025-10-20-streamline-ocr-processing-pipeline/`). Key patterns adopted:

1. **Standard Dataclass Configuration with Presets** (from `OCRConfig`)
2. **Smart Defaults for 80% of Use Cases** (from `NanonetsLoader`)
3. **Memory-Aware Processing** (from `OCRConfig.memory_constrained()`)
4. **Hardware-Specific Optimization** (MPS prioritization on Apple Silicon)

See **Related Work** section at end for detailed comparisons.

## Key Design Decisions

### 1. Configuration Management

**Decision**: Use standard Python dataclass for configuration with smart defaults, following the OCRConfig pattern.

**Rationale**:
- **Consistent with OCR pipeline streamlining** approach (see `OCRConfig`)
- Avoids adding Pydantic as a dependency (OCR uses standard dataclasses)
- Enables hardware-aware defaults
- Clear documentation through type hints
- **Pattern proven successful in OCR pipeline** with `mlx_optimized()`, `balanced()`, `memory_constrained()` presets (note: mlx_optimized actually uses MPS)

**Implementation Pattern**:
```python
from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class EmbeddingConfig:
    """Configuration for Jina Embeddings v4."""

    # Core parameters
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

    # Advanced features
    return_multivector: bool = False
    embedding_format: Literal["float", "base64", "binary", "ubinary"] = "float"

    # Performance tuning
    batch_size: int = Field(default=32, ge=1, le=256)
    max_tokens_per_batch: int = Field(default=8192, ge=1024, le=32768)

    @classmethod
    def for_query(cls, **kwargs) -> 'EmbeddingConfig':
        """Optimal config for search queries."""
        return cls(task="retrieval.query", dimensions=1024, **kwargs)

    @classmethod
    def for_documents(cls, **kwargs) -> 'EmbeddingConfig':
        """Optimal config for document storage."""
        return cls(
            task="retrieval.passage",
            dimensions=1024,
            late_chunking=True,
            **kwargs
        )

    @classmethod
    def for_code(cls, is_query: bool = False, **kwargs) -> 'EmbeddingConfig':
        """Optimal config for code search."""
        task = "code.query" if is_query else "code.passage"
        return cls(task=task, dimensions=1024, **kwargs)

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

### 2. Late Chunking Integration

**Decision**: Enable late chunking by default for document/passage embeddings, disable for queries.

**Rationale**:
- Research shows late chunking improves retrieval quality by preserving cross-chunk context
- Queries are typically single units, don't benefit from late chunking
- Documents are often chunked, benefit significantly
- Make it opt-out rather than opt-in for better defaults

**Implementation Strategy**:
- Add `late_chunking` parameter to embed methods
- Pass directly to Jina v4 model
- Document performance impact (slight latency increase, quality improvement)

### 3. Task-Specific Optimization

**Decision**: Provide clear task presets via configuration factory methods.

**Rationale**:
- Jina v4 model is optimized differently for queries vs. passages
- Users may not understand task parameter implications
- Presets reduce configuration burden and errors

**Task Mapping**:
| Use Case | Task Parameter | Typical Dimension | Late Chunking |
|----------|----------------|-------------------|---------------|
| Search queries | `retrieval.query` | 1024 | False |
| Document storage | `retrieval.passage` | 1024 | True |
| Semantic similarity | `text-matching` | 1024 | False |
| Code search (query) | `code.query` | 1024 | False |
| Code search (index) | `code.passage` | 1024 | True |

### 4. Multi-Vector Embeddings

**Decision**: Add multi-vector support as opt-in feature with adapter layer for existing vector stores.

**Rationale**:
- Multi-vector (ColBERT-style) embeddings improve retrieval accuracy
- Requires storage/retrieval changes, too complex for default
- Provide clean abstraction so users can adopt incrementally

**Architecture**:
```python
class MultiVectorHandler:
    """Handles multi-vector embedding generation and storage."""

    def embed_multivector(
        self,
        texts: List[str],
        config: EmbeddingConfig
    ) -> List[List[np.ndarray]]:
        """
        Generate multi-vector embeddings.

        Returns:
            List of token-level embeddings per text.
            Each text -> List of vectors (one per token).
        """
        # Call Jina v4 with return_multivector=True
        # Returns List[List[float]] with shape [num_texts, num_tokens, dim]
        pass

    def store_multivector(
        self,
        doc_id: str,
        vectors: List[np.ndarray],
        metadata: dict
    ):
        """Store multi-vector embeddings in adapted format."""
        # Convert to storage format (e.g., flatten with position metadata)
        pass

    def retrieve_multivector(
        self,
        query_vectors: List[np.ndarray],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """Late interaction retrieval using MaxSim."""
        # Implement MaxSim scoring: max(dot(q_i, d_j))
        pass
```

### 5. Binary Format Support

**Decision**: Support binary/ubinary formats with automatic conversion utilities.

**Rationale**:
- 8-32× storage reduction is significant for large document collections
- Quality impact is minimal for retrieval tasks (see research)
- Need conversion utilities for backward compatibility

**Format Comparison**:
| Format | Size per 1024-dim | Conversion | Quality Loss |
|--------|-------------------|------------|--------------|
| float32 | 4KB | None | 0% |
| base64 | 5.3KB | Encode/decode | 0% |
| binary | 128 bytes | Threshold | <1% MRR |
| ubinary | 128 bytes | Sign only | <2% MRR |

**Implementation**:
```python
class FormatConverter:
    """Convert embeddings between formats."""

    @staticmethod
    def to_binary(embeddings: np.ndarray, threshold: float = 0.0) -> np.ndarray:
        """Convert float embeddings to binary (1 bit per dimension)."""
        # Use sign or threshold
        binary = (embeddings > threshold).astype(np.uint8)
        # Pack 8 bits per byte
        return np.packbits(binary, axis=-1)

    @staticmethod
    def to_ubinary(embeddings: np.ndarray) -> np.ndarray:
        """Convert float embeddings to unsigned binary (sign bits only)."""
        # Use sign bits: positive=1, negative=0
        binary = (embeddings > 0).astype(np.uint8)
        return np.packbits(binary, axis=-1)

    @staticmethod
    def from_binary(binary: np.ndarray, dtype=np.float32) -> np.ndarray:
        """Convert binary back to float (approximation)."""
        # Unpack bits
        bits = np.unpackbits(binary, axis=-1)
        # Convert to -1/+1 or 0/1 based on format
        return bits.astype(dtype) * 2 - 1  # Maps to [-1, 1]

    @staticmethod
    def hamming_similarity(binary1: np.ndarray, binary2: np.ndarray) -> float:
        """Compute similarity between binary embeddings."""
        # XOR and count matching bits
        xor = np.bitwise_xor(binary1, binary2)
        return 1.0 - (np.unpackbits(xor).sum() / (binary1.size * 8))
```

### 6. Intelligent Batching

**Decision**: Implement token-aware batching with dynamic sizing based on memory constraints.

**Rationale**:
- Document-based batching is inefficient (varying lengths)
- Token-based batching maximizes GPU utilization
- Dynamic sizing prevents OOM on long documents

**Batching Strategy**:
```python
class BatchProcessor:
    """Intelligent batching for embedding generation."""

    def __init__(self, config: EmbeddingConfig, tokenizer):
        self.config = config
        self.tokenizer = tokenizer
        self.max_tokens = config.max_tokens_per_batch

    def create_batches(
        self,
        texts: List[str]
    ) -> List[List[str]]:
        """Create token-aware batches."""
        batches = []
        current_batch = []
        current_tokens = 0

        for text in texts:
            # Estimate tokens (fast, no actual tokenization)
            estimated_tokens = len(text.split()) * 1.3  # Rough estimate

            if current_tokens + estimated_tokens > self.max_tokens:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [text]
                current_tokens = estimated_tokens
            else:
                current_batch.append(text)
                current_tokens += estimated_tokens

        if current_batch:
            batches.append(current_batch)

        return batches

    def adaptive_batch_size(self, available_memory_gb: float) -> int:
        """Compute optimal batch size based on available memory."""
        # Jina v4 base memory: ~3GB on MLX, ~14GB on PyTorch
        # Per-text overhead: ~50MB per batch item
        base_memory = 3 if self._is_mlx_available() else 14
        available = available_memory_gb - base_memory

        if available < 2:
            return 8
        elif available < 8:
            return 16
        elif available < 16:
            return 32
        else:
            return 64
```

### 7. Multimodal Support Enhancement

**Decision**: Add native PDF support and optimize image processing using Jina v4's preferred formats.

**Rationale**:
- Current implementation has basic image fallback
- Jina v4 handles PDFs and images natively, better than manual conversion
- Use PIL Image objects or base64 for better performance

**Implementation**:
```python
def embed_multimodal(
    self,
    inputs: List[Union[str, Image.Image, bytes, Path]],
    config: EmbeddingConfig
) -> np.ndarray:
    """
    Embed mixed text, images, and PDFs.

    Args:
        inputs: Mix of text strings, PIL Images, image bytes, or PDF paths
        config: Embedding configuration

    Returns:
        Unified embeddings for all inputs
    """
    processed = []

    for inp in inputs:
        if isinstance(inp, str):
            processed.append(inp)
        elif isinstance(inp, Image.Image):
            processed.append(inp)  # PIL Image directly
        elif isinstance(inp, bytes):
            # Convert bytes to PIL Image
            processed.append(Image.open(BytesIO(inp)))
        elif isinstance(inp, Path) and inp.suffix.lower() == '.pdf':
            # For PDFs, Jina v4 can handle directly
            # Or convert to images first
            processed.append(str(inp))
        else:
            raise ValueError(f"Unsupported input type: {type(inp)}")

    return self._embed_batch(processed, config)
```

## Component Integration

### Integration with Existing Pipeline

The optimized embeddings integrate into the existing RAG pipeline with minimal changes:

1. **Ingestion Phase**: Use `EmbeddingConfig.for_documents()` with late chunking
2. **Query Phase**: Use `EmbeddingConfig.for_query()` without late chunking
3. **Storage Phase**: Use `FormatConverter` for binary storage if needed
4. **Retrieval Phase**: Use `MultiVectorHandler` for advanced retrieval if enabled

### Backward Compatibility

Maintain existing API while adding new features:

```python
class JinaEmbeddingsV4:
    """Enhanced Jina Embeddings v4 with backward compatibility."""

    def __init__(
        self,
        model_name: str = "jinaai/jina-embeddings-v4",
        device: Optional[str] = None,
        cache_dir: Optional[str] = None,
        trust_remote_code: bool = True,
        # NEW: Optional config override
        config: Optional[EmbeddingConfig] = None,
    ):
        # Existing initialization code...

        # NEW: Store default config
        if config is None:
            config = EmbeddingConfig.for_documents()
        self.default_config = config

    # EXISTING: Keep old embed() signature working
    def embed(
        self,
        texts: List[str],
        task: Optional[str] = None,  # DEPRECATED but supported
        **kwargs
    ) -> np.ndarray:
        """
        Embed texts (backward compatible).

        DEPRECATED: Use embed_with_config() for new features.
        """
        if task:
            warnings.warn(
                "Direct task parameter is deprecated. "
                "Use EmbeddingConfig.for_query() or for_documents()",
                DeprecationWarning
            )

        # Use default config, override with kwargs
        config = self.default_config
        if task or kwargs:
            config = dataclasses.replace(config, task=task or config.task, **kwargs)

        return self.embed_with_config(texts, config)

    # NEW: Primary API for new features
    def embed_with_config(
        self,
        texts: List[str],
        config: EmbeddingConfig
    ) -> Union[np.ndarray, List[List[np.ndarray]]]:
        """
        Embed texts with full configuration control.

        Returns:
            Standard embeddings (np.ndarray) or multi-vector embeddings.
        """
        # Implementation using new features
        pass
```

## Testing Strategy

### Unit Tests
- Configuration validation and presets
- Format conversion accuracy and invertibility
- Batch processing with various input sizes
- Multi-vector embedding generation

### Integration Tests
- End-to-end embedding pipeline with late chunking
- Storage and retrieval with binary formats
- Multi-vector retrieval accuracy vs. single-vector
- Multimodal input handling (text, images, PDFs)

### Performance Tests
- Throughput improvement from optimized batching
- Storage reduction verification (8× for ubinary)
- Memory usage under load
- Retrieval quality (MRR/NDCG) with different configurations

### Benchmark Suite
```python
def benchmark_embedding_configs():
    """Compare configurations on standard datasets."""
    configs = {
        "baseline": EmbeddingConfig(late_chunking=False, dimensions=2048),
        "optimized": EmbeddingConfig.for_documents(),
        "storage_opt": EmbeddingConfig.storage_optimized(),
        "multivector": EmbeddingConfig(return_multivector=True, dimensions=1024),
    }

    for name, config in configs.items():
        # Measure:
        # - Embedding generation time
        # - Storage size
        # - Retrieval quality (MRR@10, NDCG@10)
        # - Memory usage
        pass
```

## Migration Path

### Phase 1: Opt-In Features (Weeks 1-2)
- Add new configuration system alongside existing API
- Implement late chunking, task presets, format conversion
- Update documentation with examples
- **User Action**: None required, existing code works

### Phase 2: Enhanced Documentation (Week 3)
- Update all examples to use new configuration approach
- Publish performance benchmarks
- Create migration guide
- **User Action**: Can start adopting new features

### Phase 3: Recommended Defaults (Week 4)
- Change default config to enable late chunking
- Update tutorials to use task-specific presets
- Add deprecation warnings for old patterns
- **User Action**: May see deprecation warnings, functionality unchanged

### Phase 4: Long-Term (Month 2+)
- Consider making new API primary in documentation
- Evaluate removing deprecated parameters (breaking change, major version)
- **User Action**: Plan migration if using deprecated features

## Performance Targets

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Retrieval Quality (MRR@10) | 0.72 | 0.75-0.77 | MS MARCO dataset |
| Embedding Throughput | 100 docs/sec | 120-130 docs/sec | M4 Max, batch=32 |
| Storage per 1M docs | 8GB | 1GB | Using ubinary, 1024-dim |
| Memory Usage (peak) | 16GB | 16GB | No regression |
| Latency (p99) | 200ms | 180ms | Per-batch, 32 docs |

## Security and Privacy Considerations

- **Local Processing**: All embedding generation happens locally, no data sent to external APIs (unless explicitly configured)
- **Model Trust**: Using `trust_remote_code=True` for Hugging Face model (existing behavior, document security implications)
- **Binary Format**: Ensure binary embeddings don't leak information through compression patterns
- **Multi-Vector**: Token-level embeddings may expose more granular information than single-vector

## Open Issues for Design Review

1. **MLX Backend for Jina v4**: Should we investigate MLX quantization for Jina v4 embeddings?
   - **Pro**: Could potentially reduce memory footprint on Apple Silicon
   - **Con**: Requires separate quantization effort, may affect quality
   - **OCR Note**: MLX quantization for Nanonets OCR was attempted but not successful
   - **Recommendation**: **LOW PRIORITY** - Consider in separate proposal, but note that MLX hasn't proven successful for similar models

2. **Multi-Vector Storage Format**: What's the best way to store token-level embeddings?
   - **Option A**: Flatten with position metadata (simple, works with existing stores)
   - **Option B**: Use specialized ColBERT store (better performance, more complexity)
   - **Recommendation**: Start with Option A, provide adapter for Option B

3. **Default Dimension**: Should we default to 1024 instead of 2048?
   - **Pro**: 50% storage reduction, still excellent quality
   - **Con**: Slight quality degradation vs. full 2048
   - **OCR Insight**: Similar to Nanonets FAST preset using lower resolution
   - **Recommendation**: Default to 1024 for balance, allow override

4. **Async API**: Should we add async embedding generation for better concurrency?
   - **Pro**: Better for high-throughput scenarios
   - **Con**: Adds complexity, most usage is synchronous
   - **Recommendation**: Defer to future enhancement if needed

5. **Two-Tier Embedding Strategy**: Should we apply Nanonets two-tier pattern to embeddings?
   - **Pro**: Could provide 2-4× speedup for simple queries (similar to Nanonets 2× speedup)
   - **Con**: Requires complexity detection heuristics, may not apply well to queries
   - **OCR Success**: Nanonets two-tier achieves 2× speedup with markdown complexity analysis
   - **Recommendation**: Investigate in Phase 11 (optional) after core features complete

## Related Work: Comparison with OCR Pipeline Streamlining

This design deliberately reuses proven patterns from the OCR pipeline streamlining. Here's a detailed comparison:

### Configuration Pattern Comparison

| Aspect | OCRConfig | EmbeddingConfig |
|--------|-----------|-----------------|
| **Base Class** | Standard `@dataclass` | Standard `@dataclass` |
| **Validation** | Manual validation in methods | Manual validation in methods |
| **Presets** | `mlx_optimized()`, `balanced()`, `memory_constrained()` | `for_query()`, `for_documents()`, `storage_optimized()` |
| **Smart Defaults** | Auto-select based on hardware (MPS on Apple Silicon) | Auto-select based on task type |
| **Memory Awareness** | Dynamic batch sizing based on RAM | Token-aware batching with memory monitoring |

### Architecture Pattern Comparison

| Pattern | OCR Implementation | Embedding Implementation |
|---------|-------------------|-------------------------|
| **Backend Selection** | MPS > CUDA > CPU | Same device selection logic |
| **Memory Optimization** | Not achieved via MLX (attempted but unsuccessful) | To be investigated |
| **Batching Strategy** | Page-based with pipeline parallelism | Token-based with dynamic sizing |
| **Configuration Complexity** | 5 parameters (batch_size, render_workers, analysis_workers, pre_render_batches, checkpoint_enabled) | 7 parameters (task, dimensions, late_chunking, return_multivector, embedding_format, batch_size, max_tokens_per_batch) |
| **Zero-Config Usage** | `NanonetsLoader()` auto-configures | `JinaEmbeddingsV4()` auto-configures |

### Nanonets Two-Tier System Insights

The Nanonets two-tier system (`NANONETS_TWO_TIER_SYSTEM.md`) demonstrates a powerful optimization pattern:

**OCR Approach**:
1. Process with FAST preset (lower resolution, ~60-100 sec/page)
2. Analyze output markdown for complexity (tables, equations, images)
3. Re-process complex documents with BALANCED preset (~199 sec/page)
4. **Result**: 2× speedup for 80% simple documents

**Potential Embedding Adaptation**:
1. Embed with lower dimensions (512, ~4× faster)
2. Analyze query complexity (length, semantic depth, entity count)
3. Re-embed complex queries with full dimensions (2048)
4. **Target**: 2-4× speedup for 80% simple queries

**Challenges for Embeddings**:
- Query complexity harder to detect than markdown complexity
- Queries typically short, may not justify two-tier approach
- Need production data to validate query complexity distribution
- **Recommendation**: Investigate in Phase 11 (optional) only if production metrics warrant it

### Key Lessons Learned from OCR

1. **MLX Quantization Didn't Work**: MLX was attempted for Nanonets but unsuccessful → Be cautious about MLX for Jina v4
2. **Standard Dataclasses Work Well**: Simple configuration without dependencies → Use same pattern
3. **Presets Beat Profiles**: Clear factory methods > complex profile system → Use `for_query()` not profile strings
4. **Smart Defaults Matter**: 80% of use cases need zero configuration → Auto-detect hardware and task
5. **Two-Tier Can Work**: FAST/BALANCED routing achieves 2× speedup → Consider for embeddings if metrics support it

### References to OCR Work

- **OCR Pipeline Streamlining**: `openspec/changes/archive/2025-10-20-streamline-ocr-processing-pipeline/`
- **Nanonets Two-Tier System**: `NANONETS_TWO_TIER_SYSTEM.md`
- **OCR Configuration Guide**: `docs/guides/ocr-configuration.md`
- **OCR Migration Guide**: `docs/guides/ocr-migration.md`
