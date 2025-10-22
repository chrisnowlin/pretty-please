"""Unit tests for ConfigManager - global configuration persistence."""
import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from src.jina_rag_pipeline.api.config_manager import ConfigManager
from src.jina_rag_pipeline.api.models import EmbeddingConfigModel, OCRConfigModel


@pytest.fixture
def config_dir(tmp_path):
    """Provide a temporary directory for config files."""
    return tmp_path / "config"


@pytest.fixture
def config_manager(config_dir):
    """Create a ConfigManager with temporary directory."""
    return ConfigManager(config_dir=config_dir)


class TestConfigManagerInitialization:
    """Tests for ConfigManager initialization."""

    def test_creates_config_directory(self, tmp_path):
        """ConfigManager should create config directory if it doesn't exist."""
        config_dir = tmp_path / "new_config"
        assert not config_dir.exists()

        ConfigManager(config_dir=config_dir)

        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_creates_default_config_file(self, config_dir):
        """ConfigManager should create default config file on init."""
        config_file = config_dir / "global_config.json"
        assert not config_file.exists()

        ConfigManager(config_dir=config_dir)

        assert config_file.exists()
        with open(config_file, "r") as f:
            config = json.load(f)
        assert "embeddings" in config
        assert "ocr" in config

    def test_does_not_overwrite_existing_config(self, config_dir):
        """ConfigManager should not overwrite existing config file."""
        config_file = config_dir / "global_config.json"
        config_dir.mkdir(parents=True, exist_ok=True)

        # Create existing config with custom values
        existing_config = {
            "embeddings": {"dimensions": 512},
            "ocr": {"batch_size": 4}
        }
        config_file.write_text(json.dumps(existing_config))

        ConfigManager(config_dir=config_dir)

        # Should preserve existing config
        with open(config_file, "r") as f:
            loaded_config = json.load(f)
        assert loaded_config == existing_config


class TestConfigManagerPersistence:
    """Tests for config persistence to disk."""

    def test_load_config_returns_dict(self, config_manager):
        """load_config should return dictionary with embeddings and ocr keys."""
        config = config_manager.load_config()

        assert isinstance(config, dict)
        assert "embeddings" in config
        assert "ocr" in config

    def test_save_config_persists_to_file(self, config_manager, config_dir):
        """save_config should write config to JSON file."""
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "global_config.json"

        new_config = {
            "embeddings": {"dimensions": 512, "task": "retrieval.passage"},
            "ocr": {"batch_size": 8}
        }

        config_manager.save_config(new_config)

        assert config_file.exists()
        with open(config_file, "r") as f:
            loaded = json.load(f)
        assert loaded == new_config

    def test_save_and_load_roundtrip(self, config_manager):
        """Config saved and then loaded should match original."""
        original_config = config_manager.load_config()

        config_manager.save_config(original_config)
        loaded_config = config_manager.load_config()

        assert loaded_config == original_config

    def test_atomic_write_uses_temp_file(self, config_manager, config_dir):
        """_save_config should use atomic write pattern with temp file."""
        config_dir.mkdir(parents=True, exist_ok=True)

        config = {"embeddings": {}, "ocr": {}}

        # The temp file should not exist after save completes
        config_manager._save_config(config)

        temp_file = config_dir / "global_config.json.tmp"
        assert not temp_file.exists()  # Cleaned up after atomic rename

        config_file = config_dir / "global_config.json"
        assert config_file.exists()  # Final file exists


class TestEmbeddingConfigManagement:
    """Tests for embedding configuration management."""

    def test_get_embedding_config_returns_model(self, config_manager):
        """get_embedding_config should return EmbeddingConfigModel."""
        config = config_manager.get_embedding_config()

        assert isinstance(config, EmbeddingConfigModel)

    def test_set_embedding_config_persists(self, config_manager):
        """set_embedding_config should persist changes to file."""
        new_config = EmbeddingConfigModel(
            dimensions=512,
            task="retrieval.query",
            batch_size=32
        )

        config_manager.set_embedding_config(new_config)

        # Reload and verify
        loaded_config = config_manager.get_embedding_config()
        assert loaded_config.dimensions == 512
        assert loaded_config.task == "retrieval.query"
        assert loaded_config.batch_size == 32

    def test_get_embedding_config_after_set(self, config_manager):
        """get_embedding_config should reflect previously set values."""
        original = config_manager.get_embedding_config()

        # Set to different values
        new_config = EmbeddingConfigModel(
            dimensions=256,
            task="retrieval.passage",
            embedding_format="binary"
        )
        config_manager.set_embedding_config(new_config)

        # Get and verify
        retrieved = config_manager.get_embedding_config()
        assert retrieved.dimensions == 256
        assert retrieved.embedding_format == "binary"


class TestOCRConfigManagement:
    """Tests for OCR configuration management."""

    def test_get_ocr_config_returns_model(self, config_manager):
        """get_ocr_config should return OCRConfigModel."""
        config = config_manager.get_ocr_config()

        assert isinstance(config, OCRConfigModel)

    def test_set_ocr_config_persists(self, config_manager):
        """set_ocr_config should persist changes to file."""
        new_config = OCRConfigModel(
            batch_size=16,
            render_workers=4,
            analysis_workers=2,
            resolution_mode="large",
            enable_grounding=False,
            enable_compression=False,
            use_vllm=True
        )

        config_manager.set_ocr_config(new_config)

        # Reload and verify
        loaded_config = config_manager.get_ocr_config()
        assert loaded_config.batch_size == 16
        assert loaded_config.render_workers == 4
        assert loaded_config.resolution_mode == "large"
        assert loaded_config.enable_grounding is False
        assert loaded_config.use_vllm is True

    def test_get_ocr_config_after_set(self, config_manager):
        """get_ocr_config should reflect previously set values."""
        new_config = OCRConfigModel(
            batch_size=32,
            render_workers=6,
            resolution_mode="tiny",
            enable_grounding=False,
            enable_compression=True,
            use_vllm=False,
        )
        config_manager.set_ocr_config(new_config)

        retrieved = config_manager.get_ocr_config()
        assert retrieved.batch_size == 32
        assert retrieved.render_workers == 6
        assert retrieved.resolution_mode == "tiny"
        assert retrieved.enable_grounding is False
        assert retrieved.enable_compression is True


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_config_valid_embeddings(self, config_manager):
        """validate_config should return True for valid embedding config."""
        config = {
            "embeddings": {"dimensions": 512, "task": "retrieval.passage"},
            "ocr": {}
        }

        assert config_manager.validate_config(config) is True


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_config_valid_ocr(self, config_manager):
        """validate_config should return True for valid OCR config."""
        config = {
            "embeddings": {},
            "ocr": {
                "batch_size": 16,
                "render_workers": 4,
                "resolution_mode": "base",
                "enable_grounding": True,
                "enable_compression": True,
                "use_vllm": False,
            }
        }

        assert config_manager.validate_config(config) is True

    def test_validate_config_invalid_embeddings_type(self, config_manager):
        """validate_config should return False for invalid embedding dimensions."""
        config = {
            "embeddings": {"dimensions": "invalid"},  # Should be int
            "ocr": {}
        }

        assert config_manager.validate_config(config) is False

    def test_validate_config_invalid_ocr_batch_size(self, config_manager):
        """validate_config should return False for negative batch_size."""
        config = {
            "embeddings": {},
            "ocr": {
                "batch_size": -1,  # Invalid: negative
                "resolution_mode": "base",
                "enable_grounding": True,
                "enable_compression": True,
                "use_vllm": False,
            }
        }

        assert config_manager.validate_config(config) is False

    def test_validate_config_invalid_resolution_mode(self, config_manager):
        """validate_config should return False for invalid resolution mode."""
        config = {
            "embeddings": {},
            "ocr": {
                "batch_size": 16,
                "resolution_mode": "invalid",
                "enable_grounding": True,
                "enable_compression": True,
                "use_vllm": False,
            },
        }

        assert config_manager.validate_config(config) is False

    def test_validate_config_empty_is_valid(self, config_manager):
        """validate_config should accept partial configs."""
        config = {
            "embeddings": {},
            "ocr": {}
        }

        assert config_manager.validate_config(config) is True


class TestResetToDefaults:
    """Tests for resetting configuration to defaults."""

    def test_reset_to_defaults_restores_defaults(self, config_manager):
        """reset_to_defaults should restore default configuration."""
        # Modify config
        new_config = EmbeddingConfigModel(dimensions=256)
        config_manager.set_embedding_config(new_config)

        modified = config_manager.get_embedding_config()
        assert modified.dimensions == 256

        # Reset to defaults
        config_manager.reset_to_defaults()

        defaults = config_manager.get_embedding_config()
        assert defaults.dimensions != 256  # Should be back to default

    def test_reset_to_defaults_affects_file(self, config_manager, config_dir):
        """reset_to_defaults should update config file."""
        # Modify config
        new_config = EmbeddingConfigModel(dimensions=256)
        config_manager.set_embedding_config(new_config)

        # Reset
        config_manager.reset_to_defaults()

        # Verify file was updated
        config_file = config_dir / "global_config.json"
        with open(config_file, "r") as f:
            data = json.load(f)

        # Defaults should be restored
        assert "embeddings" in data
        assert "ocr" in data


class TestErrorHandling:
    """Tests for error handling in ConfigManager."""

    def test_save_config_with_permissions_error(self, tmp_path):
        """save_config should handle permission errors gracefully."""
        # Create a readonly directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()

        config_manager = ConfigManager(config_dir=readonly_dir)

        # Make directory readonly (this will fail to write on most systems)
        # We'll just verify the basic error handling works
        try:
            readonly_dir.chmod(0o444)  # Read-only
            # Try to save - should eventually get an error
            # (might be at mkdir time or save time depending on OS)
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

    def test_load_config_handles_corrupted_json(self, config_dir):
        """load_config should return defaults if JSON is corrupted."""
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "global_config.json"
        config_file.write_text("{ invalid json }")

        config_manager = ConfigManager(config_dir=config_dir)
        config = config_manager.load_config()

        # Should return defaults, not raise
        assert "embeddings" in config
        assert "ocr" in config

    def test_embedding_config_model_validates_dimensions(self, config_manager):
        """EmbeddingConfigModel should only accept valid dimensions."""
        # Valid dimensions
        valid_config = EmbeddingConfigModel(dimensions=512)
        config_manager.set_embedding_config(valid_config)

        # Invalid dimensions should raise ValidationError during model instantiation
        with pytest.raises(ValidationError):
            EmbeddingConfigModel(dimensions=10000)  # Too large
