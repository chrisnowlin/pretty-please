import os
import tempfile
import shutil
import time
import threading
from pathlib import Path

import pytest
import numpy as np

from src.jina_rag_pipeline.storage import ChromaVectorStore, VectorStore


@pytest.fixture
def temp_storage_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def vector_store(temp_storage_dir: str) -> ChromaVectorStore:
    store = ChromaVectorStore(persist_directory=temp_storage_dir)
    yield store
    store.close()


@pytest.fixture
def sample_embeddings():
    np.random.seed(42)
    return [np.random.rand(128).tolist() for _ in range(10)]


class TestCollectionManagement:
    def test_create_collection(self, vector_store: VectorStore) -> None:
        vector_store.create_collection(
            name="test_collection", embedding_dimension=128
        )

        collections = vector_store.list_collections()
        assert len(collections) == 1
        assert collections[0].name == "test_collection"
        assert collections[0].count == 0

    def test_create_collection_with_metadata(self, vector_store: VectorStore) -> None:
        metadata = {"description": "Test collection", "version": "1.0"}
        vector_store.create_collection(
            name="test_collection", embedding_dimension=128, metadata=metadata
        )

        stats = vector_store.get_collection_stats("test_collection")
        assert stats.metadata["description"] == "Test collection"
        assert stats.metadata["version"] == "1.0"

    def test_list_collections(self, vector_store: VectorStore) -> None:
        vector_store.create_collection("collection1", embedding_dimension=128)
        vector_store.create_collection("collection2", embedding_dimension=256)

        collections = vector_store.list_collections()
        assert len(collections) == 2
        names = {c.name for c in collections}
        assert "collection1" in names
        assert "collection2" in names

    def test_delete_collection(self, vector_store: VectorStore) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        assert len(vector_store.list_collections()) == 1

        vector_store.delete_collection("test_collection")
        assert len(vector_store.list_collections()) == 0

    def test_get_collection_stats(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        vector_store.add_embeddings("test_collection", sample_embeddings)

        stats = vector_store.get_collection_stats("test_collection")
        assert stats.name == "test_collection"
        assert stats.count == 10


class TestEmbeddingOperations:
    def test_add_embeddings_without_ids(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)

        ids = vector_store.add_embeddings("test_collection", sample_embeddings[:3])

        assert len(ids) == 3
        assert all(isinstance(id, str) for id in ids)
        stats = vector_store.get_collection_stats("test_collection")
        assert stats.count == 3

    def test_add_embeddings_with_ids(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        custom_ids = ["id1", "id2", "id3"]

        returned_ids = vector_store.add_embeddings(
            "test_collection", sample_embeddings[:3], ids=custom_ids
        )

        assert returned_ids == custom_ids

    def test_add_embeddings_with_metadata(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        metadatas = [
            {"source": "doc1", "page": 1},
            {"source": "doc2", "page": 2},
            {"source": "doc3", "page": 3},
        ]

        ids = vector_store.add_embeddings(
            "test_collection", sample_embeddings[:3], metadatas=metadatas
        )

        result = vector_store.get_embedding("test_collection", ids[0])
        assert result is not None
        assert result.metadata == metadatas[0]

    def test_add_embeddings_with_documents(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        documents = ["Document 1", "Document 2", "Document 3"]

        ids = vector_store.add_embeddings(
            "test_collection", sample_embeddings[:3], documents=documents
        )

        result = vector_store.get_embedding("test_collection", ids[0])
        assert result is not None
        assert result.document == documents[0]

    def test_update_embedding(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        ids = vector_store.add_embeddings(
            "test_collection",
            sample_embeddings[:1],
            metadatas=[{"version": 1}],
            documents=["Original"],
        )

        vector_store.update_embedding(
            "test_collection",
            ids[0],
            metadata={"version": 2},
            document="Updated",
        )

        result = vector_store.get_embedding("test_collection", ids[0])
        assert result is not None
        assert result.metadata["version"] == 2
        assert result.document == "Updated"

    def test_delete_embedding(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        ids = vector_store.add_embeddings("test_collection", sample_embeddings[:3])

        vector_store.delete_embedding("test_collection", ids[0])

        result = vector_store.get_embedding("test_collection", ids[0])
        assert result is None

        stats = vector_store.get_collection_stats("test_collection")
        assert stats.count == 2

    def test_get_embedding(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        ids = vector_store.add_embeddings(
            "test_collection",
            sample_embeddings[:1],
            metadatas=[{"test": "data"}],
            documents=["Test document"],
        )

        result = vector_store.get_embedding("test_collection", ids[0])

        assert result is not None
        assert result.id == ids[0]
        assert result.embedding is not None
        assert len(result.embedding) == 128
        assert result.metadata == {"test": "data"}
        assert result.document == "Test document"

    def test_get_nonexistent_embedding(self, vector_store: VectorStore) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)

        result = vector_store.get_embedding("test_collection", "nonexistent_id")
        assert result is None


class TestSimilaritySearch:
    def test_similarity_search_basic(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        vector_store.add_embeddings("test_collection", sample_embeddings)

        query = sample_embeddings[0]
        results = vector_store.similarity_search(
            "test_collection", query, top_k=3
        )

        assert len(results) == 3
        assert all(r.score >= 0 for r in results)
        assert results[0].score >= results[1].score >= results[2].score

    def test_similarity_search_with_metadata_filter(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)

        metadatas = [{"category": "A"} if i % 2 == 0 else {"category": "B"} for i in range(10)]
        vector_store.add_embeddings(
            "test_collection", sample_embeddings, metadatas=metadatas
        )

        query = sample_embeddings[0]
        results = vector_store.similarity_search(
            "test_collection", query, top_k=10, metadata_filter={"category": "A"}
        )

        assert len(results) == 5
        assert all(r.metadata["category"] == "A" for r in results)

    def test_similarity_search_top_k(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        vector_store.add_embeddings("test_collection", sample_embeddings)

        query = sample_embeddings[0]

        results_5 = vector_store.similarity_search(
            "test_collection", query, top_k=5
        )
        assert len(results_5) == 5

        results_3 = vector_store.similarity_search(
            "test_collection", query, top_k=3
        )
        assert len(results_3) == 3

    def test_similarity_search_different_metrics(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        for metric in ["cosine", "l2"]:
            vector_store.create_collection(
                f"test_{metric}", embedding_dimension=128, distance_metric=metric
            )
            vector_store.add_embeddings(f"test_{metric}", sample_embeddings)

            query = sample_embeddings[0]
            results = vector_store.similarity_search(
                f"test_{metric}", query, top_k=3
            )

            assert len(results) == 3
            assert all(r.score >= 0 for r in results)


class TestPersistence:
    def test_persistence_across_restarts(
        self, temp_storage_dir: str, sample_embeddings: list
    ) -> None:
        store1 = ChromaVectorStore(persist_directory=temp_storage_dir)
        store1.create_collection("test_collection", embedding_dimension=128)
        ids = store1.add_embeddings(
            "test_collection",
            sample_embeddings[:5],
            metadatas=[{"index": i} for i in range(5)],
        )
        store1.close()

        store2 = ChromaVectorStore(persist_directory=temp_storage_dir)
        collections = store2.list_collections()
        assert len(collections) == 1
        assert collections[0].name == "test_collection"
        assert collections[0].count == 5

        result = store2.get_embedding("test_collection", ids[0])
        assert result is not None
        assert result.metadata["index"] == 0

        store2.close()


class TestConcurrency:
    def test_concurrent_writes(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)

        def add_batch(batch_id: int) -> None:
            ids = [f"{batch_id}_{i}" for i in range(5)]
            vector_store.add_embeddings(
                "test_collection", sample_embeddings[:5], ids=ids
            )

        threads = [threading.Thread(target=add_batch, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = vector_store.get_collection_stats("test_collection")
        assert stats.count == 20

    def test_concurrent_read_write(
        self, vector_store: VectorStore, sample_embeddings: list
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)
        ids = vector_store.add_embeddings("test_collection", sample_embeddings)

        results = []

        def read_embeddings() -> None:
            for _ in range(10):
                result = vector_store.similarity_search(
                    "test_collection", sample_embeddings[0], top_k=3
                )
                results.append(len(result))
                time.sleep(0.01)

        def write_embeddings() -> None:
            for _ in range(5):
                vector_store.add_embeddings(
                    "test_collection", [sample_embeddings[0]]
                )
                time.sleep(0.02)

        read_thread = threading.Thread(target=read_embeddings)
        write_thread = threading.Thread(target=write_embeddings)

        read_thread.start()
        write_thread.start()

        read_thread.join()
        write_thread.join()

        assert len(results) == 10
        assert all(r >= 3 for r in results)


class TestPerformance:
    def test_batch_add_performance(
        self, vector_store: VectorStore
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)

        np.random.seed(42)
        embeddings = [np.random.rand(128).tolist() for _ in range(100)]

        start_time = time.time()
        vector_store.add_embeddings("test_collection", embeddings)
        elapsed = time.time() - start_time

        assert elapsed < 5.0

        stats = vector_store.get_collection_stats("test_collection")
        assert stats.count == 100

    def test_search_performance(
        self, vector_store: VectorStore
    ) -> None:
        vector_store.create_collection("test_collection", embedding_dimension=128)

        np.random.seed(42)
        embeddings = [np.random.rand(128).tolist() for _ in range(1000)]
        vector_store.add_embeddings("test_collection", embeddings)

        query = embeddings[0]
        start_time = time.time()
        results = vector_store.similarity_search(
            "test_collection", query, top_k=10
        )
        elapsed = time.time() - start_time

        assert elapsed < 1.0
        assert len(results) == 10
