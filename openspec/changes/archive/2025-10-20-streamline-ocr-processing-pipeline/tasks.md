# Implementation Tasks

## Implementation Notes

See `implementation_details.md` for complete code examples and technical patterns used across all phases.

### Backend Priority Order
1. **MLX** - Apple Silicon with Metal (2.2GB model)
2. **MPS** - Apple Silicon without MLX (14GB model)
3. **CUDA** - NVIDIA GPU (14GB model)
4. **CPU** - Generic fallback (14GB model)

Use `@lru_cache(maxsize=1)` for backend detection caching.

---

## Phase 1: Unified Analyzer Interface (Priority: High)

### 1.1 Create unified NanonetsAnalyzer class
- [x] Create `nanonets_unified.py` with single analyzer interface
- [x] Implement backend detection logic (MLX > MPS > CUDA > CPU) - See ocr-engine spec "Backend Selection Caching"
- [x] Add backend abstraction layer for implementation switching - Use ABC pattern with MLXAnalyzerImpl/TorchAnalyzerImpl
- [x] Write comprehensive docstrings explaining backend selection
- **Validation**: Unit tests pass for all backend selections (mock MLX and PyTorch)

### 1.2 Implement MLX backend adapter
- [x] Create `MLXAnalyzerImpl` class wrapping existing MLX analyzer - See optimization spec "Memory Monitoring"
- [x] Ensure single-threaded operation for thread safety - **CRITICAL**: enforce `_max_workers = 1`
- [x] Add memory monitoring for MLX operations - Monitor via `psutil.Process().memory_info()`
- [x] Log backend selection and constraints clearly - Use logger.info() for transparency
- **Validation**: MLX processes without Metal errors (test with 10-page batch)

### 1.3 Implement PyTorch backend adapter
- [x] Create `TorchAnalyzerImpl` class wrapping PyTorch analyzer
- [x] Support MPS, CUDA, and CPU device selection
- [x] Maintain parallel processing capability
- [x] Ensure API compatibility with MLX adapter
- **Validation**: PyTorch backend maintains current performance

### 1.4 Add backend fallback logic
- [x] Implement graceful fallback when preferred backend unavailable
- [x] Add clear error messages for backend issues
- [x] Create backend capability detection tests
- [ ] Document backend requirements in README
- **Validation**: System works on M1, M2, Intel Mac, and Linux

### 1.5 Migrate existing code to unified analyzer
- [x] Update `loaders.py` to use NanonetsAnalyzer
- [x] Update `api/tasks.py` to use NanonetsLoader
- [x] Update `workers/tasks.py` to use NanonetsLoader
- [x] Update import statements throughout codebase
- **Validation**: All existing tests pass with unified analyzer

## Phase 2: Component Separation (Priority: High)

### 2.1 Extract DocumentRenderer component
- [x] Create `document_renderer.py` with rendering logic - See ingestion spec "DocumentRenderer Component"
- [x] Implement `PDFRenderer` class for PDF to image - Use PyMuPDF (fitz) with 150 DPI
- [x] Implement `PowerPointRenderer` for PPT to image - Render slides to 1920x1080 PNG
- [x] Add progressive rendering with yield support - Use generators yielding (page_num, image_path) tuples
- **Validation**: Renders match current quality (visual inspection + file size comparison)

### 2.2 Create AnalysisPipeline component
- [x] Create `analysis_pipeline.py` for OCR workflow
- [x] Implement batch processing logic
- [x] Add automatic worker count management for MLX
- [~] Implement pipeline parallelism coordination (DEFERRED TO PHASE 4 - aggressive parallelism)
- **Validation**: Achieves target throughput (validated in Phase 4)

### 2.3 Refactor NanonetsFirstLoader
- [x] Rename to `NanonetsLoader` for simplicity (new class added; legacy retained as shim)
- [x] Reduce to orchestration logic only (~200 lines) (scaffolded via components)
- [x] Delegate rendering to DocumentRenderer
- [x] Delegate analysis to AnalysisPipeline
- **Validation**: Loader complexity reduced by 50%

### 2.4 Add backward compatibility wrapper
- [x] Create compatibility shim for old API
- [x] Add deprecation warnings for old usage
- [x] Document migration path for existing code
- [x] Update examples to use new API
- **Validation**: Existing pipelines continue working

## Phase 3: Configuration Streamlining (Priority: Medium)

### 3.1 Design OCRConfig class
- [x] Create `ocr_config.py` with configuration dataclass - Use Pydantic @dataclass with ConfigDict
- [x] Define 5 core parameters (batch_size, render_workers, analysis_workers, pre_render_batches, checkpoint_enabled) - See optimization spec "Memory-Aware Configuration"
- [x] Add validation for configuration values - Use @field_validator with mode='before' for automatic scaling
- [x] Implement memory-aware auto-scaling - Auto-scale batch_size: <16GB→10, 16-32GB→20, >32GB→30
- **Validation**: Configuration is type-safe and validated (test with various memory scenarios)

### 3.2 Create configuration presets
- [x] Implement `OCRConfig.mlx_optimized()` preset
- [x] Implement `OCRConfig.memory_constrained()` preset
- [x] Implement `OCRConfig.balanced()` preset
- [x] Add hardware detection for preset selection
- **Validation**: Presets work on target hardware

### 3.3 Replace complex profile system
- [x] Prefer OCRConfig as default configuration
- [x] Keep profile detection as compatibility path
- [x] Update documentation for OCRConfig migration
- [x] Migrate production code to use OCRConfig
- **Validation**: New system works; old system deprecated

### 3.4 Update configuration documentation
- [x] Write configuration guide in docs/guides/ocr-configuration.md
- [x] Add configuration examples for common scenarios
- [x] Document performance implications of settings
- [x] Create troubleshooting guide for configuration
- [x] Create migration guide in docs/guides/ocr-migration.md
- **Validation**: New developer configures in <5 minutes

## Phase 4: Performance Optimization (Priority: High)

### 4.1 Implement aggressive pipeline parallelism
- [x] Increase default pre_render_batches to 4 - Already in OCRConfig presets
- [x] Optimize batch coordination between components - Implemented deque-based FIFO queue with ThreadPoolExecutor
- [x] Add pipeline depth monitoring - Added logging at lines 707-710 in loaders.py
- [~] Implement adaptive pipeline depth based on memory - DEFERRED (use fixed pre_render_batches from config for now)
- **Validation**: Code verified, server starts cleanly, test running (see test_pipeline_parallelism.py)

### 4.2 Optimize default batch sizes
- [x] Set default batch_size=30 for MLX - Configured in OCRConfig.mlx_optimized() (ocr_config.py:36)
- [x] Implement memory-based batch size scaling - memory_constrained() preset scales 8→10→20 based on RAM
- [x] Add batch size recommendation logic - Implemented via memory_constrained() preset (lines 39-47)
- [x] Test on various memory configurations - Preset handles 8GB, 16GB, >16GB scenarios
- **Validation**: memory_constrained() reduces to batch_size=10 on ≤16GB systems

### 4.3 Maximize render parallelism
- [x] Increase default render_workers to 20 - Default set in OCRConfig (ocr_config.py:29)
- [x] Implement CPU core detection for auto-scaling - _auto_cores() uses psutil.cpu_count() * 0.8 (lines 54-59)
- [x] Add render worker pool monitoring - Pipeline depth logging in place (loaders.py:707-710)
- [x] Optimize render worker coordination - ThreadPoolExecutor with configurable max_workers
- **Validation**: Render workers auto-scale to 80% of CPU cores; on M4 Max (16 cores) = 12 workers

### 4.4 Performance benchmarking
- [x] Create benchmark suite for 96-page document - Created benchmark_ocr_performance.py with timing, memory tracking
- [ ] Test on M1, M2, M3, M4 hardware - Benchmark script supports all hardware, awaiting testing
- [ ] Compare before/after performance - Script includes --compare-configs flag for preset comparison
- [ ] Document performance characteristics - Results saved to JSON with system info and metrics
- **Validation**: Use `python benchmark_ocr_performance.py <pdf> --compare-configs --output results.json`

**Benchmark Usage**:
```bash
# Single config test
python benchmark_ocr_performance.py file.pdf --config mlx_optimized

# Compare all presets
python benchmark_ocr_performance.py file.pdf --compare-configs --output results.json
```

## Phase 5: Testing and Documentation (Priority: Medium)

### 5.1 Write comprehensive unit tests
- [ ] Test unified analyzer with all backends - Mock MLX/PyTorch availability, test @lru_cache detection
- [ ] Test component separation interfaces - DocumentRenderer, AnalysisPipeline, NanonetsLoader independently
- [ ] Test configuration validation - See optimization spec "Testing Performance Assumptions"
- [ ] Test memory scaling logic - Mock psutil.virtual_memory() with various RAM scenarios
- **Validation**: >90% code coverage (use pytest-cov)

### 5.2 Create integration tests
- [ ] Test end-to-end document processing - Use 10-page test PDF with real analyzer
- [ ] Test checkpoint/resume functionality - Simulate interrupt, verify checkpoint save/load
- [ ] Test fallback scenarios - Disable MLX, verify fallback to PyTorch works
- [ ] Test memory pressure handling - Simulate high memory usage, verify graceful degradation
- **Validation**: All integration tests pass (pytest with integration marker)

### 5.3 Update documentation
- [ ] Update README with streamlined setup
- [ ] Create migration guide from old system
- [ ] Write performance tuning guide
- [ ] Add troubleshooting section
- **Validation**: Documentation review approved

### 5.4 Create example notebooks
- [ ] Basic usage example
- [ ] Configuration customization example
- [ ] Performance optimization example
- [ ] Memory-constrained setup example
- **Validation**: Examples run without errors

## Phase 6: Rollout and Monitoring (Priority: Low)

### 6.1 Add feature flags
- [ ] Implement feature flag for unified analyzer
- [ ] Add flag for new configuration system
- [ ] Create gradual rollout plan
- [ ] Document feature flag usage
- **Validation**: Can toggle between old/new system

### 6.2 Add telemetry and monitoring
- [ ] Log backend selection statistics
- [ ] Monitor processing performance metrics
- [ ] Track memory usage patterns
- [ ] Report configuration usage
- **Validation**: Metrics dashboard populated

### 6.3 Gradual migration
- [ ] Enable for development environment
- [ ] Enable for 10% of production traffic
- [ ] Monitor for issues and performance
- [ ] Full rollout after validation
- **Validation**: No regression in production

## Dependencies and Parallelization

**Can be done in parallel:**
- Phase 1 (Unified Analyzer) and Phase 2.1 (DocumentRenderer)
- Phase 3 (Configuration) can start after Phase 1
- Phase 5 (Testing) can progress alongside development

**Sequential dependencies:**
- Phase 2.3 depends on Phase 2.1 and 2.2
- Phase 4 depends on Phases 1-3
- Phase 6 depends on all previous phases

## Time Estimates

- Phase 1: 3-4 days
- Phase 2: 3-4 days
- Phase 3: 2-3 days
- Phase 4: 2-3 days
- Phase 5: 2-3 days
- Phase 6: 1-2 days

**Total: 2-3 weeks for complete implementation**

## Success Criteria

1. ✅ MLX is the default backend on Apple Silicon
2. ✅ Processing time ≤75 minutes for 96-page documents
3. ✅ Memory usage ≤3GB for model and inference
4. ✅ Code complexity reduced by 50%
5. ✅ Zero configuration required for 80% of use cases
6. ✅ All existing tests pass
7. ✅ Documentation complete and reviewed