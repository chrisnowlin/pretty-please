import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .base import Document


def get_page_numbers_for_chunk(
    start_index: int,
    end_index: int,
    page_boundaries: List[Dict[str, Any]]
) -> Optional[Tuple[List[int], int]]:
    """
    Determine which page(s) a chunk spans.

    Args:
        start_index: Character position where chunk starts
        end_index: Character position where chunk ends
        page_boundaries: List of dicts with page_number, start_index, end_index

    Returns:
        Tuple of (list of page numbers, primary page number) or None if no boundaries
        Primary page is the one containing the largest portion of the chunk
    """
    if not page_boundaries:
        return None

    pages_touched = []
    page_overlaps = []  # Track how much of chunk is on each page

    for boundary in page_boundaries:
        page_start = boundary["start_index"]
        page_end = boundary["end_index"]
        page_num = boundary["page_number"]

        # Check if chunk overlaps with this page
        overlap_start = max(start_index, page_start)
        overlap_end = min(end_index, page_end)

        if overlap_start < overlap_end:
            pages_touched.append(page_num)
            overlap_length = overlap_end - overlap_start
            page_overlaps.append((page_num, overlap_length))

    if not pages_touched:
        return None

    # Primary page is the one with the most content from this chunk
    primary_page = max(page_overlaps, key=lambda x: x[1])[0]

    return (pages_touched, primary_page)


@dataclass
class Chunk:
    content: str
    metadata: Dict[str, Any]
    start_index: int
    end_index: int


class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, document: Document) -> List[Chunk]:
        pass


class FixedSizeChunker(ChunkingStrategy):
    def __init__(self, chunk_size: int = 512, overlap: int = 0) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, document: Document) -> List[Chunk]:
        content = document.content
        chunks = []
        start = 0
        page_boundaries = document.metadata.get("page_boundaries")

        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            chunk_text = content[start:end]

            if chunk_text.strip():
                metadata = document.metadata.copy()
                metadata.update({
                    "chunk_index": len(chunks),
                    "start_index": start,
                    "end_index": end,
                    "chunking_strategy": "fixed_size",
                })

                # Add page information if available
                if page_boundaries:
                    page_info = get_page_numbers_for_chunk(start, end, page_boundaries)
                    if page_info:
                        pages_touched, primary_page = page_info
                        metadata["page_number"] = primary_page
                        if len(pages_touched) > 1:
                            metadata["page_numbers"] = pages_touched
                            metadata["pages_spanned"] = len(pages_touched)

                chunks.append(Chunk(
                    content=chunk_text,
                    metadata=metadata,
                    start_index=start,
                    end_index=end,
                ))

            if end == len(content):
                break

            start = end - self.overlap

        return chunks


class SentenceChunker(ChunkingStrategy):
    def __init__(self, max_chunk_size: int = 512, overlap_sentences: int = 1) -> None:
        if max_chunk_size <= 0:
            raise ValueError("max_chunk_size must be positive")
        if overlap_sentences < 0:
            raise ValueError("overlap_sentences must be non-negative")
        
        self.max_chunk_size = max_chunk_size
        self.overlap_sentences = overlap_sentences
        self._sentence_pattern = re.compile(r'(?<=[.!?])\s+')
    
    def _split_sentences(self, text: str) -> List[str]:
        sentences = self._sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk(self, document: Document) -> List[Chunk]:
        sentences = self._split_sentences(document.content)
        chunks = []
        current_sentences = []
        current_length = 0
        overlap_buffer: List[str] = []
        position = 0
        page_boundaries = document.metadata.get("page_boundaries")

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_length + sentence_len > self.max_chunk_size and current_sentences:
                chunk_text = " ".join(current_sentences)
                start_pos = position - current_length

                metadata = document.metadata.copy()
                metadata.update({
                    "chunk_index": len(chunks),
                    "start_index": start_pos,
                    "end_index": position,
                    "sentence_count": len(current_sentences),
                    "chunking_strategy": "sentence",
                })

                # Add page information if available
                if page_boundaries:
                    page_info = get_page_numbers_for_chunk(start_pos, position, page_boundaries)
                    if page_info:
                        pages_touched, primary_page = page_info
                        metadata["page_number"] = primary_page
                        if len(pages_touched) > 1:
                            metadata["page_numbers"] = pages_touched
                            metadata["pages_spanned"] = len(pages_touched)

                chunks.append(Chunk(
                    content=chunk_text,
                    metadata=metadata,
                    start_index=start_pos,
                    end_index=position,
                ))

                overlap_buffer = current_sentences[-self.overlap_sentences:] if self.overlap_sentences > 0 else []
                current_sentences = overlap_buffer.copy()
                current_length = sum(len(s) for s in current_sentences) + len(current_sentences) - 1

            current_sentences.append(sentence)
            current_length += sentence_len + (1 if current_length > 0 else 0)
            position += sentence_len + 1

        if current_sentences:
            chunk_text = " ".join(current_sentences)
            start_pos = position - current_length

            metadata = document.metadata.copy()
            metadata.update({
                "chunk_index": len(chunks),
                "start_index": start_pos,
                "end_index": position,
                "sentence_count": len(current_sentences),
                "chunking_strategy": "sentence",
            })

            # Add page information if available
            if page_boundaries:
                page_info = get_page_numbers_for_chunk(start_pos, position, page_boundaries)
                if page_info:
                    pages_touched, primary_page = page_info
                    metadata["page_number"] = primary_page
                    if len(pages_touched) > 1:
                        metadata["page_numbers"] = pages_touched
                        metadata["pages_spanned"] = len(pages_touched)

            chunks.append(Chunk(
                content=chunk_text,
                metadata=metadata,
                start_index=start_pos,
                end_index=position,
            ))

        return chunks


class SlidingWindowChunker(ChunkingStrategy):
    def __init__(self, window_size: int = 512, step_size: int = 256) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if step_size <= 0:
            raise ValueError("step_size must be positive")
        if step_size >= window_size:
            raise ValueError("step_size should be less than window_size for overlap")
        
        self.window_size = window_size
        self.step_size = step_size
    
    def chunk(self, document: Document) -> List[Chunk]:
        content = document.content
        chunks = []
        start = 0
        page_boundaries = document.metadata.get("page_boundaries")

        while start < len(content):
            end = min(start + self.window_size, len(content))
            chunk_text = content[start:end]

            if chunk_text.strip():
                metadata = document.metadata.copy()
                metadata.update({
                    "chunk_index": len(chunks),
                    "start_index": start,
                    "end_index": end,
                    "chunking_strategy": "sliding_window",
                })

                # Add page information if available
                if page_boundaries:
                    page_info = get_page_numbers_for_chunk(start, end, page_boundaries)
                    if page_info:
                        pages_touched, primary_page = page_info
                        metadata["page_number"] = primary_page
                        if len(pages_touched) > 1:
                            metadata["page_numbers"] = pages_touched
                            metadata["pages_spanned"] = len(pages_touched)

                chunks.append(Chunk(
                    content=chunk_text,
                    metadata=metadata,
                    start_index=start,
                    end_index=end,
                ))

            if end == len(content):
                break

            start += self.step_size

        return chunks
