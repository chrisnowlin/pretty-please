# Design: PaddleOCR-VL Integration Architecture (Local Execution)

## Overview

This design document outlines the architectural approach for integrating PaddleOCR-VL as the primary OCR backend running **locally on M4 MacBook Pro** while maintaining backward compatibility with the existing Nanonets implementation.

## Current Architecture (Nanonets-OCR2-3B)

```
Document (PDF/PPT) → Image Rendering
                         ↓
                  NanonetsAnalyzer (Unified Interface)
                         ↓
            ┌────────────┴────────────┐
            ↓                         ↓
    NanonetsLayoutAnalyzer    (Future: Other Backends)
    (PyTorch: MPS/CUDA/CPU)
            ↓
    Transformers Model (3B params)
    [In-Process, ~6GB memory]
            ↓
    Structured Markdown Output
            ↓
    MarkdownParser
            ↓
    SemanticRegion Objects
            ↓
    Region-Based Processing Pipeline
            ↓
    Embeddings + ChromaDB Storage
```

**Key Characteristics**:
- Single backend (PyTorch transformers)
- In-process model inference on MPS (Apple Silicon)
- 3B parameter model (~6GB memory)
- 12+ language support

## Proposed Architecture (Multi-Backend with PaddleOCR-VL)

```
Document (PDF/PPT) → Image Rendering
                         ↓
                  NanonetsAnalyzer (Unified Interface)
                  [Backend Selection Logic]
                         ↓
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
PaddleOCRVLAnalyzer  NanonetsLayout  (Future: Others)
(PaddleOCR SDK)      (PyTorch MPS)
        ↓                ↓
PaddlePaddle Model   Transformers
(In-Process)         (In-Process)
  0.9B params          3B params
  ~2-3GB memory        ~6GB memory
  109 languages        12+ languages
  GPU/CPU execution    MPS/CPU execution
        ↓                ↓
    JSON/Markdown    Markdown
        ↓                ↓
        └────────────────┘
                ↓
        OutputAdapter
    (Normalize to SemanticRegion)
                ↓
        SemanticRegion Objects
                ↓
    Region-Based Processing Pipeline
                ↓
        Embeddings + ChromaDB Storage
```

**Key Improvements**:
- Multi-backend support (PaddleOCR-VL, Nanonets, extensible)
- **Local execution on M4 MacBook Pro** (no server infrastructure)
- Smaller default model (0.9B vs 3B → 3x memory reduction)
- Broader language coverage (109 vs 12+)
- PaddlePaddle framework with GPU acceleration support

## Hardware Environment

### M4 MacBook Pro Specifications
- **CPU**: Apple M4 (10-core CPU)
- **GPU**: Integrated 10-core GPU (Metal API)
- **Memory**: Unified memory architecture (16GB/24GB/32GB/48GB variants)
- **ML Acceleration**: Neural Engine (16-core)

### PaddlePaddle on Apple Silicon
PaddlePaddle supports GPU acceleration on Mac via:
- **CUDA**: Not available on Mac
- **GPU Mode**: Available via OpenCL/Metal backend on macOS
- **CPU Mode**: Fallback for compatibility

**Note**: PaddlePaddle 3.0+ has improved macOS support, but GPU acceleration may be limited compared to NVIDIA GPUs. We'll prioritize **CPU execution with optimizations** as the primary deployment mode.

## Component Design

### 1. PaddleOCRVLAnalyzer (Local SDK)

**Location**: `src/jina_rag_pipeline/ingestion/paddleocr_vl_analyzer.py`

**Responsibilities**:
- Initialize PaddleOCR-VL model locally via Python SDK
- Process document images in-process (no server calls)
- Parse JSON/markdown output into SemanticRegion objects
- Optimize for M4 CPU/GPU execution

**Interface**:
```python
class PaddleOCRVLAnalyzer:
    """
    PaddleOCR-VL adapter for local execution on M4 MacBook Pro.

    Uses PaddleOCR Python SDK for in-process inference.
    Supports GPU acceleration when available, CPU fallback.
    """

    def __init__(
        self,
        # Model configuration
        model_name: str = "PaddlePaddle/PaddleOCR-VL",
        use_gpu: bool = True,  # Try GPU, fallback to CPU
        # Quality settings
        enable_tables: bool = True,
        enable_equations: bool = True,
        enable_image_descriptions: bool = True,
        enable_charts: bool = True,
        # Output format
        output_format: Literal["json", "markdown"] = "json",
        # Performance tuning
        num_threads: int = 4,  # CPU threads for parallel processing
        enable_mkldnn: bool = True,  # Intel MKL-DNN acceleration
    ):
        """
        Initialize PaddleOCR-VL analyzer for local execution.

        Args:
            model_name: HuggingFace model ID for PaddleOCR-VL
            use_gpu: Attempt GPU acceleration (fallback to CPU if unavailable)
            enable_tables: Extract table structures
            enable_equations: Extract LaTeX formulas
            enable_image_descriptions: Generate chart/image descriptions
            enable_charts: Classify chart types
            output_format: "json" (structured) or "markdown" (readable)
            num_threads: CPU threads for inference (optimized for M4's 10 cores)
            enable_mkldnn: Enable MKL-DNN optimizations (Intel math library)
        """
        try:
            from paddleocr import PaddleOCRVL
        except ImportError:
            raise ImportError(
                "PaddleOCR not installed. Install with:\n"
                "  pip install 'paddleocr[doc-parser]'\n"
                "  pip install paddlepaddle-gpu==3.2.0 (or paddlepaddle==3.2.0 for CPU)"
            )

        self.output_format = output_format
        self.num_threads = num_threads

        # Initialize PaddleOCR pipeline
        logger.info("Initializing PaddleOCR-VL for local execution...")
        self.pipeline = PaddleOCRVL(
            use_gpu=use_gpu,
            enable_mkldnn=enable_mkldnn,
            cpu_threads=num_threads,
        )

        # Test GPU availability
        self._gpu_available = self._check_gpu_available()
        if use_gpu and not self._gpu_available:
            logger.warning(
                "GPU acceleration requested but not available. "
                "Falling back to CPU execution."
            )

        logger.info(
            f"PaddleOCR-VL initialized: "
            f"GPU={'enabled' if self._gpu_available else 'disabled'}, "
            f"CPU threads={num_threads}"
        )

    def _check_gpu_available(self) -> bool:
        """Check if GPU acceleration is actually available."""
        try:
            import paddle
            return paddle.device.is_compiled_with_cuda() or paddle.device.cuda.device_count() > 0
        except Exception:
            return False

    def analyze_document(self, file_path: Path, page_number: int = 1) -> str:
        """
        Analyze a single document page locally.

        Returns:
            JSON string with structured output (when output_format="json")
            or Markdown string (when output_format="markdown")
        """
        logger.debug(f"Analyzing document: {file_path}")

        # PaddleOCR processes image directly
        output = self.pipeline.predict(str(file_path))

        # Convert to requested format
        if self.output_format == "json":
            return output[0].to_json() if output else "{}"
        else:
            return output[0].to_markdown() if output else ""

    def extract_regions(
        self,
        file_path: Path,
        page_number: int = 1,
        document_id: Optional[str] = None,
    ) -> List[SemanticRegion]:
        """
        Extract semantic regions from document (primary interface).
        """
        # Get structured output
        output = self.analyze_document(file_path, page_number)

        # Parse to SemanticRegion objects
        if self.output_format == "json":
            regions = self._parse_json_output(output, page_number, document_id)
        else:
            regions = self._parse_markdown_output(output, page_number, document_id)

        return regions

    def analyze_documents_batch(
        self,
        file_paths: List[Path],
        page_numbers: Optional[List[int]] = None,
        batch_size: int = 1,
    ) -> List[str]:
        """
        Batch processing (sequential for local execution).

        Note: PaddleOCR Python SDK processes images sequentially.
        Batch size parameter kept for API compatibility but not used.
        """
        page_numbers = page_numbers or [1] * len(file_paths)
        return [
            self.analyze_document(fp, pn)
            for fp, pn in zip(file_paths, page_numbers)
        ]

    def _parse_json_output(
        self,
        json_str: str,
        page_number: int,
        document_id: Optional[str],
    ) -> List[SemanticRegion]:
        """
        Parse PaddleOCR-VL JSON output to SemanticRegion objects.

        PaddleOCR-VL JSON structure (expected):
        {
            "language": "en",
            "elements": [
                {"type": "text", "content": "...", "bbox": [...], "confidence": 0.98},
                {"type": "table", "content": "<table>...</table>", "structure": {...}},
                {"type": "formula", "latex": "E=mc^2", ...},
                {"type": "chart", "chart_type": "bar", "description": "..."}
            ]
        }
        """
        if not json_str or json_str == "{}":
            return []

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse PaddleOCR JSON output: {e}")
            return []

        regions = []
        detected_language = data.get("language", "unknown")
        elements = data.get("elements", [])

        for idx, element in enumerate(elements):
            element_type = element.get("type", "text")
            region_id = f"{document_id or 'unknown'}_page{page_number}_region{idx}"

            # Base region attributes
            region_kwargs = {
                "region_id": region_id,
                "region_type": self._map_element_type(element_type),
                "region_sequence": idx,
                "page_number": page_number,
                "content": element.get("content", ""),
                "raw_markdown": element.get("markdown", ""),
                "semantic_tags": [],
                "extraction_timestamp": datetime.now().isoformat(),
                "model": "paddleocr-vl-0.9b",
                "detected_language": detected_language,
                "confidence_score": element.get("confidence"),
                "bounding_box": tuple(element["bbox"]) if "bbox" in element else None,
            }

            # Type-specific attributes
            if element_type == "table":
                structure = element.get("structure", {})
                region_kwargs.update({
                    "table_html": element.get("content", ""),
                    "row_count": structure.get("rows"),
                    "column_count": structure.get("cols"),
                })

            elif element_type == "formula":
                region_kwargs.update({
                    "equation_latex": element.get("latex", element.get("content", "")),
                    "semantic_tags": ["latex", "formula"],
                })

            elif element_type == "chart":
                region_kwargs.update({
                    "image_description": element.get("description"),
                    "chart_type": element.get("chart_type", "chart"),
                    "semantic_tags": ["chart", element.get("chart_type", "unknown")],
                })

            regions.append(SemanticRegion(**region_kwargs))

        logger.debug(f"Parsed {len(regions)} regions from PaddleOCR output")
        return regions

    def _map_element_type(self, paddleocr_type: str) -> str:
        """Map PaddleOCR-VL element types to SemanticRegion types."""
        mapping = {
            "text": "text",
            "title": "title",
            "table": "table",
            "formula": "equation",
            "chart": "image",
            "figure": "image",
            "list": "list",
        }
        return mapping.get(paddleocr_type, "text")

    def _parse_markdown_output(
        self,
        markdown_str: str,
        page_number: int,
        document_id: Optional[str],
    ) -> List[SemanticRegion]:
        """
        Parse PaddleOCR-VL markdown output to SemanticRegion objects.

        Fallback to existing MarkdownParser if needed.
        """
        from .markdown_parser import MarkdownParser
        parser = MarkdownParser()
        return parser.parse_to_regions(
            markdown_str,
            document_id=document_id or "unknown",
            page_number=page_number,
        )
```

### 2. Backend Selection (Extended)

**Location**: `src/jina_rag_pipeline/ingestion/nanonets_unified.py`

**Updated Detection Logic**:
```python
@lru_cache(maxsize=1)
def detect_best_backend() -> str:
    """
    Auto-detect best OCR backend for M4 MacBook Pro.

    Priority (local execution only):
    1. PaddleOCR-VL (if installed and working)
    2. Nanonets-PyTorch with MPS (Apple Silicon acceleration)
    3. Nanonets-PyTorch with CPU (fallback)
    """
    import os

    # Check for explicit override
    backend_override = os.getenv("OCR_BACKEND")
    if backend_override:
        logger.info(f"Backend detection: Using override OCR_BACKEND={backend_override}")
        return backend_override

    # Try PaddleOCR-VL first (preferred for 109 languages + SOTA quality)
    try:
        from paddleocr import PaddleOCRVL
        # Quick validation that it can initialize
        logger.info("Backend detection: PaddleOCR-VL available")
        return "paddleocr-vl"
    except ImportError:
        logger.debug("Backend detection: PaddleOCR-VL not installed")
    except Exception as e:
        logger.warning(f"Backend detection: PaddleOCR-VL import failed: {e}")

    # Fall back to Nanonets with hardware acceleration
    try:
        import torch
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            logger.info("Backend detection: Nanonets MPS available")
            return "nanonets-mps"
        logger.info("Backend detection: Nanonets CPU fallback")
        return "nanonets-cpu"
    except Exception:
        logger.info("Backend detection: Nanonets CPU (torch unavailable)")
        return "nanonets-cpu"
```

### 3. Installation and Dependencies

**PaddlePaddle Installation for M4 MacBook Pro**:

```bash
# Option 1: CPU-only (recommended for stability)
pip install paddlepaddle==3.2.0

# Option 2: GPU support (experimental on macOS)
# Note: GPU support on macOS is limited, CPU may be faster
pip install paddlepaddle-gpu==3.2.0

# Install PaddleOCR with document parser
pip install 'paddleocr[doc-parser]'

# Verify installation
python -c "from paddleocr import PaddleOCRVL; print('PaddleOCR-VL ready')"
```

**Updated pyproject.toml**:
```toml
[project]
dependencies = [
    # ... existing dependencies ...

    # OCR backends (user chooses one or both)
    # Nanonets (current default)
    "transformers>=4.52.0",
    "torch>=2.6.0",

    # PaddleOCR-VL (optional, recommended)
    # Uncomment to enable:
    # "paddlepaddle>=3.2.0",
    # "paddleocr[doc-parser]",
]

[project.optional-dependencies]
# PaddleOCR-VL backend
paddleocr = [
    "paddlepaddle>=3.2.0",
    "paddleocr[doc-parser]",
]
```

**Installation Instructions**:
```bash
# Install with PaddleOCR-VL support
pip install -e ".[paddleocr]"

# Or install PaddleOCR separately
pip install paddlepaddle==3.2.0
pip install 'paddleocr[doc-parser]'
```

## Performance Considerations

### Memory Usage (M4 MacBook Pro)

| Component | Nanonets (Current) | PaddleOCR-VL (Proposed) | Improvement |
|-----------|-------------------|-------------------------|-------------|
| Model Size | 3B params | 0.9B params | 3.3x smaller |
| Memory Footprint | ~6GB | ~2-3GB | 2-3x reduction |
| Concurrent Capacity | 1-2 docs | 3-5 docs | 2-3x more |
| Peak Memory (Full Pipeline) | ~14GB | ~10GB | 30% reduction |

**M4 Memory Allocation** (assuming 32GB total):
- System: ~4GB
- Chrome/Apps: ~8GB
- PaddleOCR-VL: ~2-3GB
- Embeddings (Jina): ~2GB
- LLM (Qwen3-14B-4bit): ~8GB
- ChromaDB: ~2GB
- **Remaining**: ~6GB buffer

### Processing Speed (Estimated)

| Scenario | Nanonets (MPS) | PaddleOCR-VL (CPU) | PaddleOCR-VL (GPU) |
|----------|----------------|--------------------|--------------------|
| Single page | 4-6 sec | 5-8 sec | 3-5 sec |
| 10-page document | 50 sec | 60 sec | 40 sec |
| 100-page book | 500 sec | 600 sec | 400 sec |

**Note**: PaddleOCR-VL CPU performance may be comparable to Nanonets MPS since PaddlePaddle is highly optimized for CPU execution. GPU acceleration on macOS is experimental.

### Optimization Strategies

1. **CPU Threading**: Leverage M4's 10 cores with `cpu_threads=8`
2. **MKL-DNN**: Enable Intel Math Kernel Library optimizations
3. **Memory Pooling**: Reuse memory allocations across pages
4. **Pipeline Parallelism**: Maintain existing rendering parallelism (20 workers)

## Migration Strategy

### Phase 1: Local Installation (Week 1)
1. Install PaddlePaddle and PaddleOCR on M4 MacBook Pro
2. Test with sample documents, validate output format
3. Benchmark performance vs. Nanonets baseline
4. Document any installation issues or limitations

### Phase 2: Adapter Implementation (Week 2)
1. Create `PaddleOCRVLAnalyzer` for local SDK
2. Implement JSON parsing to SemanticRegion
3. Add backend detection logic
4. Write unit tests

### Phase 3: Integration & Testing (Week 3)
1. Integrate with existing pipeline
2. Run quality validation tests
3. Performance benchmarking
4. Edge case testing

### Phase 4: Production Readiness (Week 4)
1. Documentation and configuration guide
2. Update README with installation instructions
3. Create migration guide for existing users
4. Performance tuning and optimization

## Testing Strategy

### Unit Tests
- `test_paddleocr_vl_analyzer.py`: Model initialization, inference, parsing
- `test_backend_selection.py`: Auto-detection logic, fallback behavior
- `test_json_parsing.py`: Element parsing for all types

### Integration Tests
- `test_end_to_end_local.py`: Full pipeline on M4 MacBook Pro
- `test_memory_usage.py`: Validate memory footprint under load
- `test_quality_comparison.py`: Compare Nanonets vs PaddleOCR-VL output

### Performance Tests
- `benchmark_local_inference.py`: Processing speed on M4
- `benchmark_memory_footprint.py`: Memory usage under load
- `benchmark_concurrent_processing.py`: Multiple documents simultaneously

## Risk Mitigation

### Risk 1: PaddlePaddle Installation Issues
**Impact**: Users can't install or run PaddleOCR-VL
**Mitigation**:
- Provide detailed installation guide for macOS
- Test on clean M4 MacBook Pro environment
- Keep Nanonets as default fallback
- Document common installation errors

### Risk 2: Performance Slower Than Expected
**Impact**: Processing takes longer than Nanonets
**Mitigation**:
- Early benchmarking (Week 1)
- CPU threading optimization
- Accept slight slowdown for quality gains (109 languages, SOTA benchmarks)
- Make backend selection configurable

### Risk 3: GPU Acceleration Not Working
**Impact**: Can't leverage M4 GPU for speedup
**Mitigation**:
- Default to CPU execution (PaddlePaddle is CPU-optimized)
- CPU performance may be acceptable given smaller model size
- Monitor PaddlePaddle macOS GPU support improvements

### Risk 4: Model Download Size
**Impact**: Large model download on first use
**Mitigation**:
- PaddleOCR-VL is ~2-3GB (smaller than Nanonets 6GB)
- Cache model in ~/.paddleocr/
- Document download process and size

## Success Metrics

### Performance Metrics
- ✅ Model memory ≤ 3GB (vs 6GB baseline)
- ✅ Processing speed within 1.5x of Nanonets
- ✅ Full pipeline memory ≤ 12GB total

### Quality Metrics
- ✅ Table extraction accuracy ≥ 95%
- ✅ Formula recognition accuracy ≥ 90%
- ✅ Chart classification accuracy ≥ 85%
- ✅ Language detection accuracy ≥ 95% (109 languages)

### Operational Metrics
- ✅ Installation success rate ≥ 95% on M4 Macs
- ✅ Auto-detection selects PaddleOCR-VL when available
- ✅ Graceful fallback to Nanonets if PaddleOCR unavailable

## Future Enhancements

1. **Quantization**: Explore model quantization for further memory reduction
2. **Model Caching**: Optimize model loading time (lazy initialization)
3. **Parallel Processing**: Multi-threaded page processing when memory allows
4. **Custom Presets**: Educational-specific optimization profiles
5. **GPU Optimization**: Monitor PaddlePaddle macOS GPU improvements
