# Implementation Tasks

## Implementation Notes

See `design.md` for complete architectural decisions and code patterns used across all phases.

### Architecture Alignment with OCR Pipeline

This proposal follows the **same architectural patterns** established in the OCR pipeline streamlining (`openspec/changes/archive/2025-10-20-streamline-ocr-processing-pipeline/`), ensuring consistency across the codebase:

1. **Standard Dataclass Configuration with Presets** (Pattern from `OCRConfig`)
   - Use standard Python `@dataclass`
   - Implement preset factory methods: `EmbeddingConfig.for_query()`, `for_documents()`, `storage_optimized()`
   - Similar to: `OCRConfig.mlx_optimized()`, `balanced()`, `memory_constrained()` (note: mlx_optimized uses MPS)

2. **Smart Defaults for 80% of Use Cases** (Pattern from `NanonetsLoader`)
   - Auto-detect best configuration based on hardware and task
   - Default to sensible presets without configuration
   - Similar to: `NanonetsLoader()` auto-selecting `mlx_optimized` (actually MPS) on Apple Silicon

3. **Memory-Aware Processing** (Pattern from `OCRConfig`)
   - Dynamic batch sizing based on available memory
   - Token-aware batching (similar to page-based batching in OCR)
   - Memory monitoring with adaptive sizing (psutil integration)

4. **Hardware-Specific Optimization** (Pattern from MPS prioritization)
   - Prioritize MPS backend on Apple Silicon
   - Automatic fallback to PyTorch/CPU
   - Device selection: MPS > CUDA > CPU (same as OCR)

### Configuration Strategy
- Use standard Python `@dataclass`
- Implement presets via `@classmethod` factory methods (pattern: `OCRConfig.mlx_optimized()` - note: uses MPS)
- Use validation methods for checking parameters and smart defaults

### Key Implementation Patterns
- **Late Chunking**: Concatenate texts with `[SEP]` separator before tokenization
- **Multi-Vector**: Return token-level embeddings as `List[List[np.ndarray]]`
- **Binary Conversion**: Use `np.packbits()` for 8× storage reduction
- **Token-Aware Batching**: Estimate tokens via `len(text.split()) * 1.3`
- **Memory Monitoring**: Use `psutil.virtual_memory().percent` for adaptive sizing

---

## Phase 1: Configuration System (Priority: High)

### 1.1 Create EmbeddingConfig with Standard Dataclass
- [ ] Create `src/jina_rag_pipeline/embeddings/config.py` with standard Python dataclass
- [ ] Define 7 core parameters: task, dimensions, late_chunking, return_multivector, embedding_format, batch_size, max_tokens_per_batch
- [ ] Add validation methods for task/dimension constraints
- [ ] Implement validation in `__post_init__()` method
- **Validation**: Config validates correctly, raises errors for invalid params

### 1.2 Implement Configuration Presets
- [ ] Implement `EmbeddingConfig.for_query()` preset (task=retrieval.query, late_chunking=False)
- [ ] Implement `EmbeddingConfig.for_documents()` preset (task=retrieval.passage, late_chunking=True)
- [ ] Implement `EmbeddingConfig.for_code(is_query: bool)` preset for code search
- [ ] Implement `EmbeddingConfig.storage_optimized()` preset (dim=512, format=ubinary)
- **Validation**: All presets return valid, frozen configurations

### 1.3 Add Auto-Configuration for Query Tasks
- [ ] Implement `@field_validator('late_chunking', mode='before')` to auto-disable for `.query` tasks
- [ ] Add logging when late chunking is auto-disabled
- [ ] Document auto-configuration behavior in docstrings
- **Validation**: late_chunking=False for all query tasks regardless of input

### 1.4 Update JinaEmbeddingsV4 Constructor
- [ ] Add `config: Optional[EmbeddingConfig] = None` parameter to `__init__`
- [ ] Default to `EmbeddingConfig.for_documents()` if config is None
- [ ] Store as `self.default_config` for use in embed methods
- [ ] Update docstrings to document configuration usage
- **Validation**: Initialization works with and without explicit config

## Phase 2: Late Chunking Support (Priority: High)

### 2.1 Implement Late Chunking in embed_with_config
- [ ] Create new `embed_with_config(texts: List[str], config: EmbeddingConfig)` method
- [ ] Add late chunking logic: concatenate texts with `[SEP]` separator when enabled
- [ ] Pass `late_chunking` parameter to Jina v4 model forward pass
- [ ] Handle splitting of concatenated embeddings back to individual (if needed)
- **Validation**: Embeddings generated with late_chunking=True differ from False

### 2.2 Integrate Late Chunking with Model API
- [ ] Review Jina v4 model API for native late chunking support
- [ ] Update model forward pass to include `late_chunking` parameter
- [ ] Ensure tokenization respects late chunking flag
- [ ] Add logging when late chunking is active
- **Validation**: Model API accepts late_chunking parameter

### 2.3 Add Late Chunking Tests
- [ ] Test late chunking enabled vs disabled produces different embeddings
- [ ] Test concatenation logic with various text lengths
- [ ] Benchmark retrieval quality improvement (target: 5-10% MRR gain)
- [ ] Test edge cases: empty texts, very long texts, single text
- **Validation**: All late chunking tests pass, quality improvement validated

## Phase 3: Task-Specific Optimization (Priority: High)

### 3.1 Implement Task Parameter Passing
- [ ] Update `embed_with_config` to pass `task` parameter to model
- [ ] Ensure task parameter is used in model forward pass
- [ ] Add task validation in EmbeddingConfig (use Literal type)
- [ ] Log selected task for debugging
- **Validation**: Different tasks produce different embeddings

### 3.2 Document Task Usage Patterns
- [ ] Create usage guide in `docs/embeddings/task-optimization.md`
- [ ] Document each task type with examples: retrieval.query, retrieval.passage, text-matching, code tasks
- [ ] Add performance benchmarks for each task type
- [ ] Create code examples for common scenarios
- **Validation**: Documentation is clear and complete

### 3.3 Update Examples to Use Task Presets
- [ ] Update query embedding examples to use `EmbeddingConfig.for_query()`
- [ ] Update document indexing examples to use `EmbeddingConfig.for_documents()`
- [ ] Add code search examples with `EmbeddingConfig.for_code()`
- [ ] Update tests to use task-specific presets
- **Validation**: All examples run successfully with presets

## Phase 4: Multi-Vector Embeddings (Priority: Medium)

### 4.1 Create MultiVectorHandler Class
- [ ] Create `src/jina_rag_pipeline/embeddings/multivector.py`
- [ ] Implement `generate_multivector()` method returning `List[List[np.ndarray]]`
- [ ] Implement `maxsim_score()` for ColBERT-style retrieval
- [ ] Implement `store_multivector()` with flattened storage strategy
- **Validation**: Multi-vector generation produces token-level embeddings

### 4.2 Integrate Multi-Vector into JinaEmbeddingsV4
- [ ] Add `embed_multivector()` method to JinaEmbeddingsV4
- [ ] Pass `return_multivector=True` to model when enabled
- [ ] Handle multi-vector return type properly (List[List[np.ndarray]])
- [ ] Update type hints and docstrings
- **Validation**: Multi-vector embeddings generated successfully

### 4.3 Implement MaxSim Retrieval
- [ ] Implement MaxSim scoring in MultiVectorHandler
- [ ] Create retrieval function using MaxSim
- [ ] Add batched MaxSim for efficiency
- [ ] Benchmark retrieval accuracy vs single-vector
- **Validation**: MaxSim retrieval improves accuracy by 5-15%

### 4.4 Add Multi-Vector Storage Adapter
- [ ] Implement storage adapter for existing vector stores
- [ ] Flatten token embeddings with position metadata
- [ ] Implement retrieval that reconstructs multi-vector representations
- [ ] Add tests for store/retrieve round-trip
- **Validation**: Multi-vector embeddings can be stored and retrieved

## Phase 5: Binary Format Support (Priority: Medium)

### 5.1 Create FormatConverter Class
- [ ] Create `src/jina_rag_pipeline/embeddings/format_converter.py`
- [ ] Implement `to_binary(embeddings, threshold)` using `np.packbits()`
- [ ] Implement `to_ubinary(embeddings)` for sign-based binary
- [ ] Implement `from_binary(binary, original_dims)` with `np.unpackbits()`
- **Validation**: Binary conversion reduces size by 8× (128 bytes for 1024-dim)

### 5.2 Implement Binary Similarity Functions
- [ ] Implement `hamming_similarity(binary1, binary2)` using XOR
- [ ] Optimize for vectorized computation
- [ ] Add batch hamming similarity computation
- [ ] Benchmark similarity computation speed
- **Validation**: Hamming similarity is 10-100× faster than float cosine

### 5.3 Integrate Format Conversion into Pipeline
- [ ] Add `embedding_format` handling in `embed_with_config`
- [ ] Automatically convert to specified format after generation
- [ ] Add conversion utilities for existing embeddings
- [ ] Update storage to handle binary formats
- **Validation**: All formats (float, binary, ubinary) work end-to-end

### 5.4 Validate Binary Format Quality
- [ ] Benchmark retrieval quality with binary formats (target: <2% MRR loss)
- [ ] Test round-trip conversion maintains ranking
- [ ] Compare storage sizes (target: 8× reduction)
- [ ] Document quality/storage trade-offs
- **Validation**: Binary format achieves 8× storage reduction with <2% quality loss

## Phase 6: Intelligent Batching (Priority: High)

### 6.1 Create BatchProcessor Class
- [ ] Create `src/jina_rag_pipeline/embeddings/batch_processor.py`
- [ ] Implement `create_batches()` with token-aware batching
- [ ] Use fast token estimation: `len(text.split()) * 1.3`
- [ ] Respect `max_tokens_per_batch` configuration
- **Validation**: Batches respect token limits, maximize GPU usage

### 6.2 Implement Adaptive Batch Sizing
- [ ] Implement `adaptive_batch_size(available_memory_gb, backend)` static method
- [ ] Scale batch size: <8GB→8, 8-16GB→16, 16-32GB→32, >32GB→64
- [ ] Account for backend memory overhead (MPS/CUDA=14GB, CPU=8GB)
- [ ] Add batch size recommendation logging
- **Validation**: Batch sizes scale appropriately with available memory

### 6.3 Add Memory-Aware Processing
- [ ] Implement `process_with_memory_monitoring()` method
- [ ] Monitor memory with `psutil.virtual_memory().percent`
- [ ] Dynamically reduce batch size if memory >80%
- [ ] Force garbage collection on high memory pressure
- **Validation**: Processing completes without OOM on 16GB systems

### 6.4 Optimize Batching Performance
- [ ] Benchmark throughput improvement (target: 20-30% increase)
- [ ] Compare token-aware vs document-based batching
- [ ] Test with varying document lengths
- [ ] Optimize batch creation overhead
- **Validation**: Token-aware batching achieves 20-30% throughput improvement

## Phase 7: Enhanced Multimodal Support (Priority: Low)

### 7.1 Add Native Image Processing
- [ ] Update `embed()` to accept PIL Image objects directly
- [ ] Add automatic format detection (PIL, bytes, file path)
- [ ] Use Jina v4's native image processing
- [ ] Handle image encoding errors gracefully
- **Validation**: Images embedded successfully without manual conversion

### 7.2 Implement PDF Direct Support
- [ ] Add PDF path handling in embed methods
- [ ] Detect PDF files by extension or mime type
- [ ] Pass PDFs directly to Jina v4 model (if supported)
- [ ] Fall back to conversion if needed
- **Validation**: PDFs can be embedded directly

### 7.3 Create Multimodal Embedding API
- [ ] Implement `embed_multimodal(inputs: List[Union[str, Image, Path]])`
- [ ] Handle mixed input types in single batch
- [ ] Document multimodal capabilities
- [ ] Add multimodal examples
- **Validation**: Mixed text/image/PDF batches work correctly

## Phase 8: Backward Compatibility and Migration (Priority: High)

### 8.1 Maintain Old embed() API
- [ ] Keep existing `embed(texts, task, **kwargs)` signature working
- [ ] Add deprecation warnings for direct task parameter
- [ ] Convert old parameters to EmbeddingConfig internally
- [ ] Document migration path in deprecation message
- **Validation**: All existing code continues working

### 8.2 Create Migration Guide
- [ ] Write `docs/embeddings/migration-guide.md`
- [ ] Document old vs new API patterns
- [ ] Provide code examples for migration
- [ ] List benefits of new configuration system
- **Validation**: Migration guide is clear and complete

### 8.3 Update All Examples
- [ ] Update README examples to use new API
- [ ] Update tutorial notebooks with EmbeddingConfig
- [ ] Add comparison examples (old vs new)
- [ ] Update API reference documentation
- **Validation**: All examples use recommended patterns

### 8.4 Add Compatibility Tests
- [ ] Test old API still works with deprecation warnings
- [ ] Test parameter conversion from old to new format
- [ ] Test mixed usage (old and new API together)
- [ ] Verify no breaking changes
- **Validation**: Full backward compatibility maintained

## Phase 9: Testing and Validation (Priority: High)

### 9.1 Write Comprehensive Unit Tests
- [ ] Test EmbeddingConfig validation and presets (target: 100% coverage)
- [ ] Test late chunking enabled/disabled
- [ ] Test format conversion accuracy
- [ ] Test batch processing logic
- **Validation**: >85% overall test coverage

### 9.2 Create Integration Tests
- [ ] Test end-to-end embedding with late chunking
- [ ] Test multi-vector embedding and retrieval
- [ ] Test binary format storage and retrieval
- [ ] Test memory-aware batching under load
- **Validation**: All integration tests pass

### 9.3 Performance Benchmarking
- [ ] Benchmark retrieval quality improvement with late chunking (target: 5-10% MRR)
- [ ] Benchmark throughput improvement with optimized batching (target: 20-30%)
- [ ] Benchmark storage reduction with binary formats (target: 8×)
- [ ] Benchmark memory usage stays under 16GB
- **Validation**: All performance targets met

### 9.4 Quality Validation
- [ ] Validate late chunking improves retrieval on standard datasets (MS MARCO, BEIR)
- [ ] Validate binary formats maintain >98% retrieval quality
- [ ] Validate multi-vector embeddings improve accuracy by 5-15%
- [ ] Document all quality metrics
- **Validation**: Quality improvements validated on standard benchmarks

## Phase 10: Documentation and Examples (Priority: Medium)

### 10.1 Write Configuration Guide
- [ ] Create `docs/embeddings/configuration-guide.md`
- [ ] Document all configuration parameters
- [ ] Explain task types and when to use each
- [ ] Provide decision tree for configuration
- **Validation**: New users can configure in <5 minutes

### 10.2 Create Usage Examples
- [ ] Basic usage example with default config
- [ ] Task-specific examples (query, documents, code)
- [ ] Storage optimization example with binary formats
- [ ] Advanced example with multi-vector embeddings
- **Validation**: All examples run successfully

### 10.3 Write Performance Tuning Guide
- [ ] Document batch size recommendations
- [ ] Explain memory management strategies
- [ ] Provide hardware-specific guidance
- [ ] Include troubleshooting section
- **Validation**: Users can optimize for their hardware

### 10.4 API Reference Documentation
- [ ] Document all public classes and methods
- [ ] Include parameter descriptions and types
- [ ] Add usage examples in docstrings
- [ ] Generate API docs with Sphinx/MkDocs
- **Validation**: API documentation is complete and accurate

## Dependencies and Parallelization

**Can be done in parallel:**
- Phase 1 (Configuration) and Phase 5 (Binary Formats)
- Phase 2 (Late Chunking) and Phase 6 (Batching)
- Phase 4 (Multi-Vector) can start after Phase 1
- Phase 9 (Testing) can progress alongside development

**Sequential dependencies:**
- Phase 3 depends on Phase 1 (config must exist for task optimization)
- Phase 7 depends on Phase 1 (config needed for multimodal)
- Phase 8 depends on Phases 1-7 (migration after new features complete)
- Phase 10 depends on all previous phases (document after implementation)

## Time Estimates

- Phase 1 (Configuration): 2-3 days
- Phase 2 (Late Chunking): 2-3 days
- Phase 3 (Task Optimization): 1-2 days
- Phase 4 (Multi-Vector): 3-4 days
- Phase 5 (Binary Formats): 2-3 days
- Phase 6 (Batching): 2-3 days
- Phase 7 (Multimodal): 1-2 days
- Phase 8 (Compatibility): 1-2 days
- Phase 9 (Testing): 3-4 days
- Phase 10 (Documentation): 2-3 days

**Total: 3-4 weeks for complete implementation**

## Phase 11: Two-Tier Embedding Strategy (Optional, Priority: Low)

**Note**: This phase is **optional** and should only be pursued after validating the benefits in production. It applies the Nanonets two-tier pattern to embeddings.

### 11.1 Research Two-Tier Feasibility
- [ ] Analyze query complexity in production (length, semantic depth)
- [ ] Benchmark embedding time at different dimensions (512, 1024, 2048)
- [ ] Measure retrieval quality degradation with lower dimensions
- [ ] Define "simple" vs "complex" query criteria
- **Validation**: Clear criteria for when two-tier provides value

### 11.2 Implement Query Complexity Analyzer
- [ ] Create `QueryComplexityAnalyzer` (similar to `MarkdownComplexityAnalyzer`)
- [ ] Implement fast complexity heuristics (length, entity count, question words)
- [ ] Add configurable complexity thresholds
- [ ] Log complexity decisions for tuning
- **Validation**: Analyzer correctly identifies query complexity

### 11.3 Create Two-Tier Embedding Pipeline
- [ ] Implement `TwoTierEmbedder` class
- [ ] Process simple queries with 512 dimensions (4× faster)
- [ ] Process complex queries with 2048 dimensions (full quality)
- [ ] Track routing statistics (simple vs complex percentages)
- **Validation**: Two-tier system provides measurable speedup

### 11.4 Validate Two-Tier Performance
- [ ] Benchmark retrieval quality with two-tier vs single-tier
- [ ] Measure actual speedup in production (target: 2-3× for 80% simple queries)
- [ ] Validate storage savings (smaller embeddings for simple queries)
- [ ] Document when to use two-tier vs single-tier
- **Validation**: Two-tier provides >2× speedup with <5% quality loss

## Success Criteria

1. ✅ Retrieval quality improves 5-10% (MRR@10) with late chunking
2. ✅ Storage reduces 8× with ubinary format (<2% quality loss)
3. ✅ Throughput improves 20-30% with optimized batching
4. ✅ Memory usage stays under 16GB for 1000+ document batches
5. ✅ Full backward compatibility maintained
6. ✅ >85% test coverage achieved
7. ✅ Documentation complete with examples
8. ✅ Zero-config works for 80% of use cases
9. ✅ **(Phase 11 Optional)** Two-tier system achieves >2× speedup for 80% of queries with <5% quality loss
