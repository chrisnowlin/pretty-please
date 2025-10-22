"""Integration tests for configuration API endpoints."""
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from src.jina_rag_pipeline.api import create_app
from src.jina_rag_pipeline.api.config_manager import ConfigManager
from src.jina_rag_pipeline.embeddings import JinaEmbeddingsV4
from src.jina_rag_pipeline.storage import ChromaVectorStore


@pytest.fixture
def config_dir(tmp_path):
    """Provide a temporary directory for config files."""
    return tmp_path / "config"


@pytest.fixture
def config_manager(config_dir):
    """Create a ConfigManager with temporary directory."""
    return ConfigManager(config_dir=config_dir)


@pytest.fixture
def test_store(tmp_path):
    """Create a test vector store."""
    store = ChromaVectorStore(persist_directory=str(tmp_path / "test_db"))
    store.create_collection("test_collection", embedding_dimension=2048)
    yield store


@pytest.fixture
def test_embedder():
    """Create a test embedder."""
    embedder = JinaEmbeddingsV4(device="cpu")
    yield embedder


@pytest.fixture
def client(test_embedder, test_store, config_manager):
    """Create a test client with config manager."""
    app = create_app(
        embedder=test_embedder,
        vector_store=test_store,
        enable_cors=False,
        config_manager=config_manager
    )
    with TestClient(app) as c:
        yield c


class TestEmbeddingConfigEndpoints:
    """Tests for embedding configuration endpoints."""

    def test_get_embedding_config_returns_current_config(self, client):
        """GET /api/config/embeddings should return current configuration."""
        response = client.get("/api/config/embeddings")

        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        config = data["config"]
        assert "dimensions" in config
        assert "task" in config
        assert "batch_size" in config

    def test_get_embedding_config_has_preset(self, client):
        """GET /api/config/embeddings response should include preset."""
        response = client.get("/api/config/embeddings")

        assert response.status_code == 200
        data = response.json()
        assert "preset" in data

    def test_post_embedding_config_updates_configuration(self, client):
        """POST /api/config/embeddings should update configuration."""
        new_config = {
            "task": "retrieval.query",
            "dimensions": 512,
            "batch_size": 64
        }

        response = client.post("/api/config/embeddings", json=new_config)

        assert response.status_code == 200
        data = response.json()
        assert data["config"]["task"] == "retrieval.query"
        assert data["config"]["dimensions"] == 512
        assert data["config"]["batch_size"] == 64

    def test_post_embedding_config_persists_changes(self, client):
        """Configuration changes should persist across requests."""
        # Set new config
        new_config = {
            "task": "retrieval.passage",
            "dimensions": 256,
            "late_chunking": False
        }
        client.post("/api/config/embeddings", json=new_config)

        # Get config again
        response = client.get("/api/config/embeddings")
        assert response.status_code == 200
        retrieved = response.json()["config"]

        # Changes should be present
        assert retrieved["task"] == "retrieval.passage"
        assert retrieved["dimensions"] == 256
        assert retrieved["late_chunking"] is False

    def test_post_embedding_config_with_partial_data(self, client):
        """POST should handle partial configuration updates."""
        partial_config = {"dimensions": 768}

        response = client.post("/api/config/embeddings", json=partial_config)

        assert response.status_code == 200
        data = response.json()
        assert data["config"]["dimensions"] == 768

    def test_post_embedding_config_invalid_dimensions(self, client):
        """POST with invalid dimensions should return 400."""
        invalid_config = {"dimensions": 10000}  # Too large

        response = client.post("/api/config/embeddings", json=invalid_config)

        assert response.status_code == 400

    def test_post_embedding_config_invalid_type(self, client):
        """POST with wrong type should return 422."""
        invalid_config = {"dimensions": "invalid"}

        response = client.post("/api/config/embeddings", json=invalid_config)

        assert response.status_code in [400, 422]

    def test_embedding_config_response_structure(self, client):
        """Embedding config response should have required structure."""
        response = client.get("/api/config/embeddings")

        data = response.json()
        assert "config" in data
        assert "preset" in data

        config = data["config"]
        required_fields = [
            "task", "dimensions", "batch_size", "late_chunking",
            "return_multivector", "embedding_format", "max_tokens_per_batch"
        ]
        for field in required_fields:
            assert field in config


class TestOCRConfigEndpoints:
    """Tests for OCR configuration endpoints."""

    def test_get_ocr_config_returns_current_config(self, client):
        """GET /api/config/ocr should return current configuration."""
        response = client.get("/api/config/ocr")

        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        config = data["config"]
        assert "batch_size" in config
        assert "render_workers" in config
        assert "resolution_mode" in config
        assert "enable_grounding" in config
        assert "enable_compression" in config
        assert "use_vllm" in config

    def test_get_ocr_config_has_preset(self, client):
        """GET /api/config/ocr response should include preset."""
        response = client.get("/api/config/ocr")

        assert response.status_code == 200
        data = response.json()
        assert "preset" in data

    def test_post_ocr_config_updates_configuration(self, client):
        """POST /api/config/ocr should update configuration."""
        new_config = {
            "batch_size": 32,
            "render_workers": 4,
            "analysis_workers": 2,
            "resolution_mode": "large",
            "enable_grounding": False,
            "enable_compression": True,
            "use_vllm": True,
        }

        response = client.post("/api/config/ocr", json=new_config)

        assert response.status_code == 200
        data = response.json()
        assert data["config"]["batch_size"] == 32
        assert data["config"]["render_workers"] == 4
        assert data["config"]["resolution_mode"] == "large"
        assert data["config"]["enable_grounding"] is False
        assert data["config"]["use_vllm"] is True

    def test_post_ocr_config_persists_changes(self, client):
        """OCR configuration changes should persist across requests."""
        # Set new config
        new_config = {
            "batch_size": 16,
            "resolution_mode": "small",
            "enable_grounding": True,
            "enable_compression": False
        }
        client.post("/api/config/ocr", json=new_config)

        # Get config again
        response = client.get("/api/config/ocr")
        assert response.status_code == 200
        retrieved = response.json()["config"]

        # Changes should be present
        assert retrieved["batch_size"] == 16
        assert retrieved["resolution_mode"] == "small"
        assert retrieved["enable_grounding"] is True
        assert retrieved["enable_compression"] is False

    def test_post_ocr_config_invalid_batch_size(self, client):
        """POST with negative batch_size should return error."""
        invalid_config = {"batch_size": -1}

        response = client.post("/api/config/ocr", json=invalid_config)

        assert response.status_code == 400

    def test_post_ocr_config_invalid_workers(self, client):
        """POST with negative workers should return error."""
        invalid_config = {"render_workers": -2}

        response = client.post("/api/config/ocr", json=invalid_config)

        assert response.status_code == 400

    def test_ocr_config_response_structure(self, client):
        """OCR config response should have required structure."""
        response = client.get("/api/config/ocr")

        data = response.json()
        assert "config" in data
        assert "preset" in data

        config = data["config"]
        required_fields = [
            "batch_size", "render_workers", "analysis_workers",
            "resolution_mode", "enable_grounding",
            "enable_compression", "use_vllm"
        ]
        for field in required_fields:
            assert field in config


class TestEmbeddingPresetsEndpoints:
    """Tests for embedding preset listing endpoints."""

    def test_get_embedding_presets_returns_list(self, client):
        """GET /api/config/embeddings/presets should return list of presets."""
        response = client.get("/api/config/embeddings/presets")

        assert response.status_code == 200
        presets = response.json()
        assert isinstance(presets, list)
        assert len(presets) > 0

    def test_embedding_presets_have_required_fields(self, client):
        """Each preset should have name, description, and characteristics."""
        response = client.get("/api/config/embeddings/presets")
        presets = response.json()

        for preset in presets:
            assert "name" in preset
            assert "description" in preset
            assert isinstance(preset["name"], str)
            assert isinstance(preset["description"], str)

    def test_embedding_presets_include_documented_presets(self, client):
        """Presets should include expected preset names."""
        response = client.get("/api/config/embeddings/presets")
        presets = response.json()
        preset_names = [p["name"] for p in presets]

        # Should include documented presets
        expected_presets = {"for_documents", "for_query", "fast", "storage_optimized"}
        found_presets = set(preset_names) & expected_presets
        assert len(found_presets) > 0


class TestOCRPresetsEndpoints:
    """Tests for OCR preset listing endpoints."""

    def test_get_ocr_presets_returns_list(self, client):
        """GET /api/config/ocr/presets should return list of presets."""
        response = client.get("/api/config/ocr/presets")

        assert response.status_code == 200
        presets = response.json()
        assert isinstance(presets, list)
        assert len(presets) > 0

    def test_ocr_presets_have_required_fields(self, client):
        """Each OCR preset should have name and description."""
        response = client.get("/api/config/ocr/presets")
        presets = response.json()

        for preset in presets:
            assert "name" in preset
            assert "description" in preset

    def test_ocr_presets_include_documented_presets(self, client):
        """Presets should include expected preset names."""
        response = client.get("/api/config/ocr/presets")
        presets = response.json()
        preset_names = [p["name"] for p in presets]

        # Should include documented presets
        expected_presets = {
            "deepseek_tiny",
            "deepseek_small",
            "deepseek_balanced",
            "deepseek_high_quality",
            "deepseek_gundam",
        }
        found_presets = set(preset_names) & expected_presets
        assert len(found_presets) > 0


class TestConfigurationPersistenceAcrossInstances:
    """Tests for configuration persistence across different client instances."""

    def test_embedding_config_persists_across_new_app(self, test_embedder, test_store, config_dir):
        """Configuration changes should persist when creating new app instance."""
        # First client - set configuration
        config_mgr1 = ConfigManager(config_dir=config_dir)
        app1 = create_app(
            embedder=test_embedder,
            vector_store=test_store,
            config_manager=config_mgr1
        )

        with TestClient(app1) as client1:
            new_config = {"dimensions": 512, "task": "retrieval.passage"}
            client1.post("/api/config/embeddings", json=new_config)

        # Second client - read configuration
        config_mgr2 = ConfigManager(config_dir=config_dir)
        app2 = create_app(
            embedder=test_embedder,
            vector_store=test_store,
            config_manager=config_mgr2
        )

        with TestClient(app2) as client2:
            response = client2.get("/api/config/embeddings")
            config = response.json()["config"]
            assert config["dimensions"] == 512
            assert config["task"] == "retrieval.passage"

    def test_ocr_config_persists_across_new_app(self, test_embedder, test_store, config_dir):
        """OCR configuration changes should persist across app instances."""
        # First client - set configuration
        config_mgr1 = ConfigManager(config_dir=config_dir)
        app1 = create_app(
            embedder=test_embedder,
            vector_store=test_store,
            config_manager=config_mgr1
        )

        with TestClient(app1) as client1:
            new_config = {
                "batch_size": 24,
                "render_workers": 3,
                "resolution_mode": "gundam",
                "enable_grounding": True,
                "enable_compression": True,
                "use_vllm": False,
            }
            client1.post("/api/config/ocr", json=new_config)

        # Second client - read configuration
        config_mgr2 = ConfigManager(config_dir=config_dir)
        app2 = create_app(
            embedder=test_embedder,
            vector_store=test_store,
            config_manager=config_mgr2
        )

        with TestClient(app2) as client2:
            response = client2.get("/api/config/ocr")
            config = response.json()["config"]
            assert config["batch_size"] == 24
            assert config["render_workers"] == 3
            assert config["resolution_mode"] == "gundam"
            assert config["enable_grounding"] is True


class TestConfigErrorCases:
    """Tests for error cases in configuration endpoints."""

    def test_missing_config_manager_returns_500(self, test_embedder, test_store):
        """If config_manager is not initialized, should return 500."""
        # Create app without config_manager
        app = create_app(
            embedder=test_embedder,
            vector_store=test_store,
            enable_cors=False,
            config_manager=None
        )

        with TestClient(app) as client:
            response = client.get("/api/config/embeddings")
            assert response.status_code == 500

    def test_invalid_json_returns_422(self, client):
        """Invalid JSON should return 422."""
        response = client.post(
            "/api/config/embeddings",
            content="invalid json",
            headers={"content-type": "application/json"}
        )

        assert response.status_code == 422

    def test_missing_required_fields_still_updates(self, client):
        """Should allow updates with only subset of fields."""
        # Only update dimensions
        response = client.post(
            "/api/config/embeddings",
            json={"dimensions": 384}
        )

        assert response.status_code == 200
        assert response.json()["config"]["dimensions"] == 384


class TestConfigurationConsistency:
    """Tests for configuration consistency across requests."""

    def test_multiple_sequential_updates(self, client):
        """Multiple sequential updates should each take effect."""
        # Update 1
        client.post("/api/config/embeddings", json={"dimensions": 256})
        response1 = client.get("/api/config/embeddings")
        assert response1.json()["config"]["dimensions"] == 256

        # Update 2
        client.post("/api/config/embeddings", json={"dimensions": 512})
        response2 = client.get("/api/config/embeddings")
        assert response2.json()["config"]["dimensions"] == 512

        # Update 3
        client.post("/api/config/embeddings", json={"dimensions": 768})
        response3 = client.get("/api/config/embeddings")
        assert response3.json()["config"]["dimensions"] == 768

    def test_embedding_and_ocr_configs_independent(self, client):
        """Changes to embedding config should not affect OCR config."""
        # Get initial configs
        emb_initial = client.get("/api/config/embeddings").json()
        ocr_initial = client.get("/api/config/ocr").json()

        # Update embedding config
        client.post("/api/config/embeddings", json={"dimensions": 256})

        # OCR config should be unchanged
        ocr_after = client.get("/api/config/ocr").json()
        assert ocr_after["config"]["batch_size"] == ocr_initial["config"]["batch_size"]

        # Update OCR config
        client.post("/api/config/ocr", json={"batch_size": 32})

        # Embedding config should be unchanged from our update
        emb_after = client.get("/api/config/embeddings").json()
        assert emb_after["config"]["dimensions"] == 256  # Should still be our update
