"""Batch processing manager with dynamic sizing and optimization."""

import time
from typing import Any, Callable, Generator, Iterable, List, Optional, TypeVar, Union
from dataclasses import dataclass
import logging

from .memory import MemoryConfig, MemoryMonitor

T = TypeVar('T')
R = TypeVar('R')

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    
    initial_batch_size: int = 32
    min_batch_size: int = 1
    max_batch_size: int = 1024
    adaptive_sizing: bool = True
    measure_throughput: bool = True
    auto_adjust_interval: int = 5  # Adjust batch size every N batches
    

class BatchManager:
    """Manages batch processing with dynamic sizing and memory optimization."""
    
    def __init__(
        self,
        config: Optional[BatchConfig] = None,
        memory_config: Optional[MemoryConfig] = None
    ):
        """Initialize batch manager.
        
        Args:
            config: Batch processing configuration
            memory_config: Memory management configuration
        """
        self.config = config or BatchConfig()
        self.memory_monitor = MemoryMonitor(memory_config)
        
        self.current_batch_size = self.config.initial_batch_size
        self.batch_history: List[dict] = []
        self._throughput_history: List[float] = []
        
    def process_batches(
        self,
        items: Iterable[T],
        process_func: Callable[[List[T]], List[R]],
        total_items: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int, Optional[float]], None]] = None
    ) -> Generator[List[R], None, None]:
        """Process items in optimized batches.
        
        Args:
            items: Items to process
            process_func: Function to process a batch of items
            total_items: Total number of items (for progress tracking)
            progress_callback: Callback for progress updates (processed, total, time_remaining)
            
        Yields:
            Processed batch results
        """
        batch = []
        processed = 0
        batch_num = 0
        start_time = time.time()
        batch_times = []
        
        for item in items:
            batch.append(item)
            
            if len(batch) >= self.current_batch_size:
                # Process batch
                start_time = time.time()
                results = self._process_batch_with_monitoring(
                    batch, process_func, batch_num
                )
                batch_time = time.time() - start_time
                
                # Track metrics
                self._record_batch_metrics(len(batch), batch_time)
                
                # Adjust batch size if needed
                if self.config.adaptive_sizing and batch_num % self.config.auto_adjust_interval == 0:
                    self._adjust_batch_size()
                
                processed += len(batch)
                if progress_callback and total_items is not None:
                    # Calculate estimated time remaining
                    elapsed = time.time() - start_time
                    if processed > 0:
                        avg_time_per_item = elapsed / processed
                        remaining_items = total_items - processed
                        time_remaining = avg_time_per_item * remaining_items
                    else:
                        time_remaining = None
                    progress_callback(processed, total_items, time_remaining)
                    
                yield results
                
                batch = []
                batch_num += 1
        
        # Process remaining items
        if batch:
            results = self._process_batch_with_monitoring(
                batch, process_func, batch_num
            )
            processed += len(batch)
            if progress_callback and total_items is not None:
                # Calculate estimated time remaining
                elapsed = time.time() - start_time
                if processed > 0:
                    avg_time_per_item = elapsed / processed
                    remaining_items = total_items - processed
                    time_remaining = avg_time_per_item * remaining_items
                else:
                    time_remaining = None
                progress_callback(processed, total_items, time_remaining)
            yield results
            
    def _process_batch_with_monitoring(
        self,
        batch: List[T],
        process_func: Callable[[List[T]], List[R]],
        batch_num: int
    ) -> List[R]:
        """Process a batch with memory monitoring.
        
        Args:
            batch: Batch of items to process
            process_func: Processing function
            batch_num: Batch number for logging
            
        Returns:
            Processed results
        """
        # Check memory pressure
        under_pressure, msg = self.memory_monitor.check_memory_pressure()
        if under_pressure:
            logger.warning(f"Batch {batch_num}: {msg}")
            
            # Reduce batch size if under memory pressure
            if len(batch) > self.config.min_batch_size:
                half_size = len(batch) // 2
                logger.info(f"Splitting batch {batch_num} due to memory pressure")
                
                # Process in smaller chunks
                results = []
                results.extend(process_func(batch[:half_size]))
                results.extend(process_func(batch[half_size:]))
                return results
        
        # Normal processing
        return process_func(batch)
        
    def _record_batch_metrics(self, batch_size: int, batch_time: float):
        """Record metrics for a processed batch.
        
        Args:
            batch_size: Size of the batch
            batch_time: Time taken to process the batch
        """
        throughput = batch_size / batch_time if batch_time > 0 else 0
        
        self.batch_history.append({
            "size": batch_size,
            "time": batch_time,
            "throughput": throughput,
            "memory_gb": self.memory_monitor._get_process_memory_gb()
        })
        
        self._throughput_history.append(throughput)
        
        # Keep history limited
        if len(self.batch_history) > 100:
            self.batch_history.pop(0)
        if len(self._throughput_history) > 20:
            self._throughput_history.pop(0)
            
    def _adjust_batch_size(self):
        """Dynamically adjust batch size based on performance metrics."""
        if len(self._throughput_history) < 3:
            return
            
        # Calculate average throughput
        recent_throughput = sum(self._throughput_history[-3:]) / 3
        older_throughput = sum(self._throughput_history[-6:-3]) / 3 if len(self._throughput_history) >= 6 else recent_throughput
        
        # Adjust based on throughput trend
        if recent_throughput > older_throughput * 1.1:
            # Performance improving, try larger batches
            new_size = min(
                int(self.current_batch_size * 1.25),
                self.config.max_batch_size
            )
            if new_size != self.current_batch_size:
                logger.info(f"Increasing batch size: {self.current_batch_size} -> {new_size}")
                self.current_batch_size = new_size
                
        elif recent_throughput < older_throughput * 0.9:
            # Performance degrading, reduce batch size
            new_size = max(
                int(self.current_batch_size * 0.75),
                self.config.min_batch_size
            )
            if new_size != self.current_batch_size:
                logger.info(f"Decreasing batch size: {self.current_batch_size} -> {new_size}")
                self.current_batch_size = new_size
                
    def estimate_optimal_batch_size(
        self,
        item_size_mb: float,
        processing_overhead: float = 1.5
    ) -> int:
        """Estimate optimal batch size based on memory constraints.
        
        Args:
            item_size_mb: Estimated size of each item in MB
            processing_overhead: Processing overhead multiplier
            
        Returns:
            Estimated optimal batch size
        """
        return self.memory_monitor.calculate_optimal_batch_size(
            item_size_mb, processing_overhead
        )
        
    def get_statistics(self) -> dict:
        """Get batch processing statistics.
        
        Returns:
            Dictionary of statistics
        """
        if not self.batch_history:
            return {
                "total_batches": 0,
                "current_batch_size": self.current_batch_size,
                "memory_stats": self.memory_monitor.get_memory_stats()
            }
            
        total_items = sum(b["size"] for b in self.batch_history)
        total_time = sum(b["time"] for b in self.batch_history)
        
        return {
            "total_batches": len(self.batch_history),
            "total_items": total_items,
            "total_time": total_time,
            "average_batch_size": total_items / len(self.batch_history),
            "average_throughput": total_items / total_time if total_time > 0 else 0,
            "current_batch_size": self.current_batch_size,
            "memory_stats": self.memory_monitor.get_memory_stats()
        }