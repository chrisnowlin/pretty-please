# Proposal: Migrate to Nanonets-OCR2-3B for Layout Analysis

## Problem Statement

The current layout analysis implementation using deepdoctection has significant technical debt and operational issues:

1. **Monkey Patch Requirement**: Requires runtime patching of deepdoctection's HuggingFace integration (`deepdoctection_patch.py`) to fix an upstream bug where model file paths are passed instead of directories
2. **OCR Disabled**: doctr version mismatch forces OCR pipeline to be disabled (`USE_OCR=False`), limiting text extraction capabilities
3. **Complex Dependency Chain**: Requires deepdoctection + detectron2 + python-doctr + timm, with fragile version compatibility
4. **Limited Content Understanding**: Only provides spatial regions (bounding boxes) without semantic understanding of content
5. **Missing Features**: Cannot extract table content, mathematical equations, or generate image descriptions

## Proposed Solution

Replace deepdoctection with Nanonets-OCR2-3B, a modern vision-language model that provides:

**Core Capabilities**:
- Structured markdown output with semantic tags
- Full table extraction (HTML/markdown format)
- LaTeX equation recognition
- Image description generation
- Signature and watermark detection
- Checkbox/form handling
- Multilingual support (12+ languages)
- Handwriting recognition

**Technical Benefits**:
- Clean transformers-only dependency (no monkey patches)
- Single 3B parameter model (fits in M4 Max 48GB unified memory)
- Direct HuggingFace integration (no wrapper bugs)
- Semantic regions instead of only spatial regions
- Richer metadata for RAG retrieval

**Migration Path**:
- Semantic regions parsed from markdown structure
- Same 6-directory organized storage
- Compatible with existing region-based processing architecture
- Configuration-driven (enable/disable per collection)

## Impact Analysis

### What Changes
- **Layout analysis implementation**: Replace `LayoutAnalyzer` (deepdoctection) with `NanonetsLayoutAnalyzer`
- **Region structure**: Add semantic metadata (markdown structure, content type)
- **Dependencies**: Remove deepdoctection, detectron2, python-doctr; add Nanonets model
- **Monkey patches**: Remove `deepdoctection_patch.py` entirely

### What Stays the Same
- Region-based processing architecture in `tasks.py`
- 6-directory organized storage structure
- Collection configuration system
- Region metadata schema (extended, not replaced)
- PowerPoint/PDF loader interfaces
- Test suite structure

### Trade-offs
**Gains**:
- ✅ No monkey patches or workarounds
- ✅ Richer content extraction (tables, equations, images)
- ✅ Better semantic understanding for RAG
- ✅ Cleaner codebase and dependencies
- ✅ Multilingual and handwriting support

**Losses**:
- ❌ No exact pixel coordinates (bounding boxes)
- ❌ Larger model size (~6GB vs ~500MB)
- ❌ Slightly slower per-page processing (VLM inference)

**Assessment**: The trade-off is acceptable because:
1. RAG retrieval benefits more from semantic understanding than spatial coordinates
2. M4 Max has 48GB unified memory (6GB is comfortable)
3. Processing speed is not critical for document ingestion (one-time operation)
4. Elimination of technical debt and fragile dependencies outweighs performance cost

## Success Criteria

1. **Zero Monkey Patches**: No runtime code patching required
2. **Clean Dependencies**: Only transformers + model downloads
3. **Richer Extraction**: Successfully extract tables, equations, and image descriptions
4. **Same or Better Retrieval**: Region-based search performs as well or better than current
5. **All Tests Pass**: Existing test suite passes with new implementation
6. **Performance Acceptable**: Document processing time ≤ 2x current implementation

## Affected Capabilities

- **ingestion/Document Layout Analysis**: Complete rewrite using semantic approach
- **multimodal/Vision Processing**: Enhanced with image description generation

## Dependencies

- Requires: Completed `add-structured-document-analysis` implementation
- Blocks: None (independent improvement)
- Related: Future PDF/DOCX layout analysis can use same Nanonets approach

## Rollback Plan

If Nanonets approach fails validation:
1. Keep both implementations in codebase
2. Add configuration flag to choose analyzer backend
3. Revert to deepdoctection as default
4. Document Nanonets as experimental feature

## Timeline Estimate

- Investigation & model testing: 0.5 days (Done)
- Implementation: 1.5 days
- Testing & validation: 1 day
- Documentation: 0.5 days
- **Total**: ~3.5 days

## Open Questions

None - analysis complete, ready for implementation.
