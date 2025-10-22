"""Configuration manager for global embedding and OCR settings.

This module provides persistent storage and retrieval of global configuration
for embeddings and OCR processing. Configuration is stored in a JSON file and
automatically loaded on startup.

The ConfigManager follows the same atomic write pattern as CollectionManager
for safe concurrent access.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .models import EmbeddingConfigModel, OCRConfigModel

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages global embedding and OCR configuration persistence.

    Configuration is stored in a JSON file with the following structure:
    {
        "embeddings": {...EmbeddingConfig fields...},
        "ocr": {...OCRConfig fields...}
    }

    Configuration changes are immediately persisted to disk using atomic writes
    (write to temp file, then rename) to ensure consistency even if the process
    crashes during write.
    """

    def __init__(self, config_dir: Path = Path("data")):
        """Initialize ConfigManager.

        Args:
            config_dir: Directory to store global_config.json. Defaults to "data/".
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "global_config.json"
        self.config_dir.mkdir(exist_ok=True, parents=True)

        # Initialize config if it doesn't exist
        if not self.config_file.exists():
            self._save_config(self._get_defaults())
            logger.info(f"Created default configuration file: {self.config_file}")

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file.

        Returns:
            Dictionary with "embeddings" and "ocr" keys, or defaults if file doesn't exist.
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.debug(f"Loaded configuration from {self.config_file}")
                return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")

        return self._get_defaults()

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file with atomic write.

        Args:
            config: Dictionary with "embeddings" and "ocr" keys.

        Raises:
            IOError: If write fails.
        """
        self._save_config(config)

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Internal: Save configuration with atomic write pattern.

        Args:
            config: Dictionary to save.

        Raises:
            IOError: If write fails.
        """
        try:
            # Atomic write: write to temp file, then rename
            temp_file = self.config_file.with_suffix(".tmp")

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_file.replace(self.config_file)
            logger.debug(f"Saved configuration to {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise IOError(f"Failed to save configuration to {self.config_file}: {e}")

    def get_embedding_config(self) -> EmbeddingConfigModel:
        """Get current embedding configuration.

        Returns:
            EmbeddingConfigModel with current settings.
        """
        config = self.load_config()
        embedding_data = config.get("embeddings", {})
        return EmbeddingConfigModel(**embedding_data)

    def set_embedding_config(self, config: EmbeddingConfigModel) -> None:
        """Set embedding configuration.

        Args:
            config: New embedding configuration.
        """
        full_config = self.load_config()
        full_config["embeddings"] = config.model_dump()
        self.save_config(full_config)
        logger.info("Updated embedding configuration")

    def get_ocr_config(self) -> OCRConfigModel:
        """Get current OCR configuration.

        Returns:
            OCRConfigModel with current settings.
        """
        config = self.load_config()
        ocr_data = config.get("ocr", {})
        return OCRConfigModel(**ocr_data)

    def set_ocr_config(self, config: OCRConfigModel) -> None:
        """Set OCR configuration.

        Args:
            config: New OCR configuration.
        """
        full_config = self.load_config()
        full_config["ocr"] = config.model_dump()
        self.save_config(full_config)
        logger.info("Updated OCR configuration")

    @staticmethod
    def _get_defaults() -> Dict[str, Any]:
        """Get default configuration.

        Returns:
            Dictionary with default embedding and OCR configuration.
        """
        return {
            "embeddings": EmbeddingConfigModel().model_dump(),
            "ocr": OCRConfigModel().model_dump(),
        }

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults.

        This is useful for troubleshooting or when the user wants to start fresh.
        """
        self.save_config(self._get_defaults())
        logger.info("Reset configuration to defaults")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration dictionary.

        Args:
            config: Dictionary to validate.

        Returns:
            True if valid, False otherwise.
        """
        try:
            # Validate embeddings config
            if "embeddings" in config:
                EmbeddingConfigModel(**config["embeddings"])

            # Validate OCR config
            if "ocr" in config:
                OCRConfigModel(**config["ocr"])

            return True
        except Exception as e:
            logger.error(f"Invalid configuration: {e}")
            return False
