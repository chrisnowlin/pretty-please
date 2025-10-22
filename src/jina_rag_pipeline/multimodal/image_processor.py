"""Image processing utilities for multimodal support."""

import io
import base64
from typing import List, Optional, Tuple, Union
from pathlib import Path
import logging

from PIL import Image
import torch
import torchvision.transforms as T
import numpy as np

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process and prepare images for embedding generation."""
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (224, 224),
        max_pixels: int = 200704,  # Jina v4 default
        normalize: bool = True
    ):
        """Initialize image processor.
        
        Args:
            target_size: Target size for resizing (height, width)
            max_pixels: Maximum pixels for Jina v4
            normalize: Whether to normalize images
        """
        self.target_size = target_size
        self.max_pixels = max_pixels
        self.normalize = normalize
        
        # Standard ImageNet normalization for vision models
        self.transform = T.Compose([
            T.Resize(target_size),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], 
                       std=[0.229, 0.224, 0.225]) if normalize else T.Lambda(lambda x: x)
        ])
        
    def load_image(self, path: Union[str, Path]) -> Image.Image:
        """Load an image from file.
        
        Args:
            path: Path to image file
            
        Returns:
            PIL Image object
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
            
        try:
            image = Image.open(path)
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image
        except Exception as e:
            logger.error(f"Failed to load image {path}: {e}")
            raise
            
    def load_from_bytes(self, data: bytes) -> Image.Image:
        """Load image from bytes.
        
        Args:
            data: Image data as bytes
            
        Returns:
            PIL Image object
        """
        try:
            image = Image.open(io.BytesIO(data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image
        except Exception as e:
            logger.error(f"Failed to load image from bytes: {e}")
            raise
            
    def load_from_base64(self, base64_str: str) -> Image.Image:
        """Load image from base64 string.
        
        Args:
            base64_str: Base64 encoded image
            
        Returns:
            PIL Image object
        """
        try:
            image_data = base64.b64decode(base64_str)
            return self.load_from_bytes(image_data)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            raise
            
    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """Preprocess image for model input.
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed tensor
        """
        # Check pixel count
        width, height = image.size
        if width * height > self.max_pixels:
            # Resize to fit within max_pixels
            scale = (self.max_pixels / (width * height)) ** 0.5
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
        # Apply transforms
        tensor = self.transform(image)
        return tensor
        
    def batch_preprocess(self, images: List[Image.Image]) -> torch.Tensor:
        """Preprocess multiple images.
        
        Args:
            images: List of PIL Images
            
        Returns:
            Batch tensor
        """
        tensors = [self.preprocess(img) for img in images]
        return torch.stack(tensors)
        
    def validate_image(self, image: Image.Image) -> bool:
        """Validate if image is suitable for processing.
        
        Args:
            image: PIL Image
            
        Returns:
            True if valid
        """
        if image is None:
            return False
            
        width, height = image.size
        
        # Check minimum size
        if width < 10 or height < 10:
            logger.warning(f"Image too small: {width}x{height}")
            return False
            
        # Check maximum size
        if width * height > self.max_pixels * 4:  # Allow 4x before rejection
            logger.warning(f"Image too large: {width}x{height}")
            return False
            
        return True
        
    def extract_patches(
        self, 
        image: Image.Image,
        patch_size: int = 224,
        stride: Optional[int] = None
    ) -> List[Image.Image]:
        """Extract patches from image for detailed analysis.
        
        Args:
            image: Input image
            patch_size: Size of each patch
            stride: Stride between patches (defaults to patch_size)
            
        Returns:
            List of image patches
        """
        if stride is None:
            stride = patch_size
            
        width, height = image.size
        patches = []
        
        for y in range(0, height - patch_size + 1, stride):
            for x in range(0, width - patch_size + 1, stride):
                patch = image.crop((x, y, x + patch_size, y + patch_size))
                patches.append(patch)
                
        # Add corner patches if image is large enough
        if width > patch_size and height > patch_size:
            # Top-right
            patches.append(image.crop((width - patch_size, 0, width, patch_size)))
            # Bottom-left
            patches.append(image.crop((0, height - patch_size, patch_size, height)))
            # Bottom-right
            patches.append(image.crop((width - patch_size, height - patch_size, width, height)))
            
        return patches
        
    def get_image_stats(self, image: Image.Image) -> dict:
        """Get statistics about an image.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary of image statistics
        """
        width, height = image.size
        
        # Convert to numpy for statistics
        np_image = np.array(image)
        
        stats = {
            "width": width,
            "height": height,
            "pixels": width * height,
            "aspect_ratio": width / height,
            "mode": image.mode,
            "format": image.format,
            "mean_rgb": np_image.mean(axis=(0, 1)).tolist() if len(np_image.shape) == 3 else [np_image.mean()],
            "std_rgb": np_image.std(axis=(0, 1)).tolist() if len(np_image.shape) == 3 else [np_image.std()],
        }
        
        return stats