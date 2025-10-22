"""Multimodal context formatter for text and images with numbered citations."""

from typing import Dict, List, Any, Tuple


class ContextFormatter:
    """
    Format multimodal context (text + images) for LLM consumption.

    Uses numbered citation format ([1], [2] for text; [IMG-1], [IMG-2] for images)
    to enable clear source attribution in LLM responses.
    """

    def __init__(self):
        """Initialize formatter with empty citation mapping."""
        self.citation_map: Dict[str, Dict[str, Any]] = {}

    def format_text_context(
        self, text_results: List[Dict[str, Any]], include_relevance: bool = True
    ) -> str:
        """
        Format text search results with numbered citations.

        Args:
            text_results: List of text search results with 'content', 'source', 'score'
            include_relevance: Whether to include relevance scores in output

        Returns:
            Formatted text context with [N] citation markers
        """
        if not text_results:
            return ""

        formatted_parts = []
        for i, result in enumerate(text_results, 1):
            content = result.get("content", "")
            source = result.get("source", "Unknown")
            score = result.get("score", 0.0)
            metadata = result.get("metadata", {})

            # Build citation marker
            citation_id = f"[{i}]"

            # Store citation mapping for later reference
            self.citation_map[citation_id] = {
                "source": source,
                "score": score,
                "type": "text",
                "metadata": metadata,
            }

            # Format citation header
            if include_relevance:
                header = f"{citation_id} **Source**: {source} | **Relevance**: {score:.2f}"
            else:
                header = f"{citation_id} **Source**: {source}"

            formatted_parts.append(f"{header}\n{content}\n")

        return "\n".join(formatted_parts)

    def format_image_context(
        self, image_results: List[Dict[str, Any]], include_relevance: bool = True
    ) -> str:
        """
        Format image search results with numbered image citations.

        Args:
            image_results: List of image results with metadata
            include_relevance: Whether to include relevance scores in output

        Returns:
            Formatted image context with [IMG-N] citation markers
        """
        if not image_results:
            return ""

        formatted_parts = []
        for i, result in enumerate(image_results, 1):
            metadata = result.get("image_metadata", {})
            document_id = result.get("document_id", "unknown")
            score = result.get("score", 0.0)

            description = metadata.get(
                "description", f"Image from {metadata.get('filename', 'unknown file')}"
            )
            width = metadata.get("width", 0)
            height = metadata.get("height", 0)
            filename = metadata.get("filename", "unknown")
            img_format = metadata.get("format", "unknown")

            # Build image citation marker
            citation_id = f"[IMG-{i}]"

            # Store citation mapping
            self.citation_map[citation_id] = {
                "source": filename,
                "score": score,
                "type": "image",
                "metadata": metadata,
                "document_id": document_id,
            }

            # Format citation header
            if include_relevance:
                header = (
                    f"{citation_id} **File**: {filename} | "
                    f"**Description**: {description} | **Relevance**: {score:.2f}"
                )
            else:
                header = f"{citation_id} **File**: {filename} | **Description**: {description}"

            formatted_parts.append(
                f"{header}\n"
                f"*Dimensions*: {width}x{height} | *Format*: {img_format}\n"
            )

        return "\n".join(formatted_parts)

    def format_multimodal_context(
        self,
        text_results: List[Dict[str, Any]],
        image_results: List[Dict[str, Any]],
        include_relevance: bool = True,
    ) -> str:
        """
        Combine text and image results into unified context with citations.

        Args:
            text_results: Text search results
            image_results: Image search results
            include_relevance: Whether to include relevance scores

        Returns:
            Unified multimodal context string with numbered citations
        """
        # Clear previous citation map for new context
        self.citation_map = {}

        parts = []

        text_context = self.format_text_context(text_results, include_relevance)
        if text_context:
            parts.append("**Text Sources:**\n\n" + text_context)

        image_context = self.format_image_context(image_results, include_relevance)
        if image_context:
            parts.append("**Image Sources:**\n\n" + image_context)

        if not parts:
            return "No relevant context found."

        return "\n---\n\n".join(parts)

    def get_citation_map(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current citation ID to source mapping.

        Returns:
            Dictionary mapping citation IDs (e.g., '[1]', '[IMG-1]') to source metadata
        """
        return self.citation_map.copy()

    def extract_image_references(
        self, image_results: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract image metadata keyed by document_id for session tracking.

        Args:
            image_results: Image search results

        Returns:
            Dict mapping document_id to ImageMetadata
        """
        references = {}
        for result in image_results:
            document_id = result.get("document_id")
            if document_id and "image_metadata" in result:
                references[document_id] = result["image_metadata"]

        return references
