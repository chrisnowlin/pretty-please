# ocr-engine Specification Delta

## ADDED Requirements

### Requirement: Unified OCR Analyzer Interface
The system SHALL provide a single unified analyzer interface that automatically selects the optimal backend.

#### Scenario: Automatic MLX selection on Apple Silicon
- **GIVEN** the system is running on Apple Silicon with MLX support
- **WHEN** creating a NanonetsAnalyzer with backend="auto"
- **THEN** the analyzer uses MLX backend for 2.2GB memory footprint
- **AND** logs the backend selection for transparency

#### Scenario: Fallback to PyTorch when MLX unavailable
- **GIVEN** the system is running on non-Apple hardware
- **WHEN** creating a NanonetsAnalyzer with backend="auto"
- **THEN** the analyzer falls back to PyTorch with appropriate device (CUDA/CPU)
- **AND** maintains identical API and output format

#### Scenario: Explicit backend selection
- **GIVEN** a user wants to force a specific backend
- **WHEN** creating NanonetsAnalyzer with backend="mps" or backend="cuda"
- **THEN** the analyzer uses the specified backend
- **AND** raises clear error if backend is unavailable

### Requirement: MLX Thread Safety Management
The system SHALL transparently handle MLX's single-threaded constraint.

#### Scenario: Automatic single-worker enforcement
- **GIVEN** the analyzer is using MLX backend
- **WHEN** processing multiple images
- **THEN** the system automatically uses sequential processing
- **AND** logs that parallel processing is disabled for thread safety
- **AND** achieves stable processing without Metal command buffer errors

#### Scenario: Parallel processing for non-MLX backends
- **GIVEN** the analyzer is using PyTorch backend
- **WHEN** processing multiple images with worker count > 1
- **THEN** the system uses parallel processing with specified workers
- **AND** achieves proportional speedup based on worker count

### Requirement: Optimized Pipeline Parallelism
The system SHALL implement pipeline parallelism to compensate for MLX single-threading.

#### Scenario: Deep pipeline pre-rendering
- **GIVEN** a 96-page PDF document
- **WHEN** processing with MLX backend
- **THEN** the system pre-renders 4 batches ahead (120 pages buffered)
- **AND** keeps the MLX analyzer continuously busy
- **AND** completes processing in ≤75 minutes

#### Scenario: Memory-bounded pre-rendering
- **GIVEN** a system with limited memory (16GB)
- **WHEN** processing large documents
- **THEN** the system automatically reduces pre-render depth
- **AND** maintains total memory usage under 80% of available RAM
- **AND** logs the adjusted settings

## MODIFIED Requirements

### Requirement: Document Processing Pipeline
The system SHALL process documents through a streamlined ingestion workflow.

#### Scenario: Component-based processing
- **GIVEN** a PDF document for ingestion
- **WHEN** processing through NanonetsLoader
- **THEN** DocumentRenderer converts pages to images
- **AND** AnalysisPipeline processes images through OCR
- **AND** CheckpointManager saves progress
- **AND** each component operates independently

### Requirement: Performance Configuration
The system SHALL provide simplified configuration with optimal defaults.

#### Scenario: Default MLX-optimized configuration
- **GIVEN** no explicit configuration provided
- **WHEN** creating a NanonetsLoader
- **THEN** uses OCRConfig.mlx_optimized() preset
- **AND** sets batch_size=30, render_workers=20, mlx_workers=1
- **AND** achieves ≤75 minute processing for 96 pages

#### Scenario: Memory-constrained configuration
- **GIVEN** a system with ≤16GB RAM
- **WHEN** creating NanonetsLoader with OCRConfig.memory_constrained()
- **THEN** uses reduced batch_size=10, render_workers=8
- **AND** maintains stable processing without OOM errors
- **AND** completes processing even if slower

## Implementation Guidance

### MLX Lazy Evaluation and Thread Safety

MLX uses lazy evaluation - operations are not computed until needed. This affects how we structure the unified analyzer:

```python
import mlx.core as mx
from mlx_vlm import load, generate

class NanonetsAnalyzer:
    """Unified analyzer with automatic backend selection."""

    @staticmethod
    def _detect_best_backend() -> str:
        """Detect best available backend, prioritizing MLX."""
        try:
            import mlx.core as mx
            if mx.metal.is_available():
                return "mlx"  # Highest priority
        except ImportError:
            pass

        # Fallback chain: MPS → CUDA → CPU
        try:
            import torch
            if torch.backends.mps.is_available():
                return "mps"
            elif torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        except ImportError:
            raise RuntimeError("Neither MLX nor PyTorch available")

    def __init__(self, backend: str = "auto"):
        if backend == "auto":
            backend = self._detect_best_backend()

        logger.info(f"NanonetsAnalyzer using backend: {backend}")

        if backend == "mlx":
            self._impl = MLXAnalyzerImpl()
            # CRITICAL: MLX is NOT thread-safe due to Metal command buffers
            self._max_workers = 1
            logger.info("MLX backend - enforcing single-threaded operation")
        else:
            self._impl = TorchAnalyzerImpl(device=backend)
            self._max_workers = 4  # Can parallelize for PyTorch
```

### Key MLX Constraint

MLX models share internal Metal command buffers that are **not thread-safe**. Attempting parallel inference causes:

```
[_MTLCommandBuffer addCompletedHandler:]:1011:
failed assertion 'Completed handler provided after commit call'
```

**Solution**: Enforce `_max_workers = 1` for MLX, compensate with pipeline parallelism (see optimization spec).

### Backend Implementation Template

Each backend adapter must follow this interface:

```python
class AnalyzerImpl(ABC):
    """Interface for analyzer implementations."""

    @abstractmethod
    def analyze_document(self, image_path: Union[str, Path], **kwargs) -> str:
        """Return markdown representation of document."""
        pass

class MLXAnalyzerImpl(AnalyzerImpl):
    """MLX-optimized implementation (2.2GB model)."""
    # Uses mlx_vlm with lazy evaluation

class TorchAnalyzerImpl(AnalyzerImpl):
    """PyTorch implementation (14GB model, parallelizable)."""
    # Uses PyTorch with device placement
```

### Backend Selection Caching

Use `functools.lru_cache` to avoid repeated backend detection:

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def _detect_best_backend() -> str:
    """Cache backend detection result."""
    # Detection logic here
```

### Fallback Strategy Implementation

Provide graceful degradation through backend hierarchy:

```python
class FallbackAnalyzer:
    """Try backends in order: MLX → MPS → CUDA → CPU."""

    def __init__(self):
        self.backends = ["mlx", "mps", "cuda", "cpu"]

    def analyze_with_fallback(self, image_path: Path) -> str:
        """Attempt analysis with each backend."""
        for backend in self.backends:
            try:
                analyzer = NanonetsAnalyzer(backend=backend)
                return analyzer.analyze_document(image_path)
            except Exception as e:
                logger.warning(f"Backend {backend} failed: {e}")
                continue

        raise RuntimeError(f"All backends failed for {image_path}")
```

### Automatic Device Selection Logic

The backend priority reflects performance and availability:

| Priority | Backend | Use Case | Memory |
|----------|---------|----------|--------|
| 1 | MLX | Apple Silicon with Metal | 2.2GB |
| 2 | MPS | Apple Silicon without MLX | 8-14GB |
| 3 | CUDA | NVIDIA GPU | 14GB |
| 4 | CPU | Generic fallback | 14GB |

### Configuration Validation

Use Pydantic for type-safe configuration:

```python
from pydantic.dataclasses import dataclass
from pydantic import Field, ConfigDict

@dataclass(config=ConfigDict(validate_assignment=True))
class AnalyzerConfig:
    """Configuration for unified analyzer."""
    backend: Literal["auto", "mlx", "mps", "cuda", "cpu"] = "auto"
    max_tokens: int = Field(default=4096, ge=1000, le=8192)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    model_path: str = "./models/nanonets-ocr2-3b-mlx"
```

### Testing Backend Selection

Mock MLX and PyTorch availability to test all code paths:

```python
@patch('mlx.core.metal.is_available')
def test_mlx_selection(mock_metal):
    """Test MLX is selected when available."""
    mock_metal.return_value = True
    analyzer = NanonetsAnalyzer(backend="auto")
    assert analyzer.config.backend == "mlx"
    assert analyzer._max_workers == 1

@patch('torch.backends.mps.is_available')
def test_mps_fallback(mock_mps):
    """Test fallback when MLX unavailable."""
    mock_mps.return_value = True
    with patch('mlx.core.metal.is_available', side_effect=ImportError):
        analyzer = NanonetsAnalyzer(backend="auto")
        assert analyzer.config.backend == "mps"
```