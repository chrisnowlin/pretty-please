"""Collection directory management for organized persistent storage.

This module handles creation and validation of collection directory structures
with maximum precision and granularity for document layout analysis.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import CollectionConfig

logger = logging.getLogger(__name__)


class CollectionManager:
    """Manages collection directory structure and configuration.

    Provides organized, persistent storage for:
    - Original documents
    - Standalone images
    - Extracted images from documents
    - Extracted tables
    - Thumbnails
    - Per-document metadata
    - Collection configuration
    - Collection statistics
    """

    REQUIRED_DIRECTORIES = [
        "documents",  # Original uploaded documents
        "images",  # Standalone uploaded images
        "extracted_images",  # Images extracted from documents via layout analysis
        "tables",  # Extracted tables as HTML/JSON
        "thumbnails",  # All thumbnails (images and extracted_images)
        "metadata",  # Per-document region metadata and layout analysis results
    ]

    def __init__(self, base_dir: Path = Path("./uploads")):
        """Initialize collection manager.

        Args:
            base_dir: Base directory for all collections (default: ./uploads)
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_collection_structure(
        self,
        collection_name: str,
        config: Optional[CollectionConfig] = None,
    ) -> Path:
        """Create organized directory structure for a new collection.

        Args:
            collection_name: Name of the collection
            config: Optional collection configuration (uses defaults if not provided)

        Returns:
            Path to collection directory

        Raises:
            ValueError: If collection name is invalid
            IOError: If directory creation fails
        """
        if not collection_name or not collection_name.strip():
            raise ValueError("Collection name cannot be empty")

        # Sanitize collection name (prevent path traversal)
        safe_name = self._sanitize_name(collection_name)
        collection_dir = self.base_dir / safe_name

        # Check if collection directory already exists
        if collection_dir.exists():
            logger.warning(f"Collection directory already exists: {collection_dir}")
            # Validate existing structure
            self.validate_structure(collection_dir)
            return collection_dir

        try:
            # Create collection directory
            collection_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created collection directory: {collection_dir}")

            # Create all required subdirectories
            for dir_name in self.REQUIRED_DIRECTORIES:
                subdir = collection_dir / dir_name
                subdir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created subdirectory: {subdir}")

            # Create default configuration if not provided
            if config is None:
                config = CollectionConfig.get_default()

            # Save configuration
            config_path = collection_dir / "config.json"
            config.save_to_file(config_path)
            logger.info(f"Saved collection config: {config_path}")

            # Create initial stats file
            stats_path = collection_dir / "stats.json"
            initial_stats = {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "total_documents": 0,
                "total_images": 0,
                "total_extracted_images": 0,
                "total_tables": 0,
                "total_regions": 0,
                "total_embeddings": 0,
                "region_type_counts": {
                    "text": 0,
                    "image": 0,
                    "table": 0,
                    "title": 0,
                    "list": 0,
                },
            }

            with open(stats_path, "w", encoding="utf-8") as f:
                json.dump(initial_stats, f, indent=2, ensure_ascii=False)
            logger.info(f"Created stats file: {stats_path}")

            logger.info(f"✓ Collection structure created successfully: {collection_dir}")
            return collection_dir

        except Exception as e:
            # Clean up on failure
            if collection_dir.exists():
                import shutil
                try:
                    shutil.rmtree(collection_dir)
                    logger.warning(f"Cleaned up failed collection directory: {collection_dir}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to clean up directory: {cleanup_error}")

            raise IOError(f"Failed to create collection structure: {e}")

    def validate_structure(self, collection_dir: Path) -> bool:
        """Validate that collection directory has correct structure.

        Args:
            collection_dir: Path to collection directory

        Returns:
            True if valid, False otherwise

        Raises:
            FileNotFoundError: If collection directory doesn't exist
        """
        if not collection_dir.exists():
            raise FileNotFoundError(f"Collection directory not found: {collection_dir}")

        missing_dirs = []
        for dir_name in self.REQUIRED_DIRECTORIES:
            subdir = collection_dir / dir_name
            if not subdir.exists():
                missing_dirs.append(dir_name)

        if missing_dirs:
            logger.warning(
                f"Collection {collection_dir.name} is missing directories: {missing_dirs}"
            )
            # Auto-create missing directories
            for dir_name in missing_dirs:
                subdir = collection_dir / dir_name
                subdir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created missing directory: {subdir}")

        # Validate config.json exists
        config_path = collection_dir / "config.json"
        if not config_path.exists():
            logger.warning(f"Collection {collection_dir.name} missing config.json, creating default")
            config = CollectionConfig.get_default()
            config.save_to_file(config_path)

        # Validate stats.json exists
        stats_path = collection_dir / "stats.json"
        if not stats_path.exists():
            logger.warning(f"Collection {collection_dir.name} missing stats.json, creating default")
            initial_stats = {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "total_documents": 0,
                "total_images": 0,
                "total_extracted_images": 0,
                "total_tables": 0,
                "total_regions": 0,
                "total_embeddings": 0,
                "region_type_counts": {
                    "text": 0,
                    "image": 0,
                    "table": 0,
                    "title": 0,
                    "list": 0,
                },
            }
            with open(stats_path, "w", encoding="utf-8") as f:
                json.dump(initial_stats, f, indent=2, ensure_ascii=False)

        return True

    def get_config(self, collection_name: str) -> CollectionConfig:
        """Load collection configuration.

        Args:
            collection_name: Name of the collection

        Returns:
            CollectionConfig instance

        Raises:
            FileNotFoundError: If collection or config doesn't exist
        """
        safe_name = self._sanitize_name(collection_name)
        collection_dir = self.base_dir / safe_name

        if not collection_dir.exists():
            raise FileNotFoundError(f"Collection not found: {collection_name}")

        config_path = collection_dir / "config.json"
        if not config_path.exists():
            # Return default config and save it
            logger.warning(f"Config not found for {collection_name}, using defaults")
            config = CollectionConfig.get_default()
            config.save_to_file(config_path)
            return config

        return CollectionConfig.load_from_file(config_path)

    def update_config(
        self,
        collection_name: str,
        config: CollectionConfig,
    ) -> None:
        """Update collection configuration.

        Args:
            collection_name: Name of the collection
            config: New configuration

        Raises:
            FileNotFoundError: If collection doesn't exist
        """
        safe_name = self._sanitize_name(collection_name)
        collection_dir = self.base_dir / safe_name

        if not collection_dir.exists():
            raise FileNotFoundError(f"Collection not found: {collection_name}")

        config_path = collection_dir / "config.json"
        config.save_to_file(config_path)
        logger.info(f"Updated config for collection: {collection_name}")

    def _sanitize_name(self, name: str) -> str:
        """Sanitize collection name to prevent path traversal.

        Args:
            name: Raw collection name

        Returns:
            Sanitized name safe for filesystem use
        """
        # Remove path separators and dangerous characters
        safe_name = name.strip()
        safe_name = safe_name.replace("/", "_").replace("\\", "_")
        safe_name = safe_name.replace("..", "_")

        # Ensure name is not empty after sanitization
        if not safe_name:
            raise ValueError("Collection name is invalid after sanitization")

        return safe_name

    def validate_all_collections(self) -> None:
        """Validate structure of all existing collections on startup."""
        if not self.base_dir.exists():
            logger.info("No collections directory found, will be created on first collection")
            return

        logger.info("Validating existing collection structures...")
        for collection_dir in self.base_dir.iterdir():
            if collection_dir.is_dir():
                try:
                    self.validate_structure(collection_dir)
                    logger.debug(f"✓ {collection_dir.name} structure validated")
                except Exception as e:
                    logger.error(f"✗ Failed to validate {collection_dir.name}: {e}")

        logger.info("Collection validation complete")
