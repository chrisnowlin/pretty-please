"""ColBERT-style late interaction and multi-vector retrieval."""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import logging

from ..embeddings.config import EmbeddingConfig

logger = logging.getLogger(__name__)


class ColBERTRetriever:
    """Implements ColBERT-style late interaction retrieval."""
    
    def __init__(self, embedder, storage):
        """Initialize ColBERT retriever.
        
        Args:
            embedder: Embedding model with multi-vector support
            storage: Vector storage backend
        """
        self.embedder = embedder
        self.storage = storage
        
    def encode_query_multivector(
        self,
        query: str,
        max_length: int = 128
    ) -> np.ndarray:
        """Encode query into multiple vectors (one per token).
        
        Args:
            query: Query text
            max_length: Maximum sequence length
            
        Returns:
            Array of shape (num_tokens, embedding_dim)
        """
        # Get multi-vector embeddings
        config = EmbeddingConfig.for_query(return_multivector=True)
        query_embeddings = self.embedder.embed_with_config([query], config)[0]
        
        # Ensure 2D array
        if len(query_embeddings.shape) == 1:
            query_embeddings = query_embeddings.reshape(1, -1)
        elif len(query_embeddings.shape) == 3:
            # Batch dimension, take first
            query_embeddings = query_embeddings[0]
            
        return query_embeddings
    
    def encode_document_multivector(
        self,
        document: str,
        max_length: int = 512
    ) -> np.ndarray:
        """Encode document into multiple vectors.
        
        Args:
            document: Document text
            max_length: Maximum sequence length
            
        Returns:
            Array of shape (num_tokens, embedding_dim)
        """
        config = EmbeddingConfig.for_documents(return_multivector=True)
        doc_embeddings = self.embedder.embed_with_config([document], config)[0]
        
        # Ensure 2D array
        if len(doc_embeddings.shape) == 1:
            doc_embeddings = doc_embeddings.reshape(1, -1)
        elif len(doc_embeddings.shape) == 3:
            # Batch dimension, take first
            doc_embeddings = doc_embeddings[0]
            
        return doc_embeddings
    
    def late_interaction_score(
        self,
        query_embeddings: np.ndarray,
        doc_embeddings: np.ndarray,
        use_max_sim: bool = True
    ) -> float:
        """Compute late interaction score between query and document.
        
        Args:
            query_embeddings: Query multi-vector embeddings (Q x D)
            doc_embeddings: Document multi-vector embeddings (L x D)
            use_max_sim: Use MaxSim scoring (True) or average (False)
            
        Returns:
            Similarity score
        """
        # Compute all pairwise similarities
        # Shape: (num_query_tokens, num_doc_tokens)
        similarities = np.dot(query_embeddings, doc_embeddings.T)
        
        if use_max_sim:
            # MaxSim: for each query token, take max similarity to any doc token
            max_sims = np.max(similarities, axis=1)
            # Average over query tokens
            score = np.mean(max_sims)
        else:
            # Average all similarities
            score = np.mean(similarities)
            
        return float(score)
    
    def search_with_late_interaction(
        self,
        query: str,
        collection: str = "default",
        n_results: int = 10,
        initial_candidates: int = 100,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search using ColBERT late interaction.
        
        Args:
            query: Query text
            collection: Collection name
            n_results: Final number of results
            initial_candidates: Number of candidates for reranking
            metadata_filter: Metadata filter
            
        Returns:
            Reranked search results
        """
        # Step 1: Encode query as multi-vector
        query_multivec = self.encode_query_multivector(query)
        
        # Step 2: Get mean query vector for initial retrieval
        query_mean = np.mean(query_multivec, axis=0)
        
        # Step 3: Initial retrieval with mean vector
        initial_results = self.storage.search(
            query_embedding=query_mean,
            collection_name=collection,
            n_results=initial_candidates,
            metadata_filter=metadata_filter
        )
        
        # Step 4: Rerank with late interaction
        reranked_results = []
        
        for result in initial_results:
            # Get document text
            doc_text = result.get('text', '')
            
            # Skip if no text
            if not doc_text:
                continue
                
            # Encode document as multi-vector
            doc_multivec = self.encode_document_multivector(doc_text)
            
            # Compute late interaction score
            late_score = self.late_interaction_score(query_multivec, doc_multivec)
            
            # Add score to result
            result['colbert_score'] = late_score
            result['original_distance'] = result.get('distance', 0)
            reranked_results.append(result)
        
        # Step 5: Sort by ColBERT score
        reranked_results.sort(key=lambda x: x['colbert_score'], reverse=True)
        
        # Return top N
        return reranked_results[:n_results]
    
    def index_with_multivector(
        self,
        documents: List[str],
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
        collection: str = "default",
        batch_size: int = 32
    ):
        """Index documents with multi-vector representations.
        
        Args:
            documents: List of documents
            ids: Document IDs
            metadata: Document metadata
            collection: Collection name
            batch_size: Batch size for encoding
        """
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        if metadata is None:
            metadata = [{}] * len(documents)
            
        all_embeddings = []
        all_texts = []
        all_ids = []
        all_metadata = []
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            batch_meta = metadata[i:i+batch_size]
            
            for j, doc in enumerate(batch_docs):
                # Get multi-vector embeddings
                doc_multivec = self.encode_document_multivector(doc)
                
                # Store mean vector for initial retrieval
                mean_vec = np.mean(doc_multivec, axis=0)
                all_embeddings.append(mean_vec)
                all_texts.append(doc)
                all_ids.append(batch_ids[j])
                
                # Store multi-vector info in metadata
                meta = batch_meta[j].copy()
                meta['has_multivector'] = True
                meta['num_vectors'] = len(doc_multivec)
                all_metadata.append(meta)
                
        # Add to storage
        if all_embeddings:
            self.storage.add(
                embeddings=np.array(all_embeddings),
                texts=all_texts,
                metadata=all_metadata,
                ids=all_ids,
                collection_name=collection
            )
            logger.info(f"Indexed {len(documents)} documents with multi-vector representations")


class OptimizedMultiVectorSearch:
    """Optimized multi-vector search with caching and batching."""
    
    def __init__(self, retriever: ColBERTRetriever):
        """Initialize optimized search.
        
        Args:
            retriever: ColBERT retriever instance
        """
        self.retriever = retriever
        self._cache = {}
        self._max_cache_size = 1000
        
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_cached_multivector(self, text: str, is_query: bool = False) -> Optional[np.ndarray]:
        """Get cached multi-vector if available."""
        cache_key = f"{'q' if is_query else 'd'}_{self._get_cache_key(text)}"
        return self._cache.get(cache_key)
    
    def _cache_multivector(self, text: str, embeddings: np.ndarray, is_query: bool = False):
        """Cache multi-vector embeddings."""
        if len(self._cache) >= self._max_cache_size:
            # Simple LRU: remove oldest
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            
        cache_key = f"{'q' if is_query else 'd'}_{self._get_cache_key(text)}"
        self._cache[cache_key] = embeddings
    
    def batch_late_interaction_search(
        self,
        queries: List[str],
        collection: str = "default",
        n_results: int = 10,
        initial_candidates: int = 100
    ) -> List[List[Dict[str, Any]]]:
        """Batch search with late interaction.
        
        Args:
            queries: List of queries
            collection: Collection name
            n_results: Results per query
            initial_candidates: Candidates for reranking
            
        Returns:
            Results for each query
        """
        all_results = []
        
        for query in queries:
            # Check cache for query
            query_multivec = self._get_cached_multivector(query, is_query=True)
            
            if query_multivec is None:
                query_multivec = self.retriever.encode_query_multivector(query)
                self._cache_multivector(query, query_multivec, is_query=True)
            
            # Perform search
            results = self.retriever.search_with_late_interaction(
                query,
                collection=collection,
                n_results=n_results,
                initial_candidates=initial_candidates
            )
            
            all_results.append(results)
            
        return all_results
    
    def clear_cache(self):
        """Clear the multi-vector cache."""
        self._cache.clear()
        logger.info("Multi-vector cache cleared")