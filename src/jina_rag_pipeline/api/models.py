from enum import Enum
from typing import Any, Dict, List, Literal, Optional
import json
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict


class IngestionStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileStatus(BaseModel):
    name: str = Field(..., description="File name")
    status: IngestionStatus = Field(..., description="Processing status")
    size: int = Field(..., description="File size in bytes")
    error: Optional[str] = Field(None, description="Error message if failed")
    temp_name: Optional[str] = Field(
        default=None,
        exclude=True,
        repr=False,
        description="Internal temporary filename used by the backend",
    )


class IngestionResponse(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    files: List[FileStatus] = Field(..., description="List of files to process")


class IngestionStatusResponse(BaseModel):
    task_id: str = Field(..., description="Task identifier")
    status: IngestionStatus = Field(..., description="Overall task status")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_file: Optional[str] = Field(None, description="Currently processing file")
    processed_files: int = Field(..., description="Number of processed files")
    total_files: int = Field(..., description="Total number of files")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Processing errors")


class SupportedFormatsResponse(BaseModel):
    formats: List[str] = Field(..., description="List of supported file extensions")
    max_file_size_mb: int = Field(..., description="Maximum file size in megabytes")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Text query for semantic search")
    collection_name: str = Field(..., description="Name of the collection to search")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    metadata_filter: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadata filters to apply"
    )
    distance_metric: str = Field(
        default="cosine", description="Distance metric: cosine, l2, or ip"
    )


class ImageMetadata(BaseModel):
    """Metadata specific to image results."""
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    format: str = Field(..., description="Image format (png, jpeg, webp)")
    file_size: int = Field(..., description="File size in bytes")
    thumbnail_url: str = Field(..., description="URL to thumbnail image")
    full_image_url: str = Field(..., description="URL to full-size image")
    mean_rgb: List[float] = Field(..., description="Mean RGB values [R, G, B]")


class SearchResult(BaseModel):
    id: str = Field(..., description="Document ID")
    score: float = Field(..., description="Relevance score (0-1, higher is better)")
    document: Optional[str] = Field(None, description="Document text if available")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    result_type: Optional[str] = Field(None, description="Result type: 'text' or 'image'")
    image_metadata: Optional[ImageMetadata] = Field(None, description="Image metadata if result is an image")


class SearchResponse(BaseModel):
    results: List[SearchResult] = Field(default_factory=list, description="Search results")
    query: str = Field(..., description="Original query")
    collection: str = Field(..., description="Collection searched")
    total_results: int = Field(..., description="Number of results returned")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    embeddings_loaded: bool = Field(..., description="Whether embeddings model is loaded")


class StatsResponse(BaseModel):
    collections: int = Field(..., description="Number of collections")
    total_embeddings: int = Field(..., description="Total embeddings across all collections")


class CollectionInfo(BaseModel):
    name: str = Field(..., description="Collection name")
    count: int = Field(..., description="Number of embeddings in collection")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Collection metadata")


class CollectionsResponse(BaseModel):
    collections: List[CollectionInfo] = Field(
        default_factory=list, description="List of collections"
    )


# Collection configuration models

class CollectionConfig(BaseModel):
    """Configuration for a collection with precision-first defaults.

    All layout analysis features are ENABLED by default for maximum precision,
    granularity, and organized persistent storage.
    """

    # Version for future migrations
    config_version: str = Field(default="1.0", description="Configuration schema version")

    # Core layout analysis settings (DEFAULT: ENABLED)
    enable_layout_analysis: bool = Field(
        default=True,
        description="Enable document layout analysis for mixed-content processing"
    )
    layout_ocr_enabled: bool = Field(
        default=True,
        description="Enable OCR for scanned documents and images"
    )
    layout_table_extraction: bool = Field(
        default=True,
        description="Extract table structure as HTML/JSON"
    )

    # Storage settings (DEFAULT: SAVE EVERYTHING)
    save_extracted_images: bool = Field(
        default=True,
        description="Always save extracted images to organized persistent storage"
    )
    save_region_metadata: bool = Field(
        default=True,
        description="Save full granular metadata for each region"
    )

    # Granularity settings (DEFAULT: MAXIMUM PRECISION)
    region_granularity: Literal["fine", "coarse"] = Field(
        default="fine",
        description="Region detection granularity: 'fine' for maximum precision, 'coarse' for fewer regions"
    )

    # Processing settings
    max_image_dimension: int = Field(
        default=2048,
        ge=256,
        le=4096,
        description="Maximum image dimension (will resize larger images)"
    )

    @field_validator("config_version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate configuration version."""
        valid_versions = ["1.0"]
        if v not in valid_versions:
            raise ValueError(
                f"Invalid config version '{v}'. Supported versions: {valid_versions}"
            )
        return v

    @classmethod
    def load_from_file(cls, file_path: Path) -> "CollectionConfig":
        """Load configuration from JSON file.

        Args:
            file_path: Path to config.json file

        Returns:
            CollectionConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            return cls(**config_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load config: {e}")

    def save_to_file(self, file_path: Path) -> None:
        """Save configuration to JSON file.

        Args:
            file_path: Path to save config.json file

        Raises:
            IOError: If file cannot be written
        """
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write with pretty formatting
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.model_dump(),
                    f,
                    indent=2,
                    ensure_ascii=False
                )
        except Exception as e:
            raise IOError(f"Failed to save config to {file_path}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self.model_dump()

    @classmethod
    def get_default(cls) -> "CollectionConfig":
        """Get default configuration with precision-first settings."""
        return cls()


# Chat-related models

class ChatConfig(BaseModel):
    """Configuration for chat session."""
    # Generation parameters
    temperature: float = Field(default=0.7, ge=0, le=2, description="Generation temperature")
    top_p: float = Field(default=0.8, ge=0, le=1, description="Top-p (nucleus) sampling parameter")
    top_k: int = Field(default=20, ge=1, description="Top-k sampling parameter (limits vocabulary)")
    max_tokens: int = Field(default=512, ge=1, le=4096, description="Maximum tokens to generate")
    max_history_turns: int = Field(default=10, ge=1, le=50, description="Maximum conversation turns to keep")
    enable_thinking: bool = Field(default=False, description="Enable thinking mode for complex reasoning")

    # Optional session-specific RAG overrides (if not set, use global RAG config)
    initial_retrieval_k: Optional[int] = Field(default=None, ge=1, le=50, description="Initial number of documents to retrieve (overrides global)")
    enable_reranking: Optional[bool] = Field(default=None, description="Enable reranking (overrides global)")
    rerank_top_n: Optional[int] = Field(default=None, ge=1, le=20, description="Top N after reranking (overrides global)")


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class SessionInfo(BaseModel):
    """Information about a chat session."""
    session_id: str = Field(..., description="Unique session identifier")
    collection_name: str = Field(..., description="Collection being queried")
    created_at: str = Field(..., description="Session creation timestamp")
    last_accessed: str = Field(..., description="Last access timestamp")
    message_count: int = Field(..., description="Number of messages in conversation")
    image_references_count: int = Field(..., description="Number of tracked images")


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""
    collection_name: str = Field(..., description="Name of collection to query")
    config: Optional[ChatConfig] = Field(default=None, description="Session configuration")


class CreateSessionResponse(BaseModel):
    """Response after creating a session."""
    session_id: str = Field(..., description="Created session identifier")
    session_info: SessionInfo = Field(..., description="Session information")


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""
    type: str = Field(..., description="Message type: user_message, assistant_chunk, context, error, complete")
    content: Optional[str] = Field(None, description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ContextMessage(WebSocketMessage):
    """Context message with retrieved documents."""
    type: str = Field(default="context")
    text_results: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved text documents")
    image_results: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved images with metadata")
    retrieved_docs: int = Field(..., description="Total documents retrieved")
    retrieved_images: int = Field(..., description="Total images retrieved")
    retrieval_metrics: Optional[Dict[str, Any]] = Field(None, description="Retrieval performance metrics")
    citation_map: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Mapping of citation IDs (e.g., '[1]', '[IMG-1]') to source metadata for interactive linking"
    )


class CompleteMessage(WebSocketMessage):
    """Completion message with generation stats."""
    type: str = Field(default="complete")
    tokens_generated: int = Field(..., description="Number of tokens generated")
    duration_ms: float = Field(..., description="Generation duration in milliseconds")
    thinking_mode: bool = Field(..., description="Whether thinking mode was used")


class RAGConfigModel(BaseModel):
    """Runtime RAG configuration settings."""
    initial_retrieval_k: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Initial number of documents to retrieve before reranking"
    )
    rerank_top_n: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of documents to keep after reranking"
    )
    enable_reranking: bool = Field(
        default=True,
        description="Enable JinaAI reranking for improved relevance"
    )
    rerank_model: str = Field(
        default="jinaai/jina-reranker-m0",
        description="JinaAI reranker model (jinaai/jina-reranker-m0 or jinaai/jina-reranker-v1-turbo-en)"
    )
    enable_hybrid_search: bool = Field(
        default=False,
        description="Enable hybrid semantic + keyword search (future feature)"
    )
    hybrid_alpha: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Weight between semantic (alpha) and keyword (1-alpha) search"
    )
    citation_style: str = Field(
        default="numbered",
        description="Citation format: numbered, inline, or footnote"
    )
    include_relevance_scores: bool = Field(
        default=True,
        description="Include relevance scores in formatted context"
    )


class RAGConfigResponse(BaseModel):
    """Response containing current RAG configuration."""
    config: RAGConfigModel = Field(..., description="Current RAG configuration settings")
    description: str = Field(
        default="Runtime configuration for RAG retrieval and enhancement features",
        description="Configuration description"
    )


# ============================================================================
# Embedding and OCR Configuration Models (Advanced Configuration UI)
# ============================================================================


class PresetInfo(BaseModel):
    """Information about a configuration preset."""
    name: str = Field(..., description="Internal preset identifier")
    display_name: str = Field(..., description="User-facing preset name")
    description: str = Field(..., description="Preset description and use cases")
    performance_characteristics: Dict[str, str] = Field(
        default_factory=dict,
        description="Performance metrics (speed, memory, quality, etc.)"
    )


class EmbeddingConfigModel(BaseModel):
    """Pydantic model for embedding configuration.

    Mirrors the EmbeddingConfig dataclass to provide API-safe serialization
    with validation. Supports all presets: for_query(), for_documents(),
    storage_optimized(), fast(), and memory_constrained().
    """
    task: Literal[
        "retrieval.query",
        "retrieval.passage",
        "text-matching",
        "classification",
        "separation",
        "code.query",
        "code.passage"
    ] = Field(
        default="retrieval.passage",
        description="Embedding task type affecting model behavior"
    )

    dimensions: Literal[128, 256, 512, 1024, 2048] = Field(
        default=1024,
        description="Embedding output dimensions (tradeoff: quality vs storage)"
    )

    late_chunking: bool = Field(
        default=True,
        description="Enable late chunking for better context preservation"
    )

    return_multivector: bool = Field(
        default=False,
        description="Return both vector and multi-vector representations"
    )

    embedding_format: Literal["float", "base64", "binary", "ubinary"] = Field(
        default="float",
        description="Storage format: float (8 bytes), binary (1 byte), ubinary (0.5 bytes)"
    )

    batch_size: int = Field(
        default=32,
        ge=1,
        le=256,
        description="Documents per batch (higher = faster but more memory)"
    )

    max_tokens_per_batch: int = Field(
        default=8192,
        ge=1024,
        le=32768,
        description="Maximum tokens per batch (auto-splits large batches)"
    )


class OCRConfigModel(BaseModel):
    """Pydantic model for OCR configuration.

    Mirrors the OCRConfig dataclass to provide API-safe serialization
    with validation. Supports Deepseek presets: deepseek_tiny(), deepseek_small(),
    deepseek_balanced(), deepseek_high_quality(), deepseek_gundam(), deepseek_production().
    """
    model_config = ConfigDict(extra="ignore")

    batch_size: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Pages per processing batch"
    )

    render_workers: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Concurrent rendering threads"
    )

    analysis_workers: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Concurrent analysis threads"
    )

    pre_render_batches: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Number of batches to pre-render ahead"
    )

    checkpoint_enabled: bool = Field(
        default=True,
        description="Enable checkpoint saving for crash recovery"
    )

    resolution_mode: Literal["tiny", "small", "base", "large", "gundam"] = Field(
        default="base",
        description="Deepseek resolution mode determining render size and compression"
    )

    enable_grounding: bool = Field(
        default=True,
        description="Enable spatial grounding output (bounding boxes)"
    )

    enable_compression: bool = Field(
        default=True,
        description="Enable Deepseek optical compression for token efficiency"
    )

    use_vllm: bool = Field(
        default=False,
        description="Use vLLM backend for high-throughput inference (requires vLLM)"
    )


class EmbeddingConfigResponse(BaseModel):
    """Response containing current embedding configuration."""
    config: EmbeddingConfigModel = Field(..., description="Current embedding configuration")
    preset: str = Field(
        default="for_documents",
        description="Active preset name (for_query, for_documents, storage_optimized, fast, memory_constrained, custom)"
    )
    description: str = Field(
        default="Configuration for Jina embedding model task and optimization",
        description="Configuration description"
    )


class OCRConfigResponse(BaseModel):
    """Response containing current OCR configuration."""
    config: OCRConfigModel = Field(..., description="Current OCR configuration")
    preset: str = Field(
        default="deepseek_balanced",
        description="Active preset name (deepseek_tiny, deepseek_small, deepseek_balanced, deepseek_high_quality, deepseek_gundam, deepseek_production, custom)"
    )
    description: str = Field(
        default="Configuration for Deepseek OCR document processing pipeline",
        description="Configuration description"
    )


# Lesson Plan Generation models

class GenerateLessonRequest(BaseModel):
    """Request to generate a lesson plan."""
    topic: str = Field(..., min_length=1, max_length=200, description="Lesson topic")
    learning_objective: str = Field(..., min_length=1, max_length=500, description="Learning objective")
    grade_level: str = Field(..., description="Grade level: K, 1-12, 3-5, 6-8, 9-12, College")
    subject: str = Field(..., description="Subject area")
    duration_minutes: int = Field(default=50, ge=20, le=90, description="Lesson duration in minutes (20-90)")
    teaching_style: str = Field(default="balanced", description="Teaching style: balanced, direct, inquiry, or project")

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, v: str) -> str:
        """Validate grade level is in allowed list."""
        from ..models.educational import VALID_GRADE_LEVELS
        if v not in VALID_GRADE_LEVELS:
            raise ValueError(
                f"Invalid grade level '{v}'. Must be one of: {', '.join(VALID_GRADE_LEVELS)}"
            )
        return v

    @field_validator("teaching_style")
    @classmethod
    def validate_teaching_style(cls, v: str) -> str:
        """Validate teaching style is in allowed list."""
        from ..models.educational import VALID_TEACHING_STYLES
        if v not in VALID_TEACHING_STYLES:
            raise ValueError(
                f"Invalid teaching style '{v}'. Must be one of: {', '.join(VALID_TEACHING_STYLES)}"
            )
        return v


class LessonMarkdownResponse(BaseModel):
    """Response containing generated lesson plan."""
    lesson_id: str = Field(default="", description="Unique lesson ID for export/customization")
    markdown: str = Field(..., description="Generated lesson plan in markdown format with YAML frontmatter")
    metadata: Dict[str, Any] = Field(..., description="Lesson metadata (title, grade, subject, duration)")
    sources_count: int = Field(..., description="Number of source materials cited")
    images_count: int = Field(..., description="Number of images included")
    generation_time_seconds: float = Field(..., description="Time taken to generate lesson in seconds")


# Lesson Export models (Phase 2)

class ExportFormat(str):
    """Export format enumeration."""
    PDF = "pdf"
    JSON = "json"
    MARKDOWN = "markdown"


class LessonExportRequest(BaseModel):
    """Request to export a lesson in a specific format."""
    lesson_id: str = Field(..., description="ID of lesson to export")
    format: str = Field(..., description="Export format: pdf, json, or markdown")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate export format."""
        if v not in ["pdf", "json", "markdown"]:
            raise ValueError(f"Invalid format '{v}'. Must be one of: pdf, json, markdown")
        return v


# ============================================================================
# Phase 3: Simple Lesson Persistence Models (Single-User App)
# ============================================================================


class SaveLessonRequest(BaseModel):
    """Request to save a generated lesson to the library."""
    lesson_id: str = Field(..., description="UUID of the generated lesson from cache")


class LessonListItem(BaseModel):
    """Summary of a lesson for list views."""
    id: int
    lesson_id: str
    title: str
    grade: str
    subject: str
    topic: str
    duration_minutes: int
    teaching_style: str
    sources_count: int
    images_count: int
    is_favorite: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UpdateLessonRequest(BaseModel):
    """Request to update an existing lesson (partial updates)."""
    markdown_content: Optional[str] = Field(None, min_length=1, max_length=100000, description="Updated markdown content")
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Updated lesson title")
    duration_minutes: Optional[int] = Field(None, ge=20, le=90, description="Updated lesson duration in minutes")
    teaching_style: Optional[str] = Field(None, description="Updated teaching style")
    learning_objective: Optional[str] = Field(None, min_length=1, max_length=500, description="Updated learning objective")

    @field_validator("teaching_style")
    @classmethod
    def validate_teaching_style(cls, v: Optional[str]) -> Optional[str]:
        """Validate teaching style is in allowed list."""
        if v is not None:
            from ..models.educational import VALID_TEACHING_STYLES
            if v not in VALID_TEACHING_STYLES:
                raise ValueError(
                    f"Invalid teaching style '{v}'. Must be one of: {', '.join(VALID_TEACHING_STYLES)}"
                )
        return v


class LessonDetailResponse(BaseModel):
    """Full lesson details including content."""
    id: int
    lesson_id: str
    title: str
    markdown_content: str
    grade: str
    subject: str
    topic: str
    learning_objective: str
    duration_minutes: int
    teaching_style: str
    metadata_json: Optional[Dict[str, Any]]
    sources_count: int
    images_count: int
    is_favorite: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
