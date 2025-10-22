# Proposal: Migrate to PaddleOCR-VL for Document Parsing

## Problem Statement

The current OCR implementation using Nanonets-OCR2-3B (3B parameters) provides excellent semantic document understanding, but faces several limitations in the context of educational document processing:

### Performance Constraints
1. **Large Model Size**: 3B parameter model requires ~6GB of memory on M4 MacBook Pro, limiting ability to process multiple documents concurrently
2. **Slower Inference**: VLM-based approach trades speed for semantic understanding, but educational documents (textbooks, worksheets, assessments) are often straightforward and don't require full VLM capabilities
3. **Limited Language Support**: Only 12+ languages, insufficient for multilingual educational content processing
4. **Memory Pressure**: Running alongside embeddings (Jina) and LLM (Qwen3-14B) leaves little headroom on 32GB M4

### Quality Gaps for Educational Content
1. **Table Recognition**: Educational materials heavily feature tables (grade matrices, comparison charts, data sets) where precision is critical
2. **Mathematical Formulas**: Current LaTeX extraction is adequate but not optimal for complex STEM content
3. **Chart Understanding**: Diagrams, graphs, and visual learning aids need specialized recognition
4. **Handwriting**: Student work samples and historical educational documents require robust handwriting recognition

### Strategic Limitations
1. **Not Document-Specialized**: Nanonets-OCR2 is a general-purpose VLM, not optimized specifically for document parsing
2. **Benchmark Gap**: Doesn't lead on standard document parsing benchmarks (OmniDocBench)
3. **Local Resource Constraints**: Large model limits concurrent processing on M4 MacBook Pro

## Proposed Solution

Replace Nanonets-OCR2-3B with **PaddleOCR-VL** (0.9B parameters), a state-of-the-art vision-language model specifically designed for document parsing, running **locally on M4 MacBook Pro** via Python SDK.

### Core Capabilities

**Technical Architecture**:
- **Compact VLM**: 0.9B parameters (3x smaller than current solution)
- **Dynamic Resolution**: NaViT-style visual encoder supporting variable image sizes
- **Multilingual**: 109 languages including Chinese, English, Japanese, Latin, Korean, Russian, Arabic, Hindi, Thai
- **Element Recognition**: Text, tables, formulas, charts with SOTA accuracy

**Performance Benefits**:
- **SOTA Benchmarks**: #1 on OmniDocBench v1.0 and v1.5 (page-level parsing)
- **Element-Level Excellence**: Best-in-class for text (OmniDocBench-OCR), tables, formulas, and charts
- **Memory Efficient**: ~2-3GB model footprint (vs 6GB current) → 3x smaller
- **Concurrent Processing**: Smaller memory allows processing 3-5 documents simultaneously vs 1-2

**Local Execution Advantages**:
- **Python SDK**: Direct integration via `pip install paddleocr[doc-parser]`
- **No Infrastructure**: No Docker/server setup required, runs in-process like Nanonets
- **Apple Silicon Optimized**: PaddlePaddle supports GPU acceleration on M4 (with CPU fallback)
- **Output Formats**: JSON and markdown output for semantic region extraction
- **PaddlePaddle Ecosystem**: Active development, extensive documentation, production-ready

### Migration Path

**Phase 1: Local SDK Installation**
- Install PaddlePaddle and PaddleOCR on M4 MacBook Pro via pip
- Test with sample documents to validate output format
- Benchmark performance vs. Nanonets baseline

**Phase 2: Adapter Implementation**
- Create `PaddleOCRVLAnalyzer` implementing same interface as `NanonetsLayoutAnalyzer`
- Adapt PaddleOCR-VL output (JSON/markdown) to `SemanticRegion` format
- Maintain compatibility with existing pipeline architecture

**Phase 3: Backend Selection System**
- Extend `NanonetsAnalyzer` unified interface to support PaddleOCR-VL backend
- Auto-detection: PaddleOCR-VL (if installed) > Nanonets-MPS > Nanonets-CPU
- Configuration-driven selection via environment variable

**Phase 4: Quality Validation**
- Parallel processing with both backends on test corpus
- Compare output quality, semantic region accuracy, retrieval performance
- Benchmark processing speed and memory usage

**Phase 5: Gradual Rollout**
- Default new collections to PaddleOCR-VL
- Opt-in migration for existing collections
- Maintain Nanonets as fallback for edge cases

## Impact Analysis

### What Changes

**Core Components**:
- **New Analyzer**: `PaddleOCRVLAnalyzer` (replaces NanonetsLayoutAnalyzer as default)
- **Dependencies**: Add `paddleocr[doc-parser]`, PaddlePaddle framework (pip installable)
- **Configuration**: New OCR backend selection (`paddleocr-vl`, `nanonets`, `auto`)
- **Backend Detection**: Auto-detect PaddleOCR-VL availability on startup

**Data Processing**:
- **Output Parsing**: Adapt PaddleOCR-VL JSON/markdown to SemanticRegion format
- **Language Support**: Extend metadata to track detected language (109 options)
- **Chart Descriptions**: Enhanced image region metadata with chart type classification

### What Stays the Same

**Architecture Preservation**:
- Region-based processing pipeline (tasks.py)
- 6-directory organized storage structure
- SemanticRegion dataclass and metadata schema (extended, not replaced)
- Collection configuration system
- CheckpointManager and resume capability
- Existing PowerPoint/PDF rendering

**API Compatibility**:
- Unified `NanonetsAnalyzer` interface (backend abstracted)
- `analyze_document()` and `extract_regions()` methods unchanged
- Existing test suite structure and assertions

### Trade-offs

**Gains**:
- ✅ **3x Smaller Model**: 0.9B vs 3B parameters (~2-3GB vs ~6GB memory)
- ✅ **SOTA Quality**: Best on OmniDocBench for document parsing
- ✅ **9x More Languages**: 109 languages vs 12+ (critical for global education)
- ✅ **Better Math/Tables**: Specialized models for STEM educational content
- ✅ **Concurrent Processing**: More memory headroom for batch ingestion on M4
- ✅ **Active Development**: PaddlePaddle team continuously improving model
- ✅ **Simple Installation**: Single pip command, no Docker required

**Costs**:
- ❌ **Framework Switch**: PaddlePaddle instead of PyTorch/Transformers (adds ~500MB dependency)
- ❌ **Migration Effort**: Need to adapt output parsing and test edge cases
- ❌ **Learning Curve**: Team needs to understand PaddleOCR API and configuration
- ❌ **Performance Uncertainty**: Need to benchmark on M4 to validate speed expectations

**Assessment**: The trade-off strongly favors migration because:
1. **Educational Content Fit**: 109 languages, SOTA math/table recognition aligns perfectly with lesson planning use case
2. **M4 Efficiency**: 3x smaller model frees 4GB memory for concurrent document processing
3. **Quality Metrics**: OmniDocBench leadership means better extraction for complex textbooks and worksheets
4. **Memory Budget**: Smaller model allows running OCR + embeddings + LLM comfortably on 32GB M4
5. **Simple Deployment**: Local execution via pip, no infrastructure changes needed

## Success Criteria

### Functional Requirements
1. **API Compatibility**: All existing `NanonetsAnalyzer` calls work with PaddleOCR-VL backend
2. **Quality Parity**: OCR accuracy ≥ current Nanonets baseline on test corpus
3. **Format Consistency**: SemanticRegion output matches schema and structure
4. **Language Detection**: Automatically detect and tag document language from 109 options
5. **Fallback Reliability**: Gracefully degrade to Nanonets if PaddleOCR-VL unavailable

### Performance Requirements
1. **Memory Reduction**: Model memory usage ≤ 3GB (down from 6GB)
2. **Speed Acceptable**: Inference time within 1.5x of current Nanonets (slight slowdown acceptable for quality gains)
3. **Concurrent Capacity**: Support processing 3-5 documents simultaneously (vs 1-2 current)
4. **Startup Time**: Model initialization ≤ 10 seconds on M4

### Quality Requirements
1. **Table Extraction**: ≥ 95% structure accuracy on educational table corpus
2. **Formula Recognition**: ≥ 90% LaTeX accuracy on STEM equation dataset
3. **Chart Understanding**: Correctly classify 10+ chart types (bar, line, pie, scatter, etc.)
4. **Multilingual**: Successfully process documents in top 20 educational languages

## Affected Capabilities

### Primary Changes
- **ingestion/OCR Engine**: Replace Nanonets with PaddleOCR-VL as default (local execution)
- **ingestion/Document Analysis**: Enhanced with chart type classification, language detection
- **dependencies**: Add PaddlePaddle and PaddleOCR to project dependencies

### Secondary Changes
- **multimodal/Vision Processing**: Richer metadata from specialized document models
- **configuration/OCR Settings**: New backend selection via environment variable

## Dependencies

- **Requires**: Completed Phase 3 dynamic config system (OCRConfig integration)
- **Blocks**: None (independent improvement, backward compatible)
- **Related**:
  - `lesson-plan-rag-integration`: Better educational content extraction improves RAG quality
  - Future PDF/DOCX processing will use same PaddleOCR-VL backend

## Rollback Plan

If PaddleOCR-VL fails validation or introduces regressions:

### Immediate Rollback (Day 1)
1. Set `OCR_BACKEND=nanonets` in environment config
2. Unified analyzer automatically uses Nanonets implementation
3. No code changes needed (interface abstraction)

### Partial Rollback (Week 1)
1. Keep PaddleOCR-VL for new collections
2. Revert existing collections to Nanonets via collection config
3. Document known issues and limitations

### Full Rollback (Month 1)
1. Remove PaddleOCR-VL from default backend detection
2. Mark as experimental opt-in feature
3. Maintain code for future re-evaluation
4. Document decision rationale

## Timeline Estimate

### Week 1: Local Installation & Research (6 hours)
- Install PaddlePaddle and PaddleOCR on M4 MacBook Pro
- Test Python API with sample documents
- Validate output format and quality
- Benchmark performance vs Nanonets

### Week 2: Implementation (12 hours)
- Create `PaddleOCRVLAnalyzer` class for local SDK
- Implement output parsing (JSON/markdown → SemanticRegion)
- Integrate with unified `NanonetsAnalyzer` interface
- Add backend selection logic

### Week 3: Testing & Validation (10 hours)
- Unit tests for PaddleOCR-VL adapter
- Integration tests with full pipeline on M4
- Quality comparison on educational document corpus
- Performance benchmarking and memory profiling

### Week 4: Documentation & Polish (6 hours)
- Update installation documentation
- Update configuration guide (environment variables)
- Migration guide for existing users
- Performance tuning recommendations for M4

**Total Estimate**: ~34 hours (~1 sprint cycle)

## Open Questions

### Local Execution Questions
1. **GPU Acceleration on M4**: Does PaddlePaddle GPU mode work reliably on Apple Silicon?
   - *Recommendation*: Test GPU mode, default to CPU if unstable (PaddlePaddle optimized for CPU)

2. **Installation Method**: CPU-only or GPU-enabled PaddlePaddle package?
   - *Recommendation*: Start with CPU-only (`paddlepaddle==3.2.0`) for stability

### Integration Questions
3. **Output Format**: Use PaddleOCR-VL JSON output or markdown format?
   - *Recommendation*: JSON for structured parsing, markdown for debugging/validation

4. **Model Caching**: Where to cache downloaded PaddleOCR-VL model on M4?
   - *Recommendation*: Use default `~/.paddleocr/` directory, document size (~2-3GB)

### Performance Questions
5. **CPU Threading**: How many threads to allocate for PaddleOCR on M4 (10 cores)?
   - *Recommendation*: Start with 4-6 threads, benchmark to find optimal setting

6. **Concurrent Documents**: How many documents can process simultaneously on 32GB M4?
   - *Recommendation*: Target 3-5 concurrent, monitor memory usage

### Migration Questions
7. **Backward Compatibility**: Migrate existing indexed documents or only new ones?
   - *Recommendation*: New documents only, offer opt-in re-indexing tool

8. **Quality Threshold**: What accuracy delta triggers rollback?
   - *Recommendation*: >5% degradation on table/formula extraction = pause and investigate

### Answered Questions
- ✅ **License Compatibility**: Apache 2.0 (PaddleOCR-VL) compatible with MIT (project)
- ✅ **Language Support**: 109 languages covers all major educational markets
- ✅ **Model Size**: 0.9B fits comfortably on M4 MacBook Pro (2-3GB vs 48GB+ memory)
- ✅ **Deployment Model**: Local execution via pip, no Docker/server infrastructure needed

## Next Steps

1. **Approval**: Review proposal with team, address concerns
2. **Prototype**: Build minimal PaddleOCR-VL adapter to validate assumptions
3. **Benchmarking**: Run side-by-side comparison on representative educational corpus
4. **Design**: Create detailed design.md with architecture diagrams
5. **Specification**: Draft spec deltas for OCR engine capability
6. **Implementation**: Follow tasks.md for ordered, incremental delivery
