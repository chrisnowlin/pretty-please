# ingestion Specification Delta

## MODIFIED Requirements

### Requirement: Document Loading
The system SHALL load documents using a streamlined, component-based architecture.

#### Scenario: Simplified loader initialization
- **GIVEN** a developer wants to process documents
- **WHEN** creating a NanonetsLoader with default settings
- **THEN** the loader automatically configures for MLX with optimal settings
- **AND** requires zero configuration for 80% of use cases
- **AND** provides clear logging of selected configuration

#### Scenario: Component separation in processing
- **GIVEN** a PowerPoint file for processing
- **WHEN** loading through the streamlined pipeline
- **THEN** DocumentRenderer handles PPT to image conversion
- **AND** AnalysisPipeline manages OCR analysis
- **AND** components can be tested and modified independently

### Requirement: Nanonets OCR Integration
The system SHALL prioritize MLX-based Nanonets OCR for all supported documents.

#### Scenario: MLX as default analyzer
- **GIVEN** a PDF document on Apple Silicon hardware
- **WHEN** processing without explicit analyzer selection
- **THEN** automatically uses NanonetsMLXAnalyzer
- **AND** loads 2.2GB model (vs 14GB PyTorch)
- **AND** maintains identical OCR quality

#### Scenario: Transparent fallback handling
- **GIVEN** a document on non-Apple hardware
- **WHEN** MLX is not available
- **THEN** transparently falls back to PyTorch analyzer
- **AND** uses same API and configuration
- **AND** logs the fallback for debugging

### Requirement: Batch Processing
The system SHALL use optimized batch sizes based on available resources.

#### Scenario: Automatic batch size optimization
- **GIVEN** a system with 48GB RAM
- **WHEN** processing documents with default config
- **THEN** automatically uses batch_size=30
- **AND** processes 30 pages before checkpointing
- **AND** maintains memory usage under 3GB for model

#### Scenario: Adaptive batch sizing
- **GIVEN** a system with limited memory
- **WHEN** memory pressure exceeds 80%
- **THEN** dynamically reduces batch size
- **AND** continues processing without OOM
- **AND** logs the adjustment for visibility

## REMOVED Requirements

### Requirement: Complex Profile System
The system SHALL NO LONGER use the multi-layered profile configuration system.

#### Scenario: Profile-based configuration (REMOVED)
- **GIVEN** the old profile system with environment variables
- **WHEN** configuring the loader
- **THEN** this approach is replaced by explicit OCRConfig
- **AND** removes confusion about precedence
- **AND** simplifies configuration to 5 parameters

### Requirement: Dual Analyzer Maintenance
The system SHALL NO LONGER maintain separate analyzer implementations with different APIs.

#### Scenario: Separate MLX and PyTorch analyzers (REMOVED)
- **GIVEN** the previous dual analyzer classes
- **WHEN** selecting an analyzer
- **THEN** replaced by unified NanonetsAnalyzer
- **AND** single API regardless of backend
- **AND** reduces maintenance burden by 50%

## Implementation Guidance

### Component Architecture

The streamlined loader uses three focused components:

```
NanonetsLoader (orchestrator, ~50 lines)
    ├── DocumentRenderer (rendering, ~150 lines)
    ├── AnalysisPipeline (analysis, ~200 lines)
    └── CheckpointManager (persistence, existing)
```

### 1. DocumentRenderer Component

Handles all document-to-image conversions with progressive rendering:

```python
class DocumentRenderer:
    """Converts documents to images with deep pipeline support."""

    def __init__(self, config: OCRConfig):
        self.config = config
        # Use ThreadPoolExecutor for I/O-bound rendering
        self.render_executor = ThreadPoolExecutor(
            max_workers=config.render_workers
        )

    def render_pdf_progressive(
        self,
        file_path: Path,
        batch_size: int = 30
    ) -> Iterator[Tuple[int, Path]]:
        """Render PDF progressively, yielding (page_num, image_path)."""
        import fitz  # PyMuPDF
        doc = fitz.open(str(file_path))

        for page_idx in range(doc.page_count):
            # Submit render task (non-blocking)
            future = self.render_executor.submit(
                self._render_single_page, doc, page_idx
            )
            # Yield as complete
            image_path = future.result()
            yield (page_idx + 1, image_path)

    def _render_single_page(self, doc, page_idx: int) -> Path:
        """Render single page to temporary PNG file."""
        page = doc.load_page(page_idx)
        pix = page.get_pixmap(dpi=150)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(pix.tobytes("png"))
            return Path(tmp.name)
```

### 2. AnalysisPipeline Component

Manages OCR workflow with pipeline parallelism:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

class AnalysisPipeline:
    """Coordinates rendering and OCR analysis."""

    def __init__(self, analyzer: NanonetsAnalyzer, config: OCRConfig):
        self.analyzer = analyzer
        self.config = config

        # Enforce MLX constraint if applicable
        if analyzer._max_workers == 1:
            self.max_workers = 1
            logger.info("Single-threaded analysis for MLX")
        else:
            self.max_workers = config.analysis_workers

    def process_batch(self, images: List[Path]) -> List[str]:
        """Process batch of images through analysis pipeline."""

        if self.max_workers == 1:
            # Sequential processing for MLX
            return [
                self.analyzer.analyze_document(img)
                for img in images
            ]
        else:
            # Parallel processing for PyTorch
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self.analyzer.analyze_document, img)
                    for img in images
                ]
                return [f.result() for f in as_completed(futures)]
```

### 3. NanonetsLoader Component

Simple orchestrator that ties components together:

```python
class NanonetsLoader(DocumentLoader):
    """Streamlined document loader using component architecture."""

    def __init__(self, config: Optional[OCRConfig] = None):
        """Initialize with auto-detection of optimal config."""
        # Auto-select config based on hardware
        if config is None:
            if self._is_apple_silicon():
                config = OCRConfig.mlx_optimized()
                logger.info("Auto-selected MLX-optimized config")
            else:
                config = OCRConfig.balanced()

        self.config = config

        # Initialize components
        self.analyzer = NanonetsAnalyzer()  # Auto-detects backend
        self.renderer = DocumentRenderer(config)
        self.pipeline = AnalysisPipeline(self.analyzer, config)

        if config.checkpoint_enabled:
            from .checkpoint import CheckpointManager
            self.checkpoint_manager = CheckpointManager()

    def load(self, file_path: Path) -> Document:
        """Load document through pipeline."""
        file_path = Path(file_path)

        if file_path.suffix.lower() == ".pdf":
            return self._load_pdf(file_path)
        elif file_path.suffix.lower() in [".pptx", ".ppt"]:
            return self._load_powerpoint(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_path.suffix}")

    def _load_pdf(self, file_path: Path) -> Document:
        """Load PDF with progressive rendering."""
        regions = []
        page_count = 0

        # Progressive rendering and analysis
        for page_num, image_path in self.renderer.render_pdf_progressive(
            file_path, self.config.batch_size
        ):
            try:
                # Analyze page
                markdown = self.analyzer.analyze_document(image_path)

                # Parse to regions
                from .markdown_parser import MarkdownParser
                parser = MarkdownParser()
                page_regions = parser.parse_markdown_to_regions(
                    markdown, page_num
                )
                regions.extend(page_regions)
                page_count = page_num

                # Checkpoint periodically
                if (self.checkpoint_manager and
                    page_num % self.config.batch_size == 0):
                    self.checkpoint_manager.save_checkpoint(
                        file_path, page_num, regions
                    )
            finally:
                # Clean up temp image
                image_path.unlink(missing_ok=True)

        return Document(
            content=self._regions_to_text(regions),
            source=str(file_path),
            metadata={"regions": regions, "page_count": page_count}
        )

    @staticmethod
    def _is_apple_silicon() -> bool:
        """Detect Apple Silicon hardware."""
        import platform
        return (platform.system() == "Darwin" and
                platform.machine() == "arm64")
```

### Configuration Auto-Detection

Automatically select optimal configuration based on hardware:

```python
def get_auto_config() -> OCRConfig:
    """Select config based on available resources."""
    import platform
    import psutil

    # Check hardware
    is_apple = (platform.system() == "Darwin" and
                platform.machine() == "arm64")
    available_gb = psutil.virtual_memory().available / (1024**3)

    if is_apple:
        # Try MLX first
        try:
            import mlx.core as mx
            if mx.metal.is_available():
                return OCRConfig.mlx_optimized()
        except ImportError:
            pass

    # Fall back based on memory
    if available_gb < 16:
        return OCRConfig.memory_constrained()
    elif available_gb < 32:
        return OCRConfig.balanced()
    else:
        return OCRConfig.mlx_optimized()
```

### Testing Component Isolation

Each component should be independently testable:

```python
def test_document_renderer():
    """Test rendering without analysis."""
    renderer = DocumentRenderer(OCRConfig.balanced())
    pages = list(renderer.render_pdf_progressive("test.pdf"))
    assert len(pages) > 0
    assert all(isinstance(p, tuple) and len(p) == 2 for p in pages)

def test_analysis_pipeline():
    """Test analysis without rendering."""
    analyzer = NanonetsAnalyzer(backend="cpu")  # Mock backend
    pipeline = AnalysisPipeline(analyzer, OCRConfig.balanced())
    # Results would be tested with mock images

def test_loader_integration():
    """Test full loader with real PDF."""
    loader = NanonetsLoader(OCRConfig.memory_constrained())
    doc = loader.load("test.pdf")
    assert doc.source == "test.pdf"
    assert len(doc.metadata["regions"]) > 0
```