"""JinaAI reranker for improved retrieval precision."""

import logging
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)


class JinaReranker:
    """
    JinaAI reranker for refining retrieval results.

    Supports both cross-encoder models (v1-turbo) and vision-language models (M0)
    for improved relevance ranking. Supports lazy loading and fallback to
    original scores on errors.
    """

    # Available JinaAI models
    JINAAI_MODELS = {
        "jinaai/jina-reranker-m0": {
            "type": "vlm",  # Vision-Language Model
            "description": "Multimodal reranker (text + images)",
            "params": "2.4B"
        },
        "jinaai/jina-reranker-v1-turbo-en": {
            "type": "cross_encoder",  # Cross-Encoder
            "description": "Fast text-only reranker",
            "params": "33M"
        }
    }

    def __init__(
        self,
        model_name: str = "jinaai/jina-reranker-m0",  # Default to M0
        device: Optional[str] = None,
        use_quantization: bool = True,
    ):
        """
        Initialize the reranker.

        Args:
            model_name: JinaAI model identifier (m0 or v1-turbo-en)
            device: Device to run model on ('mps', 'cuda', 'cpu', or None for auto)
            use_quantization: Whether to use 4-bit quantization (reduces memory)
        """
        if model_name not in self.JINAAI_MODELS:
            available = list(self.JINAAI_MODELS.keys())
            raise ValueError(f"Unknown model '{model_name}'. Available: {available}")

        self.model_name = model_name
        self.model_config = self.JINAAI_MODELS[model_name]
        self.model_type = self.model_config["type"]
        self.use_quantization = use_quantization

        # Lazy loading - model and tokenizer are None until first use
        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None

        # Auto-detect device if not specified
        if device is None:
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
        else:
            self.device = device

        logger.info(
            f"Initialized JinaReranker with model={model_name} ({self.model_config['description']}), "
            f"device={self.device}, quantization={use_quantization}"
        )

    def _load_model(self) -> None:
        """Load the JinaAI model and tokenizer."""
        if self.model is not None:
            return  # Already loaded

        logger.info(f"Loading JinaAI model: {self.model_name} ({self.model_config['description']})")

        try:
            if self.model_type == "vlm":  # Vision-Language Model (M0)
                # JinaAI M0 uses AutoModel with custom compute_score method
                self.model = AutoModel.from_pretrained(
                    self.model_name,
                    torch_dtype="auto",
                    trust_remote_code=True,
                )
                self.model.eval()
                logger.info(f"Successfully loaded VLM {self.model_name}")

            elif self.model_type == "cross_encoder":  # Cross-Encoder (v1-turbo)
                # JinaAI v1-turbo uses standard cross-encoder architecture
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

                # Load model with optional quantization
                if self.use_quantization and self.device != "mps":
                    logger.info("Attempting 4-bit quantization...")
                    self.model = AutoModelForSequenceClassification.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16,
                        device_map="auto",
                    )
                else:
                    self.model = AutoModelForSequenceClassification.from_pretrained(
                        self.model_name
                    )
                    self.model.to(self.device)

                self.model.eval()
                logger.info(f"Successfully loaded cross-encoder {self.model_name} on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load JinaAI model {self.model_name}: {e}")
            raise

    def _compute_scores(
        self,
        query: str,
        documents: List[str],
        batch_size: int = 8
    ) -> List[float]:
        """
        Compute relevance scores for query-document pairs.

        Args:
            query: Query string
            documents: List of document text strings
            batch_size: Batch size for processing

        Returns:
            List of relevance scores (higher is better)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call _load_model() first.")

        if self.model_type == "vlm":  # JinaAI M0
            # Use the model's native compute_score method
            pairs = [[query, doc] for doc in documents]
            scores = self.model.compute_score(pairs, max_length=1024, doc_type="text")
            # Ensure we return a list of floats
            if hasattr(scores, 'tolist'):
                return scores.tolist()
            elif hasattr(scores, '__iter__'):
                return list(scores)
            else:
                return [float(scores)]

        elif self.model_type == "cross_encoder":  # JinaAI v1-turbo
            # Standard cross-encoder approach
            if self.tokenizer is None:
                raise RuntimeError("Tokenizer not loaded for cross-encoder model.")

            scores = []

            with torch.no_grad():
                for i in range(0, len(documents), batch_size):
                    batch_docs = documents[i:i + batch_size]

                    # Create query-document pairs
                    pairs = [[query, doc] for doc in batch_docs]

                    # Tokenize
                    inputs = self.tokenizer(
                        pairs,
                        padding=True,
                        truncation=True,
                        max_length=512,
                        return_tensors="pt"
                    ).to(self.device)

                    # Get scores
                    outputs = self.model(**inputs)
                    batch_scores = outputs.logits.squeeze(-1).cpu().float().tolist()

                    # Handle single-item batch (logits might not have batch dim)
                    if isinstance(batch_scores, float):
                        batch_scores = [batch_scores]

                    scores.extend(batch_scores)

            return scores

        # Fallback (should not reach here)
        return []

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = 5,
        score_key: str = "score",
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using JinaAI model.

        Args:
            query: Query string
            documents: List of document dictionaries with 'content' and optional 'score'
            top_n: Number of top documents to return after reranking
            score_key: Key to use for original score (preserved as 'original_score')

        Returns:
            Top-N reranked documents with added 'rerank_score' field and preserved 'original_score'
        """
        if not documents:
            return []

        try:
            # Lazy load model on first use
            if self.model is None:
                self._load_model()

            # Extract document content
            doc_texts = [doc.get("content", "") for doc in documents]

            # Compute reranking scores
            rerank_scores = self._compute_scores(query, doc_texts)

            # Add scores to documents and preserve original scores
            reranked_docs = []
            for doc, score in zip(documents, rerank_scores):
                reranked_doc = doc.copy()
                reranked_doc["original_score"] = doc.get(score_key, 0.0)
                reranked_doc["rerank_score"] = score
                reranked_doc[score_key] = score  # Update primary score
                reranked_docs.append(reranked_doc)

            # Sort by rerank score (descending) and return top_n
            reranked_docs.sort(key=lambda x: x["rerank_score"], reverse=True)

            logger.info(
                f"Reranked {len(documents)} documents with {self.model_name}, returning top {top_n}. "
                f"Top score: {reranked_docs[0]['rerank_score']:.3f}"
            )

            return reranked_docs[:top_n]

        except Exception as e:
            logger.error(f"JinaAI reranking failed: {e}. Falling back to original scores.")
            # Fallback: return original documents sorted by original score
            fallback_docs = sorted(
                documents,
                key=lambda x: x.get(score_key, 0.0),
                reverse=True
            )
            return fallback_docs[:top_n]

    def __del__(self) -> None:
        """Cleanup: free model memory on deletion."""
        if self.model is not None:
            del self.model
            if hasattr(self, 'tokenizer') and self.tokenizer is not None:
                del self.tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
