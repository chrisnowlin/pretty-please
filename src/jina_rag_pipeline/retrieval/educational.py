"""Educational retrieval with metadata filtering and source attribution."""

import logging
from typing import List, Optional, Dict, Any

from ..storage.chroma_store import ChromaVectorStore
from ..storage.base import SearchResult
from ..embeddings.jina_v4 import JinaEmbeddingsV4
from ..embeddings.config import EmbeddingConfig
from ..models.educational import RetrievedMaterial
from ..ingestion.educational import extract_metadata_hints

logger = logging.getLogger(__name__)


class EducationalRetriever:
    """
    Retriever for educational content with metadata filtering.

    Wraps ChromaVectorStore to add educational-specific features:
    - Optional metadata filtering (grade, subject)
    - Separate text and image retrieval
    - Source attribution tracking
    - Conversion to RetrievedMaterial objects
    """

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embedder: JinaEmbeddingsV4,
        text_collection: str = "educational_content",
        image_collection: str = "educational_images",
    ):
        """
        Initialize the educational retriever.

        Args:
            vector_store: ChromaVectorStore instance
            embedder: JinaEmbeddingsV4 instance for encoding queries
            text_collection: Name of text embeddings collection
            image_collection: Name of image embeddings collection
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.text_collection = text_collection
        self.image_collection = image_collection

    def retrieve_for_lesson(
        self,
        topic: str,
        grade: Optional[str] = None,
        subject: Optional[str] = None,
        top_k: int = 5,
    ) -> List[RetrievedMaterial]:
        """
        Retrieve text materials for lesson planning.

        Args:
            topic: Learning topic or objective
            grade: Optional grade level filter (e.g., "3", "6-8")
            subject: Optional subject filter (e.g., "Mathematics")
            top_k: Number of results to return

        Returns:
            List of RetrievedMaterial objects with source attribution
        """
        # Encode query as embedding using optimized query config
        # Benefits: Disables late_chunking (not needed for queries), optimized task parameter
        query_config = EmbeddingConfig.for_query()
        query_embedding = self.embedder.embed_with_config([topic], query_config)[0]

        # Build metadata filter if grade/subject provided
        metadata_filter = self._build_metadata_filter(grade, subject)

        # Search vector store
        try:
            search_results = self.vector_store.similarity_search(
                collection_name=self.text_collection,
                query_embedding=query_embedding.tolist(),
                top_k=top_k,
                metadata_filter=metadata_filter,
            )

            # If metadata filtering returns no results, retry without filter
            if not search_results and metadata_filter:
                logger.warning("No results with metadata filter, retrying without filter")
                search_results = self.vector_store.similarity_search(
                    collection_name=self.text_collection,
                    query_embedding=query_embedding.tolist(),
                    top_k=top_k,
                    metadata_filter=None,
                )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # If metadata filtering fails, retry without filter
            if metadata_filter:
                logger.warning("Retrying without metadata filter")
                search_results = self.vector_store.similarity_search(
                    collection_name=self.text_collection,
                    query_embedding=query_embedding.tolist(),
                    top_k=top_k,
                    metadata_filter=None,
                )
            else:
                raise

        # Convert to RetrievedMaterial objects
        materials = []
        for result in search_results:
            material = self._search_result_to_material(result, source_type="text")
            materials.append(material)

        logger.info(
            f"Retrieved {len(materials)} text materials for topic='{topic}', "
            f"grade={grade}, subject={subject}"
        )

        return materials

    def retrieve_images(
        self,
        topic: str,
        grade: Optional[str] = None,
        subject: Optional[str] = None,
        top_k: int = 3,
    ) -> List[RetrievedMaterial]:
        """
        Retrieve image materials for lesson planning.

        Args:
            topic: Learning topic or objective
            grade: Optional grade level filter
            subject: Optional subject filter
            top_k: Number of images to return

        Returns:
            List of RetrievedMaterial objects for images
        """
        # Encode query as embedding using optimized query config
        # Benefits: Disables late_chunking (not needed for queries), optimized task parameter
        query_config = EmbeddingConfig.for_query()
        query_embedding = self.embedder.embed_with_config([topic], query_config)[0]

        # Build metadata filter
        metadata_filter = self._build_metadata_filter(grade, subject)

        # Search image collection
        try:
            search_results = self.vector_store.similarity_search(
                collection_name=self.image_collection,
                query_embedding=query_embedding.tolist(),
                top_k=top_k,
                metadata_filter=metadata_filter,
            )

            # If metadata filtering returns no results, retry without filter
            if not search_results and metadata_filter:
                logger.warning("No image results with metadata filter, retrying without filter")
                search_results = self.vector_store.similarity_search(
                    collection_name=self.image_collection,
                    query_embedding=query_embedding.tolist(),
                    top_k=top_k,
                    metadata_filter=None,
                )
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            # Retry without filter if needed
            if metadata_filter:
                logger.warning("Retrying image search without metadata filter")
                search_results = self.vector_store.similarity_search(
                    collection_name=self.image_collection,
                    query_embedding=query_embedding.tolist(),
                    top_k=top_k,
                    metadata_filter=None,
                )
            else:
                raise

        # Convert to RetrievedMaterial objects
        materials = []
        for result in search_results:
            material = self._search_result_to_material(result, source_type="image")
            materials.append(material)

        logger.info(
            f"Retrieved {len(materials)} images for topic='{topic}', "
            f"grade={grade}, subject={subject}"
        )

        return materials

    def retrieve_combined(
        self,
        topic: str,
        grade: Optional[str] = None,
        subject: Optional[str] = None,
        text_top_k: int = 5,
        image_top_k: int = 3,
    ) -> Dict[str, List[RetrievedMaterial]]:
        """
        Retrieve both text and images in a single call.

        Args:
            topic: Learning topic or objective
            grade: Optional grade level filter
            subject: Optional subject filter
            text_top_k: Number of text materials to retrieve
            image_top_k: Number of images to retrieve

        Returns:
            Dictionary with 'text' and 'images' keys containing materials
        """
        text_materials = self.retrieve_for_lesson(
            topic=topic,
            grade=grade,
            subject=subject,
            top_k=text_top_k,
        )

        image_materials = self.retrieve_images(
            topic=topic,
            grade=grade,
            subject=subject,
            top_k=image_top_k,
        )

        return {
            "text": text_materials,
            "images": image_materials,
        }

    def _build_metadata_filter(
        self,
        grade: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Build ChromaDB metadata filter from grade/subject.

        Args:
            grade: Grade level
            subject: Subject area

        Returns:
            Metadata filter dict or None
        """
        if not grade and not subject:
            return None

        # ChromaDB uses "$and", "$or", "$eq" operators
        filters = []

        if grade:
            filters.append({"edu_grade": {"$eq": grade}})

        if subject:
            filters.append({"edu_subject": {"$eq": subject}})

        # Combine with AND if multiple filters
        if len(filters) == 1:
            return filters[0]
        elif len(filters) > 1:
            return {"$and": filters}

        return None

    def _search_result_to_material(
        self,
        result: SearchResult,
        source_type: str,
    ) -> RetrievedMaterial:
        """
        Convert ChromaDB SearchResult to RetrievedMaterial.

        Extracts source attribution from metadata:
        - document_name: Source file name
        - page_number: Page in PDF/document
        - slide_number: Slide in PPTX

        Args:
            result: SearchResult from ChromaDB
            source_type: "text" or "image"

        Returns:
            RetrievedMaterial with full source attribution
        """
        metadata = result.metadata or {}

        # Extract source attribution
        document_name = metadata.get("source_file", "Unknown Source")
        page_number = metadata.get("page_number")
        slide_number = metadata.get("slide_number")

        # Content is stored in document field
        content = result.document or ""

        # Create RetrievedMaterial
        material = RetrievedMaterial(
            content=content,
            document_name=document_name,
            chunk_id=result.id,
            relevance_score=result.score,
            source_type=source_type,
            page_number=page_number,
            slide_number=slide_number,
        )

        return material
