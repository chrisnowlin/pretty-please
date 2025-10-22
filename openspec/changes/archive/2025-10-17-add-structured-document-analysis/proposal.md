# Proposal: Add Structured Document Analysis

## Overview
Integrate deepdoctection library to enable structured layout analysis for documents with mixed content (text, images, tables). This enhancement addresses the current limitation where images embedded within PDFs, Word documents, and PowerPoint presentations are discarded during text extraction, resulting in incomplete document understanding.

## Problem Statement
The current document ingestion pipeline has a significant gap:

1. **Text-only extraction**: PDFs and DOCX files use `extract_text()` methods that discard embedded images
2. **Separate image handling**: Standalone image files are processed independently with vision encoders
3. **No PowerPoint support**: Cannot process .pptx files, which typically contain mixed text and visual content
4. **Loss of document structure**: Layout information (regions, positioning, relationships) is not preserved
5. **Incomplete retrieval**: Users cannot search for visual content embedded in documents

### Example Impact
A PowerPoint slide with a revenue chart and accompanying text:
- **Current behavior**: Only text is extracted ("Revenue increased 20% YoY"), chart is lost
- **Desired behavior**: Both text and chart are indexed, preserving their relationship

## Proposed Solution
Integrate deepdoctection to add structured document layout analysis:

1. **Layout detection**: Identify text regions, image regions, table regions, and their spatial relationships
2. **PowerPoint support**: Add .pptx and .ppt file format support
3. **Region-based processing**: Process each region with appropriate encoder (text vs. vision)
4. **Structure preservation**: Maintain document layout in metadata for context-aware retrieval
5. **Backward compatibility**: Enhance existing loaders without breaking current functionality

## Capabilities Addressed

### 1. Document Layout Analysis (NEW)
- Detect and classify document regions (text, image, table, title, list)
- Extract bounding boxes and spatial relationships
- Support scanned documents via OCR integration
- Deskew and rotate images automatically

### 2. Enhanced Ingestion (MODIFIED)
- Add PowerPointLoader for .pptx and .ppt files
- Modify PDFLoader to extract embedded images
- Modify DocxLoader to preserve inline images
- Add configuration for layout analysis enablement

### 3. Multimodal Processing (MODIFIED)
- Process documents with mixed content
- Maintain text-image relationships within documents
- Support region-level metadata (position, type, confidence)

### 4. API Enhancements (MODIFIED)
- Add .pptx and .ppt to supported formats whitelist
- Add configuration endpoint for layout analysis settings
- Include region metadata in search results

## Dependencies (Required)
All dependencies are **required** for maximum precision and capability:

- `deepdoctection>=0.43.0` - Core layout analysis library (REQUIRED)
- `transformers` (already present) - Required by deepdoctection
- `detectron2` - For PyTorch-based layout detection models (REQUIRED)
- `python-doctr>=0.10.0` - OCR capabilities (REQUIRED)
- `python-pptx>=0.6.21` - PowerPoint file parsing (REQUIRED)

**Rationale**: We prioritize precision and completeness over optional features. All users get full capabilities.

## Architecture Impact
- **Low risk**: Deepdoctection integrates at the loader layer, downstream pipeline unchanged
- **Memory**: ~500MB additional for layout detection models (fits within M4 Max 48GB)
- **Performance**: ~2-3x slower document processing (worthwhile for maximum precision)
- **Default behavior**: Layout analysis ENABLED by default for new collections
- **Backward compatible**: Existing collections can opt-in via configuration

## Non-Goals
- Real-time document processing (batch processing remains acceptable)
- Video or audio multimodal support
- Handwriting recognition (though deepdoctection supports it)
- Fine-tuning custom layout models (use pre-trained models)

## Success Criteria
1. PowerPoint files (.pptx, .ppt) can be uploaded and processed successfully
2. PDFs with embedded images index both text and visual content
3. Users can search for visual content embedded in documents
4. Document structure (regions, layout) is preserved in metadata
5. Existing document processing continues to work without regression
6. Processing time remains under 30 seconds for typical documents (< 10 pages)

## Open Questions
1. **Configuration granularity**: Should layout analysis be enabled per-collection or globally?
   - **Decision**: Per-collection with DEFAULT ENABLED for maximum precision
   - Users can opt-out for text-only collections if needed

2. **Region chunking strategy**: How should we chunk documents with detected regions?
   - **Decision**: Option A - Each region is a separate chunk
   - **Rationale**: Maximizes retrieval precision and granularity
   - Preserves structure, enables precise attribution

3. **OCR vs native text**: For PDFs, should we use OCR even when native text exists?
   - **Decision**: Use native text when available (faster, equally accurate)
   - OCR only for scanned documents or regions without native text

4. **Image extraction format**: Should we save extracted images as separate files?
   - **Decision**: YES - Always save to organized persistent storage
   - Path: `uploads/{collection}/extracted_images/{document_id}_page{N}_region{M}.{ext}`
   - Enables debugging, re-embedding, visual search results display

## Related Changes
- Builds on: `add-multimodal-support` (archived)
- Builds on: `add-document-ingestion` (archived)
- Complements: `link-citations-to-sources` (provides better source tracking with regions)

## Timeline Estimate
- **Phase 1**: Dependencies and PowerPoint loader (4 hours)
- **Phase 2**: Layout analysis integration (6 hours)
- **Phase 3**: Enhanced loaders for PDF/DOCX (4 hours)
- **Phase 4**: Testing and documentation (4 hours)
- **Total**: ~18 hours (2-3 days)

## Risks and Mitigations
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Deepdoctection dependencies conflict with existing packages | High | Low | Pin compatible versions, test in isolated environment |
| Layout detection models too large for some systems | Medium | Low | Make layout analysis optional, fall back to simple extraction |
| Processing time too slow for user experience | Medium | Medium | Add progress indicators, process asynchronously |
| Detectron2 installation issues on macOS | High | Medium | Provide clear installation docs, consider CPU-only fallback |

## Alternatives Considered

### Alternative 1: Use LLM vision models (GPT-4V, Claude)
- **Pros**: No local dependencies, state-of-the-art understanding
- **Cons**: Requires API calls, violates local-first constraint, cost per document
- **Verdict**: Rejected due to local-first requirement

### Alternative 2: Build custom layout detection with LayoutLM
- **Pros**: Full control, optimized for our use case
- **Cons**: Requires training data, significant development time
- **Verdict**: Deferred (use pre-trained models first, customize later if needed)

### Alternative 3: Use Unstructured.io library
- **Pros**: Simpler API, good PowerPoint support
- **Cons**: Less control over layout detection, fewer customization options
- **Verdict**: Considered but deepdoctection provides better layout analysis

## Stakeholder Input
- **User need**: "I uploaded my presentation slides but search doesn't find the charts"
- **Technical lead**: "Ensure solution works offline and fits in memory budget"
- **Performance requirement**: "Document processing should complete within 1 minute"
