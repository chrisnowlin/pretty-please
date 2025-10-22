"""Thumbnail generation utilities for image files."""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """Generate and cache thumbnails for images."""

    def __init__(
        self,
        thumbnail_size: Tuple[int, int] = (256, 256),
        quality: int = 85,
        cache_dir: Optional[Path] = None,
    ):
        """Initialize thumbnail generator.

        Args:
            thumbnail_size: Target size for thumbnails (width, height)
            quality: JPEG quality for compression (1-100)
            cache_dir: Directory to cache thumbnails (default: ./uploads/thumbnails/)
        """
        self.thumbnail_size = thumbnail_size
        self.quality = quality
        self.cache_dir = cache_dir or Path("./uploads/thumbnails")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate_thumbnail(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        force_regenerate: bool = False,
    ) -> Path:
        """Generate thumbnail for an image.

        Args:
            image_path: Path to source image
            output_path: Path to save thumbnail (optional, auto-generated if None)
            force_regenerate: If True, regenerate even if thumbnail exists

        Returns:
            Path to generated thumbnail
        """
        # Generate output path if not provided
        if output_path is None:
            # Use content-addressed naming (hash-based) for caching
            content_hash = self._compute_file_hash(image_path)
            filename = f"{content_hash}_thumb.jpg"
            output_path = self.cache_dir / filename

        # Check if thumbnail already exists
        if output_path.exists() and not force_regenerate:
            logger.debug(f"Thumbnail already exists: {output_path}")
            return output_path

        try:
            # Load source image
            image = Image.open(image_path)

            # Convert to RGB if needed (for formats like PNG with transparency)
            if image.mode != 'RGB':
                # Create white background for transparency
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[3])  # Alpha channel
                else:
                    background.paste(image)
                image = background

            # Generate thumbnail with aspect ratio preservation
            image.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

            # Save thumbnail
            image.save(output_path, "JPEG", quality=self.quality, optimize=True)

            logger.debug(f"Generated thumbnail: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {image_path}: {e}")
            raise

    def generate_thumbnail_with_padding(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        background_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Path:
        """Generate thumbnail with padding to exact dimensions.

        This creates a thumbnail with letterboxing/pillarboxing to maintain
        the exact thumbnail_size dimensions.

        Args:
            image_path: Path to source image
            output_path: Path to save thumbnail
            background_color: RGB color for padding (default: white)

        Returns:
            Path to generated thumbnail
        """
        # Generate output path if not provided
        if output_path is None:
            content_hash = self._compute_file_hash(image_path)
            filename = f"{content_hash}_thumb_padded.jpg"
            output_path = self.cache_dir / filename

        try:
            # Load and convert source image
            image = Image.open(image_path)
            if image.mode != 'RGB':
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[3])
                else:
                    background.paste(image)
                image = background

            # Calculate scaling to fit within thumbnail size
            image.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

            # Create canvas with background color
            canvas = Image.new('RGB', self.thumbnail_size, background_color)

            # Calculate position to center the image
            x_offset = (self.thumbnail_size[0] - image.width) // 2
            y_offset = (self.thumbnail_size[1] - image.height) // 2

            # Paste thumbnail onto canvas
            canvas.paste(image, (x_offset, y_offset))

            # Save
            canvas.save(output_path, "JPEG", quality=self.quality, optimize=True)

            logger.debug(f"Generated padded thumbnail: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate padded thumbnail for {image_path}: {e}")
            raise

    def get_thumbnail_path(self, image_path: Path) -> Path:
        """Get the expected thumbnail path for an image.

        Args:
            image_path: Path to source image

        Returns:
            Expected path to thumbnail
        """
        content_hash = self._compute_file_hash(image_path)
        filename = f"{content_hash}_thumb.jpg"
        return self.cache_dir / filename

    def thumbnail_exists(self, image_path: Path) -> bool:
        """Check if thumbnail exists for an image.

        Args:
            image_path: Path to source image

        Returns:
            True if thumbnail exists
        """
        thumbnail_path = self.get_thumbnail_path(image_path)
        return thumbnail_path.exists()

    def regenerate_if_missing(self, image_path: Path) -> Path:
        """Regenerate thumbnail if it doesn't exist.

        Args:
            image_path: Path to source image

        Returns:
            Path to thumbnail (existing or newly generated)
        """
        thumbnail_path = self.get_thumbnail_path(image_path)

        if not thumbnail_path.exists():
            logger.info(f"Thumbnail missing for {image_path}, regenerating...")
            return self.generate_thumbnail(image_path, thumbnail_path)

        return thumbnail_path

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content.

        Args:
            file_path: Path to file

        Returns:
            Hex string of file hash
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]  # Use first 16 chars for shorter filenames

    def clear_cache(self) -> int:
        """Clear all cached thumbnails.

        Returns:
            Number of thumbnails deleted
        """
        count = 0
        for thumbnail_file in self.cache_dir.glob("*_thumb.jpg"):
            try:
                thumbnail_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete thumbnail {thumbnail_file}: {e}")

        logger.info(f"Cleared {count} thumbnails from cache")
        return count
