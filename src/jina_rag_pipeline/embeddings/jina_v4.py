"""Jina Embeddings v4 implementation optimized for Apple Silicon."""

import os
import warnings
from typing import List, Optional, Union, Literal
import logging

import torch
import numpy as np
from transformers import AutoModel, AutoTokenizer
from tqdm import tqdm
from PIL import Image

from .config import EmbeddingConfig
from .multivector import MultiVectorHandler
from .format_converter import FormatConverter
from .batch_processor import BatchProcessor

logger = logging.getLogger(__name__)

TaskType = Literal["retrieval", "text-matching", "code"]
PromptType = Literal["query", "passage"]


class JinaEmbeddingsV4:
    """Jina Embeddings v4 model with MPS backend support for Apple Silicon."""
    
    def __init__(
        self,
        model_name: str = "jinaai/jina-embeddings-v4",
        device: Optional[str] = None,
        cache_dir: Optional[str] = None,
        trust_remote_code: bool = True,
        config: Optional[EmbeddingConfig] = None,
    ):
        """Initialize Jina Embeddings v4 model.

        Args:
            model_name: Hugging Face model identifier
            device: Device to use (auto-detects MPS if available)
            cache_dir: Directory for caching model weights
            trust_remote_code: Whether to trust remote code from Hugging Face
            config: Default embedding configuration (uses for_documents() if not provided)

        Examples:
            >>> # Default configuration
            >>> embedder = JinaEmbeddingsV4()

            >>> # With custom config
            >>> config = EmbeddingConfig.for_query()
            >>> embedder = JinaEmbeddingsV4(config=config)

            >>> # Storage-optimized
            >>> config = EmbeddingConfig.storage_optimized()
            >>> embedder = JinaEmbeddingsV4(config=config)
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/huggingface")
        self.trust_remote_code = trust_remote_code

        # Set default configuration
        if config is None:
            config = EmbeddingConfig.for_documents()
        self.default_config = config
        logger.info(f"Using default embedding configuration: {config}")

        # Set device with MPS priority
        if device:
            self.device = device
        elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
            self.device = "mps"
            logger.info("Using MPS backend for acceleration")
        elif torch.cuda.is_available():
            self.device = "cuda"
            logger.info("Using CUDA backend")
        else:
            self.device = "cpu"
            logger.warning("No GPU acceleration available, using CPU")

        # Lazy loading - model is loaded on first use
        self._model = None
        self._tokenizer = None

        # Multi-vector handler for ColBERT-style retrieval
        self.multivector_handler = MultiVectorHandler()

        # Format converter for binary/ubinary formats
        self.format_converter = FormatConverter()

        # Batch processor for token-aware batching
        self.batch_processor = BatchProcessor(
            max_tokens_per_batch=config.max_tokens_per_batch if config else 8192,
            adaptive=True,
        )
        
    @property
    def model(self):
        """Lazy load the model on first access."""
        if self._model is None:
            self._load_model()
        return self._model
    
    @property
    def tokenizer(self):
        """Lazy load the tokenizer on first access."""
        if self._tokenizer is None:
            self._load_tokenizer()
        return self._tokenizer
    
    def _load_model(self):
        """Load the model with proper configuration."""
        logger.info(f"Loading model {self.model_name}...")
        
        try:
            # Use float32 for vision models on MPS (float16 can cause issues)
            # The model internally uses bfloat16 for vision components
            dtype = torch.float32
            
            self._model = AutoModel.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=self.trust_remote_code,
                torch_dtype=dtype,
            )
            
            # Move model to device
            self._model = self._model.to(self.device)
            self._model.eval()
            
            logger.info(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            if self.device == "mps":
                logger.warning(f"Failed to load on MPS: {e}, falling back to CPU")
                self.device = "cpu"
                self._model = AutoModel.from_pretrained(
                    self.model_name,
                    cache_dir=self.cache_dir,
                    trust_remote_code=self.trust_remote_code,
                    torch_dtype=torch.float32,
                )
                self._model.eval()
            else:
                raise
    
    def _load_tokenizer(self):
        """Load the tokenizer."""
        logger.info(f"Loading tokenizer for {self.model_name}...")
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            trust_remote_code=self.trust_remote_code,
        )
    
    def _encode_batch(
        self,
        texts: List[str],
        task: TaskType = "retrieval",
        prompt_name: Optional[PromptType] = None,
        truncate_dim: Optional[int] = None,
        max_length: int = 8192,
        batch_size: int = 8,
        show_progress: bool = False,
        return_multivector: bool = False,
        late_chunking: bool = False,
    ) -> np.ndarray:
        """Internal method to encode text into embeddings.

        Args:
            texts: List of texts to encode
            task: Task type for adapter selection
            prompt_name: Prompt type for retrieval task (query/passage)
            truncate_dim: Truncate embeddings to this dimension (128-2048)
            max_length: Maximum sequence length
            batch_size: Batch size for processing
            show_progress: Show progress bar
            return_multivector: Return multi-vector embeddings
            late_chunking: Enable late chunking for better context preservation

        Returns:
            Numpy array of embeddings with shape (len(texts), dimensions)
        """
        # Validate truncation dimension
        if truncate_dim is not None:
            if truncate_dim not in [128, 256, 512, 1024, 2048]:
                raise ValueError(f"truncate_dim must be one of [128, 256, 512, 1024, 2048], got {truncate_dim}")

        all_embeddings = []

        # Process in batches
        for i in tqdm(range(0, len(texts), batch_size), disable=not show_progress, desc="Encoding"):
            batch_texts = texts[i:i + batch_size]

            # Tokenize
            inputs = self.tokenizer(
                batch_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length,
            ).to(self.device)

            # Generate embeddings
            with torch.no_grad():
                if hasattr(self.model, 'encode_text'):
                    # Use model's built-in encode_text if available
                    # Build kwargs conditionally to support models with/without late_chunking
                    encode_kwargs = {
                        'texts': batch_texts,
                        'task': task,
                        'prompt_name': prompt_name,
                        'return_multivector': return_multivector,
                    }

                    # Add late_chunking if supported by the model
                    if late_chunking:
                        # Check if model accepts late_chunking parameter
                        import inspect
                        if 'late_chunking' in inspect.signature(self.model.encode_text).parameters:
                            encode_kwargs['late_chunking'] = late_chunking
                            logger.debug(f"Late chunking enabled for batch {i//batch_size + 1}")
                        else:
                            logger.warning(
                                "Late chunking requested but model doesn't support it. "
                                "Proceeding without late chunking."
                            )

                    embeddings = self.model.encode_text(**encode_kwargs)
                    # The model's encode_text returns tensors or list
                    if isinstance(embeddings, list):
                        # Convert each tensor in list to numpy
                        embeddings = np.array([e.cpu().numpy() if isinstance(e, torch.Tensor) else e for e in embeddings])
                    elif isinstance(embeddings, torch.Tensor):
                        embeddings = embeddings.cpu().numpy()
                    else:
                        # Already numpy array
                        embeddings = np.array(embeddings)
                else:
                    # Fallback to standard forward pass
                    outputs = self.model(**inputs)

                    if return_multivector:
                        # Return all token embeddings for multi-vector
                        embeddings = outputs.last_hidden_state
                    else:
                        # Mean pooling for single vector
                        attention_mask = inputs['attention_mask'].unsqueeze(-1)
                        embeddings = (outputs.last_hidden_state * attention_mask).sum(1) / attention_mask.sum(1)

                    # Move to CPU and convert to numpy
                    embeddings = embeddings.cpu().numpy()

                # Apply dimension truncation if requested
                if truncate_dim is not None and not return_multivector:
                    embeddings = embeddings[:, :truncate_dim]

                all_embeddings.append(embeddings)

        # Concatenate all batches
        result = np.vstack(all_embeddings)

        return result
    
    def encode_image(
        self,
        images: Union[Image.Image, List[Image.Image], str, List[str]],
        task: TaskType = "retrieval",
        truncate_dim: Optional[int] = None,
        return_multivector: bool = False,
        batch_size: int = 8,
        show_progress: bool = False,
    ) -> np.ndarray:
        """Encode images into embeddings using vision adapter.
        
        Args:
            images: Image(s) as PIL Images or paths
            task: Task type for adapter selection
            truncate_dim: Truncate embeddings to this dimension
            return_multivector: Return multi-vector embeddings
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            Numpy array of embeddings
        """
        # Ensure model is loaded
        if self._model is None:
            self._load_model()
            
        # Handle single image input
        single_input = False
        if isinstance(images, (str, Image.Image)):
            images = [images]
            single_input = True
            
        # Load images if paths are provided
        loaded_images = []
        for img in images:
            if isinstance(img, str):
                from ..multimodal.image_processor import ImageProcessor
                processor = ImageProcessor()
                loaded_images.append(processor.load_image(img))
            elif isinstance(img, Image.Image):
                loaded_images.append(img)
            else:
                raise ValueError(f"Unsupported image type: {type(img)}")
                
        all_embeddings = []
        
        # Process in batches
        for i in tqdm(range(0, len(loaded_images), batch_size), disable=not show_progress, desc="Encoding images"):
            batch_images = loaded_images[i:i + batch_size]
            
            # Generate embeddings
            with torch.no_grad():
                if hasattr(self.model, 'encode_image'):
                    # Use model's built-in encode_image if available
                    # Note: The model expects PIL Images directly, not preprocessed tensors
                    embeddings = self.model.encode_image(
                        images=batch_images,
                        task=task,
                        return_multivector=return_multivector,
                    )
                    
                    # Handle list of tensors output
                    if isinstance(embeddings, list):
                        # Convert list of tensors to numpy array
                        embeddings_np = []
                        for emb in embeddings:
                            if hasattr(emb, 'cpu'):
                                embeddings_np.append(emb.cpu().numpy())
                            else:
                                embeddings_np.append(np.array(emb))
                        embeddings = np.array(embeddings_np)
                    elif isinstance(embeddings, torch.Tensor):
                        embeddings = embeddings.cpu().numpy()
                    else:
                        embeddings = np.array(embeddings)
                else:
                    # Fallback: use text model with image features
                    # This is a simplified approach - real multimodal would need proper vision encoder
                    logger.warning("Model does not have encode_image method. Using fallback text encoding.")

                    # Convert PIL images to simple text descriptions
                    batch_texts = []
                    for img in batch_images:
                        # Get image statistics
                        img_array = np.array(img)
                        mean_vals = img_array.mean(axis=(0, 1))
                        feature_text = f"Image features: RGB means {mean_vals[0]:.2f}, {mean_vals[1]:.2f}, {mean_vals[2]:.2f}"
                        batch_texts.append(feature_text)

                    # Encode as text
                    embeddings = self._encode_batch(
                        batch_texts,
                        task=task,
                        prompt_name="passage",
                        truncate_dim=truncate_dim,
                        return_multivector=return_multivector,
                        batch_size=batch_size,
                        show_progress=False
                    )
                
                # Apply dimension truncation if requested
                if truncate_dim is not None and not return_multivector:
                    embeddings = embeddings[:, :truncate_dim]
                
                all_embeddings.append(embeddings)
        
        # Concatenate all batches
        result = np.vstack(all_embeddings) if all_embeddings else np.array([])
        
        # Return single embedding if input was single image
        if single_input and len(result) > 0:
            result = result[0]
        
        return result
    
    def get_device_info(self) -> dict:
        """Get information about the current device configuration."""
        info = {
            "device": self.device,
            "model_loaded": self._model is not None,
            "tokenizer_loaded": self._tokenizer is not None,
        }

        if self.device == "mps":
            info["mps_available"] = torch.backends.mps.is_available()
            info["mps_built"] = torch.backends.mps.is_built()
        elif self.device == "cuda":
            info["cuda_version"] = torch.version.cuda
            info["gpu_name"] = torch.cuda.get_device_name(0)

        return info

    def embed_with_config(
        self,
        texts: Union[str, List[str]],
        config: Optional[EmbeddingConfig] = None,
        show_progress: bool = False,
    ) -> np.ndarray:
        """Embed texts using configuration-based API (recommended).

        This is the primary API for embedding with full configuration control.
        It supports all advanced features including late chunking, task-specific
        optimization, dimension truncation, and format conversion.

        Args:
            texts: Single text or list of texts to embed
            config: Embedding configuration (uses default_config if not provided)
            show_progress: Show progress bar during embedding

        Returns:
            Numpy array of embeddings with shape:
                - Single text: (dimensions,)
                - Multiple texts: (num_texts, dimensions)

        Examples:
            >>> embedder = JinaEmbeddingsV4()

            >>> # Use default configuration
            >>> embeddings = embedder.embed_with_config(["document text"])

            >>> # Query configuration
            >>> config = EmbeddingConfig.for_query()
            >>> query_emb = embedder.embed_with_config("search query", config)

            >>> # Storage-optimized with ubinary format
            >>> config = EmbeddingConfig.storage_optimized()
            >>> embeddings = embedder.embed_with_config(documents, config)

            >>> # Custom configuration
            >>> config = EmbeddingConfig(
            ...     task="retrieval.passage",
            ...     dimensions=512,
            ...     late_chunking=True,
            ...     batch_size=16
            ... )
            >>> embeddings = embedder.embed_with_config(texts, config)
        """
        # Use default config if not provided
        if config is None:
            config = self.default_config
            logger.debug("Using default configuration for embedding")

        # Parse task parameter (e.g., "retrieval.query" -> task="retrieval", prompt="query")
        task_parts = config.task.split(".")
        if len(task_parts) == 2:
            task = task_parts[0]
            prompt_name = task_parts[1]
        else:
            task = config.task
            prompt_name = None

        # Ensure texts is a list
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
        else:
            single_input = False

        # Log configuration being used
        logger.info(
            f"Embedding with config: task={config.task}, dims={config.dimensions}, "
            f"late_chunking={config.late_chunking}, batch_size={config.batch_size}"
        )

        # Encode using internal batch encoder
        embeddings = self._encode_batch(
            texts=texts,
            task=task,
            prompt_name=prompt_name,
            truncate_dim=config.dimensions if config.dimensions != 2048 else None,
            batch_size=config.batch_size,
            show_progress=show_progress,
            return_multivector=config.return_multivector,
            late_chunking=config.late_chunking,  # Phase 2: Late chunking support
        )

        # Phase 5: Apply format conversion if requested
        if config.embedding_format != "float" and not config.return_multivector:
            logger.info(f"Converting embeddings to {config.embedding_format} format")

            if config.embedding_format == "ubinary":
                embeddings = self.format_converter.to_ubinary(embeddings, normalize=True)
            elif config.embedding_format == "binary":
                embeddings = self.format_converter.to_binary(embeddings, threshold=0.0)
            elif config.embedding_format == "base64":
                # Convert to ubinary first, then base64 encode
                embeddings = self.format_converter.to_base64(embeddings, binary_format="ubinary")

            logger.debug(
                f"Format conversion complete. "
                f"Size reduction: ~{32 if config.embedding_format in ['binary', 'ubinary'] else 1}×"
            )
        elif config.embedding_format != "float" and config.return_multivector:
            logger.warning(
                f"Format conversion to {config.embedding_format} is not supported with "
                "return_multivector=True. Returning float embeddings."
            )

        # Return single embedding if input was single text
        if single_input and embeddings.ndim > 0:
            embeddings = embeddings[0]

        return embeddings

    def generate_multivector_embeddings(
        self,
        texts: Union[str, List[str]],
        config: Optional[EmbeddingConfig] = None,
    ) -> List[np.ndarray]:
        """Generate multi-vector (token-level) embeddings for ColBERT-style retrieval.

        Multi-vector embeddings represent each text as a sequence of token embeddings
        rather than a single pooled vector. This enables late interaction retrieval
        using MaxSim scoring for improved accuracy.

        Args:
            texts: Single text or list of texts to encode
            config: Embedding configuration (uses config with return_multivector=True)

        Returns:
            List of numpy arrays, one per text. Each array has shape (num_tokens, dim)

        Examples:
            >>> embedder = JinaEmbeddingsV4()

            >>> # Generate multi-vector embeddings for documents
            >>> doc_config = EmbeddingConfig.for_documents()
            >>> doc_vectors = embedder.generate_multivector_embeddings(
            ...     ["Document with multiple tokens"],
            ...     doc_config
            ... )
            >>> print(doc_vectors[0].shape)  # (num_tokens, 1024)

            >>> # Use MultiVectorHandler for retrieval
            >>> query_vectors = embedder.generate_multivector_embeddings(["query"])
            >>> score = embedder.multivector_handler.maxsim_score(
            ...     query_vectors[0],
            ...     doc_vectors[0]
            ... )
            >>> print(f"MaxSim score: {score:.4f}")
        """
        # Use default config if not provided
        if config is None:
            config = self.default_config

        # Ensure texts is a list
        if isinstance(texts, str):
            texts = [texts]

        # Parse task parameter
        task_parts = config.task.split(".")
        if len(task_parts) == 2:
            task = task_parts[0]
            prompt_name = task_parts[1]
        else:
            task = config.task
            prompt_name = None

        logger.info(
            f"Generating multi-vector embeddings for {len(texts)} texts with "
            f"task={config.task}, dims={config.dimensions}"
        )

        # Use MultiVectorHandler to generate embeddings
        multivectors = self.multivector_handler.generate_multivector(
            model=self.model,
            texts=texts,
            task=task,
            prompt_name=prompt_name,
            device=self.device,
        )

        logger.info(
            f"Generated multi-vector embeddings: {len(multivectors)} texts, "
            f"avg {np.mean([len(v) for v in multivectors]):.1f} tokens/text"
        )

        return multivectors

    def clear_cache(self):
        """Clear model from memory."""
        self._model = None
        self._tokenizer = None

        if self.device == "mps":
            torch.mps.empty_cache()
        elif self.device == "cuda":
            torch.cuda.empty_cache()

        logger.info("Model cache cleared")