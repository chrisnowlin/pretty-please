# Spec Delta: Document Analysis

## Capability: multimodal/Document Analysis

This spec defines enhanced document understanding capabilities including language detection, chart classification, and confidence scoring.

---

## ADDED Requirements

### Requirement: Multilingual Document Detection
The system MUST automatically detect document language from 109 supported languages.

#### Scenario: Language Detection
**Given** a document image in any supported language (Chinese, English, Japanese, etc.)
**When** the OCR analyzer processes the document
**Then** the system MUST detect the primary language
**And** MUST return an ISO 639-1 language code (e.g., "en", "zh", "ja", "ar", "hi")
**And** MUST include language in `SemanticRegion.detected_language` field
**And** MUST achieve ≥95% accuracy on standard language detection benchmarks

#### Scenario: Multilingual Document Handling
**Given** a document with mixed languages (e.g., English title, Chinese content)
**When** the OCR analyzer processes each page
**Then** the system MUST detect the primary language per page
**And** MUST allow regions on the same page to have different detected languages
**And** MUST include per-region language metadata in storage

#### Scenario: Language-Specific Retrieval
**Given** a document collection with multilingual content
**When** a user queries in a specific language
**Then** the retrieval system SHOULD prioritize regions with matching `detected_language`
**And** SHOULD support language filter in query parameters: `?language=zh`

### Requirement: Chart Type Classification
The system MUST classify chart types for visual elements in documents.

#### Scenario: Chart Type Detection
**Given** a document image containing a chart or graph
**When** the OCR analyzer processes the image
**Then** the system MUST classify the chart type from supported categories:
- `bar`: Bar chart (vertical/horizontal)
- `line`: Line graph
- `pie`: Pie chart
- `scatter`: Scatter plot
- `area`: Area chart
- `histogram`: Histogram
- `stacked-bar`: Stacked bar chart
- `stacked-area`: Stacked area chart
- `bubble`: Bubble chart
- `mixed`: Mixed chart types (e.g., bar-line combination)
- `other`: Unclassified chart type

**And** MUST include chart type in `SemanticRegion.chart_type` field
**And** MUST add chart type to `semantic_tags` list

#### Scenario: Chart Description Generation
**Given** a chart element is detected
**When** the analyzer generates region metadata
**Then** the system MUST create a natural language description of the chart
**And** description MUST include chart type, data summary, and context
**Example**: "Bar chart showing quarterly revenue by region, with North America leading at $2.5M"
**And** MUST store description in `SemanticRegion.image_description`

#### Scenario: Educational Chart Recognition
**Given** an educational document with learning-specific charts (concept maps, Venn diagrams, flowcharts)
**When** the analyzer processes these visual elements
**Then** the system SHOULD classify them with educational-specific types:
- `venn-diagram`: Venn diagram
- `concept-map`: Concept map or mind map
- `flowchart`: Flowchart or process diagram
- `timeline`: Timeline
- `diagram`: General educational diagram

### Requirement: Confidence Scoring
The system MUST provide confidence scores for OCR element detection.

#### Scenario: Element Confidence Scores
**Given** the OCR backend returns confidence metrics
**When** a `SemanticRegion` is created
**Then** the system MUST include `confidence_score` (0.0 to 1.0)
**And** MUST track confidence per element type (text, table, formula, chart)
**And** MUST log warnings for elements with confidence < 0.7

#### Scenario: Quality-Based Filtering
**Given** a collection of processed documents
**When** low-confidence regions (score < 0.6) are detected
**Then** the system SHOULD flag these for human review
**And** SHOULD allow administrators to set minimum confidence thresholds per collection
**And** SHOULD exclude low-confidence regions from retrieval results (configurable)

### Requirement: Enhanced Table Understanding
The system MUST extract rich table metadata beyond basic structure.

#### Scenario: Table Structure Metadata
**Given** a table element is detected
**When** the analyzer extracts table metadata
**Then** the system MUST capture:
- `row_count`: Number of table rows (including header)
- `column_count`: Number of table columns
- `has_header`: Boolean indicating header row presence
- `table_html`: Full HTML representation
**And** MUST validate HTML structure (proper `<table>`, `<tr>`, `<td>` nesting)

#### Scenario: Educational Table Classification
**Given** tables in educational documents (grade matrices, comparison charts, data sets)
**When** the analyzer processes table content
**Then** the system SHOULD classify table purpose:
- `grade-matrix`: Grading rubric or score matrix
- `comparison`: Comparison chart or feature matrix
- `data`: Data table with numerical values
- `schedule`: Schedule or calendar table
- `roster`: List or roster table
**And** SHOULD add classification to `semantic_tags`

### Requirement: Mathematical Formula Enhancement
The system MUST provide enhanced formula recognition and metadata.

#### Scenario: LaTeX Formula Extraction
**Given** a document containing mathematical formulas
**When** the analyzer detects a formula element
**Then** the system MUST extract LaTeX representation
**And** MUST store in both `content` and `equation_latex` fields
**And** MUST handle inline formulas (e.g., `$x^2$`) and display formulas (e.g., `$$E=mc^2$$`)
**And** MUST achieve ≥90% accuracy on standard formula recognition benchmarks

#### Scenario: Formula Complexity Classification
**Given** formula elements with varying complexity
**When** metadata is generated
**Then** the system SHOULD classify formula complexity:
- `simple`: Basic arithmetic or single-variable expressions (e.g., `x + 5 = 10`)
- `moderate`: Multi-variable or common functions (e.g., `f(x) = \sin(x) + x^2`)
- `complex`: Advanced notation (integrals, matrices, summations)
**And** SHOULD add complexity to `semantic_tags`

---

## MODIFIED Requirements

### Requirement: Semantic Region Metadata Schema
The `SemanticRegion` dataclass MUST be extended to support enhanced document analysis.

#### Scenario: Extended Metadata Fields
**Given** a `SemanticRegion` object
**Then** the object MUST support the following NEW fields:
- `detected_language: Optional[str]` - ISO 639-1 language code
- `chart_type: Optional[str]` - Chart classification (bar, line, pie, etc.)
- `confidence_score: Optional[float]` - Detection confidence (0.0-1.0)
- `equation_latex: Optional[str]` - LaTeX formula (for equation regions)
- `bounding_box: Optional[Tuple[int, int, int, int]]` - Element bbox (x1, y1, x2, y2)

**And** all existing fields MUST remain backward compatible
**And** new fields MUST be optional (default `None`)

#### Scenario: Metadata Serialization
**Given** a `SemanticRegion` with extended metadata
**When** `region.to_dict()` is called
**Then** the dictionary MUST include all extended fields when present
**And** MUST omit fields with `None` values (compact representation)
**And** MUST serialize to valid JSON for storage

#### Scenario: Metadata Querying
**Given** regions stored in ChromaDB with extended metadata
**When** a user queries with metadata filters
**Then** the system MUST support filtering by:
- `language`: Filter by detected language (e.g., `language="zh"`)
- `chart_type`: Filter by chart type (e.g., `chart_type="bar"`)
- `confidence`: Filter by minimum confidence (e.g., `confidence >= 0.8`)
**And** MUST support combined filters (e.g., `language="en" AND chart_type="bar"`)

---

## Cross-Capability Dependencies

### Depends On
- **ingestion/OCR Engine**: Requires PaddleOCR-VL backend for 109-language support and chart classification
- **storage/Vector Storage**: Requires metadata schema extension to store new fields

### Impacts
- **retrieval/Semantic Search**: Enhanced filtering by language, chart type, confidence
- **generation/Lesson Planning**: Language-aware content selection for multilingual curricula
- **monitoring/Quality Metrics**: Confidence scores enable quality tracking and alerting

---

## Migration Notes

### Breaking Changes
**None** - All new fields are optional. Existing code continues to work.

### Data Migration
Existing `SemanticRegion` records in storage remain valid. New fields will populate on next re-indexing:
```python
# Existing regions without extended metadata
{
  "region_id": "doc1_page1_region0",
  "region_type": "text",
  "content": "...",
  # No language, chart_type, confidence (OK)
}

# New regions with extended metadata
{
  "region_id": "doc2_page1_region0",
  "region_type": "chart",
  "content": "[IMAGE]",
  "detected_language": "en",
  "chart_type": "bar",
  "confidence_score": 0.95,
  "image_description": "Bar chart showing..."
}
```

### Testing
Add integration tests for:
- Language detection accuracy across 20+ languages
- Chart type classification accuracy (≥85% on test corpus)
- Confidence score distribution (should be ≥0.7 for 90% of elements)
- Metadata filtering in retrieval queries
