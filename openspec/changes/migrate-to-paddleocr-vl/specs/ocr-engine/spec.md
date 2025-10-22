# Spec Delta: OCR Engine

## Capability: ingestion/OCR Engine

This spec defines the OCR engine abstraction layer and backend implementations for document text and structure extraction.

---

## MODIFIED Requirements

### Requirement: OCR Backend Selection
The system MUST support multiple OCR backends with automatic detection and manual override capabilities.

#### Scenario: Automatic Backend Detection
**Given** the system is starting up with no explicit backend configuration
**When** the OCR analyzer is initialized with `backend="auto"`
**Then** the system MUST detect available backends in priority order:
1. PaddleOCR-VL server (if reachable at `OCR_SERVER_URL`)
2. Nanonets with hardware acceleration (MPS/CUDA)
3. PaddleOCR CLI (if installed locally)
4. Nanonets CPU fallback

**And** the system MUST log the selected backend for observability

#### Scenario: Manual Backend Override
**Given** multiple OCR backends are available
**When** the user specifies `backend="paddleocr-vl"` in configuration
**Then** the system MUST use PaddleOCR-VL exclusively
**And** MUST raise an error if the specified backend is unavailable
**And** MUST NOT fall back to alternative backends

#### Scenario: Graceful Degradation
**Given** the preferred backend (PaddleOCR-VL server) is unavailable
**When** `enable_cli_fallback=True` is configured
**Then** the system MUST fall back to PaddleOCR CLI
**And** MUST log a warning about the fallback
**And** MUST continue processing without user intervention

### Requirement: Unified Analyzer Interface
All OCR backends MUST implement a consistent interface for document analysis.

#### Scenario: Single Document Analysis
**Given** any OCR backend is active
**When** `analyzer.analyze_document(file_path, page_number)` is called
**Then** the analyzer MUST return structured output (JSON or markdown)
**And** the output format MUST be consistent across backends
**And** processing MUST complete within the configured timeout

#### Scenario: Region Extraction
**Given** any OCR backend is active
**When** `analyzer.extract_regions(file_path, page_number, document_id)` is called
**Then** the analyzer MUST return a list of `SemanticRegion` objects
**And** each region MUST have a unique `region_id`
**And** regions MUST be ordered by `region_sequence`
**And** all regions MUST belong to the specified `page_number`

#### Scenario: Batch Processing
**Given** the OCR backend supports batch processing (PaddleOCR-VL server)
**When** `analyzer.analyze_documents_batch(file_paths, batch_size=4)` is called
**Then** the analyzer MUST process images in batches of the specified size
**And** MUST return results in the same order as input
**And** MUST NOT fail entirely if individual images fail (collect errors)

---

## ADDED Requirements

### Requirement: PaddleOCR-VL Backend Support
The system MUST support PaddleOCR-VL as an OCR backend with both server and CLI modes.

#### Scenario: Server-Based Processing
**Given** a PaddleOCR-VL inference server is running at `http://localhost:8080/v1`
**When** the analyzer processes a document image
**Then** the system MUST send the image to the server via HTTP POST
**And** MUST include processing parameters (enable_tables, enable_equations, output_format)
**And** MUST receive structured JSON response with elements
**And** MUST handle server errors gracefully with retry logic (up to 3 retries)

#### Scenario: CLI-Based Processing (Fallback)
**Given** the PaddleOCR-VL server is unavailable
**And** PaddleOCR SDK is installed locally
**When** the analyzer processes a document image with `enable_cli_fallback=True`
**Then** the system MUST use `paddleocr doc_parser` CLI command
**And** MUST parse the CLI output to JSON format
**And** MUST log a warning that CLI mode is slower than server mode

#### Scenario: Server Health Monitoring
**Given** a PaddleOCR-VL server URL is configured
**When** the analyzer initializes
**Then** the system MUST verify server health via `/health` endpoint
**And** MUST complete health check within 5 seconds
**And** MUST mark server as unavailable if health check fails
**And** MUST re-check health on next processing request after 60-second cooldown

### Requirement: Output Format Adaptation
The system MUST convert backend-specific output to unified `SemanticRegion` format.

#### Scenario: PaddleOCR-VL JSON Parsing
**Given** PaddleOCR-VL returns JSON with elements array
**When** the output parser processes the response
**Then** the system MUST extract each element and create a `SemanticRegion`
**And** MUST map element types: `text→text`, `table→table`, `formula→equation`, `chart→image`
**And** MUST preserve element order via `region_sequence`
**And** MUST enrich regions with detected language metadata
**And** MUST include confidence scores when available

#### Scenario: Table Element Parsing
**Given** PaddleOCR-VL detects a table element
```json
{
  "type": "table",
  "content": "<table><tr><th>Name</th><th>Score</th></tr>...</table>",
  "structure": {"rows": 5, "cols": 2},
  "bbox": [100, 200, 400, 500]
}
```
**When** the parser creates a `SemanticRegion`
**Then** the region MUST have `region_type="table"`
**And** MUST set `table_html=content`
**And** MUST set `row_count=5` and `column_count=2`
**And** MUST include `bbox` for potential future use

#### Scenario: Formula Element Parsing
**Given** PaddleOCR-VL detects a formula element
```json
{
  "type": "formula",
  "content": "E=mc^2",
  "latex": "E=mc^2",
  "bbox": [150, 300, 250, 350]
}
```
**When** the parser creates a `SemanticRegion`
**Then** the region MUST have `region_type="equation"`
**And** MUST set `content=content` and `equation_latex=latex`
**And** MUST add semantic tags `["latex", "formula"]`

#### Scenario: Chart Element Parsing
**Given** PaddleOCR-VL detects a chart element
```json
{
  "type": "chart",
  "chart_type": "bar",
  "description": "Bar chart showing quarterly revenue by region",
  "bbox": [50, 100, 550, 400]
}
```
**When** the parser creates a `SemanticRegion`
**Then** the region MUST have `region_type="image"`
**And** MUST set `chart_type="bar"`
**And** MUST set `image_description=description`
**And** MUST add semantic tags `["chart", "bar"]`

### Requirement: Performance Optimization
The OCR engine MUST optimize for throughput and memory efficiency.

#### Scenario: Batch Inference Optimization
**Given** the PaddleOCR-VL server backend is active
**And** a batch of 10 document images needs processing
**When** batch processing is invoked with `batch_size=4`
**Then** the system MUST send images in 3 batches: [4, 4, 2]
**And** MUST process batches in parallel when possible
**And** MUST complete all 10 images in ≤ 2x the time of single image
**And** MUST use ≤ 1GB additional memory for batch buffering

#### Scenario: Memory Isolation
**Given** the PaddleOCR-VL server backend is active
**When** processing a document
**Then** the OCR model memory MUST be isolated to the server process
**And** the client process MUST use ≤ 500MB for image buffering
**And** MUST NOT load model weights in the client process

---

## REMOVED Requirements

### Requirement: Single Backend Architecture
**Removed**: The previous requirement mandating a single OCR backend (Nanonets-only) is replaced by multi-backend support.

**Reason**: Educational content requires flexibility in OCR quality vs. speed trade-offs. Different document types (textbooks vs. worksheets) benefit from different backends.

### Requirement: In-Process Model Inference
**Removed**: The requirement that OCR models run in the same process as the application.

**Reason**: Server-based inference enables better resource utilization, horizontal scaling, and memory isolation. In-process inference remains available as fallback.

---

## Cross-Capability Dependencies

### Depends On
- **storage/Vector Storage**: Requires `SemanticRegion` metadata schema to store language and chart type
- **configuration/Dynamic Config**: Uses `OCRConfig` for backend selection and performance tuning

### Impacts
- **retrieval/Semantic Search**: Enhanced metadata (language, chart_type) enables better filtering
- **monitoring/Performance Metrics**: New metrics for backend selection and server health

---

## Migration Notes

### Breaking Changes
**None** - The unified `NanonetsAnalyzer` interface remains unchanged. Backend selection is internal.

### Configuration Changes
```python
# NEW: Explicit backend selection (optional)
analyzer = NanonetsAnalyzer(backend="paddleocr-vl")

# NEW: Server URL configuration (optional, defaults to localhost)
analyzer = NanonetsAnalyzer(
    backend="paddleocr-vl",
    server_url="http://paddleocr-server:8080/v1"
)

# UNCHANGED: Auto-detection still works
analyzer = NanonetsAnalyzer()  # Selects best available backend
```

### Data Migration
**Not Required** - Existing `SemanticRegion` objects remain valid. New fields are optional.

### Testing
Existing integration tests MUST pass with PaddleOCR-VL backend selected. Add new tests for:
- Backend auto-detection logic
- Server health monitoring and fallback
- PaddleOCR-VL specific output parsing (tables, charts, formulas)
- Batch processing performance
