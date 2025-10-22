"""Tests for batch processing module."""

import time
import tempfile
import json
from pathlib import Path
from typing import List

import pytest
import psutil

from src.jina_rag_pipeline.batch import (
    BatchManager,
    MemoryMonitor,
    ParallelProcessor,
    StreamingPipeline,
    BatchProfiler,
)
from src.jina_rag_pipeline.batch.memory import MemoryConfig


class TestMemoryMonitor:
    """Test memory monitoring functionality."""
    
    def test_memory_detection(self):
        """Test memory detection and stats."""
        monitor = MemoryMonitor()
        
        stats = monitor.get_memory_stats()
        assert "total_gb" in stats
        assert "available_gb" in stats
        assert "used_gb" in stats
        assert stats["total_gb"] > 0
        assert stats["available_gb"] > 0
        
    def test_batch_size_calculation(self):
        """Test optimal batch size calculation."""
        monitor = MemoryMonitor()
        
        # Test with different item sizes
        batch_size_small = monitor.calculate_optimal_batch_size(item_size_mb=10)
        batch_size_large = monitor.calculate_optimal_batch_size(item_size_mb=100)
        
        assert batch_size_small > batch_size_large
        assert batch_size_small >= 1
        assert batch_size_large >= 1
        
    def test_memory_pressure_detection(self):
        """Test memory pressure detection."""
        monitor = MemoryMonitor()
        
        under_pressure, message = monitor.check_memory_pressure()
        assert isinstance(under_pressure, bool)
        assert isinstance(message, str)
        

class TestBatchManager:
    """Test batch processing manager."""
    
    def test_basic_batch_processing(self):
        """Test basic batch processing."""
        manager = BatchManager()
        
        # Test data
        items = list(range(100))
        
        def process_batch(batch):
            return [x * 2 for x in batch]
            
        # Process batches
        results = []
        for batch_result in manager.process_batches(items, process_batch):
            results.extend(batch_result)
            
        assert len(results) == 100
        assert results[0] == 0
        assert results[50] == 100
        
    def test_adaptive_batch_sizing(self):
        """Test adaptive batch size adjustment."""
        manager = BatchManager()
        manager.config.adaptive_sizing = True
        manager.config.auto_adjust_interval = 2
        
        items = list(range(200))
        
        def process_batch(batch):
            # Simulate varying processing time
            time.sleep(0.001 * len(batch))
            return batch
            
        initial_size = manager.current_batch_size
        
        # Process with adaptive sizing
        list(manager.process_batches(items, process_batch))
        
        # Batch size might have changed
        assert manager.current_batch_size > 0
        
    def test_progress_callback(self):
        """Test progress tracking."""
        manager = BatchManager()
        
        items = list(range(50))
        progress_updates = []
        
        def track_progress(processed, total, time_remaining=None):
            progress_updates.append((processed, total))
            
        def process_batch(batch):
            return batch
            
        list(manager.process_batches(
            items, 
            process_batch,
            total_items=50,
            progress_callback=track_progress
        ))
        
        assert len(progress_updates) > 0
        assert progress_updates[-1][0] == 50
        

class TestParallelProcessor:
    """Test parallel processing functionality."""
    
    def test_parallel_map(self):
        """Test parallel mapping."""
        processor = ParallelProcessor(max_workers=2, use_processes=False)
        
        def square(x):
            return x * x
            
        items = list(range(10))
        results = processor.map(square, items)
        
        assert len(results) == 10
        assert results[0] == 0
        assert results[3] == 9
        assert results[9] == 81
        
    def test_batch_parallel_processing(self):
        """Test batch parallel processing."""
        processor = ParallelProcessor(max_workers=2, use_processes=False)
        
        def process_batch(batch):
            return [x * 2 for x in batch]
            
        items = list(range(100))
        results = processor.map_batches(process_batch, items, batch_size=20)
        
        assert len(results) == 100
        assert results[0] == 0
        assert results[50] == 100
        
    def test_io_parallel(self):
        """Test I/O parallel processing."""
        processor = ParallelProcessor()
        
        def simulate_io(x):
            time.sleep(0.001)  # Simulate I/O delay
            return x * 2
            
        items = list(range(20))
        results = processor.parallel_io(simulate_io, items)
        
        assert len(results) == 20
        assert results[10] == 20
        
    def test_optimal_workers_detection(self):
        """Test optimal worker count detection."""
        cpu_workers = ParallelProcessor.get_optimal_workers("cpu")
        io_workers = ParallelProcessor.get_optimal_workers("io")
        
        assert cpu_workers > 0
        assert io_workers >= cpu_workers
        

class TestStreamingPipeline:
    """Test streaming pipeline functionality."""
    
    def test_basic_streaming(self):
        """Test basic streaming processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = StreamingPipeline(checkpoint_dir=tmpdir)
            
            items = list(range(20))
            
            def process(x):
                return x * 2
                
            results = list(pipeline.stream_process(items, process))
            
            assert len(results) == 20
            assert results[0] == 0
            assert results[10] == 20
            
    def test_checkpoint_resume(self):
        """Test checkpoint and resume functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = StreamingPipeline(
                checkpoint_dir=tmpdir,
                checkpoint_interval=5
            )
            
            items = list(range(20))
            processed = []
            
            def process(x):
                if x == 8:  # Simulate failure
                    raise ValueError("Simulated error")
                return x * 2
                
            def get_id(x):
                return str(x)
                
            # First attempt - will fail at item 8
            try:
                for result in pipeline.stream_process(
                    items, process, "test", get_id
                ):
                    processed.append(result)
            except ValueError:
                pass
                
            assert len(processed) < 20
            
            # Resume from checkpoint
            pipeline2 = StreamingPipeline(checkpoint_dir=tmpdir)
            
            def process_safe(x):
                return x * 2
                
            resumed = list(pipeline2.stream_process(
                items, process_safe, "test", get_id, resume=True
            ))
            
            # Should have processed remaining items
            assert len(resumed) > 0
            
    def test_batch_streaming(self):
        """Test batch streaming processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = StreamingPipeline(checkpoint_dir=tmpdir)
            
            items = list(range(50))
            
            def process_batch(batch):
                return [x * 2 for x in batch]
                
            results = []
            for batch_result in pipeline.batch_stream_process(
                items, process_batch, batch_size=10
            ):
                results.extend(batch_result)
                
            assert len(results) == 50
            assert results[25] == 50
            
    def test_checkpoint_management(self):
        """Test checkpoint management."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = StreamingPipeline(checkpoint_dir=tmpdir)
            
            # Create a checkpoint
            items = list(range(10))
            list(pipeline.stream_process(items, lambda x: x))
            
            # Check checkpoint info
            info = pipeline.get_checkpoint_info("default")
            assert info is not None
            assert info["total_processed"] == 10
            
            # Clear checkpoint
            pipeline.clear_checkpoint("default")
            info = pipeline.get_checkpoint_info("default")
            assert info is None
            

class TestBatchProfiler:
    """Test performance profiling."""
    
    def test_basic_profiling(self):
        """Test basic profiling functionality."""
        profiler = BatchProfiler()
        
        with profiler.profile("test_operation", items_count=100) as prof:
            time.sleep(0.01)
            prof.metadata["test"] = "value"
            
        assert len(profiler.results) == 1
        result = profiler.results[0]
        assert result.name == "test_operation"
        assert result.duration >= 0.01
        assert result.items_processed == 100
        assert result.throughput is not None
        
    def test_function_profiling(self):
        """Test function profiling."""
        profiler = BatchProfiler()
        
        def slow_function(n):
            time.sleep(0.01)
            return n * 2
            
        result = profiler.profile_function(
            slow_function, 5, 
            name="slow_op",
            items_count=1
        )
        
        assert result == 10
        assert len(profiler.results) == 1
        
    def test_comparison(self):
        """Test approach comparison."""
        profiler = BatchProfiler()
        
        def approach1(data):
            return [x * 2 for x in data]
            
        def approach2(data):
            result = []
            for x in data:
                result.append(x * 2)
            return result
            
        test_data = list(range(1000))
        
        comparison = profiler.compare_approaches(
            {"list_comp": approach1, "loop": approach2},
            test_data,
            iterations=2
        )
        
        assert "list_comp" in comparison
        assert "loop" in comparison
        assert comparison["list_comp"]["iterations"] == 2
        
    def test_bottleneck_detection(self):
        """Test bottleneck identification."""
        profiler = BatchProfiler()
        
        # Create some profiling results
        with profiler.profile("fast_op"):
            time.sleep(0.001)
            
        with profiler.profile("slow_op"):
            time.sleep(0.01)
            
        with profiler.profile("medium_op"):
            time.sleep(0.005)
            
        bottlenecks = profiler.get_bottlenecks(2)
        assert len(bottlenecks) == 2
        assert bottlenecks[0].name == "slow_op"
        
    def test_report_generation(self):
        """Test report generation."""
        profiler = BatchProfiler()
        
        with profiler.profile("test_op", 100):
            time.sleep(0.01)
            
        report = profiler.generate_report()
        assert "Performance Profiling Report" in report
        assert "test_op" in report
        assert "System Information" in report
        
    def test_export(self):
        """Test result export."""
        profiler = BatchProfiler()
        
        with profiler.profile("op1", 50):
            pass
            
        # Test JSON export
        json_export = profiler.export_results("json")
        data = json.loads(json_export)
        assert len(data) == 1
        assert data[0]["name"] == "op1"
        
        # Test CSV export
        csv_export = profiler.export_results("csv")
        lines = csv_export.split("\n")
        assert len(lines) >= 2
        assert "op1" in lines[1]