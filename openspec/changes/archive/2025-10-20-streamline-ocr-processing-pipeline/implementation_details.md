# Enhanced Implementation Details

Based on research from MLX, Python concurrency, and configuration management best practices.

## 1. MLX Integration Details

### Key MLX Characteristics (from MLX documentation)

**Lazy Evaluation**: MLX uses lazy evaluation, meaning operations are not computed until needed:
```python
# From MLX docs - operations are built but not executed
c = a + b    # c not yet evaluated
mx.eval(c)   # evaluates c
```

**Thread Safety Limitation**: MLX models share internal Metal command buffers that are NOT thread-safe:
```python
# WRONG - Will cause Metal command buffer errors
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(mlx_model.generate, img) for img in images]

# CORRECT - Sequential processing for MLX
for img in images:
    result = mlx_model.generate(img)
```

**Unified Memory**: MLX arrays reside in unified memory accessible by both CPU and GPU:
```python
# Arrays can be processed on CPU or GPU without explicit transfers
mx.add(a, b, stream=mx.cpu)
mx.add(a, b, stream=mx.gpu)
```

### Implementing the Unified NanonetsAnalyzer

```python
import mlx.core as mx
from mlx_vlm import load, generate
from typing import Optional, Union, Literal
from functools import lru_cache
from dataclasses import dataclass

@dataclass
class AnalyzerConfig:
    """Configuration for the unified analyzer."""
    backend: Literal["auto", "mlx", "mps", "cuda", "cpu"] = "auto"
    max_tokens: int = 4096
    temperature: float = 0.0  # Deterministic for OCR
    model_path: str = "./models/nanonets-ocr2-3b-mlx"

class NanonetsAnalyzer:
    """Unified analyzer with automatic backend selection."""

    @staticmethod
    @lru_cache(maxsize=1)
    def _detect_best_backend() -> str:
        """Detect the best available backend, prioritizing MLX."""
        try:
            import mlx.core as mx
            # Check if MLX is available and Metal is supported
            if mx.metal.is_available():
                return "mlx"
        except ImportError:
            pass

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

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        self.config = config or AnalyzerConfig()

        if self.config.backend == "auto":
            self.config.backend = self._detect_best_backend()

        # Log the selected backend for transparency
        logger.info(f"NanonetsAnalyzer using backend: {self.config.backend}")

        # Initialize the appropriate implementation
        if self.config.backend == "mlx":
            self._impl = MLXAnalyzerImpl(self.config)
            # CRITICAL: Enforce single-threaded operation for MLX
            self._max_workers = 1
            logger.info("MLX backend selected - single-threaded operation enforced")
        else:
            self._impl = TorchAnalyzerImpl(self.config)
            self._max_workers = 4  # PyTorch can handle parallel processing

    def analyze_document(self, image_path: Union[str, Path], **kwargs):
        """Analyze a document image and return markdown."""
        return self._impl.analyze_document(image_path, **kwargs)
```

## 2. Pipeline Parallelism Implementation

### Using concurrent.futures for Pipeline Stages

Based on the Python documentation, we'll implement pipeline parallelism using `ThreadPoolExecutor` for I/O-bound rendering and careful coordination for MLX processing:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from threading import Lock
import asyncio
from typing import Iterator, Tuple

class AnalysisPipeline:
    """Manages the OCR analysis workflow with pipeline parallelism."""

    def __init__(self, analyzer: NanonetsAnalyzer, config: OCRConfig):
        self.analyzer = analyzer
        self.config = config

        # Determine max workers based on analyzer backend
        if hasattr(analyzer._impl, '__class__') and \
           analyzer._impl.__class__.__name__ == 'MLXAnalyzerImpl':
            self.max_analysis_workers = 1  # MLX constraint
            logger.info("MLX backend detected - using single analysis worker")
        else:
            self.max_analysis_workers = config.analysis_workers

        # Pre-render queue for pipeline depth
        self.render_queue = Queue(maxsize=config.pre_render_batches * config.batch_size)
        self.analysis_results = []
        self._lock = Lock()

    def process_batch(self, images: List[Path]) -> List[str]:
        """Process a batch of images through the pipeline."""

        # Stage 1: Render in parallel (I/O bound)
        with ThreadPoolExecutor(max_workers=self.config.render_workers) as render_executor:
            # Submit all rendering tasks
            render_futures = {
                render_executor.submit(self._render_page, img): i
                for i, img in enumerate(images)
            }

            # Stage 2: Analyze as renders complete
            if self.max_analysis_workers == 1:
                # Sequential processing for MLX
                results = [None] * len(images)
                for future in as_completed(render_futures):
                    idx = render_futures[future]
                    try:
                        rendered_img = future.result()
                        # Process immediately after render completes
                        result = self.analyzer.analyze_document(rendered_img)
                        results[idx] = result
                    except Exception as e:
                        logger.error(f"Pipeline error at index {idx}: {e}")
                        results[idx] = ""
                return results
            else:
                # Parallel processing for PyTorch
                with ThreadPoolExecutor(max_workers=self.max_analysis_workers) as analysis_executor:
                    analysis_futures = {}
                    results = [None] * len(images)

                    for future in as_completed(render_futures):
                        idx = render_futures[future]
                        rendered_img = future.result()
                        # Submit for parallel analysis
                        analysis_future = analysis_executor.submit(
                            self.analyzer.analyze_document, rendered_img
                        )
                        analysis_futures[analysis_future] = idx

                    # Collect analysis results
                    for future in as_completed(analysis_futures):
                        idx = analysis_futures[future]
                        results[idx] = future.result()

                    return results
```

### Deep Pipeline with Pre-rendering

```python
class DocumentRenderer:
    """Handles document to image conversion with deep pipeline."""

    def __init__(self, config: OCRConfig):
        self.config = config
        self.render_executor = ThreadPoolExecutor(max_workers=config.render_workers)

    def render_pdf_progressive_pipeline(
        self,
        file_path: Path,
        batch_size: int = 30
    ) -> Iterator[Tuple[int, Path]]:
        """
        Progressive rendering with deep pipeline for maximum throughput.
        Yields (page_number, image_path) tuples as they become available.
        """
        import fitz  # PyMuPDF
        doc = fitz.open(str(file_path))
        page_count = doc.page_count

        # Pre-render first N batches ahead of analysis
        pre_render_depth = self.config.pre_render_batches * batch_size
        render_buffer = Queue(maxsize=pre_render_depth)

        # Submit initial batch for rendering
        futures = []
        for page_idx in range(min(pre_render_depth, page_count)):
            future = self.render_executor.submit(self._render_single_page, doc, page_idx)
            futures.append((page_idx, future))

        # Yield rendered pages while submitting new ones
        next_to_render = pre_render_depth

        for page_idx, future in futures:
            # Get the rendered result
            try:
                image_path = future.result()
                yield (page_idx + 1, image_path)

                # Submit next page for rendering if available
                if next_to_render < page_count:
                    new_future = self.render_executor.submit(
                        self._render_single_page, doc, next_to_render
                    )
                    futures.append((next_to_render, new_future))
                    next_to_render += 1
            except Exception as e:
                logger.error(f"Render error for page {page_idx + 1}: {e}")
                raise
```

## 3. Configuration Management with Pydantic

### Using Pydantic for Type-Safe Configuration

Based on Pydantic best practices, we'll use dataclasses with validation:

```python
from pydantic import Field, field_validator, ConfigDict
from pydantic.dataclasses import dataclass
from typing import Optional
import psutil

@dataclass(config=ConfigDict(validate_assignment=True, frozen=True))
class OCRConfig:
    """Immutable, validated configuration for OCR processing."""

    # Core parameters (only 5 as promised)
    batch_size: int = Field(default=30, ge=1, le=100)
    render_workers: int = Field(default=20, ge=1, le=32)
    analysis_workers: int = Field(default=1, ge=1, le=8)
    pre_render_batches: int = Field(default=4, ge=1, le=10)
    checkpoint_enabled: bool = Field(default=True)

    # Computed fields
    max_memory_gb: Optional[float] = Field(default=None)

    @field_validator('batch_size', mode='before')
    @classmethod
    def adjust_batch_size_for_memory(cls, v, info):
        """Auto-adjust batch size based on available memory."""
        if 'max_memory_gb' not in info.data or info.data['max_memory_gb'] is None:
            available_gb = psutil.virtual_memory().available / (1024**3)

            if available_gb < 16:
                return min(v, 10)  # Conservative for low memory
            elif available_gb < 32:
                return min(v, 20)  # Moderate
            else:
                return v  # Use requested size
        return v

    @field_validator('render_workers', mode='before')
    @classmethod
    def adjust_render_workers_for_cpu(cls, v):
        """Scale render workers based on CPU cores."""
        cpu_count = psutil.cpu_count(logical=True)
        # Use 80% of available cores for rendering
        max_workers = max(4, int(cpu_count * 0.8))
        return min(v, max_workers)

    @classmethod
    def mlx_optimized(cls) -> 'OCRConfig':
        """Optimized configuration for MLX on Apple Silicon."""
        return cls(
            batch_size=30,
            render_workers=20,
            analysis_workers=1,  # MLX constraint
            pre_render_batches=4,
            checkpoint_enabled=True
        )

    @classmethod
    def memory_constrained(cls) -> 'OCRConfig':
        """Configuration for systems with limited memory (<16GB)."""
        return cls(
            batch_size=10,
            render_workers=8,
            analysis_workers=1,
            pre_render_batches=2,
            checkpoint_enabled=True
        )

    @classmethod
    def balanced(cls) -> 'OCRConfig':
        """Balanced configuration for typical systems."""
        return cls(
            batch_size=20,
            render_workers=12,
            analysis_workers=2,
            pre_render_batches=3,
            checkpoint_enabled=True
        )
```

## 4. Streamlined Loader Implementation

### Component-Based Architecture

```python
from typing import Optional, Dict, Any
import logging

class NanonetsLoader:
    """Streamlined document loader with clear separation of concerns."""

    def __init__(self, config: Optional[OCRConfig] = None):
        """Initialize with explicit configuration or smart defaults."""
        # Use MLX-optimized config by default on Apple Silicon
        if config is None:
            if self._is_apple_silicon():
                config = OCRConfig.mlx_optimized()
                logger.info("Auto-selected MLX-optimized configuration")
            else:
                config = OCRConfig.balanced()
                logger.info("Auto-selected balanced configuration")

        self.config = config

        # Initialize components
        self.analyzer = NanonetsAnalyzer()  # Auto-detects backend
        self.renderer = DocumentRenderer(config)
        self.pipeline = AnalysisPipeline(self.analyzer, config)

        if config.checkpoint_enabled:
            from .checkpoint import CheckpointManager
            self.checkpoint_manager = CheckpointManager()
        else:
            self.checkpoint_manager = None

        logger.info(f"NanonetsLoader initialized: {config}")

    @staticmethod
    def _is_apple_silicon() -> bool:
        """Detect if running on Apple Silicon."""
        import platform
        return platform.system() == "Darwin" and platform.machine() == "arm64"

    def load(self, file_path: Path) -> Document:
        """
        Load a document with streamlined processing.

        This is the main entry point - delegates to appropriate components.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type and process accordingly
        if file_path.suffix.lower() == ".pdf":
            return self._load_pdf(file_path)
        elif file_path.suffix.lower() in [".pptx", ".ppt"]:
            return self._load_powerpoint(file_path)
        elif file_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            return self._load_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

    def _load_pdf(self, file_path: Path) -> Document:
        """Load PDF with progressive rendering and pipeline processing."""
        regions = []

        # Use progressive pipeline rendering
        for page_num, image_path in self.renderer.render_pdf_progressive_pipeline(
            file_path, self.config.batch_size
        ):
            # Process through analyzer
            markdown = self.analyzer.analyze_document(image_path)

            # Parse to regions
            from .markdown_parser import MarkdownParser
            parser = MarkdownParser()
            page_regions = parser.parse_markdown_to_regions(markdown, page_num)
            regions.extend(page_regions)

            # Checkpoint if enabled
            if self.checkpoint_manager and page_num % self.config.batch_size == 0:
                self.checkpoint_manager.save_checkpoint(file_path, page_num, regions)

            # Clean up temporary image
            image_path.unlink(missing_ok=True)

        return Document(
            content=self._regions_to_text(regions),
            source=str(file_path),
            metadata={"regions": regions, "page_count": page_num}
        )
```

## 5. Memory Management Strategy

### Monitoring and Auto-Scaling

```python
import psutil
from threading import Thread
from time import sleep

class MemoryMonitor:
    """Monitor memory usage and adjust processing dynamically."""

    def __init__(self, threshold_percent: float = 80.0):
        self.threshold_percent = threshold_percent
        self.monitoring = False
        self._monitor_thread = None

    def start_monitoring(self, pipeline: AnalysisPipeline):
        """Start background memory monitoring."""
        self.monitoring = True
        self._monitor_thread = Thread(
            target=self._monitor_loop,
            args=(pipeline,),
            daemon=True
        )
        self._monitor_thread.start()

    def _monitor_loop(self, pipeline: AnalysisPipeline):
        """Background monitoring loop."""
        while self.monitoring:
            memory_percent = psutil.virtual_memory().percent

            if memory_percent > self.threshold_percent:
                logger.warning(f"Memory usage high: {memory_percent}%")

                # Reduce batch size dynamically
                if hasattr(pipeline.config, '_mutable_batch_size'):
                    old_size = pipeline.config._mutable_batch_size
                    new_size = max(5, old_size // 2)
                    pipeline.config._mutable_batch_size = new_size
                    logger.info(f"Reduced batch size: {old_size} -> {new_size}")

                # Force garbage collection
                import gc
                gc.collect()

                # If using MLX, clear caches
                try:
                    import mlx.core as mx
                    mx.clear_cache()
                except ImportError:
                    pass

            sleep(5)  # Check every 5 seconds
```

## 6. Error Handling and Fallback

### Graceful Degradation

```python
class FallbackAnalyzer:
    """Fallback analyzer when primary backends fail."""

    def __init__(self):
        self.backends = ["mlx", "mps", "cuda", "cpu"]
        self.current_backend = None

    def analyze_with_fallback(self, image_path: Path) -> str:
        """Try each backend until one succeeds."""
        errors = []

        for backend in self.backends:
            try:
                analyzer = NanonetsAnalyzer(
                    AnalyzerConfig(backend=backend)
                )
                result = analyzer.analyze_document(image_path)
                logger.info(f"Successfully processed with {backend}")
                return result
            except Exception as e:
                errors.append(f"{backend}: {e}")
                logger.warning(f"Backend {backend} failed: {e}")
                continue

        # All backends failed
        error_msg = "All backends failed:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
```

## 7. Testing Strategy Implementation

### Unit Tests with Mocking

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future

class TestUnifiedAnalyzer:
    """Test suite for the unified analyzer."""

    @patch('mlx.core.metal.is_available')
    def test_mlx_backend_selection(self, mock_metal):
        """Test that MLX is selected when available."""
        mock_metal.return_value = True

        analyzer = NanonetsAnalyzer()
        assert analyzer.config.backend == "mlx"
        assert analyzer._max_workers == 1  # Thread safety constraint

    @patch('torch.backends.mps.is_available')
    def test_mps_fallback(self, mock_mps):
        """Test fallback to MPS when MLX unavailable."""
        mock_mps.return_value = True

        with patch('mlx.core.metal.is_available', side_effect=ImportError):
            analyzer = NanonetsAnalyzer()
            assert analyzer.config.backend == "mps"
            assert analyzer._max_workers > 1  # Can parallelize

    def test_config_immutability(self):
        """Test that configuration is immutable."""
        config = OCRConfig.mlx_optimized()

        with pytest.raises(AttributeError):
            config.batch_size = 50  # Should fail - frozen dataclass

    @patch('psutil.virtual_memory')
    def test_memory_aware_batch_sizing(self, mock_memory):
        """Test automatic batch size adjustment."""
        # Simulate low memory
        mock_memory.return_value = MagicMock(available=8 * 1024**3)

        config = OCRConfig()
        assert config.batch_size <= 10  # Should be conservative
```

## 8. Performance Benchmarking

### Benchmark Suite

```python
import time
from contextlib import contextmanager
from typing import Dict, Any

@contextmanager
def benchmark_timer(name: str) -> Dict[str, Any]:
    """Context manager for benchmarking code sections."""
    result = {"name": name}
    start_memory = psutil.Process().memory_info().rss / 1024**2  # MB
    start_time = time.perf_counter()

    try:
        yield result
    finally:
        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss / 1024**2  # MB

        result.update({
            "duration_sec": end_time - start_time,
            "memory_delta_mb": end_memory - start_memory,
            "throughput": result.get("items", 0) / (end_time - start_time)
        })

def benchmark_pipeline():
    """Comprehensive pipeline benchmark."""
    test_doc = Path("test_data/96_page_document.pdf")

    configs = {
        "mlx_optimized": OCRConfig.mlx_optimized(),
        "balanced": OCRConfig.balanced(),
        "memory_constrained": OCRConfig.memory_constrained()
    }

    results = {}

    for name, config in configs.items():
        with benchmark_timer(name) as bench:
            loader = NanonetsLoader(config)
            doc = loader.load(test_doc)
            bench["items"] = doc.metadata.get("page_count", 0)

        results[name] = bench

    # Print comparison
    print("\nBenchmark Results:")
    print("-" * 60)
    for name, result in results.items():
        print(f"{name:20} | {result['duration_sec']:>8.2f}s | "
              f"{result['memory_delta_mb']:>8.1f}MB | "
              f"{result['throughput']:>6.2f} pages/sec")
```

## Key Implementation Insights

1. **MLX Thread Safety**: Must enforce single-threaded operation for MLX due to Metal command buffer limitations
2. **Pipeline Parallelism**: Compensates for MLX single-threading by maximizing render parallelism
3. **Memory Management**: Use psutil for dynamic memory monitoring and adjustment
4. **Configuration**: Pydantic dataclasses provide type safety and validation
5. **Fallback Strategy**: Graceful degradation through backend hierarchy
6. **Testing**: Mock MLX/PyTorch availability to test all code paths

This implementation achieves our goals of simplicity, performance, and maintainability while properly handling MLX's constraints.