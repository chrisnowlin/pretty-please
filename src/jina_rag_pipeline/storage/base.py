from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass


DistanceMetric = Literal["cosine", "l2", "ip"]


@dataclass
class SearchResult:
    id: str
    score: float
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    document: Optional[str] = None


@dataclass
class CollectionInfo:
    name: str
    count: int
    metadata: Optional[Dict[str, Any]] = None


class VectorStore(ABC):
    @abstractmethod
    def create_collection(
        self,
        name: str,
        embedding_dimension: int,
        distance_metric: DistanceMetric = "cosine",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        pass

    @abstractmethod
    def list_collections(self) -> List[CollectionInfo]:
        pass

    @abstractmethod
    def delete_collection(self, name: str) -> None:
        pass

    @abstractmethod
    def get_collection_stats(self, name: str) -> CollectionInfo:
        pass

    @abstractmethod
    def add_embeddings(
        self,
        collection_name: str,
        embeddings: List[List[float]],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[str]] = None,
    ) -> List[str]:
        pass

    @abstractmethod
    def update_embedding(
        self,
        collection_name: str,
        id: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        document: Optional[str] = None,
    ) -> None:
        pass

    @abstractmethod
    def delete_embedding(self, collection_name: str, id: str) -> None:
        pass

    @abstractmethod
    def get_embedding(self, collection_name: str, id: str) -> Optional[SearchResult]:
        pass

    @abstractmethod
    def similarity_search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
