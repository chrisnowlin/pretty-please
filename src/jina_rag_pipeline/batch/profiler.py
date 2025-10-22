"""Performance profiling tools for batch processing optimization."""

import time
import psutil
import platform
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProfileResult:
    """Result from a profiling session."""
    
    name: str
    duration: float
    memory_start: float
    memory_peak: float
    memory_end: float
    throughput: Optional[float] = None
    items_processed: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def memory_used(self) -> float:
        """Memory used during operation."""
        return self.memory_peak - self.memory_start
        
    def __str__(self) -> str:
        """String representation."""
        parts = [
            f"Profile: {self.name}",
            f"Duration: {self.duration:.2f}s",
            f"Memory: {self.memory_used:.1f}MB",
        ]
        if self.throughput:
            parts.append(f"Throughput: {self.throughput:.1f} items/s")
        return " | ".join(parts)


class BatchProfiler:
    """Profiler for batch processing performance analysis."""
    
    def __init__(self):
        """Initialize profiler."""
        self.results: List[ProfileResult] = []
        self._current_profile: Optional[Dict[str, Any]] = None
        
    @contextmanager
    def profile(self, name: str, items_count: Optional[int] = None):
        """Context manager for profiling a code block.
        
        Args:
            name: Name of the operation being profiled
            items_count: Number of items being processed
            
        Yields:
            ProfileResult object (can be modified during execution)
        """
        process = psutil.Process()
        
        # Start profiling
        start_time = time.time()
        memory_start = process.memory_info().rss / (1024 * 1024)  # MB
        memory_peak = memory_start
        
        result = ProfileResult(
            name=name,
            duration=0,
            memory_start=memory_start,
            memory_peak=memory_peak,
            memory_end=memory_start,
            items_processed=items_count
        )
        
        try:
            yield result
            
            # Track peak memory during execution
            memory_current = process.memory_info().rss / (1024 * 1024)
            memory_peak = max(memory_peak, memory_current)
            
        finally:
            # Finish profiling
            end_time = time.time()
            memory_end = process.memory_info().rss / (1024 * 1024)
            
            result.duration = end_time - start_time
            result.memory_peak = memory_peak
            result.memory_end = memory_end
            
            if result.items_processed and result.duration > 0:
                result.throughput = result.items_processed / result.duration
                
            self.results.append(result)
            logger.info(str(result))
            
    def profile_function(
        self,
        func: Callable,
        *args,
        name: Optional[str] = None,
        items_count: Optional[int] = None,
        **kwargs
    ) -> Any:
        """Profile a function call.
        
        Args:
            func: Function to profile
            *args: Function arguments
            name: Name for the profile (defaults to function name)
            items_count: Number of items being processed
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        profile_name = name or func.__name__
        
        with self.profile(profile_name, items_count):
            return func(*args, **kwargs)
            
    def compare_approaches(
        self,
        approaches: Dict[str, Callable],
        test_data: Any,
        iterations: int = 3
    ) -> Dict[str, Dict[str, float]]:
        """Compare performance of different approaches.
        
        Args:
            approaches: Dictionary of approach name to function
            test_data: Data to test with
            iterations: Number of iterations per approach
            
        Returns:
            Comparison results
        """
        results = {}
        
        for name, func in approaches.items():
            approach_results = []
            
            for i in range(iterations):
                profile_name = f"{name}_iter_{i+1}"
                
                with self.profile(profile_name) as prof:
                    func(test_data)
                    approach_results.append(prof)
                    
            # Calculate averages
            avg_duration = sum(r.duration for r in approach_results) / iterations
            avg_memory = sum(r.memory_used for r in approach_results) / iterations
            
            results[name] = {
                "avg_duration": avg_duration,
                "avg_memory_mb": avg_memory,
                "iterations": iterations
            }
            
        return results
        
    def get_bottlenecks(self, top_n: int = 5) -> List[ProfileResult]:
        """Identify performance bottlenecks.
        
        Args:
            top_n: Number of top bottlenecks to return
            
        Returns:
            List of slowest operations
        """
        sorted_results = sorted(self.results, key=lambda x: x.duration, reverse=True)
        return sorted_results[:top_n]
        
    def get_memory_intensive(self, top_n: int = 5) -> List[ProfileResult]:
        """Identify memory-intensive operations.
        
        Args:
            top_n: Number of top memory users to return
            
        Returns:
            List of most memory-intensive operations
        """
        sorted_results = sorted(self.results, key=lambda x: x.memory_used, reverse=True)
        return sorted_results[:top_n]
        
    def generate_report(self) -> str:
        """Generate a performance report.
        
        Returns:
            Formatted report string
        """
        if not self.results:
            return "No profiling results available"
            
        lines = [
            "=" * 60,
            "Performance Profiling Report",
            "=" * 60,
            f"Total operations profiled: {len(self.results)}",
            ""
        ]
        
        # Overall statistics
        total_duration = sum(r.duration for r in self.results)
        total_memory = sum(r.memory_used for r in self.results)
        
        lines.extend([
            "Overall Statistics:",
            f"  Total duration: {total_duration:.2f}s",
            f"  Total memory used: {total_memory:.1f}MB",
            f"  Average duration: {total_duration/len(self.results):.2f}s",
            f"  Average memory: {total_memory/len(self.results):.1f}MB",
            ""
        ])
        
        # Top bottlenecks
        lines.append("Top 5 Bottlenecks (by duration):")
        for i, result in enumerate(self.get_bottlenecks(5), 1):
            lines.append(f"  {i}. {result}")
            
        lines.append("")
        
        # Top memory users
        lines.append("Top 5 Memory Users:")
        for i, result in enumerate(self.get_memory_intensive(5), 1):
            lines.append(f"  {i}. {result.name}: {result.memory_used:.1f}MB")
            
        # System info
        lines.extend([
            "",
            "System Information:",
            f"  Platform: {platform.system()} {platform.machine()}",
            f"  CPU count: {psutil.cpu_count()}",
            f"  Total RAM: {psutil.virtual_memory().total / (1024**3):.1f}GB",
        ])
        
        if platform.system() == "Darwin" and platform.processor() == "arm":
            lines.append("  Hardware: Apple Silicon (optimized for M4 Max)")
            
        lines.append("=" * 60)
        
        return "\n".join(lines)
        
    def clear(self):
        """Clear all profiling results."""
        self.results.clear()
        
    def export_results(self, format: str = "json") -> str:
        """Export profiling results.
        
        Args:
            format: Export format ("json" or "csv")
            
        Returns:
            Exported data as string
        """
        if format == "json":
            import json
            data = [
                {
                    "name": r.name,
                    "duration": r.duration,
                    "memory_used": r.memory_used,
                    "throughput": r.throughput,
                    "items_processed": r.items_processed
                }
                for r in self.results
            ]
            return json.dumps(data, indent=2)
            
        elif format == "csv":
            lines = ["name,duration,memory_used,throughput,items_processed"]
            for r in self.results:
                lines.append(
                    f"{r.name},{r.duration:.2f},{r.memory_used:.1f},"
                    f"{r.throughput or ''},{r.items_processed or ''}"
                )
            return "\n".join(lines)
            
        else:
            raise ValueError(f"Unsupported format: {format}")


def benchmark_batch_sizes(
    process_func: Callable,
    data: List[Any],
    batch_sizes: List[int],
    profiler: Optional[BatchProfiler] = None
) -> Dict[int, float]:
    """Benchmark different batch sizes to find optimal.
    
    Args:
        process_func: Function to process a batch
        data: Data to process
        batch_sizes: List of batch sizes to test
        profiler: Optional profiler instance
        
    Returns:
        Dictionary of batch size to throughput
    """
    if profiler is None:
        profiler = BatchProfiler()
        
    results = {}
    
    for batch_size in batch_sizes:
        # Process data in batches
        batches = [data[i:i+batch_size] for i in range(0, len(data), batch_size)]
        
        with profiler.profile(f"batch_size_{batch_size}", len(data)) as prof:
            for batch in batches:
                process_func(batch)
                
        results[batch_size] = prof.throughput or 0
        
    return results