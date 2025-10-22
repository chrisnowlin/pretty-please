"""Semantic-aware chunking that preserves document structure.

Creates chunks based on semantic regions from layout analysis,
preserving tables, equations, and document boundaries.
"""

import logging
from typing import Any, Dict, List
from .chunking import Chunk, ChunkingStrategy, FixedSizeChunker
from .base import Document
from .semantic_region import SemanticRegion

logger = logging.getLogger(__name__)


class SemanticRegionChunker(ChunkingStrategy):
    """Chunk documents based on semantic regions from Nanonets layout analysis.

    Strategy:
    - Tables: Single chunk (never split)
    - Equations: Single chunk with LaTeX
    - Figures: Single chunk with description
    - Text: Group until max_size, respect paragraphs
    - Headings: Start new chunk

    Fallback:
    - If no semantic regions available, uses character-based chunking
    """

    def __init__(
        self,
        max_chunk_size: int = 1000,
        preserve_tables: bool = True,
        preserve_equations: bool = True,
        preserve_images: bool = True,
        fallback_to_character: bool = True
    ):
        """Initialize semantic region chunker.

        Args:
            max_chunk_size: Maximum characters per chunk for text regions
            preserve_tables: Keep tables as single chunks (never split)
            preserve_equations: Keep equations as single chunks
            preserve_images: Keep image regions as single chunks
            fallback_to_character: Fall back to character chunking if no regions
        """
        self.max_chunk_size = max_chunk_size
        self.preserve_tables = preserve_tables
        self.preserve_equations = preserve_equations
        self.preserve_images = preserve_images
        self.fallback_to_character = fallback_to_character

    def chunk(self, document: Document) -> List[Chunk]:
        """Create chunks from semantic regions.

        Args:
            document: Document with semantic regions metadata

        Returns:
            List of chunks preserving semantic structure
        """
        # Check if document has semantic regions
        regions_data = document.metadata.get("regions", [])

        if not regions_data:
            logger.info("No semantic regions found in document")
            if self.fallback_to_character:
                logger.info("Falling back to character-based chunking")
                return FixedSizeChunker(chunk_size=self.max_chunk_size).chunk(document)
            else:
                logger.warning("No fallback enabled, returning empty chunks")
                return []

        logger.info(f"Processing {len(regions_data)} semantic regions")

        # Parse regions
        regions = []
        for region_data in regions_data:
            if isinstance(region_data, dict):
                regions.append(SemanticRegion.from_dict(region_data))
            else:
                regions.append(region_data)

        # Create chunks from regions
        chunks = []
        current_section = []
        current_size = 0

        for idx, region in enumerate(regions):
            region_type = region.region_type
            content = str(region.content)
            size = len(content)

            # Atomic regions (never split)
            if self._is_atomic_region(region_type):
                # Flush current section first
                if current_section:
                    chunk = self._merge_regions(current_section, len(chunks))
                    chunks.append(chunk)
                    current_section = []
                    current_size = 0

                # Add atomic region as single chunk
                chunk = self._create_atomic_chunk(region, len(chunks))
                chunks.append(chunk)
                continue

            # Section boundaries (headings/titles)
            if region_type in ["title", "heading"]:
                # Flush previous section
                if current_section:
                    chunk = self._merge_regions(current_section, len(chunks))
                    chunks.append(chunk)

                # Start new section with heading
                current_section = [region]
                current_size = size
                continue

            # Regular text/list content
            if current_size + size > self.max_chunk_size and current_section:
                # Section too large, flush and start new
                chunk = self._merge_regions(current_section, len(chunks))
                chunks.append(chunk)
                current_section = [region]
                current_size = size
            else:
                # Add to current section
                current_section.append(region)
                current_size += size

        # Flush remaining regions
        if current_section:
            chunk = self._merge_regions(current_section, len(chunks))
            chunks.append(chunk)

        logger.info(
            f"Created {len(chunks)} semantic chunks from {len(regions)} regions"
        )

        return chunks

    def _is_atomic_region(self, region_type: str) -> bool:
        """Check if region should be kept as a single atomic chunk.

        Args:
            region_type: Type of semantic region

        Returns:
            True if region should never be split
        """
        if region_type == "table" and self.preserve_tables:
            return True
        if region_type == "equation" and self.preserve_equations:
            return True
        if region_type == "image" and self.preserve_images:
            return True
        return False

    def _create_atomic_chunk(self, region: SemanticRegion, chunk_index: int) -> Chunk:
        """Create chunk from single atomic region.

        Args:
            region: Semantic region to convert to chunk
            chunk_index: Index of this chunk

        Returns:
            Chunk containing single region
        """
        content = str(region.content)

        # Build metadata
        metadata = {
            "chunk_index": chunk_index,
            "chunking_strategy": "semantic_region",
            "region_id": region.region_id,
            "region_type": region.region_type,
            "region_sequence": region.region_sequence,
            "page_number": region.page_number,
            "atomic": True,  # Mark as indivisible
            "start_index": 0,
            "end_index": len(content),
        }

        # Add region-specific metadata
        if region.semantic_tags:
            metadata["semantic_tags"] = region.semantic_tags

        if region.region_type == "table":
            if region.table_html:
                metadata["table_html"] = region.table_html
            if region.table_rows:
                metadata["table_rows"] = region.table_rows
            if region.table_cols:
                metadata["table_cols"] = region.table_cols

        if region.region_type == "equation":
            if region.equation_latex:
                metadata["equation_latex"] = region.equation_latex
            if region.equation_type:
                metadata["equation_type"] = region.equation_type

        if region.region_type == "image":
            if region.image_description:
                metadata["image_description"] = region.image_description
            if region.image_type:
                metadata["image_type"] = region.image_type

        if region.markdown_level is not None:
            metadata["markdown_level"] = region.markdown_level

        return Chunk(
            content=content,
            metadata=metadata,
            start_index=0,
            end_index=len(content),
        )

    def _merge_regions(self, regions: List[SemanticRegion], chunk_index: int) -> Chunk:
        """Merge multiple regions into a single chunk.

        Args:
            regions: List of regions to merge
            chunk_index: Index of this chunk

        Returns:
            Chunk containing merged regions
        """
        # Combine content with double newlines between regions
        content_parts = [str(r.content) for r in regions]
        content = "\n\n".join(content_parts)

        # Collect metadata
        region_types = [r.region_type for r in regions]
        page_numbers = sorted(set(r.page_number for r in regions))
        region_ids = [r.region_id for r in regions]

        metadata = {
            "chunk_index": chunk_index,
            "chunking_strategy": "semantic_region",
            "merged_regions": len(regions),
            "region_types": region_types,
            "region_ids": region_ids,
            "page_number": page_numbers[0] if page_numbers else None,
            "start_index": 0,
            "end_index": len(content),
        }

        # Add page_numbers if spans multiple pages
        if len(page_numbers) > 1:
            metadata["page_numbers"] = page_numbers
            metadata["pages_spanned"] = len(page_numbers)

        # Collect semantic tags from all regions
        all_tags = []
        for region in regions:
            if region.semantic_tags:
                all_tags.extend(region.semantic_tags)
        if all_tags:
            metadata["semantic_tags"] = list(set(all_tags))

        return Chunk(
            content=content,
            metadata=metadata,
            start_index=0,
            end_index=len(content),
        )
