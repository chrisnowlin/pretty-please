import io
import pytest
from fastapi.testclient import TestClient

from src.jina_rag_pipeline.api import create_app
from src.jina_rag_pipeline.embeddings import JinaEmbeddingsV4
from src.jina_rag_pipeline.storage import ChromaVectorStore


@pytest.fixture
def test_store(tmp_path):
    store = ChromaVectorStore(persist_directory=str(tmp_path / "test_db"))
    store.create_collection("test_collection", embedding_dimension=2048)
    yield store


@pytest.fixture
def test_embedder():
    embedder = JinaEmbeddingsV4(device="cpu")
    yield embedder


@pytest.fixture
def client(test_embedder, test_store):
    app = create_app(embedder=test_embedder, vector_store=test_store, enable_cors=False)
    with TestClient(app) as c:
        yield c


class TestIngestionEndpoints:
    def test_get_supported_formats(self, client):
        response = client.get("/api/ingest/supported-formats")
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert "max_file_size_mb" in data
        assert isinstance(data["formats"], list)
        assert len(data["formats"]) > 0

    def test_upload_documents(self, client):
        file_content = b"This is a test document for ingestion."
        files = {
            "files": ("test.txt", io.BytesIO(file_content), "text/plain")
        }
        data = {"collection_name": "test_collection"}
        
        response = client.post("/api/ingest/upload", files=files, data=data)
        assert response.status_code == 200
        result = response.json()
        assert "task_id" in result
        assert "files" in result
        assert len(result["files"]) == 1
        assert result["files"][0]["name"] == "test.txt"
        assert result["files"][0]["status"] in ["queued", "processing"]

    def test_upload_multiple_documents(self, client):
        files = [
            ("files", ("test1.txt", io.BytesIO(b"Document 1"), "text/plain")),
            ("files", ("test2.txt", io.BytesIO(b"Document 2"), "text/plain"))
        ]
        data = {"collection_name": "test_collection"}
        
        response = client.post("/api/ingest/upload", files=files, data=data)
        assert response.status_code == 200
        result = response.json()
        assert "task_id" in result
        assert len(result["files"]) == 2

    def test_upload_unsupported_format(self, client):
        files = {
            "files": ("test.xyz", io.BytesIO(b"test"), "application/octet-stream")
        }
        data = {"collection_name": "test_collection"}
        
        response = client.post("/api/ingest/upload", files=files, data=data)
        assert response.status_code == 200
        result = response.json()
        assert result["files"][0]["status"] == "failed"
        assert "Unsupported file format" in result["files"][0]["error"]

    def test_get_ingestion_status(self, client):
        file_content = b"Test document"
        files = {
            "files": ("test.txt", io.BytesIO(file_content), "text/plain")
        }
        data = {"collection_name": "test_collection"}
        
        upload_response = client.post("/api/ingest/upload", files=files, data=data)
        task_id = upload_response.json()["task_id"]
        
        status_response = client.get(f"/api/ingest/status/{task_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "task_id" in status_data
        assert "status" in status_data
        assert "progress" in status_data
        assert "processed_files" in status_data
        assert "total_files" in status_data

    def test_get_ingestion_status_not_found(self, client):
        response = client.get("/api/ingest/status/nonexistent-task-id")
        assert response.status_code == 404


class TestIngestionValidation:
    def test_upload_without_collection(self, client):
        files = {
            "files": ("test.txt", io.BytesIO(b"test"), "text/plain")
        }
        
        response = client.post("/api/ingest/upload", files=files)
        assert response.status_code == 422

    def test_upload_without_files(self, client):
        data = {"collection_name": "test_collection"}
        
        response = client.post("/api/ingest/upload", data=data)
        assert response.status_code == 422
