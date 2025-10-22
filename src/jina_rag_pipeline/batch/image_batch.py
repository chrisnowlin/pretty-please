"""Batched image processing for multimodal embeddings."""

from typing import List, Union, Optional, Callable
from pathlib import Path
import logging

import numpy as np
from PIL import Image

from .manager import BatchManager
from .profiler import BatchProfiler
from ..multimodal.image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class ImageBatchProcessor:
    """Optimized batch processing for image embeddings."""
    
    def __init__(
        self,
        embedder,
        batch_size: int = 8,
        use_profiler: bool = False
    ):
        """Initialize image batch processor.
        
        Args:
            embedder: Embedding model with encode_image support
            batch_size: Default batch size for processing
            use_profiler: Whether to enable profiling
        """
        self.embedder = embedder
        self.batch_manager = BatchManager()
        self.batch_manager.current_batch_size = batch_size
        self.image_processor = ImageProcessor()
        self.profiler = BatchProfiler() if use_profiler else None
        
    def encode_image_batch(
        self,
        images: Union[List[str], List[Image.Image], List[Union[str, Image.Image]]],
        task: str = "retrieval",
        truncate_dim: Optional[int] = None,
        return_multivector: bool = False,
        show_progress: bool = True,
        optimize_memory: bool = True
    ) -> np.ndarray:
        """Encode a batch of images with memory optimization.
        
        Args:
            images: List of image paths or PIL Images
            task: Task type for encoding
            truncate_dim: Truncate embeddings to this dimension
            return_multivector: Return multi-vector embeddings
            show_progress: Show progress bar
            optimize_memory: Use dynamic batch sizing
            
        Returns:
            Array of embeddings
        """
        # Prepare images
        prepared_images = []
        for img in images:
            if isinstance(img, str):
                prepared_images.append(self.image_processor.load_image(img))
            elif isinstance(img, Image.Image):
                prepared_images.append(img)
            else:
                raise ValueError(f"Unsupported image type: {type(img)}")
                
        # Calculate optimal batch size if optimizing
        if optimize_memory:
            # Estimate memory per image (rough estimate: 3*224*224*4 bytes for float32)
            image_size_mb = (3 * 224 * 224 * 4) / (1024 * 1024)
            # Add overhead for model processing
            optimal_batch = self.batch_manager.memory_monitor.calculate_optimal_batch_size(
                item_size_mb=image_size_mb * 2,  # 2x overhead for processing
                processing_overhead=1.5
            )
            self.batch_manager.current_batch_size = min(optimal_batch, len(prepared_images))
            logger.info(f"Optimal batch size for images: {self.batch_manager.current_batch_size}")
            
        # Process function for batch manager
        def process_batch(batch_images: List[Image.Image]) -> np.ndarray:
            if self.profiler:
                with self.profiler.profile(f"encode_{len(batch_images)}_images", len(batch_images)):
                    return self.embedder.encode_image(
                        batch_images,
                        task=task,
                        truncate_dim=truncate_dim,
                        return_multivector=return_multivector,
                        batch_size=len(batch_images),
                        show_progress=False
                    )
            else:
                return self.embedder.encode_image(
                    batch_images,
                    task=task,
                    truncate_dim=truncate_dim,
                    return_multivector=return_multivector,
                    batch_size=len(batch_images),
                    show_progress=False
                )
                
        # Process with batch manager
        all_embeddings = []
        progress_callback = (lambda p, t: logger.info(f"Processed {p}/{t} images")) if show_progress else None
        
        for batch_result in self.batch_manager.process_batches(
            prepared_images,
            process_batch,
            total_items=len(prepared_images),
            progress_callback=progress_callback
        ):
            all_embeddings.append(batch_result)
            
        # Concatenate results
        if all_embeddings:
            return np.vstack(all_embeddings)
        return np.array([])
        
    def process_image_directory(
        self,
        directory: Union[str, Path],
        extensions: List[str] = ['.jpg', '.jpeg', '.png', '.bmp'],
        recursive: bool = True,
        **encode_kwargs
    ) -> tuple[List[str], np.ndarray]:
        """Process all images in a directory.
        
        Args:
            directory: Directory containing images
            extensions: Image file extensions to process
            recursive: Search recursively
            **encode_kwargs: Arguments for encode_image_batch
            
        Returns:
            Tuple of (image_paths, embeddings)
        """
        directory = Path(directory)
        
        # Find all image files
        image_paths = []
        if recursive:
            for ext in extensions:
                image_paths.extend(directory.rglob(f"*{ext}"))
        else:
            for ext in extensions:
                image_paths.extend(directory.glob(f"*{ext}"))
                
        image_paths = [str(p) for p in image_paths]
        
        if not image_paths:
            logger.warning(f"No images found in {directory}")
            return [], np.array([])
            
        logger.info(f"Found {len(image_paths)} images to process")
        
        # Process images
        embeddings = self.encode_image_batch(image_paths, **encode_kwargs)
        
        return image_paths, embeddings
        
    def get_profiling_report(self) -> str:
        """Get profiling report if profiler is enabled.
        
        Returns:
            Profiling report string
        """
        if self.profiler:
            return self.profiler.generate_report()
        return "Profiling not enabled"