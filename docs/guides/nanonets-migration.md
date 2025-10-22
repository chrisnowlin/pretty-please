# Nanonets Migration Guide

## Overview

This guide covers migrating from the legacy `LayoutAnalyzer` (using deepdoctection) to the new `NanonetsLayoutAnalyzer` with semantic region extraction and markdown parsing capabilities.

## Why Migrate?

### Benefits of Nanonets

- **No Monkey Patches**: Clean architecture with no runtime patches required
- **Rich Table Extraction**: Full HTML table structure with rows, columns, headers
- **Equation Recognition**: LaTeX format for mathematical equations
- **Image Descriptions**: Natural language descriptions of charts, diagrams, logos
- **Better Multilingual**: Superior support for CJK, RTL languages
- **Semantic Metadata**: Rich semantic tagging for improved retrieval
- **Handwriting Support**: Basic handwriting recognition capabilities
- **Simpler Dependencies**: Just transformers + torch, no detectron2/doctr

### Limitations of Old Approach

- **Monkey Patches Required**: Runtime patching of deepdoctection's HuggingFace integration
- **Complex Dependencies**: Requires deepdoctection, detectron2, python-doctr
- **No Table Content**: Only detects table regions, doesn't extract content
- **No Equations**: Cannot recognize or extract mathematical formulas
- **Basic Image Support**: No semantic understanding of visual content
- **OCR Issues**: Version compatibility problems with doctr

---

## Migration Steps

### Step 1: Update Dependencies

#### Remove Legacy Dependencies

```bash
# Old dependencies are now optional
pip uninstall deepdoctection python-doctr detectron2
```

#### Install Fresh (Recommended)

```bash
# New installation only needs standard dependencies
pip install -e .

# For development
pip install -e ".[dev]"
```

#### Keep Legacy Support (Temporary)

```bash
# Install both new and old
pip install -e ".[legacy]"
```

### Step 2: Update Code

#### Before (Old LayoutAnalyzer)

```python
from jina_rag_pipeline.ingestion.layout_analysis import LayoutAnalyzer, Region

analyzer = LayoutAnalyzer(
    enable_ocr=False,
    enable_table_extraction=True,
)

regions = analyzer.extract_regions(file_path)

for region in regions:
    print(f"Type: {region.region_type}")
    print(f"BBox: {region.bbox}")
    print(f"Content: {region.content}")
```

#### After (New NanonetsLayoutAnalyzer)

```python
from jina_rag_pipeline.ingestion.nanonets_layout import NanonetsLayoutAnalyzer, create_analyzer
from jina_rag_pipeline.ingestion.semantic_region import SemanticRegion

analyzer = create_analyzer()  # Simple factory with defaults
# OR
analyzer = NanonetsLayoutAnalyzer(
    enable_tables=True,
    enable_equations=True,
    enable_image_descriptions=True,
)

regions = analyzer.extract_regions(file_path)

for region in regions:
    print(f"Type: {region.region_type}")
    print(f"Content: {region.content}")

    if region.region_type == "table":
        print(f"HTML: {region.table_html}")
        print(f"Rows: {region.table_rows}, Cols: {region.table_cols}")

    elif region.region_type == "image":
        print(f"Description: {region.image_description}")
        print(f"Image Type: {region.image_type}")

    elif region.region_type == "equation":
        print(f"LaTeX: {region.equation_latex}")
        print(f"Type: {region.equation_type}")
```

### Step 3: Update PowerPointLoader Usage

#### Before

```python
from jina_rag_pipeline.ingestion.loaders import PowerPointLoader

loader = PowerPointLoader(use_layout_analysis=True)
doc = loader.load(file_path)
```

#### After

```python
from jina_rag_pipeline.ingestion.loaders import PowerPointLoader

# Loader now uses NanonetsLayoutAnalyzer by default
loader = PowerPointLoader(use_layout_analysis=True)
doc = loader.load(file_path)

# Regions now have semantic metadata automatically
```

**No code changes needed!** The `PowerPointLoader` automatically uses Nanonets now.

### Step 4: Update Region Processing

#### Before (Region)

```python
from jina_rag_pipeline.ingestion.layout_analysis import Region

region_dict = {
    "region_id": "doc1_page1_region0",
    "region_type": "text",
    "region_sequence": 0,
    "page_number": 1,
    "bbox": (100, 200, 300, 400),
    "bbox_normalized": (0.1, 0.2, 0.3, 0.4),
    "width": 200,
    "height": 200,
    "content": "Sample text",
    "confidence": 0.95,
    "detection_model": "deepdoctection-layoutlm",
}

region = Region(**region_dict)
```

#### After (SemanticRegion)

```python
from jina_rag_pipeline.ingestion.semantic_region import SemanticRegion

region_dict = {
    "region_id": "doc1_page1_region0",
    "region_type": "table",
    "region_sequence": 0,
    "page_number": 1,
    "content": "Q1 2024 Results",
    "raw_markdown": "<table><tr><td>Q1</td><td>$150M</td></tr></table>",
    
    # Semantic metadata
    "semantic_tags": ["financial", "quarterly"],
    
    # Table-specific
    "table_html": "<table><tr><td>Q1</td><td>$150M</td></tr></table>",
    "table_rows": 1,
    "table_cols": 2,
    
    "model": "nanonets/Nanonets-OCR2-3B",
}

region = SemanticRegion.from_dict(region_dict)
```

---

## Data Structure Changes

### Region → SemanticRegion

| Old (Region) | New (SemanticRegion) | Notes |
|--------------|---------------------|-------|
| `bbox` | *(removed)* | Spatial coordinates not provided by VLM |
| `bbox_normalized` | *(removed)* | Semantic extraction is content-first |
| `width` / `height` | *(removed)* | Not needed for semantic understanding |
| `confidence` | *(removed)* | VLM doesn't provide confidence scores |
| `detection_model` | `model` | Renamed for clarity |
| *(none)* | `raw_markdown` | **NEW**: Original markdown from model |
| *(none)* | `semantic_tags` | **NEW**: Semantic classification tags |
| *(none)* | `table_html` | **NEW**: Full HTML table structure |
| *(none)* | `table_rows/cols` | **NEW**: Table dimensions |
| *(none)* | `image_description` | **NEW**: Natural language description |
| *(none)* | `image_type` | **NEW**: chart, logo, diagram, etc. |
| *(none)* | `equation_latex` | **NEW**: LaTeX equation representation |
| *(none)* | `equation_type` | **NEW**: inline or display |

### Region Types

| Type | Old Support | New Support | Notes |
|------|-------------|-------------|-------|
| `text` | ✅ | ✅ | Plain text paragraphs |
| `title` | ✅ | ✅ | Headings with markdown level |
| `list` | ✅ | ✅ | Ordered and unordered lists |
| `table` | ⚠️ | ✅ | Now includes full HTML content + structure |
| `image` | ⚠️ | ✅ | Now includes description + classification |
| `equation` | ❌ | ✅ | **NEW**: LaTeX mathematical equations |

---

## Performance Comparison

### Benchmark Results (M4 Max, 48GB Unified Memory)

| Metric | Old (deepdoctection) | New (Nanonets) | Notes |
|--------|---------------------|----------------|-------|
| **Avg Processing Time** | ~2.5s/slide | 8.22s/slide | 3.3x slower (acceptable) |
| **Peak Memory** | ~1.2GB | 1.77GB | Still well within budget |
| **Table Content** | ❌ (regions only) | ✅ (full HTML) | Major quality improvement |
| **Equations** | ❌ | ✅ (LaTeX) | New capability |
| **Image Descriptions** | ❌ | ✅ (natural language) | New capability |
| **Monkey Patches** | ⚠️ Required | ✅ None | Cleaner architecture |
| **Dependencies** | 3+ complex | 2 standard | Simpler installation |

**Recommendation**: Accept 3.3x slower processing for significantly better quality and features.

---

## Batch Processing

For presentations with many slides (10+), use batch processing for improved throughput:

### API

```python
from jina_rag_pipeline.ingestion.nanonets_layout import create_analyzer

analyzer = create_analyzer()

# Multiple files (batch processing)
paths = ["slide1.png", "slide2.png", "slide3.png"]
all_regions = analyzer.extract_regions_batch(
    paths,
    page_numbers=[1, 2, 3],
    batch_size=4  # Process 4 slides at once
)

for i, regions in enumerate(all_regions, 1):
    print(f"Slide {i}: {len(regions)} regions")
```

### When to Use Batch Processing

| Presentation Size | Recommended Approach | Batch Size |
|------------------|----------------------|------------|
| 1-5 slides | Sequential | N/A |
| 6-20 slides | Batch processing | 2-4 |
| 20+ slides | Batch processing | 4-8 |

**Note**: Batch processing reduces overhead but requires more memory. Adjust `batch_size` based on available GPU memory.

---

## Using the Markdown Parser

### Basic Usage

```python
from jina_rag_pipeline.ingestion.markdown_parser import MarkdownParser

parser = MarkdownParser()

markdown_text = """
# Document Title

Some introductory text.

<table>
  <tr><th>Column 1</th><th>Column 2</th></tr>
  <tr><td>Data 1</td><td>Data 2</td></tr>
</table>

$$E = mc^2$$
"""

regions = parser.parse_markdown_to_regions(markdown_text)

for region in regions:
    print(f"Type: {region.region_type}")
    print(f"Content: {region.content[:50]}...")
```

### Region Types

The parser extracts 6 types of semantic regions:

#### 1. Tables
```python
if region.region_type == "table":
    metadata = parser.extract_table_metadata(region.table_html)
    print(f"Table: {metadata['rows']}x{metadata['cols']}")
    print(f"Has header: {metadata['has_header']}")
```

#### 2. Images
```python
if region.region_type == "image":
    print(f"Image: {region.image_description}")
```

#### 3. Equations
```python
if region.region_type == "equation":
    print(f"LaTeX: {region.equation_latex}")
```

#### 4. Headings/Titles
```python
if region.region_type == "title":
    level = region.markdown_level  # 1-6 (H1-H6)
    print(f"H{level}: {region.content}")
```

#### 5. Lists
```python
if region.region_type == "list":
    items = region.content.split('\n')
    print(f"List with {len(items)} items")
```

#### 6. Text Paragraphs
```python
if region.region_type == "text":
    print(f"Paragraph: {region.content}")
```

### Common Patterns

```python
# Filter by region type
tables = [r for r in regions if r.region_type == "table"]
headings = [r for r in regions if r.region_type == "title"]
equations = [r for r in regions if r.region_type == "equation"]

# Build heading hierarchy
for region in regions:
    if region.region_type == "title":
        indent = "  " * (region.markdown_level - 1)
        print(f"{indent}{'#' * region.markdown_level} {region.content}")

# Count regions by type
from collections import Counter
type_counts = Counter(r.region_type for r in regions)
print(f"Found: {dict(type_counts)}")
```

### Nanonets Format

The parser expects markdown with these semantic tags:

```markdown
# Standard Markdown Headings

Regular paragraphs of text.

- Bullet lists
- Use standard markdown syntax

1. Numbered lists
2. Also supported

<table>
  <tr><th>Header</th></tr>
  <tr><td>Data</td></tr>
</table>

<img>Image description goes here</img>

Display equation: $$E = mc^2$$
```

### Performance Tips

1. **Reuse parser instance**: Create once, parse multiple times
2. **Filter early**: Only process regions you need
3. **Batch processing**: Process multiple documents in parallel

---

## Testing After Migration

### Run Test Suite

```bash
# Run all tests
pytest

# Run only Nanonets-related tests
pytest tests/unit/test_semantic_region.py
pytest tests/unit/test_markdown_parser.py
pytest tests/integration/test_nanonets_layout.py
pytest tests/integration/test_nanonets_e2e.py

# Run benchmarks
python benchmarks/benchmark_nanonets.py
```

### Validate Performance

```bash
python test_nanonets_model.py

# Expected results (M4 Max):
# ✓ Model loads in < 30 seconds
# ✓ Inference: 8-16 seconds per slide
# ✓ Memory: < 2GB peak
# ✓ MPS acceleration enabled
```

---

## Backwards Compatibility

### Keeping Legacy Code Temporarily

```python
from jina_rag_pipeline.ingestion.nanonets_layout import create_analyzer as create_nanonets
from jina_rag_pipeline.ingestion.layout_analysis import LayoutAnalyzer

# Feature flag for gradual migration
USE_NANONETS = True

if USE_NANONETS:
    analyzer = create_nanonets()
    print("Using Nanonets (recommended)")
else:
    # Legacy support (requires pip install -e ".[legacy]")
    analyzer = LayoutAnalyzer(enable_ocr=False)
    print("Using legacy deepdoctection (deprecated)")
```

### Deprecation Timeline

- **Current Version**: Both analyzers available, Nanonets default
- **Next Minor Version**: Deprecation warnings for all legacy usage
- **Next Major Version**: Legacy code removed entirely

---

## Troubleshooting

### Model Download Issues

**Problem**: Model download fails or is very slow

**Solution**:
```bash
python -c "from transformers import AutoModelForImageTextToText; \
  AutoModelForImageTextToText.from_pretrained('nanonets/Nanonets-OCR2-3B')"
```

### Memory Issues

**Problem**: Out of memory errors on smaller machines

**Solution**: The model requires ~6GB for weights + ~2GB for inference. Minimum 10GB RAM recommended.

```python
analyzer = NanonetsLayoutAnalyzer(
    enable_image_descriptions=False,  # Reduce processing
    torch_dtype=torch.float16,  # Use half precision (if supported)
)
```

### MPS Acceleration Not Working

**Problem**: Model runs on CPU instead of GPU on Apple Silicon

**Solution**:
```python
import torch
print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"MPS built: {torch.backends.mps.is_built()}")

# If False, reinstall PyTorch
# pip install --upgrade torch torchvision
```

### Markdown Parser Issues

**No regions extracted**: Check if markdown uses Nanonets format with semantic tags (`<table>`, `<img>`, etc.)

**Lists not grouping correctly**: Ensure list items are within 100 characters of each other

**Table metadata incorrect**: Verify table HTML is well-formed with proper `<tr>`, `<th>`, `<td>` tags

**Inline equations disappearing**: This is expected. Inline `$...$` equations are currently removed. Use display equations `$$...$$`

---

## Common Questions

**Q: Do I need to reinstall dependencies?**
A: Fresh installs don't need legacy dependencies. Existing installations can optionally remove them.

**Q: Will my existing PowerPoint collections still work?**
A: Yes! The loader is backwards compatible and will use Nanonets automatically.

**Q: Can I reprocess old documents with Nanonets?**
A: Yes, just re-run ingestion. New semantic metadata will be extracted.

**Q: Is the performance acceptable for production?**
A: Yes. 8.22s/slide is acceptable for one-time ingestion pipelines.

**Q: What about PDF documents?**
A: Nanonets works with PDFs the same way. Each page is processed as an image.

---

## Performance Benchmarks

See [benchmarks/NANONETS_BENCHMARK_RESULTS.md](../../benchmarks/NANONETS_BENCHMARK_RESULTS.md) for detailed performance data.

---

## Next Steps

1. ✅ **Update dependencies** - Remove legacy or install fresh
2. ✅ **Update code** - Migrate to `NanonetsLayoutAnalyzer` and `SemanticRegion`
3. ✅ **Run tests** - Validate everything works
4. ✅ **Benchmark performance** - Ensure acceptable on your hardware
5. ✅ **Use batch processing** - For presentations with 10+ slides
6. ✅ **Reprocess documents** - Extract richer semantic metadata

---

## Related Documentation

- [Async Processing Guide](async-processing.md)
- [Citations Feature](../features/citations.md)
- [System Architecture](../architecture/system-overview.md)
