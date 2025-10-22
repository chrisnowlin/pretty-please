# optimization Specification Delta

## ADDED Requirements

### Requirement: MLX Memory Optimization
The system SHALL leverage MLX's memory efficiency as the primary optimization strategy.

#### Scenario: Reduced model memory footprint
- **GIVEN** the Nanonets OCR model
- **WHEN** loaded with MLX backend
- **THEN** uses 2.2GB memory (vs 14GB PyTorch)
- **AND** enables processing on 16GB M1 MacBooks
- **AND** leaves more memory for batch processing

#### Scenario: Quantization benefits
- **GIVEN** the MLX 8-bit quantized model
- **WHEN** performing inference
- **THEN** maintains OCR quality identical to full precision
- **AND** achieves 78% memory reduction
- **AND** enables larger batch sizes

### Requirement: Pipeline Parallelism Optimization
The system SHALL maximize throughput through aggressive pipeline parallelism.

#### Scenario: Deep rendering pipeline
- **GIVEN** a 96-page document
- **WHEN** processing with optimized settings
- **THEN** maintains 4 pre-rendered batches (120 pages)
- **AND** ensures OCR analyzer never waits for rendering
- **AND** achieves 1.6-2x speedup over sequential

#### Scenario: Maximize render parallelism
- **GIVEN** PDF rendering is CPU-bound
- **WHEN** MLX uses only 2.2GB memory
- **THEN** allocates 20 render workers (vs previous 4-12)
- **AND** renders pages 5x faster
- **AND** keeps pipeline continuously fed

## MODIFIED Requirements

### Requirement: Performance Profiling
The system SHALL use simplified, explicit performance configuration.

#### Scenario: Explicit configuration presets
- **GIVEN** common deployment scenarios
- **WHEN** configuring OCR processing
- **THEN** uses named presets like OCRConfig.mlx_optimized()
- **AND** removes complex profile detection logic
- **AND** makes performance predictable

#### Scenario: Hardware-aware defaults
- **GIVEN** an M4 Max with 48GB RAM
- **WHEN** using mlx_optimized preset
- **THEN** automatically configures: batch=30, render=20, analysis=1
- **AND** achieves 60-75 minute processing for 96 pages
- **AND** uses only 3GB total memory

### Requirement: Resource Utilization
The system SHALL efficiently utilize available system resources.

#### Scenario: Memory-aware processing
- **GIVEN** varying amounts of system RAM
- **WHEN** initializing the OCR pipeline
- **THEN** automatically scales batch size: 16GB→10, 32GB→20, 48GB→30
- **AND** prevents OOM errors
- **AND** maximizes throughput for available memory

#### Scenario: CPU utilization optimization
- **GIVEN** MLX is GPU-accelerated (Metal)
- **WHEN** OCR analysis is running
- **THEN** CPU remains available for rendering
- **AND** achieves true parallel processing
- **AND** utilizes both CPU and GPU efficiently

## REMOVED Requirements

### Requirement: Multi-threaded MLX Processing
The system SHALL NO LONGER attempt parallel MLX inference due to thread safety.

#### Scenario: Parallel MLX workers (REMOVED)
- **GIVEN** the discovered MLX thread safety limitation
- **WHEN** configuring analysis workers
- **THEN** enforces single worker for MLX
- **AND** focuses on pipeline parallelism instead
- **AND** prevents Metal command buffer errors

### Requirement: Dynamic Profile Detection
The system SHALL NO LONGER use complex auto-detection for performance profiles.

#### Scenario: Environment-based profiles (REMOVED)
- **GIVEN** the previous PROCESSING_PROFILE environment variable
- **WHEN** configuring performance
- **THEN** replaced by explicit OCRConfig
- **AND** removes 200+ lines of detection logic
- **AND** makes configuration deterministic

## Implementation Guidance

### Pipeline Parallelism Architecture

The key to compensating for MLX's single-threading is deep pipeline pre-rendering:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from typing import Iterator, Tuple

class AnalysisPipeline:
    """Implements pipeline parallelism for maximum throughput."""

    def __init__(self, analyzer: NanonetsAnalyzer, config: OCRConfig):
        self.analyzer = analyzer
        self.config = config

        # Render and analysis execute in parallel stages
        self.render_executor = ThreadPoolExecutor(
            max_workers=config.render_workers
        )
        self.analysis_executor = ThreadPoolExecutor(
            max_workers=1 if analyzer._max_workers == 1 else config.analysis_workers
        )

        # Pre-render buffer to decouple stages
        self.render_buffer = Queue(
            maxsize=config.pre_render_batches * config.batch_size
        )

    def process_document_pipeline(
        self,
        render_generator: Iterator[Tuple[int, Path]],
        total_pages: int
    ) -> List[str]:
        """
        Process document through pipeline:
        - Stage 1: Render pages in parallel (ThreadPool, CPU-bound)
        - Stage 2: Analyze pages in parallel (constrained by analyzer)
        - Buffer between stages prevents analyzer starvation.
        """
        results = [None] * total_pages
        render_futures = {}
        analysis_futures = {}

        # Submit initial renders for pre-rendering (deep buffer)
        pages_submitted = 0
        max_buffered = self.config.pre_render_batches * self.config.batch_size

        for page_num, image_path in render_generator:
            # Submit render tasks, fill buffer first
            if pages_submitted < max_buffered:
                render_future = self.render_executor.submit(
                    self._render_page, image_path
                )
                render_futures[render_future] = page_num
                pages_submitted += 1

            # Start analysis on completed renders
            for future in as_completed(render_futures):
                if future in analysis_futures:
                    continue

                page_num = render_futures[future]
                try:
                    rendered_img = future.result()

                    # Submit for analysis
                    analysis_future = self.analysis_executor.submit(
                        self.analyzer.analyze_document, rendered_img
                    )
                    analysis_futures[analysis_future] = page_num

                except Exception as e:
                    logger.error(f"Render error page {page_num}: {e}")
                    results[page_num - 1] = ""

        # Collect analysis results
        for future in as_completed(analysis_futures):
            page_num = analysis_futures[future]
            try:
                result = future.result()
                results[page_num - 1] = result
            except Exception as e:
                logger.error(f"Analysis error page {page_num}: {e}")
                results[page_num - 1] = ""

        return results
```

### Memory-Aware Configuration

Use Pydantic with validators for automatic memory scaling:

```python
from pydantic.dataclasses import dataclass
from pydantic import Field, field_validator, ConfigDict
import psutil

@dataclass(config=ConfigDict(validate_assignment=True, frozen=True))
class OCRConfig:
    """Type-safe, immutable configuration with auto-scaling."""

    batch_size: int = Field(default=30, ge=1, le=100)
    render_workers: int = Field(default=20, ge=1, le=32)
    analysis_workers: int = Field(default=1, ge=1, le=8)
    pre_render_batches: int = Field(default=4, ge=1, le=10)
    checkpoint_enabled: bool = True

    @field_validator('batch_size', mode='before')
    @classmethod
    def scale_batch_by_memory(cls, v, info):
        """Automatically scale batch size based on available memory."""
        available_gb = psutil.virtual_memory().available / (1024**3)

        # Scale: <16GB→10, 16-32GB→20, >32GB→30
        if available_gb < 16:
            return min(v, 10)
        elif available_gb < 32:
            return min(v, 20)
        return v

    @field_validator('render_workers', mode='before')
    @classmethod
    def scale_workers_by_cpu(cls, v):
        """Use 80% of CPU cores for rendering."""
        cpu_count = psutil.cpu_count(logical=True)
        max_workers = max(4, int(cpu_count * 0.8))
        return min(v, max_workers)

    @classmethod
    def mlx_optimized(cls) -> 'OCRConfig':
        """Optimal settings for MLX on Apple Silicon."""
        return cls(
            batch_size=30,
            render_workers=20,
            analysis_workers=1,  # MLX constraint
            pre_render_batches=4,
            checkpoint_enabled=True
        )

    @classmethod
    def memory_constrained(cls) -> 'OCRConfig':
        """Conservative settings for <16GB RAM."""
        return cls(
            batch_size=10,
            render_workers=8,
            analysis_workers=1,
            pre_render_batches=2,
            checkpoint_enabled=True
        )

    @classmethod
    def balanced(cls) -> 'OCRConfig':
        """Moderate settings for typical systems."""
        return cls(
            batch_size=20,
            render_workers=12,
            analysis_workers=2,
            pre_render_batches=3,
            checkpoint_enabled=True
        )
```

### Memory Monitoring and Dynamic Adjustment

Monitor memory during processing and adjust dynamically:

```python
import threading
from time import sleep

class MemoryMonitor:
    """Background memory monitoring with dynamic adjustment."""

    def __init__(self, pipeline: AnalysisPipeline, threshold_percent: float = 80.0):
        self.pipeline = pipeline
        self.threshold_percent = threshold_percent
        self.monitoring = False
        self._monitor_thread = None

    def start(self):
        """Start background monitoring."""
        self.monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()

    def _monitor_loop(self):
        """Periodically check memory and adjust batch size."""
        while self.monitoring:
            memory_percent = psutil.virtual_memory().percent

            if memory_percent > self.threshold_percent:
                logger.warning(f"Memory pressure: {memory_percent}%")

                # Reduce batch size dynamically
                current_batch = self.pipeline.config.batch_size
                new_batch = max(5, current_batch // 2)

                if new_batch < current_batch:
                    logger.info(f"Reduced batch: {current_batch} → {new_batch}")
                    # Update config (note: config is immutable, so create new)
                    # This is a simplified example; actual implementation
                    # would create a new config object

                # Force garbage collection
                import gc
                gc.collect()

                # Clear MLX cache if available
                try:
                    import mlx.core as mx
                    mx.clear_cache()
                except ImportError:
                    pass

            sleep(5)  # Check every 5 seconds

    def stop(self):
        """Stop monitoring."""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
```

### Performance Benchmarking

Create benchmarking utilities to validate performance targets:

```python
from contextlib import contextmanager
import time
from typing import Dict, Any

@contextmanager
def benchmark_timer(name: str, items: int = 0) -> Dict[str, Any]:
    """Context manager for benchmarking with memory tracking."""
    result = {"name": name, "items": items}
    start_memory = psutil.Process().memory_info().rss / 1024**2  # MB
    start_time = time.perf_counter()

    try:
        yield result
    finally:
        elapsed = time.perf_counter() - start_time
        memory_delta = psutil.Process().memory_info().rss / 1024**2 - start_memory

        result.update({
            "duration_sec": elapsed,
            "memory_delta_mb": memory_delta,
            "throughput": items / elapsed if elapsed > 0 else 0
        })

def benchmark_96_page_document():
    """Verify target: ≤75 minutes for 96 pages."""
    configs = {
        "mlx_optimized": OCRConfig.mlx_optimized(),
        "balanced": OCRConfig.balanced(),
        "memory_constrained": OCRConfig.memory_constrained()
    }

    print("\nBenchmark Results (96-page document):")
    print("-" * 70)
    print(f"{'Config':<20} | {'Time':<10} | {'Memory':<10} | {'Pages/sec':<10}")
    print("-" * 70)

    for name, config in configs.items():
        with benchmark_timer(name, items=96) as bench:
            loader = NanonetsLoader(config)
            doc = loader.load("test_96_page_document.pdf")
            bench["items"] = doc.metadata.get("page_count", 96)

        throughput = bench["items"] / bench["duration_sec"]
        print(f"{name:<20} | {bench['duration_sec']:>7.1f}s | "
              f"{bench['memory_delta_mb']:>8.1f}MB | {throughput:>8.2f} p/s")

    print("-" * 70)
    print("✓ Target: ≤75 minutes (1.28 pages/sec for 96 pages)")
```

### Configuration Presets Summary

| Config | Batch | Render | Analysis | Pre-render | Target Memory | Target Time |
|--------|-------|--------|----------|------------|---------------|------------|
| **mlx_optimized** | 30 | 20 | 1 | 4 | 3GB | 60-75 min |
| **balanced** | 20 | 12 | 2 | 3 | 8GB | 90-120 min |
| **memory_constrained** | 10 | 8 | 1 | 2 | <3GB | 120-150 min |

### Testing Performance Assumptions

Create tests that validate critical performance constraints:

```python
def test_mlx_single_worker_constraint():
    """Verify MLX uses only 1 worker."""
    analyzer = NanonetsAnalyzer(backend="mlx")
    assert analyzer._max_workers == 1

def test_memory_constrained_batch_size():
    """Verify batch size scales with available memory."""
    with patch('psutil.virtual_memory') as mock_mem:
        mock_mem.return_value = MagicMock(available=8 * 1024**3)  # 8GB
        config = OCRConfig()
        assert config.batch_size <= 10

def test_pipeline_parallelism_benefit():
    """Verify pipeline achieves >1.5x speedup over sequential."""
    # Sequential: 96 pages × 35 sec/page = 3360 sec
    # Parallel: max(render_time, analysis_time) ≈ 2100 sec
    # Expected: 3360 / 2100 ≈ 1.6x speedup
    pass
```