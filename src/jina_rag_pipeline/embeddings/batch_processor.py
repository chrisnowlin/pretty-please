"""Batch processor for token-aware batching of embeddings."""

from typing import List, Optional
import numpy as np


class BatchProcessor:
    """Processes batches with token-aware splitting."""

    def __init__(self, max_tokens_per_batch: int = 8192, adaptive: bool = True):
        """Initialize the batch processor.

        Args:
            max_tokens_per_batch: Maximum tokens per batch
            adaptive: Whether to adaptively adjust batch size
        """
        self.max_tokens_per_batch = max_tokens_per_batch
        self.adaptive = adaptive

    def split_into_batches(
        self,
        texts: List[str],
        max_batch_size: int = 32,
        tokenizer=None
    ) -> List[List[str]]:
        """Split texts into batches respecting token limits.

        Args:
            texts: List of text strings
            max_batch_size: Maximum texts per batch
            tokenizer: Optional tokenizer to count tokens

        Returns:
            List of batches (each batch is a list of texts)
        """
        if not texts:
            return []

        batches = []
        current_batch = []
        current_tokens = 0

        for text in texts:
            # Simple token estimation: assume 1.3 tokens per word
            tokens = len(text.split()) * 1.3 if tokenizer is None else len(tokenizer.encode(text))
            tokens = int(tokens)

            if (current_tokens + tokens > self.max_tokens_per_batch and current_batch) or len(current_batch) >= max_batch_size:
                batches.append(current_batch)
                current_batch = [text]
                current_tokens = tokens
            else:
                current_batch.append(text)
                current_tokens += tokens

        if current_batch:
            batches.append(current_batch)

        return batches

    def process_batch(self, batch: List[str]) -> dict:
        """Process a batch of texts.

        Args:
            batch: List of texts to process

        Returns:
            Dictionary with batch metadata
        """
        return {
            "batch_size": len(batch),
            "texts": batch,
            "estimated_tokens": sum(len(text.split()) for text in batch) * 1.3,
        }
