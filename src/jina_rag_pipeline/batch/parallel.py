"""Parallel processing utilities for batch operations."""

import os
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable, List, Optional, TypeVar, Union
import logging
from functools import partial
import platform

T = TypeVar('T')
R = TypeVar('R')

logger = logging.getLogger(__name__)


class ParallelProcessor:
    """Parallel processing for CPU-intensive and I/O-bound operations."""
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_processes: bool = True,
        chunk_size: int = 1
    ):
        """Initialize parallel processor.
        
        Args:
            max_workers: Maximum number of workers (None for auto-detect)
            use_processes: Use processes (True) or threads (False)
            chunk_size: Size of chunks for parallel processing
        """
        self.use_processes = use_processes
        self.chunk_size = chunk_size
        
        if max_workers is None:
            # Auto-detect optimal workers
            if platform.system() == "Darwin" and platform.processor() == "arm":
                # M4 Max has 12 performance cores + 4 efficiency cores
                # Use performance cores for CPU-intensive work
                self.max_workers = min(12, mp.cpu_count() - 4)
            else:
                self.max_workers = mp.cpu_count()
        else:
            self.max_workers = max_workers
            
        logger.info(f"Parallel processor initialized with {self.max_workers} workers")
        
    def map(
        self,
        func: Callable[[T], R],
        items: Iterable[T],
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[R]:
        """Map function over items in parallel.
        
        Args:
            func: Function to apply to each item
            items: Items to process
            progress_callback: Optional progress callback
            
        Returns:
            List of results in original order
        """
        items_list = list(items)
        total = len(items_list)
        
        if total == 0:
            return []
            
        # Choose executor based on configuration
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        
        results: List[R] = []
        result_dict = {}
        completed = 0
        
        with executor_class(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(func, item): i
                for i, item in enumerate(items_list)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result_dict[index] = future.result()
                except Exception as e:
                    logger.error(f"Error processing item {index}: {e}")
                    raise
                    
                completed += 1
                if progress_callback:
                    progress_callback(completed)
        
        # Sort results by original index
        for i in range(total):
            results.append(result_dict[i])
                    
        return results
        
    def map_batches(
        self,
        func: Callable[[List[T]], List[R]],
        items: Iterable[T],
        batch_size: int = 32,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[R]:
        """Process items in batches using parallel workers.
        
        Args:
            func: Function to process a batch
            items: Items to process
            batch_size: Size of each batch
            progress_callback: Optional progress callback
            
        Returns:
            Flattened list of all results
        """
        # Create batches
        batches = []
        current_batch = []
        
        for item in items:
            current_batch.append(item)
            if len(current_batch) >= batch_size:
                batches.append(current_batch)
                current_batch = []
                
        if current_batch:
            batches.append(current_batch)
            
        if not batches:
            return []
            
        # Process batches in parallel (preserve original order)
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        completed = 0
        results_by_index = {}

        with executor_class(max_workers=self.max_workers) as executor:
            # Submit batch processing tasks with their indices
            future_to_index = {
                executor.submit(func, batch): i for i, batch in enumerate(batches)
            }

            # Collect results as they complete
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    results_by_index[idx] = future.result()
                except Exception as e:
                    logger.error(f"Error processing batch {idx}: {e}")
                    raise
                completed += 1
                if progress_callback:
                    progress_callback(completed)

        # Flatten results in original batch order
        all_results: List[R] = []
        for i in range(len(batches)):
            all_results.extend(results_by_index[i])
        return all_results
        
    def parallel_io(
        self,
        func: Callable[[T], R],
        items: Iterable[T],
        max_workers: Optional[int] = None
    ) -> List[R]:
        """Execute I/O-bound operations in parallel using threads.
        
        Args:
            func: I/O-bound function to execute
            items: Items to process
            max_workers: Override default max workers
            
        Returns:
            List of results
        """
        workers = max_workers or self.max_workers * 2  # More threads for I/O
        
        items_list = list(items)
        results: List[R] = []
        result_dict = {}
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_index = {
                executor.submit(func, item): i
                for i, item in enumerate(items_list)
            }
            
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result_dict[index] = future.result()
                except Exception as e:
                    logger.error(f"I/O error for item {index}: {e}")
                    raise
        
        # Sort results by original index            
        for i in range(len(items_list)):
            results.append(result_dict[i])
                    
        return results
        
    def process_queue(
        self,
        input_queue: mp.Queue,
        output_queue: mp.Queue,
        process_func: Callable[[Any], Any],
        num_workers: Optional[int] = None
    ):
        """Process items from a queue using multiple workers.
        
        Args:
            input_queue: Queue containing input items
            output_queue: Queue for results
            process_func: Function to process each item
            num_workers: Number of worker processes
        """
        workers = num_workers or self.max_workers
        
        def worker():
            while True:
                item = input_queue.get()
                if item is None:  # Sentinel value
                    break
                    
                try:
                    result = process_func(item)
                    output_queue.put(result)
                except Exception as e:
                    logger.error(f"Queue processing error: {e}")
                    output_queue.put(None)
                    
        # Start workers
        processes = []
        for _ in range(workers):
            p = mp.Process(target=worker)
            p.start()
            processes.append(p)
            
        # Add sentinel values to stop workers
        for _ in range(workers):
            input_queue.put(None)
            
        # Wait for workers to finish
        for p in processes:
            p.join()
            
    @staticmethod
    def get_optimal_workers(task_type: str = "cpu") -> int:
        """Get optimal number of workers for the system.
        
        Args:
            task_type: Type of task ("cpu", "io", "mixed")
            
        Returns:
            Recommended number of workers
        """
        cpu_count = mp.cpu_count()
        
        if platform.system() == "Darwin" and platform.processor() == "arm":
            # Apple Silicon optimization
            if task_type == "cpu":
                # Use performance cores
                return min(12, cpu_count - 4)
            elif task_type == "io":
                # Can use all cores for I/O
                return cpu_count * 2
            else:  # mixed
                return cpu_count
        else:
            if task_type == "cpu":
                return cpu_count
            elif task_type == "io":
                return cpu_count * 2
            else:  # mixed
                return cpu_count