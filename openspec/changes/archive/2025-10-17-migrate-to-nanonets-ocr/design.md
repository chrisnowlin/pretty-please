# Design: Nanonets-Based Layout Analysis Architecture

## Overview

This design replaces the spatial-first layout analysis (deepdoctection) with a semantic-first approach (Nanonets-OCR2-3B) that provides richer content understanding while eliminating technical debt.

## Current Architecture (deepdoctection)

```
PowerPoint Slide → Image
                     ↓
            deepdoctection Analyzer
          (Layout Detection Models)
                     ↓
          Spatial Regions + Bbox
          ┌─────────────────┐
          │ Region          │
          │ - type: "text"  │
          │ - bbox: (x,y,w,h)│
          │ - content: "..."│
          │ - confidence    │
          └─────────────────┘
                     ↓
          Region-Based Processing
                     ↓
          Embeddings + Storage

Issues:
- Monkey patch for HuggingFace bug
- OCR disabled (version conflict)
- Limited content extraction
- Fragile dependencies
```

## Proposed Architecture (Nanonets)

```
PowerPoint Slide → Image
                     ↓
        Nanonets-OCR2-3B Model
        (Vision-Language Model)
                     ↓
          Structured Markdown
          ┌────────────────────┐
          │ # Title            │
          │                    │
          │ Text content...    │
          │                    │
          │ | Col 1 | Col 2 |  │
          │ |-------|---------|  │
          │ | Data  | More  |  │
          │                    │
          │ <img>chart desc    │
          │ </img>             │
          │                    │
          │ $$E=mc^2$$         │
          └────────────────────┘
                     ↓
          Markdown Parser
          (Extract Semantic Regions)
                     ↓
          Semantic Regions
          ┌──────────────────────┐
          │ Region               │
          │ - type: "table"      │
          │ - content: "<table>..│
          │ - semantic_tags: []  │
          │ - markdown_level: 2  │
          └──────────────────────┘
                     ↓
          Region-Based Processing
                     ↓
          Embeddings + Storage

Benefits:
- No monkey patches
- Rich content extraction
- Clean dependencies
- Semantic metadata
```

## Component Design

### 1. NanonetsLayoutAnalyzer

**Location**: `src/jina_rag_pipeline/ingestion/nanonets_layout.py`

**Responsibilities**:
- Load Nanonets-OCR2-3B model from HuggingFace
- Process document images to structured markdown
- Parse markdown into semantic regions
- Generate region metadata

**Key Methods**:
```python
class NanonetsLayoutAnalyzer:
    def __init__(
        self,
        model_name: str = "nanonets/Nanonets-OCR2-3B",
        device: str = "mps",  # Apple Silicon
        enable_tables: bool = True,
        enable_equations: bool = True,
        enable_image_descriptions: bool = True,
    ):
        """Initialize Nanonets model."""

    def analyze_document(self, file_path: Path) -> str:
        """
        Analyze document and return structured markdown.

        Returns:
            Markdown string with semantic tags
        """

    def extract_regions(
        self,
        file_path: Path,
        page_number: int = 1,
        document_id: Optional[str] = None
    ) -> List[SemanticRegion]:
        """
        Extract semantic regions from markdown output.

        Returns:
            List of SemanticRegion objects
        """
```

### 2. SemanticRegion Dataclass

**Location**: `src/jina_rag_pipeline/ingestion/nanonets_layout.py`

**Structure**:
```python
@dataclass
class SemanticRegion:
    """Represents a semantic region extracted from markdown."""

    # Core identification
    region_id: str
    region_type: Literal["text", "table", "image", "equation", "list", "title"]
    region_sequence: int  # Order in document

    # Page context
    page_number: int

    # Content
    content: Union[str, Path]  # Markdown/HTML/LaTeX or image path
    raw_markdown: str  # Original markdown block

    # Semantic metadata
    semantic_tags: List[str]  # e.g., ["watermark"], ["checkbox"], ["signature"]
    markdown_level: Optional[int]  # Heading level (1-6)
    list_type: Optional[Literal["ordered", "unordered"]]  # For lists

    # Table structure (for table regions)
    table_html: Optional[str]  # HTML representation
    row_count: Optional[int]
    column_count: Optional[int]

    # Image metadata (for image regions)
    image_description: Optional[str]  # Generated description
    image_type: Optional[Literal["logo", "chart", "diagram", "photo"]]

    # Detection metadata
    extraction_timestamp: str
    model: str = "nanonets-ocr2-3b"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
```

### 3. Markdown Parser

**Location**: `src/jina_rag_pipeline/ingestion/markdown_parser.py`

**Responsibilities**:
- Parse Nanonets markdown output
- Identify region boundaries
- Extract semantic tags (`<table>`, `<img>`, `$$...$$`)
- Build SemanticRegion objects

**Algorithm**:
```python
def parse_markdown_to_regions(markdown: str, document_id: str, page_num: int) -> List[SemanticRegion]:
    """
    Parse markdown into semantic regions.

    Steps:
    1. Split on major structural elements (headers, tables, images, equations)
    2. Identify semantic tags
    3. Extract metadata for each region type
    4. Create SemanticRegion objects
    5. Assign sequence numbers
    """
    regions = []

    # Regex patterns for different region types
    table_pattern = r'<table>.*?</table>'  # HTML tables
    img_pattern = r'<img>(.*?)</img>'  # Image descriptions
    equation_pattern = r'\$\$(.*?)\$\$'  # LaTeX equations
    header_pattern = r'^(#{1,6})\s+(.+)$'  # Markdown headers

    # Extract tables
    for match in re.finditer(table_pattern, markdown, re.DOTALL):
        region = SemanticRegion(
            region_type="table",
            content=match.group(0),
            table_html=match.group(0),
            # ... extract row/col counts
        )
        regions.append(region)

    # Extract images
    for match in re.finditer(img_pattern, markdown):
        region = SemanticRegion(
            region_type="image",
            content="[IMAGE]",
            image_description=match.group(1),
            # ... parse image type from description
        )
        regions.append(region)

    # Extract equations
    for match in re.finditer(equation_pattern, markdown):
        region = SemanticRegion(
            region_type="equation",
            content=match.group(1),  # LaTeX
            semantic_tags=["latex"],
        )
        regions.append(region)

    # ... continue for other types

    return sorted(regions, key=lambda r: r.region_sequence)
```

### 4. Updated PowerPointLoader

**Location**: `src/jina_rag_pipeline/ingestion/loaders.py`

**Changes**:
```python
class PowerPointLoader:
    def __init__(self, use_layout_analysis: bool = False):
        if use_layout_analysis:
            try:
                from .nanonets_layout import NanonetsLayoutAnalyzer
                self.layout_analyzer = NanonetsLayoutAnalyzer()
                logger.info("NanonetsLayoutAnalyzer initialized")
            except ImportError:
                raise ImportError(
                    "Nanonets-OCR2 dependencies required. "
                    "Install with: pip install transformers torch"
                )
        else:
            self.layout_analyzer = None

    def load(self, file_path: Path) -> Document:
        # ... existing slide conversion ...

        if self.layout_analyzer:
            # Use Nanonets for semantic region extraction
            regions = self.layout_analyzer.extract_regions(
                file_path=slide_image_path,
                page_number=slide_num,
                document_id=file_path.stem
            )
            # Convert SemanticRegion to Document format
        else:
            # Simple text extraction (current fallback)
```

## Data Flow

### Region Processing Pipeline

```
1. Document Input
   ↓
2. Slide → Image Conversion
   ↓
3. Nanonets Model Inference
   | Input: PIL Image
   | Output: Structured Markdown
   ↓
4. Markdown Parsing
   | Extract: Tables, Images, Equations, Text
   | Create: SemanticRegion objects
   ↓
5. Region-Based Processing (tasks.py)
   | For each region:
   | - Route to appropriate encoder (text/vision)
   | - Generate embeddings
   | - Save to storage
   ↓
6. Vector Storage
   | ChromaDB with semantic metadata
   | Organized directory structure
```

### Metadata Structure

```python
{
    "document_id": "presentation_001",
    "page_number": 1,
    "region_id": "presentation_001_page1_region2",
    "region_type": "table",
    "region_sequence": 2,
    "content_type": "html",
    "semantic_tags": ["financial", "quarterly-results"],
    "table_structure": {
        "rows": 5,
        "columns": 4,
        "has_header": true
    },
    "extraction": {
        "model": "nanonets-ocr2-3b",
        "timestamp": "2025-10-17T08:30:00Z",
        "confidence": 0.95
    }
}
```

## Migration Strategy

### Phase 1: Parallel Implementation
- Keep existing deepdoctection code
- Add Nanonets implementation alongside
- Configuration flag to choose analyzer

### Phase 2: Testing & Validation
- Run both analyzers on test documents
- Compare output quality
- Validate retrieval performance
- Ensure all tests pass

### Phase 3: Gradual Migration
- Default to Nanonets for new collections
- Allow opt-in for existing collections
- Document both approaches

### Phase 4: Deprecation
- Mark deepdoctection as deprecated
- Remove monkey patches
- Clean up dependencies
- Update documentation

## Performance Considerations

### Memory Usage
- **Nanonets Model**: ~6GB loaded in unified memory
- **Input Image**: ~10MB per slide (temporary)
- **Total Peak**: ~6.5GB (well within 48GB available)

### Processing Speed
- **Current (deepdoctection)**: ~2-3 seconds per slide
- **Estimated (Nanonets)**: ~4-6 seconds per slide
- **Trade-off**: Acceptable for richer content extraction
- **Mitigation**: Batch processing, async operations

### Disk Space
- **Model Download**: ~6GB one-time
- **Extracted Content**: Similar to current (images, metadata)
- **Total Impact**: +6GB for model cache

## Testing Strategy

### Unit Tests
- `test_nanonets_layout.py`: Model loading, inference, parsing
- `test_markdown_parser.py`: Region extraction from markdown
- `test_semantic_regions.py`: Dataclass validation

### Integration Tests
- `test_powerpoint_nanonets.py`: End-to-end PowerPoint processing
- `test_region_processing.py`: Region-based embedding generation
- `test_storage.py`: Semantic metadata storage

### Validation Tests
- Compare retrieval quality (semantic vs spatial)
- Verify table extraction accuracy
- Test equation recognition
- Validate multilingual support

## Risk Mitigation

### Risk 1: Model Download Failures
**Mitigation**: Implement retry logic, cache validation, fallback to deepdoctection

### Risk 2: Slower Processing
**Mitigation**: Batch processing, async operations, progress tracking

### Risk 3: Memory Constraints
**Mitigation**: Monitor unified memory usage, implement model offloading if needed

### Risk 4: Parse Errors
**Mitigation**: Robust markdown parser with error recovery, validation tests

## Success Metrics

1. **Code Quality**: Zero monkey patches, clean imports
2. **Content Richness**: >90% table extraction accuracy, equation recognition working
3. **Performance**: Processing time ≤ 2x current, memory usage < 10GB
4. **Retrieval Quality**: Semantic search performs ≥ current baseline
5. **Test Coverage**: 100% of existing tests passing + new Nanonets tests

## Future Enhancements

1. **PDF Support**: Extend Nanonets to PDF documents
2. **DOCX Support**: Use for Word document analysis
3. **OCR Optimization**: Fine-tune for specific document types
4. **Streaming**: Process very large documents in chunks
5. **Multi-page**: Optimize for presentations with hundreds of slides
