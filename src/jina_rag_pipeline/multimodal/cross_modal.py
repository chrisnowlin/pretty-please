"""Cross-modal search functionality for text-to-image and image-to-text retrieval."""

from typing import List, Dict, Any, Optional, Union, Literal
import logging
import numpy as np
from PIL import Image

from ..embeddings.config import EmbeddingConfig

logger = logging.getLogger(__name__)

SearchMode = Literal["text-to-image", "image-to-text", "image-to-image", "unified"]


class CrossModalSearch:
    """Enable cross-modal search between text and images."""
    
    def __init__(self, embedder, storage):
        """Initialize cross-modal search.
        
        Args:
            embedder: Embeddings model with text and image support
            storage: Vector storage backend
        """
        self.embedder = embedder
        self.storage = storage
        
    def search_text_to_image(
        self,
        query: str,
        collection: str = "default",
        n_results: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for images using text query.
        
        Args:
            query: Text query
            collection: Collection name
            n_results: Number of results to return
            metadata_filter: Filter by metadata
            
        Returns:
            List of search results with images
        """
        # Generate text embedding
        config = EmbeddingConfig.for_query()
        query_embedding = self.embedder.embed_with_config([query], config)[0]
        
        # Add filter for image results
        if metadata_filter is None:
            metadata_filter = {}
        metadata_filter["content_type"] = "image"
        
        # Search in vector store
        results = self.storage.similarity_search(
            collection_name=collection,
            query_embedding=query_embedding,
            top_k=n_results,
            metadata_filter=metadata_filter
        )
        
        return results
        
    def search_image_to_text(
        self,
        image: Union[str, Image.Image],
        collection: str = "default",
        n_results: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for text using image query.
        
        Args:
            image: Image query (path or PIL Image)
            collection: Collection name
            n_results: Number of results to return
            metadata_filter: Filter by metadata
            
        Returns:
            List of search results with text
        """
        # Generate image embedding
        query_embedding = self.embedder.encode_image(image, task="retrieval")
        
        # Add filter for text results
        if metadata_filter is None:
            metadata_filter = {}
        metadata_filter["content_type"] = "text"
        
        # Search in vector store
        results = self.storage.similarity_search(
            collection_name=collection,
            query_embedding=query_embedding,
            top_k=n_results,
            metadata_filter=metadata_filter
        )
        
        return results
        
    def search_image_to_image(
        self,
        image: Union[str, Image.Image],
        collection: str = "default",
        n_results: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
        exclude_self: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for similar images using image query.
        
        Args:
            image: Image query (path or PIL Image)
            collection: Collection name
            n_results: Number of results to return
            metadata_filter: Filter by metadata
            exclude_self: Exclude the query image from results
            
        Returns:
            List of search results with similar images
        """
        # Generate image embedding
        query_embedding = self.embedder.encode_image(image, task="retrieval")
        
        # Add filter for image results
        if metadata_filter is None:
            metadata_filter = {}
        metadata_filter["content_type"] = "image"
        
        # Search in vector store
        results = self.storage.similarity_search(
            collection_name=collection,
            query_embedding=query_embedding,
            top_k=n_results,
            metadata_filter=metadata_filter
        )
        
        # Exclude self if needed
        if exclude_self and results:
            # Skip first result if it's too similar (likely the same image)
            if results[0]["distance"] < 0.01:
                results = results[1:]
            else:
                results = results[:n_results]
                
        return results
        
    def unified_search(
        self,
        query: Union[str, Image.Image],
        collection: str = "default",
        n_results: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
        result_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Unified search across all content types.
        
        Args:
            query: Text or image query
            collection: Collection name
            n_results: Number of results to return
            metadata_filter: Filter by metadata
            result_types: Filter result types (e.g., ["text", "image"])
            
        Returns:
            List of mixed search results
        """
        # Generate appropriate embedding
        if isinstance(query, str):
            config = EmbeddingConfig.for_query()
            query_embedding = self.embedder.embed_with_config([query], config)[0]
        else:
            query_embedding = self.embedder.encode_image(query, task="retrieval")
            
        # Apply result type filter if specified
        if result_types and metadata_filter is None:
            metadata_filter = {}
        if result_types:
            metadata_filter["content_type"] = {"$in": result_types}
            
        # Search in vector store
        results = self.storage.similarity_search(
            collection_name=collection,
            query_embedding=query_embedding,
            top_k=n_results,
            metadata_filter=metadata_filter
        )
        
        return results
        
    def index_multimodal_document(
        self,
        document_id: str,
        text_content: Optional[str] = None,
        image_content: Optional[Union[str, Image.Image]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        collection: str = "default"
    ):
        """Index a document with both text and image content.
        
        Args:
            document_id: Unique document ID
            text_content: Text content to index
            image_content: Image content to index
            metadata: Additional metadata
            collection: Collection name
        """
        if metadata is None:
            metadata = {}
            
        embeddings = []
        texts = []
        metadatas = []
        ids = []
        
        # Index text content
        if text_content:
            config = EmbeddingConfig.for_documents()
            text_embedding = self.embedder.embed_with_config([text_content], config)[0]
            embeddings.append(text_embedding)
            texts.append(text_content)
            
            text_meta = metadata.copy()
            text_meta["content_type"] = "text"
            text_meta["document_id"] = document_id
            metadatas.append(text_meta)
            ids.append(f"{document_id}_text")
            
        # Index image content
        if image_content:
            image_embedding = self.embedder.encode_image(image_content, task="retrieval")
            embeddings.append(image_embedding)
            
            # Store image reference
            if isinstance(image_content, str):
                texts.append(f"Image: {image_content}")
            else:
                texts.append(f"Image: {document_id}")
                
            image_meta = metadata.copy()
            image_meta["content_type"] = "image"
            image_meta["document_id"] = document_id
            metadatas.append(image_meta)
            ids.append(f"{document_id}_image")
            
        # Add to storage
        if embeddings:
            self.storage.add_embeddings(
                collection_name=collection,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas,
                documents=texts
            )
            
    def rerank_results(
        self,
        results: List[Dict[str, Any]],
        query: Union[str, Image.Image],
        use_cross_attention: bool = False
    ) -> List[Dict[str, Any]]:
        """Rerank search results using cross-modal similarity.
        
        Args:
            results: Initial search results
            query: Original query
            use_cross_attention: Use cross-attention scoring (if available)
            
        Returns:
            Reranked results
        """
        if not results:
            return results
            
        # For simple reranking, use cosine similarity
        # In production, use more sophisticated cross-modal models
        
        # Get query embedding
        if isinstance(query, str):
            config = EmbeddingConfig(task="text-matching", late_chunking=False)
            query_emb = self.embedder.embed_with_config([query], config)[0]
        else:
            query_emb = self.embedder.encode_image(query, task="retrieval")
            
        # Score each result
        for result in results:
            # Get result embedding (would be stored in real system)
            if result.get("metadata", {}).get("content_type") == "image":
                # For images, compute cross-modal similarity
                result["cross_modal_score"] = result["distance"]
            else:
                # For text, use text similarity
                result["cross_modal_score"] = result["distance"]
                
        # Sort by cross-modal score
        results.sort(key=lambda x: x.get("cross_modal_score", 1.0))
        
        return results