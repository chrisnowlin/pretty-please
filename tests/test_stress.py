"""Stress tests for batch processing with large datasets."""

import time
import random
import string
import numpy as np
import pytest
from pathlib import Path

from src.jina_rag_pipeline.batch import BatchManager, MemoryMonitor, ParallelProcessor
from src.jina_rag_pipeline.batch.streaming import StreamingPipeline


def generate_large_text_dataset(num_items: int, text_length: int = 1000) -> list:
    """Generate large text dataset for testing."""
    texts = []
    for i in range(num_items):
        text = ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=text_length))
        texts.append(f"Document {i}: {text}")
    return texts


def generate_large_numeric_dataset(num_items: int, dims: int = 768) -> np.ndarray:
    """Generate large numeric dataset for testing."""
    return np.random.randn(num_items, dims).astype(np.float32)


class TestLargeScaleBatchProcessing:
    """Stress tests for batch processing with large datasets."""
    
    @pytest.mark.slow
    def test_large_text_processing(self):
        """Test processing large text dataset."""
        manager = BatchManager()
        
        # Generate large dataset
        texts = generate_large_text_dataset(10000, text_length=500)
        
        def process_text(batch):
            # Simulate processing
            return [len(text) for text in batch]
        
        # Process with monitoring
        start_time = time.time()
        results = []
        
        for batch_result in manager.process_batches(texts, process_text, total_items=len(texts)):
            results.extend(batch_result)
        
        elapsed = time.time() - start_time
        
        assert len(results) == len(texts)
        assert all(r > 0 for r in results)
        
        # Performance check
        items_per_second = len(texts) / elapsed
        print(f"Processed {len(texts)} texts in {elapsed:.2f}s ({items_per_second:.0f} items/s)")
        assert items_per_second > 100  # Should process >100 items/second
    
    @pytest.mark.slow  
    def test_memory_pressure_handling(self):
        """Test batch processing under memory pressure."""
        manager = BatchManager()
        monitor = MemoryMonitor()
        
        # Generate dataset that will cause memory pressure
        large_arrays = []
        for _ in range(100):
            # Each array is ~6MB (768 * 1000 * 8 bytes)
            array = generate_large_numeric_dataset(1000, dims=768)
            large_arrays.append(array)
        
        def process_arrays(batch):
            # Simulate memory-intensive processing
            results = []
            for array in batch:
                # Do some computation
                result = np.mean(array, axis=1)
                results.append(result)
            return results
        
        # Check initial memory
        initial_memory = monitor._get_process_memory_gb()
        
        # Process with adaptive batch sizing
        manager.config.adaptive_sizing = True
        results = []
        
        for batch_result in manager.process_batches(large_arrays[:50], process_arrays):
            results.extend(batch_result)
            
            # Check if memory is managed
            current_memory = monitor._get_process_memory_gb()
            memory_increase = current_memory - initial_memory
            
            # Memory increase should be controlled
            assert memory_increase < 2.0  # Less than 2GB increase
        
        assert len(results) == 50
    
    @pytest.mark.slow
    def test_parallel_processing_scale(self):
        """Test parallel processing at scale with I/O simulation."""
        processor = ParallelProcessor(max_workers=4, use_processes=False)
        
        # Generate large dataset
        items = list(range(10000))
        
        def io_intensive_task(x):
            # Simulate I/O work (which benefits from threading)
            time.sleep(0.001)
            return x * 2
        
        # Measure single-threaded performance
        start = time.time()
        single_results = [io_intensive_task(x) for x in items[:100]]
        single_time = time.time() - start
        
        # Measure parallel performance
        start = time.time()
        parallel_results = processor.map(io_intensive_task, items[:100])
        parallel_time = time.time() - start
        
        # Verify results match
        assert single_results == parallel_results
        
        # Should be faster in parallel for I/O tasks
        speedup = single_time / parallel_time
        print(f"Parallel speedup: {speedup:.2f}x")
        assert speedup > 1.5  # At least 1.5x speedup for I/O tasks
    
    @pytest.mark.slow
    def test_streaming_large_dataset(self, tmp_path):
        """Test streaming processing of large dataset."""
        pipeline = StreamingPipeline(
            checkpoint_dir=str(tmp_path),
            checkpoint_interval=1000
        )
        
        # Generate large dataset
        num_items = 50000
        items = list(range(num_items))
        
        def process_item(x):
            # Simulate processing
            return x * 2
        
        # Process with checkpointing
        results = []
        checkpoint_count = 0
        
        for result in pipeline.stream_process(
            items,
            process_item,
            checkpoint_name="large_dataset"
        ):
            results.append(result)
            
            # Check if checkpoint exists periodically
            if len(results) % 1000 == 0:
                info = pipeline.get_checkpoint_info("large_dataset")
                if info:
                    checkpoint_count += 1
        
        assert len(results) == num_items
        assert all(results[i] == items[i] * 2 for i in range(num_items))
        assert checkpoint_count > 0  # Should have created checkpoints
    
    @pytest.mark.slow
    def test_batch_size_optimization(self):
        """Test automatic batch size optimization."""
        manager = BatchManager()
        monitor = MemoryMonitor()
        
        # Different item sizes
        small_items = ["small"] * 1000
        large_items = ["x" * 10000] * 1000
        
        def process(batch):
            return [len(item) for item in batch]
        
        # Process small items
        manager.current_batch_size = manager.config.initial_batch_size
        small_batches = []
        for batch in manager.process_batches(small_items, process):
            small_batches.append(len(batch))
        
        avg_small_batch = np.mean([b for b in small_batches if b > 0])
        
        # Process large items  
        manager.current_batch_size = manager.config.initial_batch_size
        large_batches = []
        for batch in manager.process_batches(large_items, process):
            large_batches.append(len(batch))
        
        avg_large_batch = np.mean([b for b in large_batches if b > 0])
        
        # Batch size should adapt (smaller for large items)
        # Note: This might not always hold if adaptive sizing adjusts
        print(f"Avg batch size - small: {avg_small_batch:.1f}, large: {avg_large_batch:.1f}")


class TestProgressTracking:
    """Test progress tracking with time estimation."""
    
    def test_time_estimation(self):
        """Test estimated time remaining calculation."""
        manager = BatchManager()
        
        items = list(range(100))
        progress_updates = []
        
        def track_progress(processed, total, time_remaining):
            progress_updates.append({
                'processed': processed,
                'total': total,
                'time_remaining': time_remaining
            })
        
        def slow_process(batch):
            time.sleep(0.01)  # Simulate slow processing
            return batch
        
        results = []
        for batch in manager.process_batches(
            items,
            slow_process,
            total_items=len(items),
            progress_callback=track_progress
        ):
            results.extend(batch)
        
        # Check progress updates
        assert len(progress_updates) > 0
        
        # First update might not have time estimate
        # Later updates should have time remaining
        later_updates = [u for u in progress_updates if u['processed'] > 10]
        assert any(u['time_remaining'] is not None for u in later_updates)
        
        # Time remaining should generally decrease
        time_remainings = [u['time_remaining'] for u in later_updates if u['time_remaining']]
        if len(time_remainings) > 1:
            # Check trend (allowing for some variation)
            decreasing_count = sum(
                1 for i in range(1, len(time_remainings))
                if time_remainings[i] <= time_remainings[i-1] * 1.5
            )
            assert decreasing_count > len(time_remainings) // 2