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


class TestHealthEndpoints:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["embeddings_loaded"] is True

    def test_stats(self, client, test_store):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert "total_embeddings" in data

    def test_list_collections(self, client):
        response = client.get("/api/collections")
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert len(data["collections"]) >= 1


class TestSearchEndpoint:
    def test_search_basic(self, client, test_embedder, test_store):
        docs = ["Machine learning is great", "AI is the future", "Deep learning rocks"]
        embeddings = [test_embedder.encode_text(doc, task="retrieval").tolist() for doc in docs]

        test_store.add_embeddings(
            collection_name="test_collection", embeddings=embeddings, documents=docs
        )

        response = client.post(
            "/api/search",
            json={"query": "artificial intelligence", "collection_name": "test_collection"},
        )

        if response.status_code != 200:
            print(f"Error response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
        assert data["query"] == "artificial intelligence"
        assert data["collection"] == "test_collection"

    def test_search_with_top_k(self, client, test_embedder, test_store):
        docs = ["Doc 1", "Doc 2", "Doc 3", "Doc 4", "Doc 5"]
        embeddings = [test_embedder.encode_text(doc, task="retrieval").tolist() for doc in docs]

        test_store.add_embeddings(
            collection_name="test_collection", embeddings=embeddings, documents=docs
        )

        response = client.post(
            "/api/search",
            json={"query": "document", "collection_name": "test_collection", "top_k": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 3

    def test_search_with_metadata_filter(self, client, test_embedder, test_store):
        docs = ["Red apple", "Green apple", "Yellow banana"]
        embeddings = [test_embedder.encode_text(doc, task="retrieval").tolist() for doc in docs]
        metadatas = [{"color": "red"}, {"color": "green"}, {"color": "yellow"}]

        test_store.add_embeddings(
            collection_name="test_collection",
            embeddings=embeddings,
            documents=docs,
            metadatas=metadatas,
        )

        response = client.post(
            "/api/search",
            json={
                "query": "fruit",
                "collection_name": "test_collection",
                "metadata_filter": {"color": "red"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) >= 1

    def test_search_invalid_collection(self, client):
        response = client.post(
            "/api/search", json={"query": "test", "collection_name": "nonexistent_collection"}
        )

        assert response.status_code == 500

    def test_search_validation(self, client):
        response = client.post("/api/search", json={"query": "test"})

        assert response.status_code == 422


class TestCaching:
    def test_query_caching(self, client, test_embedder, test_store):
        docs = ["Test document"]
        embeddings = [test_embedder.encode_text(doc, task="retrieval").tolist() for doc in docs]

        test_store.add_embeddings(
            collection_name="test_collection", embeddings=embeddings, documents=docs
        )

        response1 = client.post(
            "/api/search", json={"query": "test query", "collection_name": "test_collection"}
        )
        response2 = client.post(
            "/api/search", json={"query": "test query", "collection_name": "test_collection"}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()
