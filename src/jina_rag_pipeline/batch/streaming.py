"""Streaming and checkpoint functionality for large-scale processing."""

import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, List, Optional, TypeVar
from dataclasses import dataclass, asdict
import logging

T = TypeVar('T')
R = TypeVar('R')

logger = logging.getLogger(__name__)


@dataclass
class CheckpointState:
    """State of a processing checkpoint."""
    
    total_processed: int
    last_checkpoint_time: float
    last_item_id: Optional[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: dict) -> 'CheckpointState':
        """Create from dictionary."""
        return cls(**data)


class StreamingPipeline:
    """Pipeline for streaming processing with checkpoint support."""
    
    def __init__(
        self,
        checkpoint_dir: Optional[str] = None,
        checkpoint_interval: int = 1000,
        enable_checkpoints: bool = True
    ):
        """Initialize streaming pipeline.
        
        Args:
            checkpoint_dir: Directory for checkpoints
            checkpoint_interval: Items between checkpoints
            enable_checkpoints: Whether to enable checkpointing
        """
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path(".checkpoints")
        self.checkpoint_interval = checkpoint_interval
        self.enable_checkpoints = enable_checkpoints
        
        if self.enable_checkpoints:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
        self.current_state: Optional[CheckpointState] = None
        self._processed_count = 0
        
    def stream_process(
        self,
        items: Iterable[T],
        process_func: Callable[[T], R],
        checkpoint_name: str = "default",
        item_id_func: Optional[Callable[[T], str]] = None,
        resume: bool = True
    ) -> Generator[R, None, None]:
        """Process items in a streaming fashion with checkpointing.
        
        Args:
            items: Iterable of items to process
            process_func: Function to process each item
            checkpoint_name: Name for the checkpoint
            item_id_func: Function to get unique ID for each item
            resume: Whether to resume from checkpoint
            
        Yields:
            Processed results
        """
        # Load checkpoint if resuming
        skip_until_id = None
        if resume and self.enable_checkpoints:
            self.current_state = self._load_checkpoint(checkpoint_name)
            if self.current_state:
                skip_until_id = self.current_state.last_item_id
                self._processed_count = self.current_state.total_processed
                logger.info(f"Resuming from checkpoint: {self._processed_count} items processed")
                
        # Process items
        skipping = skip_until_id is not None
        
        for item in items:
            # Get item ID if function provided
            item_id = item_id_func(item) if item_id_func else None
            
            # Skip items until we reach the checkpoint
            if skipping:
                if item_id == skip_until_id:
                    skipping = False
                continue
                
            # Process item
            try:
                result = process_func(item)
                self._processed_count += 1
                
                # Save checkpoint if needed
                if self.enable_checkpoints and self._processed_count % self.checkpoint_interval == 0:
                    self._save_checkpoint(checkpoint_name, item_id)
                    
                yield result
                
            except Exception as e:
                logger.error(f"Error processing item {item_id}: {e}")
                if self.enable_checkpoints:
                    self._save_checkpoint(checkpoint_name, item_id, error=str(e))
                raise
                
        # Final checkpoint
        if self.enable_checkpoints:
            self._save_checkpoint(checkpoint_name, None, final=True)
            
    def batch_stream_process(
        self,
        items: Iterable[T],
        process_func: Callable[[List[T]], List[R]],
        batch_size: int = 32,
        checkpoint_name: str = "batch_default"
    ) -> Generator[List[R], None, None]:
        """Process items in batches with streaming and checkpointing.
        
        Args:
            items: Items to process
            process_func: Batch processing function
            batch_size: Size of each batch
            checkpoint_name: Name for checkpoint
            
        Yields:
            Batch results
        """
        batch = []
        batch_num = 0
        
        # Load checkpoint
        if self.enable_checkpoints:
            state = self._load_checkpoint(checkpoint_name)
            if state:
                batch_num = state.metadata.get("batch_num", 0)
                logger.info(f"Resuming from batch {batch_num}")
                
        # Skip processed batches
        current_batch = 0
        items_iter = iter(items)
        
        # Skip to resume point
        if batch_num > 0:
            skip_items = batch_num * batch_size
            for _ in range(skip_items):
                try:
                    next(items_iter)
                except StopIteration:
                    break
            current_batch = batch_num
            
        # Process remaining items
        for item in items_iter:
            batch.append(item)
            
            if len(batch) >= batch_size:
                # Process batch
                results = process_func(batch)
                
                # Checkpoint
                if self.enable_checkpoints:
                    self._save_checkpoint(
                        checkpoint_name,
                        None,
                        metadata={"batch_num": current_batch + 1}
                    )
                    
                yield results
                
                batch = []
                current_batch += 1
                
        # Process final batch
        if batch:
            results = process_func(batch)
            if self.enable_checkpoints:
                self._save_checkpoint(checkpoint_name, None, final=True)
            yield results
            
    def create_data_pipeline(
        self,
        source: Callable[[], Iterable[T]],
        transforms: List[Callable[[Any], Any]],
        sink: Callable[[Any], None],
        buffer_size: int = 1000
    ) -> Generator[None, None, None]:
        """Create a data processing pipeline with backpressure handling.
        
        Args:
            source: Function that returns iterable of source data
            transforms: List of transformation functions
            sink: Function to consume processed data
            buffer_size: Maximum buffer size for backpressure
            
        Yields:
            None (processes data through pipeline)
        """
        from collections import deque
        
        buffer = deque(maxlen=buffer_size)
        
        # Get source data
        data_iter = source()
        
        for item in data_iter:
            # Apply transforms
            result = item
            for transform in transforms:
                result = transform(result)
                
            # Add to buffer
            buffer.append(result)
            
            # Process buffer when full
            if len(buffer) >= buffer_size:
                while buffer:
                    sink(buffer.popleft())
                    yield
                    
        # Process remaining items
        while buffer:
            sink(buffer.popleft())
            yield
            
    def _save_checkpoint(
        self,
        name: str,
        last_item_id: Optional[str] = None,
        error: Optional[str] = None,
        final: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Save checkpoint state.
        
        Args:
            name: Checkpoint name
            last_item_id: ID of last processed item
            error: Error message if any
            final: Whether this is the final checkpoint
            metadata: Additional metadata
        """
        state = CheckpointState(
            total_processed=self._processed_count,
            last_checkpoint_time=time.time(),
            last_item_id=last_item_id,
            metadata=metadata or {}
        )
        
        if error:
            state.metadata["error"] = error
        if final:
            state.metadata["completed"] = True
            
        checkpoint_file = self.checkpoint_dir / f"{name}.checkpoint"
        
        # Save as JSON for readability
        with open(checkpoint_file, 'w') as f:
            json.dump(state.to_dict(), f, indent=2)
            
        logger.debug(f"Saved checkpoint: {self._processed_count} items")
        
    def _load_checkpoint(self, name: str) -> Optional[CheckpointState]:
        """Load checkpoint state.
        
        Args:
            name: Checkpoint name
            
        Returns:
            Checkpoint state if exists
        """
        checkpoint_file = self.checkpoint_dir / f"{name}.checkpoint"
        
        if not checkpoint_file.exists():
            return None
            
        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)
            return CheckpointState.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
            
    def clear_checkpoint(self, name: str):
        """Clear a checkpoint.
        
        Args:
            name: Checkpoint name to clear
        """
        checkpoint_file = self.checkpoint_dir / f"{name}.checkpoint"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            logger.info(f"Cleared checkpoint: {name}")
            
    def get_checkpoint_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a checkpoint.
        
        Args:
            name: Checkpoint name
            
        Returns:
            Checkpoint information if exists
        """
        state = self._load_checkpoint(name)
        if state:
            return state.to_dict()
        return None