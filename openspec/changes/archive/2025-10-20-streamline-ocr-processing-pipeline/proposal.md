# Streamline OCR Processing Pipeline

## Problem Statement

The current Nanonets OCR model integration has accumulated significant complexity through iterative development, resulting in:

1. **Dual Analyzer Implementations**: Two separate analyzer classes (`NanonetsLayoutAnalyzer` and `NanonetsMLXAnalyzer`) with similar but inconsistent APIs, creating confusion and maintenance burden.

2. **Overly Complex Loader**: The `NanonetsFirstLoader` class (400+ lines) handles too many concerns: progressive rendering, checkpointing, profile management, worker configuration, and batch processing.

3. **Configuration Sprawl**: Multiple overlapping configuration mechanisms (profiles, constructor params, environment variables) make it difficult to understand which settings take precedence.

4. **Suboptimal MLX Utilization**: Despite MLX's 78% memory reduction (2.2GB vs 14GB), the system defaults to PyTorch, and MLX's thread-safety limitations aren't properly abstracted.

5. **Performance Bottlenecks**: Current processing takes ~2 hours for 96 pages. While optimized settings can achieve 60-75 minutes, the configuration required is complex and error-prone.

## Goals

### Primary Goal
**Prioritize MLX as the default OCR engine** to benefit from its reduced memory footprint (2.2GB) and Apple Silicon optimization, while simplifying the overall architecture.

### Specific Objectives

1. **Unify Analyzer Interface**
   - Single `NanonetsAnalyzer` class that automatically selects MLX when available
   - Consistent API regardless of backend (MLX or PyTorch fallback)
   - Clear device selection logic (MLX > MPS > CUDA > CPU)

2. **Simplify Document Loading**
   - Extract concerns from `NanonetsFirstLoader` into focused components
   - Separate rendering, analysis, and checkpoint management
   - Reduce loader to ~200 lines with clear single responsibility

3. **Streamline Configuration**
   - Single source of truth for configuration
   - Smart defaults that work well for 80% of cases
   - Override mechanism that's predictable and documented
   - Remove redundant profile system in favor of explicit settings

4. **Abstract MLX Limitations**
   - Hide thread-safety concerns behind clean interface
   - Automatic single-worker enforcement for MLX
   - Pipeline parallelism as default strategy
   - Clear performance expectations in documentation

5. **Optimize Default Performance**
   - Target: 60-75 minutes for 96-page documents out-of-the-box
   - Optimal batch size (30 pages) as default
   - Aggressive pre-rendering (4 batches ahead)
   - Maximum render parallelism (20 workers)

## Success Criteria

1. **Memory Efficiency**: Default configuration uses ≤3GB for model (MLX)
2. **Performance**: 96-page document processes in ≤75 minutes with defaults
3. **Code Simplicity**: 50% reduction in loader complexity (200 vs 400 lines)
4. **API Consistency**: Single analyzer interface for all backends
5. **Developer Experience**: New developers can understand and modify the pipeline within 30 minutes

## Constraints

1. **Backward Compatibility**: Existing ingestion pipelines must continue to work
2. **Fallback Support**: System must gracefully handle environments without MLX
3. **Quality Preservation**: OCR quality must remain identical or improve
4. **Resource Limits**: Must work on 16GB M1 MacBooks (minimum target)

## Implementation Approach

The streamlining will be implemented in phases to minimize risk:

1. **Phase 1**: Unify analyzers with MLX prioritization
2. **Phase 2**: Refactor loader into focused components
3. **Phase 3**: Implement streamlined configuration
4. **Phase 4**: Optimize and document performance settings

Each phase will be independently testable and deployable, allowing for incremental validation.

## Risk Mitigation

- **Compatibility Testing**: Extensive testing on various Apple Silicon models
- **Performance Benchmarks**: Before/after comparisons for all configurations
- **Gradual Rollout**: Feature flags to enable new pipeline progressively
- **Fallback Paths**: Maintain PyTorch analyzer for non-Apple platforms