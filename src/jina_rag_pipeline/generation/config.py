"""Generation and RAG configuration models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RAGConfig:
    """Configuration for RAG retrieval and enhancement features."""

    # Retrieval settings
    initial_retrieval_k: int = 20  # Initial batch size for retrieval
    final_top_n: int = 5  # Final number of documents to use in context

    # Hybrid search
    enable_hybrid_search: bool = False  # Enable semantic + keyword search
    hybrid_alpha: float = 0.5  # Weight between semantic (alpha) and keyword (1-alpha)

    # Reranking
    enable_reranking: bool = True  # Enable JinaAI reranking
    rerank_model: str = "jinaai/jina-reranker-m0"  # JinaAI reranker model (m0 or v1-turbo-en)
    rerank_top_n: int = 5  # Number of documents to keep after reranking

    # Compression
    enable_compression: bool = False  # Enable contextual compression (future)
    compression_chunk_size: int = 500  # Chunk size for compression
    compression_threshold: float = 0.7  # Similarity threshold for filtering
    compression_max_chunks: int = 10  # Max chunks to keep per document

    # Formatting
    citation_style: str = "numbered"  # Citation format: numbered, inline, footnote
    include_relevance_scores: bool = True  # Include scores in context

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.initial_retrieval_k < 1 or self.initial_retrieval_k > 50:
            raise ValueError(
                f"initial_retrieval_k must be between 1 and 50, got {self.initial_retrieval_k}"
            )
        if self.final_top_n < 1 or self.final_top_n > 20:
            raise ValueError(f"final_top_n must be between 1 and 20, got {self.final_top_n}")
        if self.rerank_top_n < 1 or self.rerank_top_n > 20:
            raise ValueError(f"rerank_top_n must be between 1 and 20, got {self.rerank_top_n}")
        if self.hybrid_alpha < 0 or self.hybrid_alpha > 1:
            raise ValueError(f"hybrid_alpha must be between 0 and 1, got {self.hybrid_alpha}")
        if self.compression_threshold < 0.5 or self.compression_threshold > 0.95:
            raise ValueError(
                f"compression_threshold must be between 0.5 and 0.95, "
                f"got {self.compression_threshold}"
            )
        if self.compression_chunk_size < 200 or self.compression_chunk_size > 1000:
            raise ValueError(
                f"compression_chunk_size must be between 200 and 1000, "
                f"got {self.compression_chunk_size}"
            )
        if self.citation_style not in ("numbered", "inline", "footnote"):
            raise ValueError(
                f"citation_style must be 'numbered', 'inline', or 'footnote', "
                f"got {self.citation_style}"
            )


@dataclass
class GenerationConfig:
    """Configuration for LLM generation."""

    # Model parameters
    model_name: str = "mlx-community/Qwen3-14B-4bit"
    max_tokens: int = 5000
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 20

    # Context window
    max_context_length: int = 32768
    max_history_turns: int = 10

    # Thinking mode
    enable_thinking: bool = False

    @classmethod
    def for_thinking_mode(cls, **kwargs) -> "GenerationConfig":
        """Create config optimized for thinking mode."""
        defaults = {
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "enable_thinking": True,
        }
        defaults.update(kwargs)
        return cls(**defaults)

    @classmethod
    def for_non_thinking_mode(cls, **kwargs) -> "GenerationConfig":
        """Create config optimized for non-thinking mode with comprehensive citations."""
        defaults = {
            "temperature": 0.4,  # Lower temperature for more deterministic, focused citation behavior
            "top_p": 0.9,  # Balanced top_p for diversity while maintaining focus
            "top_k": 20,
            "max_tokens": 600,  # Increased to allow comprehensive source citation
            "enable_thinking": False,
        }
        defaults.update(kwargs)
        return cls(**defaults)

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError(f"Temperature must be between 0 and 2, got {self.temperature}")
        if self.top_p < 0 or self.top_p > 1:
            raise ValueError(f"top_p must be between 0 and 1, got {self.top_p}")
        if self.top_k < 1:
            raise ValueError(f"top_k must be >= 1, got {self.top_k}")
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be >= 1, got {self.max_tokens}")
