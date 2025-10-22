"""Qwen3-14B-4bit generator using MLX framework."""

import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from .config import GenerationConfig

logger = logging.getLogger(__name__)

# Import MLX at module level for performance
# These will fail gracefully if MLX is not installed
try:
    import mlx.core as mx
    import mlx_lm
    from mlx_lm.sample_utils import make_sampler
    MLX_AVAILABLE = True
except ImportError as e:
    MLX_AVAILABLE = False
    _mlx_import_error = e


class GenerationError(Exception):
    """Wrapper for errors that occur during token generation."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


class QwenGenerator:
    """MLX-based generator for Qwen3-14B-4bit model."""

    def __init__(self, config: Optional[GenerationConfig] = None):
        """
        Initialize generator with lazy model loading.

        Args:
            config: Generation configuration

        Raises:
            RuntimeError: If MLX framework is not available
        """
        self.config = config or GenerationConfig()
        self.model = None
        self.tokenizer = None
        self._model_loaded = False
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._lock = asyncio.Lock()

        # Verify MLX availability (checked at module import time)
        if not MLX_AVAILABLE:
            logger.error(f"MLX not available: {_mlx_import_error}")
            raise RuntimeError(
                "MLX framework is required but not installed. "
                "Install with: pip install mlx mlx-lm"
            ) from _mlx_import_error

        logger.info("MLX framework available")

    async def _load_model(self) -> None:
        """Load model and tokenizer (called automatically on first use)."""
        if self._model_loaded:
            return

        async with self._lock:
            if self._model_loaded:  # Double-check after acquiring lock
                return

            logger.info(f"Loading model: {self.config.model_name}")

            try:
                # Load model in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self.model, self.tokenizer = await loop.run_in_executor(
                    self._executor,
                    lambda: mlx_lm.load(self.config.model_name)
                )

                self._model_loaded = True
                logger.info("Model loaded successfully")

            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise RuntimeError(f"Model loading failed: {e}") from e

    def apply_chat_template(
        self,
        messages: List[Dict[str, str]],
        enable_thinking: Optional[bool] = None,
    ) -> str:
        """
        Apply Qwen3 chat template to messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            enable_thinking: Override thinking mode setting

        Returns:
            Formatted prompt string
        """
        thinking = enable_thinking if enable_thinking is not None else self.config.enable_thinking

        # Simple template for Qwen3 (adjust based on actual model requirements)
        formatted_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                formatted_parts.append(f"<|im_start|>system\n{content}<|im_end|>")
            elif role == "user":
                formatted_parts.append(f"<|im_start|>user\n{content}<|im_end|>")
            elif role == "assistant":
                formatted_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")

        # Add generation prompt
        formatted_parts.append("<|im_start|>assistant")

        return "\n".join(formatted_parts)

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate response with streaming.

        Args:
            messages: List of chat messages
            max_tokens: Override max tokens
            temperature: Override temperature (must be >= 0, typically 0-2)
            top_p: Override top_p (must be in [0, 1])
            top_k: Override top_k (must be >= 0, 0 means disabled)

        Yields:
            Generated tokens as strings

        Raises:
            ValueError: If parameters are out of valid range
            GenerationError: If generation fails
        """
        # Ensure model is loaded
        await self._load_model()

        # Apply chat template
        prompt = self.apply_chat_template(messages)

        # Use config defaults if not specified
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature if temperature is not None else self.config.temperature
        top_p = top_p if top_p is not None else self.config.top_p

        # Validate parameters
        if temperature < 0:
            raise ValueError(f"temperature must be >= 0, got {temperature}")
        if not 0 <= top_p <= 1:
            raise ValueError(f"top_p must be in [0, 1], got {top_p}")
        if top_k is not None and top_k < 0:
            raise ValueError(f"top_k must be >= 0, got {top_k}")
        if max_tokens <= 0:
            raise ValueError(f"max_tokens must be > 0, got {max_tokens}")

        logger.info(
            f"Generating with max_tokens={max_tokens}, temp={temperature}, "
            f"top_p={top_p}, top_k={top_k or 0}"
        )

        try:
            # Stream generation in thread pool
            loop = asyncio.get_event_loop()

            # Create a queue for streaming tokens (or errors)
            token_queue: asyncio.Queue[Optional[str | GenerationError]] = asyncio.Queue()

            def _generate():
                """Generate tokens in separate thread."""
                try:
                    # Create sampler with temperature and top_p
                    sampler = make_sampler(
                        temp=temperature,
                        top_p=top_p,
                        top_k=top_k or 0,  # 0 means disabled
                    )

                    for response in mlx_lm.stream_generate(
                        self.model,
                        self.tokenizer,
                        prompt,
                        max_tokens=max_tokens,
                        sampler=sampler,
                    ):
                        # Extract text from response object
                        if hasattr(response, 'text'):
                            token = response.text
                        else:
                            logger.warning(
                                f"Response object missing 'text' attribute, "
                                f"using str(): {type(response)}"
                            )
                            token = str(response)

                        # Put token in queue (this is thread-safe)
                        asyncio.run_coroutine_threadsafe(token_queue.put(token), loop)

                    # Signal completion
                    asyncio.run_coroutine_threadsafe(token_queue.put(None), loop)

                except Exception as e:
                    logger.error(f"Generation error: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

                    # Put error in queue so consumer knows it failed
                    error = GenerationError("Token generation failed", e)
                    asyncio.run_coroutine_threadsafe(token_queue.put(error), loop)

            # Start generation in thread pool
            loop.run_in_executor(self._executor, _generate)

            # Yield tokens as they arrive, filtering thinking tags if needed
            thinking_disabled = not self.config.enable_thinking
            token_count = 0

            while True:
                item = await token_queue.get()

                # Check for error
                if isinstance(item, GenerationError):
                    raise item

                # Check for completion
                if item is None:
                    break

                # Count tokens (rough estimate: 3 chars per token for safety)
                token_count += len(item) // 3

                # If we've exceeded the limit, stop yielding
                if token_count >= max_tokens:
                    logger.warning(f"Token limit ({max_tokens}) exceeded, truncating response")
                    break

                # If thinking is disabled, filter out thinking patterns
                if thinking_disabled:
                    # Check if this token contains thinking tags
                    import re

                    # Skip tokens that are part of thinking tags
                    if re.search(r'<think>|</think>|<thinking>|</thinking>|\\boxed|\\[\[]|\\[\]]', item):
                        continue

                    # Yield the token as-is (preserving spaces)
                    yield item
                else:
                    # Thinking enabled, yield everything
                    yield item

        except GenerationError:
            # Re-raise GenerationError as-is
            raise
        except Exception as e:
            logger.error(f"Stream generation failed: {e}")
            raise GenerationError("Stream generation failed", e) from e

    async def rerank(
        self, query: str, documents: List[str], top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Re-rank documents using LLM-based relevance scoring.

        Args:
            query: Search query
            documents: List of document texts
            top_k: Number of top documents to return

        Returns:
            List of (document, score) tuples sorted by relevance
        """
        await self._load_model()

        if not documents:
            return []

        top_k = top_k or len(documents)

        # Simple re-ranking: score each document
        scored_docs = []
        for doc in documents:
            # Create a simple relevance prompt
            prompt = f"""Rate the relevance of this document to the query on a scale of 0-1.

Query: {query}

Document: {doc}

Relevance score (0-1):"""

            try:
                score = 0.5  # Default neutral score

                # Generate score (just get first few tokens)
                tokens = []
                async for token in self.generate_stream(
                    [{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0.1,
                ):
                    tokens.append(token)
                    if len(tokens) >= 5:  # Just get a few tokens
                        break

                # Try to parse score from response
                response = "".join(tokens).strip()
                try:
                    score = float(response.split()[0])
                    score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
                except:
                    score = 0.5

                scored_docs.append((doc, score))

            except Exception as e:
                logger.warning(f"Re-ranking error for document, using default score: {e}")
                scored_docs.append((doc, 0.5))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return scored_docs[:top_k]

    def clear_cache(self) -> None:
        """Clear model cache and unload model."""
        if self._model_loaded:
            logger.info("Clearing model cache")
            self.model = None
            self.tokenizer = None
            self._model_loaded = False

    def __del__(self):
        """Cleanup on deletion."""
        self._executor.shutdown(wait=False)
