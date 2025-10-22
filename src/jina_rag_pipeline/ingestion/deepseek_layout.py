"""
Deepseek-OCR based layout analysis for document understanding with grounding support.

This module provides semantic layout analysis using the Deepseek-OCR 3B MoE
vision-language model with spatial grounding capabilities. Deepseek-OCR provides:
- Native grounding support (bounding boxes)
- 10x visual-text compression with 97% precision
- Multiple resolution modes (tiny/small/base/large/gundam)
- Flash-attention 2.0 on CUDA (with graceful fallback to SDPA)

Features:
- Table extraction with full structure (HTML + markdown)
- Equation recognition (LaTeX format)
- Image descriptions with type classification
- Spatial grounding with normalized bounding boxes
- Compression for efficient token usage
- CUDA and MPS support with optimized attention mechanisms
"""

import logging
import gc
import re
import inspect
from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Literal
from enum import Enum

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import torch
    from transformers import AutoTokenizer, AutoProcessor, AutoModel
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False

from .semantic_region import SemanticRegion, BoundingBox
from .markdown_parser import MarkdownParser

# Provide CPU/MPS compatibility for remote Deepseek modules that expect flash-attention.
try:  # pragma: no cover - environment-specific patch
    import transformers.models.llama.modeling_llama as _llama_module

    if not hasattr(_llama_module, "LlamaFlashAttention2"):
        class LlamaFlashAttention2(_llama_module.LlamaAttention):  # type: ignore[attr-defined]
            """Compatibility stub mapping flash attention to standard attention."""

        _llama_module.LlamaFlashAttention2 = LlamaFlashAttention2  # type: ignore[attr-defined]
        logger = logging.getLogger(__name__)
        logger.debug("Injected global LlamaFlashAttention2 compatibility stub for CPU/MPS execution")
except Exception:  # pragma: no cover - defensive
    pass

logger = logging.getLogger(__name__)


class ResolutionMode(str, Enum):
    """Resolution modes balancing speed and quality."""
    TINY = "tiny"       # 512x512, 64 tokens - 2-3x faster
    SMALL = "small"     # 640x640, 100 tokens - Speed/quality balance
    BASE = "base"       # 1024x1024, 256 tokens - Default quality
    LARGE = "large"     # 1280x1280, 400 tokens - High quality
    GUNDAM = "gundam"   # Dynamic multi-resolution - Complex layouts


class DeepseekLayoutAnalyzer:
    """
    Semantic layout analyzer using Deepseek-OCR with grounding support.

    This analyzer uses a 3B MoE vision-language model to understand document content
    and extract structured information with optional spatial localization.

    Key Advantages over Nanonets:
    - Native grounding support with bounding boxes
    - 10x visual-text compression (97% precision)
    - Higher throughput (2500 tokens/s with vLLM on A100)
    - Multiple resolution modes for speed/quality tradeoffs
    - CUDA-first with flash-attention 2.0

    Example:
        # Fast preset for simple documents
        analyzer = DeepseekLayoutAnalyzer(resolution_mode="tiny")
        regions = analyzer.extract_regions("slide.png", page_number=1)

        # High quality with grounding
        analyzer = DeepseekLayoutAnalyzer(
            resolution_mode="large",
            enable_grounding=True
        )
        regions = analyzer.extract_regions("complex_doc.png")
    """

    def __init__(
        self,
        model_name: str = "deepseek-ai/DeepSeek-OCR",
        device: str = "auto",
        torch_dtype=None,
        resolution_mode: str = "base",
        # Deepseek-specific features
        enable_grounding: bool = True,
        enable_compression: bool = True,
        use_vllm: bool = False,
        # Content extraction controls
        enable_tables: bool = True,
        enable_equations: bool = True,
        enable_image_descriptions: bool = True,
        max_new_tokens: int = 4096,
        # Attention mechanism
        attn_implementation: str = "auto",
        # Memory management
        enable_preprocessing: bool = True,
        enable_memory_management: bool = True,
        memory_fraction: float = 0.8,
        enable_memory_monitoring: bool = False,
    ):
        """
        Initialize Deepseek layout analyzer.

        Args:
            model_name: HuggingFace model identifier
            device: Device to run on ("auto", "cuda", "mps", "cpu")
            torch_dtype: Torch dtype (defaults to bfloat16)
            resolution_mode: Resolution mode ("tiny", "small", "base", "large", "gundam")
            enable_grounding: Enable spatial grounding (bounding boxes)
            enable_compression: Enable visual-text compression
            use_vllm: Use vLLM backend for production throughput (optional)
            enable_tables: Extract tables in HTML format
            enable_equations: Extract equations in LaTeX format
            enable_image_descriptions: Generate image descriptions
            max_new_tokens: Maximum tokens for model generation
            attn_implementation: Attention mechanism ("auto", "flash_attention_2", "sdpa")
            enable_preprocessing: Enable image preprocessing pipeline
            enable_memory_management: Enable memory management
            memory_fraction: Fraction of GPU memory to use (0.0-1.0)
            enable_memory_monitoring: Log memory usage for debugging
        """
        if not DEEPSEEK_AVAILABLE:
            raise ImportError(
                "Deepseek dependencies not available. "
                "Install with: pip install pillow torch transformers"
            )

        self.model_name = model_name
        self.resolution_mode = ResolutionMode(resolution_mode)
        self.enable_grounding = enable_grounding
        self.enable_compression = enable_compression
        self.use_vllm = use_vllm
        self.enable_tables = enable_tables
        self.enable_equations = enable_equations
        self.enable_image_descriptions = enable_image_descriptions
        self.max_new_tokens = max_new_tokens
        self.enable_preprocessing = enable_preprocessing
        self.enable_memory_management = enable_memory_management
        self.memory_fraction = memory_fraction
        self.enable_memory_monitoring = enable_memory_monitoring

        # Auto-detect device
        if device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
                logger.warning("No GPU available, using CPU (will be very slow)")
        else:
            self.device = device

        # Set dtype optimized for device
        if torch_dtype is None:
            if self.device == "cuda":
                self.torch_dtype = torch.bfloat16  # Best for CUDA
            elif self.device == "mps":
                self.torch_dtype = torch.float16   # MPS compatibility
            else:
                self.torch_dtype = torch.float32   # CPU fallback
        else:
            self.torch_dtype = torch_dtype

        # Determine attention implementation
        self.attn_implementation = self._determine_attention(attn_implementation)

        # Apply resolution mode parameters
        self._apply_resolution_mode()

        # Initialize parser
        self.parser = MarkdownParser()

        # Lazy load model (only when needed)
        self._model = None
        self._tokenizer = None
        self._processor = None
        self._chat_template_available: Optional[bool] = None
        self._images_processed = 0
        self._offline_mode = False
        self._current_source_document: Optional[Path] = None
        self._offline_page_text_cache: Dict[int, str] = {}

        # Configure device environment
        if self.device == "mps":
            self._configure_mps_environment()

        logger.info(
            f"DeepseekLayoutAnalyzer initialized: "
            f"model={model_name}, device={self.device}, dtype={self.torch_dtype}, "
            f"resolution={resolution_mode}, grounding={enable_grounding}, "
            f"compression={enable_compression}, attention={self.attn_implementation}"
        )

    def _determine_attention(self, attn_implementation: str) -> str:
        """Determine which attention mechanism to use."""
        if attn_implementation != "auto":
            return attn_implementation

        # Flash-attention 2.0 only available on CUDA
        if self.device == "cuda":
            try:
                import flash_attn
                logger.info("Flash-attention detected, using flash_attention_2")
                return "flash_attention_2"
            except ImportError:
                logger.warning(
                    "Flash-attention not installed on CUDA. "
                    "Install with: pip install flash-attn==2.7.3 for 2-3x speedup. "
                    "Falling back to SDPA."
                )
                return "sdpa"
        else:
            # MPS and CPU use SDPA (PyTorch scaled dot-product attention)
            logger.info(f"Using SDPA attention on {self.device}")
            return "sdpa"

    def _apply_resolution_mode(self):
        """Apply resolution mode parameters."""
        # Resolution parameters based on Deepseek-OCR documentation
        if self.resolution_mode == ResolutionMode.TINY:
            self.base_size = 512
            self.image_size = 512
            self.crop_mode = False
            self.vision_tokens = 64
            logger.info("Using TINY mode: 512x512, 64 tokens - 2-3x faster")

        elif self.resolution_mode == ResolutionMode.SMALL:
            self.base_size = 640
            self.image_size = 640
            self.crop_mode = False
            self.vision_tokens = 100
            logger.info("Using SMALL mode: 640x640, 100 tokens - Speed/quality balance")

        elif self.resolution_mode == ResolutionMode.BASE:
            self.base_size = 1024
            self.image_size = 1024
            self.crop_mode = False
            self.vision_tokens = 256
            logger.info("Using BASE mode: 1024x1024, 256 tokens - Default quality")

        elif self.resolution_mode == ResolutionMode.LARGE:
            self.base_size = 1280
            self.image_size = 1280
            self.crop_mode = False
            self.vision_tokens = 400
            logger.info("Using LARGE mode: 1280x1280, 400 tokens - High quality")

        else:  # GUNDAM
            self.base_size = 1024
            self.image_size = 640
            self.crop_mode = True
            self.vision_tokens = None  # Dynamic
            logger.info("Using GUNDAM mode: Dynamic multi-resolution - Complex layouts")

    def _configure_mps_environment(self):
        """Configure MPS-specific environment variables for optimal performance."""
        import os
        os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
        logger.info("MPS environment configured: fallback enabled")

    def _load_model(self):
        """Lazy load the model with flash-attention or SDPA fallback."""
        if self._model is not None:
            return

        if self.use_vllm:
            self._load_vllm_model()
            return

        logger.info(f"Loading Deepseek model: {self.model_name}")
        logger.info("(First load may take several minutes to download ~6.7GB)")

        try:
            # Set memory fraction before loading
            if self.device == "mps" and self.enable_memory_management:
                torch.mps.set_per_process_memory_fraction(self.memory_fraction)
                logger.info(f"Set MPS memory fraction to {self.memory_fraction}")
            elif self.device == "cuda" and self.enable_memory_management:
                # CUDA memory management handled by PyTorch
                pass

            # Provide flash-attention stubs for CPU/MPS environments.
            try:
                import transformers.models.llama.modeling_llama as llama_module

                if not hasattr(llama_module, "LlamaFlashAttention2"):
                    class LlamaFlashAttention2(llama_module.LlamaAttention):  # type: ignore[attr-defined]
                        """Compatibility stub mapping flash-attn to standard attention."""

                    llama_module.LlamaFlashAttention2 = LlamaFlashAttention2  # type: ignore[attr-defined]
                    logger.debug("Injected LlamaFlashAttention2 compatibility stub for CPU/MPS execution")
            except Exception as stub_error:  # pragma: no cover - defensive
                logger.debug(f"Unable to inject flash attention stub: {stub_error}")

            # Load model with attention implementation
            # Note: DeepseekOCR model requires eager attention implementation
            try:
                logger.info(f"Loading with {self.attn_implementation} attention...")
                self._model = AutoModel.from_pretrained(
                    self.model_name,
                    torch_dtype=self.torch_dtype,
                    attn_implementation=self.attn_implementation,
                    trust_remote_code=True,
                    use_safetensors=True,
                    low_cpu_mem_usage=True,
                )
            except Exception as e:
                # If attention implementation fails, fallback to eager mode
                if "attention" in str(e).lower() or "flash_attn" in str(e).lower():
                    logger.warning(
                        f"{self.attn_implementation} attention failed: {e}. "
                        f"Falling back to eager attention..."
                    )
                    self._model = AutoModel.from_pretrained(
                        self.model_name,
                        torch_dtype=self.torch_dtype,
                        attn_implementation='eager',
                        trust_remote_code=True,
                        use_safetensors=True,
                        low_cpu_mem_usage=True,
                    )
                    self.attn_implementation = "eager"
                else:
                    raise

            # Move to device
            self._model = self._model.to(self.device)
            self._model.eval()

            # Load processor and tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            self._processor = AutoProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            self._chat_template_available = bool(
                getattr(self._processor, "chat_template", None)
            )
            if not self._chat_template_available:
                logger.debug(
                    "Deepseek processor does not include a chat template; "
                    "manual prompt formatting will be used."
                )
            try:
                processor_signature = inspect.signature(self._processor.__call__)
                supports_images = "images" in processor_signature.parameters
            except (AttributeError, TypeError, ValueError):
                supports_images = False

            self._offline_mode = not supports_images
            if self._offline_mode:
                logger.info(
                    "Deepseek processor lacks multimodal inputs; "
                    "enabling offline OCR fallback."
                )

            logger.info(
                f"Model loaded successfully on device: {self._model.device}, "
                f"attention: {self.attn_implementation}"
            )

            if self.enable_memory_monitoring:
                self._log_memory_usage()

        except Exception as e:
            logger.error(f"Failed to load Deepseek model: {e}")
            raise RuntimeError(f"Deepseek model loading failed: {e}") from e

    def _load_vllm_model(self):
        """Load model using vLLM for production throughput."""
        try:
            from vllm import LLM, SamplingParams
        except ImportError:
            raise ImportError(
                "vLLM not available. Install with: pip install vllm>=0.8.5"
            )

        logger.info("Loading Deepseek model with vLLM backend...")
        self._model = LLM(model=self.model_name)
        self._sampling_params = SamplingParams(max_tokens=self.max_new_tokens)
        logger.info("vLLM model loaded successfully")

    def _log_memory_usage(self):
        """Log current memory usage."""
        if self.device == "mps":
            try:
                current_mem = torch.mps.current_allocated_memory()
                driver_mem = torch.mps.driver_allocated_memory()
                logger.info(
                    f"MPS Memory - Current: {current_mem / 1024**3:.2f}GB, "
                    f"Driver: {driver_mem / 1024**3:.2f}GB"
                )
            except Exception as e:
                logger.debug(f"Could not read MPS memory: {e}")
        elif self.device == "cuda":
            try:
                current_mem = torch.cuda.memory_allocated()
                max_mem = torch.cuda.max_memory_allocated()
                logger.info(
                    f"CUDA Memory - Current: {current_mem / 1024**3:.2f}GB, "
                    f"Max: {max_mem / 1024**3:.2f}GB"
                )
            except Exception as e:
                logger.debug(f"Could not read CUDA memory: {e}")

    def _clear_memory_cache(self):
        """Clear memory cache to free memory."""
        if self.enable_memory_management:
            gc.collect()
            if self.device == "mps":
                torch.mps.empty_cache()
            elif self.device == "cuda":
                torch.cuda.empty_cache()
            if self.enable_memory_monitoring:
                logger.debug("Memory cache cleared")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Optimize image for faster OCR processing.

        Applies:
        - RGB conversion
        - DPI optimization (downsample if > 300 DPI)
        - Contrast enhancement
        - Light sharpening
        """
        if not self.enable_preprocessing:
            return image

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Optimize DPI (downsample if too high)
        dpi = image.info.get('dpi', (72, 72))
        if max(dpi) > 300:
            scale = 300 / max(dpi)
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.LANCZOS)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)

        # Light sharpening
        image = image.filter(ImageFilter.SHARPEN)

        return image

    def _create_prompt(self) -> str:
        """
        Create the prompt for document analysis with optional grounding.

        Returns:
            Formatted prompt string
        """
        # Start with grounding token if enabled
        prompt_parts = []

        if self.enable_grounding:
            prompt_parts.append("<|grounding|>")

        # Base extraction instructions
        prompt_parts.append(
            "Extract the text from the document in markdown format, maintaining the original structure."
        )

        if self.enable_tables:
            prompt_parts.append("Return tables in HTML format.")

        if self.enable_equations:
            prompt_parts.append("Return equations in LaTeX representation.")

        if self.enable_image_descriptions:
            prompt_parts.append(
                "If there is an image without a caption, add a description inside <img></img> tags; "
                "otherwise, use the existing caption."
            )

        # Formatting guidelines
        prompt_parts.append(
            "Watermarks should be wrapped as: <watermark>TEXT</watermark>. "
            "Page numbers should be wrapped as: <page_number>N</page_number>. "
            "Use ☐ for empty checkboxes and ☑ for checked boxes."
        )

        return " ".join(prompt_parts)

    def _parse_grounding_metadata(self, markdown: str) -> List[Dict[str, Any]]:
        """
        Parse grounding metadata from Deepseek markdown output.

        Deepseek outputs grounding in this format:
        # Heading <bbox>0.1,0.2,0.9,0.3</bbox>

        Args:
            markdown: Raw markdown with bbox tags

        Returns:
            List of grounding metadata dictionaries
        """
        if not self.enable_grounding:
            return []

        # Regex to extract <bbox>x1,y1,x2,y2</bbox> tags
        bbox_pattern = r'<bbox>([\d.]+),([\d.]+),([\d.]+),([\d.]+)</bbox>'
        matches = re.finditer(bbox_pattern, markdown)

        grounding_data = []
        for match in matches:
            try:
                x_min = float(match.group(1))
                y_min = float(match.group(2))
                x_max = float(match.group(3))
                y_max = float(match.group(4))

                # Create BoundingBox
                bbox = BoundingBox(
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max
                )
                grounding_data.append({
                    'bbox': bbox,
                    'position': match.start(),
                })
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse bounding box: {match.group(0)}, error: {e}")

        return grounding_data

    def analyze_document(
        self,
        file_path: Union[str, Path],
        page_number: int = 1
    ) -> str:
        """
        Analyze a document image and return structured markdown.

        Args:
            file_path: Path to image file (PNG, JPG, etc.)
            page_number: Page number for logging (default: 1)

        Returns:
            Structured markdown with semantic tags (and optional bbox tags)

        Raises:
            FileNotFoundError: If file doesn't exist
            RuntimeError: If model inference fails
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        self._load_model()

        if self._offline_mode:
            return self._offline_analyze_document(page_number=page_number)

        logger.info(f"Analyzing document: {file_path} (page {page_number})")

        try:
            # Load and preprocess image
            image = Image.open(file_path)
            image = self._preprocess_image(image)

            # Create prompt
            prompt = self._create_prompt()

            # Format as messages (Deepseek uses chat format)
            messages = [
                {"role": "user", "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ]},
            ]

            # Apply chat template
            text = self._format_chat_prompt(messages)

            # Process inputs
            inputs = self._processor(
                text=[text],
                images=[image],
                return_tensors="pt"
            )
            inputs = inputs.to(self._model.device)

            # Generate
            logger.debug(f"Running inference on {file_path}")
            with torch.inference_mode():
                output_ids = self._model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=False,
                    use_cache=True,
                )

            # Decode
            generated_ids = [
                output_ids[len(input_ids):]
                for input_ids, output_ids in zip(inputs.input_ids, output_ids)
            ]
            output_text = self._processor.batch_decode(
                generated_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]

            logger.info(f"Analysis complete: {len(output_text)} characters extracted")

            # Track and maintain
            self._images_processed += 1
            if self._images_processed % 10 == 0:
                self._clear_memory_cache()

            if self.enable_memory_monitoring:
                self._log_memory_usage()

            return output_text

        except Exception as e:
            logger.error(f"Failed to analyze document {file_path}: {e}")
            raise RuntimeError(f"Document analysis failed: {e}") from e

    def _format_chat_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format chat messages for Deepseek when tokenizer lacks a chat template.

        The upstream Deepseek repository formats prompts using `<|User|>` /
        `<|Assistant|>` roles with explicit `<image>` tokens. Recreate that
        behaviour locally when the tokenizer does not ship a template.
        """
        if self._processor is None:
            raise RuntimeError("Processor not loaded before formatting chat prompt")

        if self._chat_template_available is None:
            template = getattr(self._processor, "chat_template", None)
            self._chat_template_available = bool(template)
            if not self._chat_template_available:
                logger.info(
                    "Deepseek tokenizer does not expose a chat template; "
                    "falling back to manual prompt formatting."
                )

        if self._chat_template_available:
            try:
                return self._processor.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except (AttributeError, TypeError, ValueError) as template_error:
                logger.debug(
                    "Chat template application failed (%s); "
                    "switching to manual formatter.",
                    template_error,
                )
                self._chat_template_available = False

        return self._format_chat_prompt_fallback(messages)

    @staticmethod
    def _format_chat_prompt_fallback(messages: List[Dict[str, Any]]) -> str:
        """Manual formatter matching Deepseek's reference conversation style."""
        prompt_parts: List[str] = []

        for message in messages:
            role = (message.get("role") or "").lower()
            content = message.get("content")

            if role == "user" or role == "<|user|>":
                prompt_parts.append("<|User|>\n")

                if isinstance(content, str):
                    content = [{"type": "text", "text": content}]
                elif content is None:
                    content = []

                for item in content:
                    if isinstance(item, dict):
                        item_type = item.get("type")
                        if item_type == "image":
                            prompt_parts.append("<image>\n")
                        elif item_type == "text":
                            text = item.get("text", "")
                            prompt_parts.append(text)
                            if not text.endswith("\n"):
                                prompt_parts.append("\n")
                    else:
                        prompt_parts.append(str(item))
                        prompt_parts.append("\n")

                prompt_parts.append("<|Assistant|>")

            elif role == "assistant" or role == "<|assistant|>":
                assistant_content = message.get("content", "")
                if assistant_content:
                    if not str(assistant_content).startswith("<|Assistant|>"):
                        prompt_parts.append("\n<|Assistant|>\n")
                    prompt_parts.append(str(assistant_content))

        prompt = "".join(prompt_parts).strip("\n")
        return prompt if prompt else "<|User|>\n<image>\n<|Assistant|>"

    def set_source_document(self, source_path: Optional[Union[str, Path]]) -> None:
        """Provide the original document path for offline fallback mode."""
        if source_path is None:
            self._current_source_document = None
            self._offline_page_text_cache.clear()
            return

        path = Path(source_path)
        if self._current_source_document != path:
            self._current_source_document = path
            self._offline_page_text_cache.clear()

    def _offline_analyze_document(self, page_number: int) -> str:
        """Offline fallback returning plain text for the requested page."""
        text = self._offline_extract_text(page_number)
        if not text:
            logger.debug(
                "Offline OCR fallback returned empty text for page %s (source=%s)",
                page_number,
                self._current_source_document,
            )
            return ""
        return text

    def _offline_extract_regions(
        self,
        page_number: int,
        document_id: Optional[str] = None,
    ) -> List[SemanticRegion]:
        """Build minimal semantic regions for offline fallback mode."""
        text = self._offline_extract_text(page_number)
        content = text or ""
        region_id = f"{document_id or 'doc'}_{page_number}_0"

        region = SemanticRegion(
            region_id=region_id,
            region_type="text",
            region_sequence=0,
            page_number=page_number,
            content=content,
            raw_markdown=content,
            model="deepseek-ocr-offline",
        )
        return [region]

    def _offline_extract_text(self, page_number: int) -> str:
        """Extract text directly from the source document when offline."""
        if self._current_source_document is None:
            return ""

        if page_number in self._offline_page_text_cache:
            return self._offline_page_text_cache[page_number]

        suffix = self._current_source_document.suffix.lower()
        text = ""

        try:
            if suffix == ".pdf":
                import fitz  # PyMuPDF

                with fitz.open(str(self._current_source_document)) as doc:
                    if 1 <= page_number <= doc.page_count:
                        page = doc.load_page(page_number - 1)
                        text = page.get_text("text") or page.get_text()
            elif suffix in (".pptx", ".ppt"):
                from pptx import Presentation

                presentation = Presentation(str(self._current_source_document))
                if 1 <= page_number <= len(presentation.slides):
                    slide = presentation.slides[page_number - 1]
                    segments: List[str] = []
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            shape_text = shape.text.strip()
                            if shape_text:
                                segments.append(shape_text)
                    text = "\n".join(segments)
            else:
                logger.debug(
                    "Offline fallback does not support document type: %s",
                    suffix,
                )
        except Exception as offline_error:
            logger.warning(
                "Offline text extraction failed for page %s (%s): %s",
                page_number,
                self._current_source_document,
                offline_error,
            )
            text = ""

        text = (text or "").strip()
        self._offline_page_text_cache[page_number] = text
        return text

    def extract_regions(
        self,
        file_path: Union[str, Path],
        page_number: int = 1,
        document_id: Optional[str] = None
    ) -> List[SemanticRegion]:
        """
        Extract semantic regions from a document with optional grounding.

        Args:
            file_path: Path to image file
            page_number: Page number (1-indexed)
            document_id: Optional document identifier

        Returns:
            List of SemanticRegion objects with optional bbox fields

        Raises:
            FileNotFoundError: If file doesn't exist
            RuntimeError: If extraction fails
        """
        if self._offline_mode:
            return self._offline_extract_regions(
                page_number=page_number,
                document_id=document_id,
            )

        # Generate markdown (potentially with bbox tags)
        markdown = self.analyze_document(file_path, page_number)

        # Parse grounding metadata
        grounding_data = self._parse_grounding_metadata(markdown)

        # Clean markdown (remove bbox tags for parsing)
        clean_markdown = re.sub(r'<bbox>[\d.,]+</bbox>', '', markdown)

        # Parse into regions
        region_stubs = self.parser.parse_markdown_to_regions(
            clean_markdown,
            page_number=page_number,
            document_id=document_id
        )

        # Convert to SemanticRegion objects
        regions = []
        for i, stub in enumerate(region_stubs):
            region_id = f"{document_id or 'doc'}_{page_number}_{i}"

            # Try to associate bbox with region (simple heuristic: first bbox for first region, etc.)
            bbox = grounding_data[i]['bbox'] if i < len(grounding_data) else None

            # Build SemanticRegion with bbox
            region = SemanticRegion(
                region_id=region_id,
                region_type=stub.region_type,
                region_sequence=i,
                page_number=page_number,
                content=stub.content,
                raw_markdown=stub.raw_markdown,
                markdown_level=stub.markdown_level,
                bbox=bbox,  # Deepseek grounding
                table_html=stub.table_html if stub.region_type == "table" else None,
                table_rows=getattr(stub, 'table_rows', None),
                table_cols=getattr(stub, 'table_cols', None),
                image_description=stub.image_description if stub.region_type == "image" else None,
                image_type=getattr(stub, 'image_type', None),
                equation_latex=stub.equation_latex if stub.region_type == "equation" else None,
                equation_type=getattr(stub, 'equation_type', None),
                model="deepseek-ocr",  # Update model identifier
            )

            regions.append(region)

        logger.info(
            f"Extracted {len(regions)} semantic regions from {file_path} "
            f"({len(grounding_data)} with grounding)"
        )
        return regions

    def extract_regions_batch(
        self,
        file_paths: List[Union[str, Path]],
        page_numbers: Optional[List[int]] = None,
        batch_size: Optional[int] = None,
        document_ids: Optional[List[Optional[str]]] = None,
    ) -> List[List[SemanticRegion]]:
        """
        Fallback sequential batch processor used by loaders when analyzer does not
        provide native batched inference. Keeps interface compatibility with
        Nanonets loader logic while reusing the internal model instance.
        """
        if page_numbers is None:
            page_numbers = list(range(1, len(file_paths) + 1))

        results: List[List[SemanticRegion]] = []
        for idx, file_path in enumerate(file_paths):
            page_number = page_numbers[idx] if idx < len(page_numbers) else idx + 1
            document_id = None
            if document_ids and idx < len(document_ids):
                document_id = document_ids[idx]

            regions = self.extract_regions(
                file_path=file_path,
                page_number=page_number,
                document_id=document_id,
            )
            results.append(regions)

        return results


def create_analyzer(
    device: Optional[str] = None,
    resolution_mode: str = "base",
    enable_grounding: bool = True,
    **kwargs
) -> DeepseekLayoutAnalyzer:
    """
    Factory function to create a DeepseekLayoutAnalyzer with smart defaults.

    Args:
        device: Device to use (auto-detected if None)
        resolution_mode: Resolution mode ("tiny", "small", "base", "large", "gundam")
        enable_grounding: Enable spatial grounding
        **kwargs: Additional arguments for DeepseekLayoutAnalyzer

    Returns:
        Configured analyzer instance
    """
    if device is None:
        device = "auto"

    logger.info(
        f"Creating Deepseek analyzer with device={device}, "
        f"resolution={resolution_mode}, grounding={enable_grounding}"
    )
    return DeepseekLayoutAnalyzer(
        device=device,
        resolution_mode=resolution_mode,
        enable_grounding=enable_grounding,
        **kwargs
    )
