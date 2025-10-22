"""Database persistence for processed documents.

Handles chunking, embedding generation, and storage of processed documents
to ChromaVectorStore for searchability.
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..storage import ChromaVectorStore
from ..embeddings import JinaEmbeddings, EmbeddingConfig
from .semantic_chunking import SemanticRegionChunker
from .base import Document

logger = logging.getLogger(__name__)


class DocumentDatabasePersistence:
    """Manages persistence of processed documents to vector database.

    Handles:
    - Semantic chunking of documents
    - Embedding generation
    - Storage in ChromaVectorStore
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_model: str = "jinaai/jina-embeddings-v4",
        chunk_size: int = 1000,
        preserve_structure: bool = True,
        embedding_config: Optional[EmbeddingConfig] = None,
        enable_storage_optimization: bool = False
    ):
        """Initialize persistence handler.

        Args:
            persist_directory: Directory for ChromaVectorStore persistence
            embedding_model: Model to use for embeddings
            chunk_size: Maximum chunk size in characters
            preserve_structure: Whether to preserve document structure in chunks
            embedding_config: Optional EmbeddingConfig for custom embedding settings
            enable_storage_optimization: If True, uses storage_optimized config (64× reduction)
        """
        self.vector_store = ChromaVectorStore(persist_directory=persist_directory)

        # Configure embeddings based on parameters
        if embedding_config is not None:
            self.embedding_config = embedding_config
        elif enable_storage_optimization:
            # Use storage-optimized config for 64× reduction
            self.embedding_config = EmbeddingConfig.storage_optimized()
            logger.info("⚡ Storage optimization ENABLED: 64× storage reduction with ubinary format")
        else:
            # Default: documents config for backward compatibility
            self.embedding_config = EmbeddingConfig.for_documents()

        self.embedder = JinaEmbeddings(model_name=embedding_model, config=self.embedding_config)
        self.chunker = SemanticRegionChunker(
            max_chunk_size=chunk_size,
            preserve_tables=preserve_structure,
            preserve_equations=preserve_structure,
            preserve_images=preserve_structure
        )
        self.persist_directory = persist_directory or "./db"

        logger.info(f"DocumentDatabasePersistence initialized")
        logger.info(f"  Persist directory: {self.persist_directory}")
        logger.info(f"  Embedding model: {embedding_model}")
        logger.info(f"  Embedding config: {self.embedding_config.task}, {self.embedding_config.dimensions}D, {self.embedding_config.embedding_format}")
        logger.info(f"  Chunk size: {chunk_size}")

    def save_document(
        self,
        document: Document,
        collection_name: str,
        embedding_dimension: Optional[int] = None
    ) -> dict:
        """Save processed document to database.

        Args:
            document: Processed document with semantic regions
            collection_name: Name of collection to save to
            embedding_dimension: Optional override for embedding dimension.
                               If None, uses dimension from embedding_config.

        Returns:
            Dictionary with save statistics

        Note:
            Embedding dimensions are now controlled by embedding_config:
            - Default (for_documents): 1024-dim for general retrieval
            - Storage optimized: 512-dim for 64× storage reduction
            - Custom: Specify via embedding_config parameter in __init__
        """
        # Use configured dimension unless explicitly overridden
        if embedding_dimension is None:
            embedding_dimension = self.embedding_config.dimensions
        logger.info(f"Saving document to database: {collection_name}")
        logger.info(f"  Document source: {document.source}")
        logger.info(f"  Document length: {len(document.content):,} characters")
        logger.info(f"  Semantic regions: {len(document.metadata.get('regions', []))}")

        # Create collection if it doesn't exist
        try:
            self.vector_store.create_collection(
                name=collection_name,
                embedding_dimension=embedding_dimension,
                metadata={
                    "source": document.source,
                    "created_at": datetime.now().isoformat(),
                    "page_count": document.metadata.get("page_count", 0),
                    "region_count": document.metadata.get("region_count", 0),
                }
            )
            logger.info(f"Created collection: {collection_name}")
        except Exception as e:
            # Collection may already exist
            logger.debug(f"Collection creation info: {e}")

        # Chunk the document
        logger.info("Chunking document using semantic regions...")
        chunks = self.chunker.chunk(document)
        logger.info(f"Created {len(chunks)} chunks from document")

        if not chunks:
            logger.warning("No chunks created from document!")
            return {
                "collection_name": collection_name,
                "total_chunks": 0,
                "saved_chunks": 0,
                "status": "failed - no chunks"
            }

        # Generate embeddings for chunks using configured settings
        chunk_texts = [chunk.content for chunk in chunks]
        logger.info(f"Generating {self.embedding_config.dimensions}-dim embeddings for {len(chunks)} chunks...")
        logger.info(f"  Format: {self.embedding_config.embedding_format}")
        logger.info(f"  Late chunking: {self.embedding_config.late_chunking}")

        # Use new config-based API for optimized embedding generation
        embeddings = self.embedder.embed_with_config(chunk_texts, self.embedding_config)
        logger.info(f"Generated {len(embeddings)} embeddings at {self.embedding_config.dimensions} dimensions")

        # Prepare metadata for each chunk
        metadatas = []
        documents = []
        for i, chunk in enumerate(chunks):
            metadata = {
                "chunk_id": i,
                "total_chunks": len(chunks),
                "source": str(document.source),
                "region_type": chunk.metadata.get("region_type", "text"),
                "page_number": chunk.metadata.get("page_number", 0),
                **chunk.metadata
            }
            metadatas.append(metadata)
            documents.append(chunk.content)

        # Save to vector store
        logger.info(f"Saving {len(chunks)} chunks to vector store...")
        try:
            ids = self.vector_store.add_embeddings(
                collection_name=collection_name,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Successfully saved {len(ids)} chunks to database")

            # Get collection stats
            stats = self.vector_store.get_collection_stats(collection_name)
            logger.info(f"Collection stats: {stats.count} total embeddings")

            return {
                "collection_name": collection_name,
                "total_chunks": len(chunks),
                "saved_chunks": len(ids),
                "embedding_ids": ids[:10],  # Return first 10 IDs as sample
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Failed to save chunks to database: {e}")
            return {
                "collection_name": collection_name,
                "total_chunks": len(chunks),
                "saved_chunks": 0,
                "error": str(e),
                "status": "failed"
            }

    def close(self) -> None:
        """Close database connections."""
        if hasattr(self, 'vector_store'):
            self.vector_store.close()
            logger.info("Database persistence closed")
