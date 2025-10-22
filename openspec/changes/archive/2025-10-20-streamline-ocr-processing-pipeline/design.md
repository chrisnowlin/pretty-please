# Design: Streamline OCR Processing Pipeline

## Overview

This design document outlines the architectural changes to streamline the Nanonets OCR processing pipeline, prioritizing MLX for its memory efficiency while simplifying the overall system architecture.

## Key Design Decisions

### 1. Unified Analyzer Architecture

**Decision**: Create a single `NanonetsAnalyzer` class that internally manages backend selection.

**Rationale**:
- Eliminates API inconsistencies between MLX and PyTorch implementations
- Reduces cognitive load for developers
- Enables transparent backend switching without code changes
- Simplifies testing and maintenance

**Implementation**:
```python
class NanonetsAnalyzer:
    def __init__(self, backend="auto", **kwargs):
        # Auto-detect best backend: MLX > MPS > CUDA > CPU
        if backend == "auto":
            backend = self._detect_best_backend()

        if backend == "mlx" and MLX_AVAILABLE:
            self._impl = MLXAnalyzerImpl(**kwargs)
        elif backend in ["mps", "cuda", "cpu"]:
            self._impl = TorchAnalyzerImpl(device=backend, **kwargs)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def analyze_document(self, image_path, **kwargs):
        return self._impl.analyze_document(image_path, **kwargs)
```

### 2. Component Separation for Loader

**Decision**: Split `NanonetsFirstLoader` into three focused components:

1. **DocumentRenderer**: Handles PDF/PPT to image conversion
2. **AnalysisPipeline**: Manages OCR analysis workflow
3. **CheckpointManager**: Handles persistence and recovery (existing)

**Rationale**:
- Single Responsibility Principle - each component has one clear job
- Easier to test individual components
- Allows reuse of components in different contexts
- Reduces complexity of main loader class

**Architecture**:
```
NanonetsLoader (orchestrator, ~200 lines)
    ├── DocumentRenderer (rendering, ~150 lines)
    │   ├── PDFRenderer
    │   └── PowerPointRenderer
    ├── AnalysisPipeline (analysis, ~200 lines)
    │   ├── BatchProcessor
    │   └── NanonetsAnalyzer
    └── CheckpointManager (persistence, existing)
```

### 3. Configuration Simplification

**Decision**: Replace complex profile system with explicit configuration class.

**Before** (complex):
```python
# Multiple ways to configure:
# 1. Profile selection via environment
# 2. Constructor parameters
# 3. Profile overrides
# 4. Auto-detection logic
loader = NanonetsFirstLoader(
    batch_size=None,  # Auto-detect from profile
    max_render_workers=None,  # Auto-detect
    max_analysis_workers=None,  # Auto-detect
)
```

**After** (simple):
```python
# Single configuration object with smart defaults
config = OCRConfig(
    batch_size=30,  # Optimal for MLX
    render_workers=20,  # Max parallelism
    mlx_workers=1,  # Thread-safety constraint
    pre_render_batches=4,  # Pipeline depth
)
loader = NanonetsLoader(config)

# Or use presets for common scenarios
loader = NanonetsLoader(OCRConfig.mlx_optimized())
loader = NanonetsLoader(OCRConfig.memory_constrained())
```

**Rationale**:
- Explicit is better than implicit
- Configuration becomes documentable and type-safe
- Presets provide good defaults while allowing customization
- Removes confusion about precedence and overrides

### 4. MLX Thread-Safety Abstraction

**Decision**: Hide MLX's single-worker limitation behind the pipeline interface.

**Implementation Strategy**:
```python
class AnalysisPipeline:
    def __init__(self, analyzer, config):
        self.analyzer = analyzer
        self.config = config

        # Automatically enforce single worker for MLX
        if isinstance(analyzer._impl, MLXAnalyzerImpl):
            self.max_workers = 1
            logger.info("MLX backend detected - using single worker for thread safety")
        else:
            self.max_workers = config.analysis_workers

    def process_batch(self, images):
        if self.max_workers == 1:
            # Sequential processing for MLX
            return [self.analyzer.analyze(img) for img in images]
        else:
            # Parallel processing for PyTorch
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                return list(executor.map(self.analyzer.analyze, images))
```

**Rationale**:
- Users don't need to know about MLX limitations
- Prevents configuration errors
- Maintains performance optimization for PyTorch path
- Clear logging explains behavior

### 5. Performance Optimization Strategy

**Decision**: Implement aggressive pipeline parallelism as the default strategy.

**Key Optimizations**:
1. **Maximize Rendering Parallelism**: 20 workers for PDF/PPT rendering
2. **Deep Pipeline**: Pre-render 4 batches ahead of analysis
3. **Optimal Batch Size**: 30 pages (tested for M4 Max, scales down for smaller systems)
4. **Memory-Aware Scaling**: Auto-adjust based on available RAM

**Pipeline Flow**:
```
[Render Batch 1] → [Analyze Page 1] → [Store Results]
[Render Batch 2] ↘    ↓
[Render Batch 3]   [Analyze Page 2]
[Render Batch 4]       ↓
    ↓              [Analyze Page 3]
[Continue...]          ↓
                  [Continue...]
```

**Rationale**:
- Compensates for MLX single-worker limitation
- Keeps analyzer constantly busy (no waiting for renders)
- Memory usage remains bounded (4 batches max)
- Achieves target performance (60-75 minutes for 96 pages)

## Migration Strategy

### Phase 1: Analyzer Unification (Week 1)
1. Create unified `NanonetsAnalyzer` class
2. Implement backend detection logic
3. Migrate existing code to use new analyzer
4. Validate OCR quality remains unchanged

### Phase 2: Loader Refactoring (Week 2)
1. Extract `DocumentRenderer` component
2. Create `AnalysisPipeline` component
3. Refactor `NanonetsFirstLoader` to use components
4. Maintain backward compatibility with wrapper

### Phase 3: Configuration Streamlining (Week 3)
1. Design `OCRConfig` class
2. Create configuration presets
3. Update loader to use new configuration
4. Document configuration options

### Phase 4: Performance Optimization (Week 4)
1. Implement pipeline parallelism improvements
2. Tune default settings for common hardware
3. Run comprehensive benchmarks
4. Update documentation with performance guide

## Testing Strategy

### Unit Tests
- Backend selection logic
- Component isolation tests
- Configuration validation
- Memory usage monitoring

### Integration Tests
- End-to-end document processing
- Checkpoint/resume functionality
- Fallback scenarios (no MLX, low memory)
- Performance benchmarks

### Compatibility Tests
- Existing pipeline compatibility
- API backward compatibility
- Multi-platform testing (M1, M2, M3, Intel)

## Performance Targets

| Metric | Current | Target | Method |
|--------|---------|---------|---------|
| Model Memory | 14GB (PyTorch) | 2.2GB | MLX quantization |
| 96-page Processing | 120 min | 60-75 min | Pipeline parallelism |
| Loader Complexity | 400+ lines | ~200 lines | Component separation |
| Configuration Options | 15+ params | 5 params | Smart defaults |
| Setup Time | 10+ minutes | 2 minutes | Simplified config |

## Risk Analysis

### Technical Risks
1. **MLX Compatibility**: Some systems may not support MLX
   - *Mitigation*: Automatic fallback to PyTorch

2. **Performance Regression**: Changes might slow processing
   - *Mitigation*: Comprehensive benchmarking before/after

3. **Memory Issues**: Aggressive settings might cause OOM
   - *Mitigation*: Auto-scaling based on available RAM

### Migration Risks
1. **Breaking Changes**: Existing code might break
   - *Mitigation*: Compatibility wrapper for old API

2. **Quality Degradation**: OCR accuracy might decrease
   - *Mitigation*: Extensive quality testing with test corpus

## Success Metrics

1. **Code Simplicity**: 50% reduction in lines of code
2. **Performance**: ≤75 minutes for 96-page document
3. **Memory Usage**: ≤3GB for model + inference
4. **Developer Onboarding**: <30 minutes to understand pipeline
5. **Test Coverage**: >90% for critical paths

## Future Considerations

1. **Batch Inference**: When MLX supports true batching, adapt pipeline
2. **Distributed Processing**: Design allows for future distribution
3. **Model Updates**: Architecture supports easy model swapping
4. **Platform Expansion**: Structure enables Windows/Linux MLX when available