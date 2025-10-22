# Design: Structured Document Analysis Integration

## Architecture Overview

### Current State
```
Document Upload
    ↓
Loader (text-only extraction)
    ↓
Document(content=text, metadata={})
    ↓
FixedSizeChunker
    ↓
Text Encoder → ChromaDB
```

**Problem**: Images embedded in documents are discarded.

### Proposed State
```
Document Upload
    ↓
Layout-Aware Loader
    ├→ Deepdoctection Analyzer (optional, configurable)
    │   ├→ Layout Detection (text/image/table regions)
    │   ├→ OCR (if needed)
    │   └→ Region Extraction
    ↓
Document(content=text, metadata={regions: [...]})
    ↓
Region-Aware Processor
    ├→ Text Regions → Text Encoder
    ├→ Image Regions → Vision Encoder
    └→ Table Regions → Text Encoder (HTML)
    ↓
ChromaDB (with region metadata)
```

**Benefit**: Both text and visual content are indexed and searchable.

## Component Design

### 1. Layout Analysis Integration Layer

**Location**: `src/jina_rag_pipeline/ingestion/layout_analysis.py` (new file)

**Purpose**: Abstracts deepdoctection integration to keep loaders clean.

```python
class LayoutAnalyzer:
    """Wrapper for deepdoctection document layout analysis."""

    def __init__(self, enable_ocr: bool = True, enable_tables: bool = True):
        import deepdoctection as dd
        self.analyzer = dd.get_dd_analyzer()
        self.enable_ocr = enable_ocr
        self.enable_tables = enable_tables

    def analyze_document(self, file_path: Path) -> DocumentLayout:
        """
        Analyze document layout and return structured regions.

        Returns:
            DocumentLayout with:
            - text_regions: List[TextRegion]
            - image_regions: List[ImageRegion]
            - table_regions: List[TableRegion]
            - metadata: Dict (page count, dimensions, etc.)
        """
        pass

    def extract_regions(self, file_path: Path) -> List[Region]:
        """Extract all regions from document as unified list."""
        pass

@dataclass
class Region:
    """Base class for document regions."""
    type: Literal["text", "image", "table", "title", "list"]
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    page_number: int
    content: Union[str, Path]  # Text content or path to extracted image
    metadata: Dict[str, Any]
```

**Design Decision**: Separate layout analysis from loaders
- **Rationale**: Keeps loader classes focused on format-specific concerns
- **Benefit**: Layout analysis can be disabled without modifying loaders
- **Trade-off**: Extra abstraction layer, but improves testability

### 2. Enhanced Loader Classes

**Modified**: `src/jina_rag_pipeline/ingestion/loaders.py`

```python
class PowerPointLoader(DocumentLoader):
    """Load PowerPoint presentations with layout analysis support."""

    def __init__(self, use_layout_analysis: bool = True):
        self.use_layout_analysis = use_layout_analysis
        if use_layout_analysis:
            from .layout_analysis import LayoutAnalyzer
            self.layout_analyzer = LayoutAnalyzer()

    def load(self, file_path: Path) -> Document:
        if self.use_layout_analysis:
            return self._load_with_layout(file_path)
        else:
            return self._load_simple(file_path)

    def _load_with_layout(self, file_path: Path) -> Document:
        """Extract regions using deepdoctection."""
        # Convert PPTX to images temporarily
        # Run layout analysis on each slide
        # Extract regions and combine
        pass

    def _load_simple(self, file_path: Path) -> Document:
        """Simple text-only extraction."""
        from pptx import Presentation
        prs = Presentation(file_path)
        slides_text = []
        for slide in prs.slides:
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    slide_text.append(shape.text)
            slides_text.append("\n".join(slide_text))

        content = "\n\n".join(slides_text)
        metadata = {"format": "pptx", "slide_count": len(prs.slides)}
        return Document(content=content, source=str(file_path), metadata=metadata)

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in [".pptx", ".ppt"]


class EnhancedPDFLoader(DocumentLoader):
    """PDF loader with optional layout analysis for embedded images."""

    def __init__(self, use_layout_analysis: bool = False):
        # Use layout analysis only when explicitly enabled
        # Default to fast native text extraction
        pass
```

**Design Decision**: Dual-mode loaders with layout-aware as DEFAULT
- **Rationale**: Maximize precision and granularity by default
- **Configuration**: Per-collection setting `enable_layout_analysis: bool`
- **Default**: Layout-aware mode ENABLED (precision-first approach)
- **Opt-out**: Users can disable for simple text-only collections if needed

### 3. Region-Based Processing

**Modified**: `src/jina_rag_pipeline/api/tasks.py`

```python
async def process_task(self, task_id: str) -> None:
    # ... existing code ...

    # Load document (may include regions)
    document = loader.load(file_path)

    # Check if document has regions
    if "regions" in document.metadata:
        # Process each region appropriately
        for region in document.metadata["regions"]:
            if region["type"] == "image":
                # Extract image and encode with vision encoder
                image_path = region["content"]
                pil_image = Image.open(image_path)
                embedding = self.embedder.encode_image(pil_image, task="retrieval")

                metadata = {
                    "source": file_status.name,
                    "document_id": document_id,
                    "region_type": "image",
                    "page_number": region["page_number"],
                    "bbox": region["bbox"],
                    "confidence": region["confidence"],
                }

                self.vector_store.add_embeddings(
                    collection_name=task.collection_name,
                    embeddings=[embedding.tolist()],
                    documents=[f"Image from {file_status.name}, page {region['page_number']}"],
                    metadatas=[metadata],
                )

            elif region["type"] in ["text", "table", "title", "list"]:
                # Process as text
                text_content = region["content"]
                # Chunk if needed
                # Encode with text encoder
                pass
    else:
        # Fall back to existing text-only processing
        chunks = self.processor.process(file_path, skip_if_processed=False)
        # ... existing code ...
```

**Design Decision**: Region-level storage (maximum granularity)
- **Chosen**: Each region is a separate vector entry with full metadata
- **Rationale**:
  - **Maximum precision**: Search matches specific regions, not entire documents
  - **Fine granularity**: Each text block, image, table indexed independently
  - **Organized storage**: Clear attribution to source document and position
  - **Better RAG quality**: Retrieval returns exactly relevant content
- **Trade-off**: More vector entries (increased storage), but WORTH IT for precision
- **Storage cost**: ~2-10x more vectors per document, acceptable for quality gain

### 4. Configuration Schema

**New**: `src/jina_rag_pipeline/api/config.py` (or extend existing)

```python
@dataclass
class CollectionConfig:
    """Configuration for a collection."""
    name: str
    enable_layout_analysis: bool = True  # Default: ENABLED for maximum precision
    layout_ocr_enabled: bool = True
    layout_table_extraction: bool = True
    max_image_dimension: int = 2048  # Resize large images
    save_extracted_images: bool = True  # Always save for organized storage
    region_granularity: Literal["fine", "coarse"] = "fine"  # Default: fine-grained

    # Existing config...
```

**Design Decision**: Collection-level configuration with precision-first defaults
- **Rationale**: Maximum precision and granularity by default
  - All collections → layout analysis ON by default
  - Users can opt-out for simple text-only collections if needed
  - Fine-grained regions for precise attribution
- **Storage**: Save in `uploads/{collection}/config.json`

## Data Model Changes

### Region Metadata Schema (Maximum Granularity)

```python
{
    # Document identification
    "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "source": "presentation.pptx",
    "collection_name": "presentations",

    # Region classification
    "region_type": "image" | "text" | "table" | "title" | "list" | "figure" | "chart",
    "region_id": "a1b2c3_page1_region0",  # Unique region identifier
    "region_sequence": 0,  # Order within page (reading order)
    "modality": "image" | "text",

    # Position and structure
    "page_number": 3,
    "slide_number": 3,  # For PowerPoint (same as page_number)
    "bbox": [x1, y1, x2, y2],  # Bounding box in page coordinates
    "bbox_normalized": [x1_norm, y1_norm, x2_norm, y2_norm],  # 0-1 range
    "width": 800,  # Pixel width
    "height": 600,  # Pixel height

    # Detection metadata
    "confidence": 0.95,  # Layout detection confidence score
    "detection_model": "detectron2-layoutlm",
    "extraction_timestamp": "2025-10-17T12:34:56.789Z",

    # Region-specific fields (varies by type)
    # For images:
    "image_path": "uploads/presentations/extracted_images/a1b2c3_page1_region0_chart.png",
    "thumbnail_path": "uploads/presentations/thumbnails/a1b2c3_page1_region0_thumb.jpg",
    "image_format": "png",
    "image_size_bytes": 245678,
    "visual_type": "chart" | "diagram" | "photo" | "logo" | "illustration",

    # For tables:
    "table_html": "<table>...</table>",
    "table_json": {...},  # Structured table data
    "table_path": "uploads/presentations/tables/a1b2c3_page1_table0.html",
    "row_count": 5,
    "column_count": 3,

    # For text regions:
    "text_content": "Revenue increased 20% YoY",
    "word_count": 5,
    "char_count": 30,
    "language": "en",

    # Relationships
    "parent_region_id": null,  # For nested regions (e.g., caption under image)
    "related_region_ids": ["a1b2c3_page1_region1"],  # Semantically related regions
    "spans_pages": false,  # True if region crosses page boundary

    # Embedding metadata
    "embedding_model": "jina-embeddings-v4",
    "embedding_dimension": 2048,
    "embedding_task": "retrieval",

    # Standard fields
    "upload_timestamp": "2025-10-17T12:30:00.000Z",
    "processed_timestamp": "2025-10-17T12:34:56.789Z",
}
```

**Granularity Benefits:**
- **Precise search**: Match on region type, position, size, confidence
- **Rich filtering**: Filter by visual_type, table structure, language
- **Attribution**: Exact region_id enables precise citation
- **Debugging**: Full detection metadata aids troubleshooting
- **Re-processing**: Can regenerate embeddings with new models

### Document Storage Structure (Organized & Persistent)

```
uploads/
  {collection}/
    documents/          # Original uploaded documents (persistent)
      {uuid}.pdf
      {uuid}.pptx
      {uuid}.docx
    images/             # Standalone uploaded images (persistent)
      {uuid}.png
      {uuid}.jpg
    extracted_images/   # Images extracted from documents (NEW - persistent)
      {doc_uuid}_page{N}_region{M}_{type}.{ext}
      # Example: "a1b2c3_page1_region0_chart.png"
      # Example: "a1b2c3_page2_region1_diagram.webp"
    tables/             # Extracted tables (NEW - persistent)
      {doc_uuid}_page{N}_table{M}.html
      {doc_uuid}_page{N}_table{M}.json
    thumbnails/         # Image thumbnails (generated)
      {uuid}_thumb.jpg
      {doc_uuid}_page{N}_region{M}_thumb.jpg  # Thumbnails for extracted images
    metadata/           # Per-document metadata (NEW - persistent)
      {uuid}_regions.json  # Detailed region information
      {uuid}_layout.json   # Layout analysis results
    config.json         # Collection configuration (persistent)
    stats.json          # Collection statistics (generated)
```

**Storage Principles:**
1. **Persistent**: All extracted images and regions saved permanently
2. **Organized**: Clear naming convention with document_id, page, region sequence
3. **Typed**: Region type in filename (chart, diagram, table, photo, etc.)
4. **Granular**: Separate files for each region enable fine-grained access
5. **Metadata-rich**: JSON files preserve full layout analysis results
6. **Reproducible**: Can regenerate embeddings without re-analysis

## Dependency Management

### Installation Strategy

**DECISION**: Include all dependencies as REQUIRED (Option B)

```toml
dependencies = [
    # ... existing ...
    "deepdoctection>=0.43.0",
    "python-doctr>=0.10.0",
    "python-pptx>=0.6.21",
]
```

**Additional manual installation required**:
```bash
# Detectron2 must be installed from git (not on PyPI)
pip install detectron2@git+https://github.com/deepdoctection/detectron2.git
```

**Rationale**:
- **Maximum precision**: All users get full capabilities
- **No optional features**: Simplifies support and ensures consistency
- **Organized storage**: Always save extracted images for persistent retrieval
- **Fine granularity**: All documents benefit from region-level indexing
- The M4 Max has sufficient memory (48GB) for all models

### Detectron2 Installation

Detectron2 is **REQUIRED** for layout detection:

```bash
# Installation steps (add to README)
pip install detectron2@git+https://github.com/deepdoctection/detectron2.git
```

**No Fallback Strategy**: Installation must succeed
1. Provide clear installation documentation
2. Test installation in CI/CD pipeline
3. Fail fast if dependencies missing (better than degraded experience)

## Performance Considerations

### Memory Budget
- **M4 Max Total**: 48GB unified memory
- **Jina Embeddings**: ~8GB (already loaded)
- **Deepdoctection Models**: ~500MB
- **Document Processing**: ~2GB temporary (slides → images)
- **Remaining**: ~37GB for OS and other processes
- **Verdict**: ✅ Fits within budget

### Processing Time Estimates
| Document Type | Current | With Layout Analysis | Overhead |
|---------------|---------|---------------------|----------|
| Text file (10 pages) | 2s | 2s | 0x (no layout needed) |
| PDF (10 pages) | 5s | 15s | 3x |
| PowerPoint (10 slides) | N/A | 20s | N/A (new feature) |
| DOCX (10 pages) | 3s | 10s | 3.3x |

**Mitigation**:
- Background async processing (already implemented)
- Progress indicators (already implemented)
- Make layout analysis opt-in per collection

## Testing Strategy

### Unit Tests
1. Test `LayoutAnalyzer` with sample documents
2. Test `PowerPointLoader` with/without layout analysis
3. Test region extraction and metadata preservation
4. Test fallback behavior when deepdoctection unavailable

### Integration Tests
1. Upload PowerPoint → verify regions extracted
2. Search for image content → verify retrieval works
3. Mixed document processing → verify both text and images indexed
4. Configuration toggle → verify simple mode fallback

### Performance Tests
1. Measure processing time for various document sizes
2. Monitor memory usage during layout analysis
3. Ensure processing completes within 60s for typical documents

## Migration Path

### For Existing Users
1. **No breaking changes**: Existing collections continue to work
2. **Opt-in**: Enable layout analysis via collection config
3. **Gradual adoption**: Reprocess specific collections as needed

### For New Users
1. **Default**: Layout analysis OFF (for performance)
2. **Recommendation**: Enable for presentation/visual-heavy collections
3. **Documentation**: Clear guidance on when to enable

## Rollback Plan

If layout analysis causes issues:
1. **Immediate**: Set `enable_layout_analysis = False` globally
2. **Code**: Loaders fall back to simple mode automatically
3. **Data**: Existing vector entries remain valid
4. **Uninstall**: Remove deepdoctection dependency if needed

## Open Design Questions

### Q1: Should we chunk across regions or treat each region independently?

**Option A**: Each region is a separate chunk
- Pros: Precise retrieval, clear attribution
- Cons: More vectors, may fragment context

**Option B**: Chunk across regions (maintain reading order)
- Pros: Maintains document flow, fewer vectors
- Cons: Harder to attribute results to specific regions

**Recommendation**: Option A (region-level chunks)
- Better for RAG applications where precision matters
- Aligns with citation/source linking feature

### Q2: How to handle large PowerPoint presentations (50+ slides)?

**Option A**: Process all slides
- Pros: Complete indexing
- Cons: Long processing time, many vectors

**Option B**: Limit to first N slides (e.g., 20)
- Pros: Faster processing
- Cons: Incomplete coverage

**Recommendation**: Option A with progress indicators
- Use async processing (already implemented)
- Show clear progress to user
- Consider adding max_slides config option later if needed

### Q3: Should extracted images be saved permanently or discarded after embedding?

**DECISION**: Option A (ALWAYS save to organized persistent storage)

**Rationale**:
- **Maximum precision**: Can verify what was indexed
- **Granular access**: Each region independently accessible
- **Re-embedding**: Can regenerate with improved models
- **Visual results**: Display actual images in search results
- **Debugging**: Inspect extraction quality
- **Storage cost**: Minimal (~1-2MB per image, worth it for quality)
- **Organized**: Clear naming enables efficient retrieval

**Storage paths**:
```
extracted_images/{doc_id}_page{N}_region{M}_{type}.{ext}
thumbnails/{doc_id}_page{N}_region{M}_thumb.jpg
metadata/{doc_id}_regions.json
```

## Security Considerations

1. **File size limits**: Enforce max file size to prevent memory exhaustion
   - PowerPoint: 50MB max (same as other documents)
   - Extracted images: 20MB max per image

2. **Malicious files**: Deepdoctection uses PIL/pypdf which are well-tested
   - No additional security risks beyond existing loaders

3. **Temporary files**: Clean up slide-to-image conversions
   - Use `tempfile.TemporaryDirectory()` with automatic cleanup

## Future Enhancements

1. **Custom layout models**: Fine-tune for domain-specific documents
2. **Table-aware retrieval**: Special handling for structured data
3. **Multi-page spanning**: Handle elements that cross page boundaries
4. **Layout-aware citations**: Link citations to specific regions within pages
