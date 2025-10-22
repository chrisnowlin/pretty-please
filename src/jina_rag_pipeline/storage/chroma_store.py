import os
import uuid
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings

from .base import VectorStore, SearchResult, CollectionInfo, DistanceMetric


class ChromaVectorStore(VectorStore):
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        client_settings: Optional[Settings] = None,
    ):
        if persist_directory is None:
            persist_directory = os.path.join(os.getcwd(), ".chroma_db")

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        settings = client_settings or Settings(
            persist_directory=str(self.persist_directory),
            anonymized_telemetry=False,
        )

        self._client = chromadb.PersistentClient(
            path=str(self.persist_directory), settings=settings
        )
        self._lock = threading.Lock()
        self._collections_cache: Dict[str, Any] = {}

    def _get_distance_function(self, metric: DistanceMetric) -> str:
        metric_map = {"cosine": "cosine", "l2": "l2", "ip": "ip"}
        return metric_map.get(metric, "cosine")

    def create_collection(
        self,
        name: str,
        embedding_dimension: int,
        distance_metric: DistanceMetric = "cosine",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock:
            collection_metadata = metadata or {}
            collection_metadata["embedding_dimension"] = embedding_dimension
            collection_metadata["distance_metric"] = distance_metric

            self._client.create_collection(
                name=name, metadata=collection_metadata
            )

            self._collections_cache.pop(name, None)

    def list_collections(self) -> List[CollectionInfo]:
        collections = self._client.list_collections()
        return [
            CollectionInfo(
                name=col.name, count=col.count(), metadata=col.metadata or {}
            )
            for col in collections
        ]

    def delete_collection(self, name: str) -> None:
        with self._lock:
            self._client.delete_collection(name=name)
            self._collections_cache.pop(name, None)

    def get_collection_stats(self, name: str) -> CollectionInfo:
        collection = self._get_collection(name)
        return CollectionInfo(
            name=collection.name, count=collection.count(), metadata=collection.metadata
        )

    def _get_collection(self, name: str) -> Any:
        if name not in self._collections_cache:
            self._collections_cache[name] = self._client.get_collection(
                name=name, embedding_function=None
            )
        return self._collections_cache[name]

    def add_embeddings(
        self,
        collection_name: str,
        embeddings: List[List[float]],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[str]] = None,
    ) -> List[str]:
        collection = self._get_collection(collection_name)

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]

        with self._lock:
            collection.add(
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas,
                documents=documents,
            )

        return ids

    def update_embedding(
        self,
        collection_name: str,
        id: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        document: Optional[str] = None,
    ) -> None:
        collection = self._get_collection(collection_name)

        if embedding is None and document is not None:
            existing = collection.get(ids=[id], include=["embeddings"])
            if existing["ids"] and existing["embeddings"] is not None:
                embedding = existing["embeddings"][0]

        update_kwargs: Dict[str, Any] = {"ids": [id]}

        if embedding is not None:
            update_kwargs["embeddings"] = [embedding]
        if metadata is not None:
            update_kwargs["metadatas"] = [metadata]
        if document is not None:
            update_kwargs["documents"] = [document]

        with self._lock:
            collection.update(**update_kwargs)

    def delete_embedding(self, collection_name: str, id: str) -> None:
        collection = self._get_collection(collection_name)

        with self._lock:
            collection.delete(ids=[id])

    def get_embedding(
        self, collection_name: str, id: str
    ) -> Optional[SearchResult]:
        collection = self._get_collection(collection_name)

        result = collection.get(ids=[id], include=["embeddings", "metadatas", "documents"])

        if not result["ids"]:
            return None

        return SearchResult(
            id=result["ids"][0],
            score=1.0,
            embedding=result["embeddings"][0] if result["embeddings"] is not None else None,
            metadata=result["metadatas"][0] if result["metadatas"] else None,
            document=result["documents"][0] if result["documents"] else None,
        )

    def similarity_search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        collection = self._get_collection(collection_name)

        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["embeddings", "metadatas", "documents", "distances"],
        }

        if metadata_filter:
            query_kwargs["where"] = metadata_filter

        results = collection.query(**query_kwargs)

        search_results = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i] if results["distances"] else 0.0
            score = max(0.0, 1.0 - distance)
            
            search_results.append(
                SearchResult(
                    id=results["ids"][0][i],
                    score=score,
                    embedding=results["embeddings"][0][i]
                    if results["embeddings"] is not None
                    else None,
                    metadata=results["metadatas"][0][i]
                    if results["metadatas"]
                    else None,
                    document=results["documents"][0][i]
                    if results["documents"]
                    else None,
                )
            )

        return search_results

    def close(self) -> None:
        with self._lock:
            self._collections_cache.clear()
