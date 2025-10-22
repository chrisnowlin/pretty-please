import asyncio
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..embeddings import JinaEmbeddingsV4
from ..embeddings.config import EmbeddingConfig
from ..storage import ChromaVectorStore

from .models import (
    CollectionConfig,
    CollectionInfo,
    CollectionsResponse,
    EmbeddingConfigModel,
    EmbeddingConfigResponse,
    FileStatus,
    GenerateLessonRequest,
    HealthResponse,
    ImageMetadata,
    IngestionResponse,
    IngestionStatus,
    IngestionStatusResponse,
    LessonMarkdownResponse,
    LessonDetailResponse,
    LessonListItem,
    OCRConfigModel,
    OCRConfigResponse,
    PresetInfo,
    RAGConfigModel,
    RAGConfigResponse,
    SaveLessonRequest,
    SearchRequest,
    SearchResponse,
    SearchResult,
    StatsResponse,
    UpdateLessonRequest,
    SupportedFormatsResponse,
)
from .tasks import TaskManager
from .collection_manager import CollectionManager
from .config_manager import ConfigManager
from . import chat
from . import endpoints_admin


class RAGAPIState:
    def __init__(self) -> None:
        self.embedder: Optional[JinaEmbeddingsV4] = None
        self.vector_store: Optional[ChromaVectorStore] = None
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl: int = 300
        self.task_manager: Optional[TaskManager] = None
        self.collection_manager: Optional[CollectionManager] = None
        self.config_manager: Optional[ConfigManager] = None
        # Phase 2: Lesson cache for export functionality
        self.lesson_cache: Dict[str, str] = {}  # lesson_id -> markdown content


SUPPORTED_FORMATS = [
    ".txt", ".pdf", ".md", ".json", ".csv",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp",
    ".pptx", ".ppt",  # PowerPoint presentations
]
IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]
MAX_FILE_SIZE_MB = 1024  # 1GB for documents
MAX_IMAGE_SIZE_MB = 100  # 100MB for images

# Deepseek OCR routing configuration (enabled by default)
_deepseek_flag = os.getenv("DEEPSEEK_OCR_ENABLED", "true")
DEEPSEEK_OCR_ENABLED = _deepseek_flag.lower() in ("true", "1", "yes")


def create_app(
    embedder: Optional[JinaEmbeddingsV4] = None,
    vector_store: Optional[ChromaVectorStore] = None,
    enable_cors: bool = True,
    config_manager: Optional[ConfigManager] = None,
) -> FastAPI:
    app = FastAPI(
        title="Jina RAG Pipeline API",
        description="REST API for semantic search and document ingestion using Jina Embeddings v4",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    state = RAGAPIState()
    state.embedder = embedder
    state.vector_store = vector_store
    state.config_manager = config_manager

    @app.on_event("startup")
    async def startup_event() -> None:
        import logging
        import sys

        logger = logging.getLogger("uvicorn")
        logger.info("="* 60)
        logger.info("STARTUP EVENT TRIGGERED")
        logger.info(f"State embedder: {state.embedder is not None}")
        logger.info(f"State vector_store: {state.vector_store is not None}")
        logger.info("=" * 60)

        # Initialize collection manager first (needed for Task 3.4: configuration loading)
        logger.info("Initializing CollectionManager...")
        state.collection_manager = CollectionManager(base_dir=Path("./uploads"))
        state.collection_manager.validate_all_collections()
        logger.info("CollectionManager initialized")

        # Initialize configuration manager for embedding and OCR settings
        logger.info("Initializing ConfigManager...")
        state.config_manager = ConfigManager(config_dir=Path("./data"))
        logger.info("ConfigManager initialized")

        if state.embedder and state.vector_store:
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "pretty_please_uploads"
            temp_dir.mkdir(parents=True, exist_ok=True)
            state.task_manager = TaskManager(
                state.embedder,
                state.vector_store,
                temp_dir,
                collection_manager=state.collection_manager,  # Pass collection manager for config loading
                config_manager=state.config_manager,  # Pass config manager for dynamic embedding config
            )
            logger.info(f"TaskManager initialized with temp_dir: {temp_dir}")

        # Initialize chat module
        logger.info("Initializing chat module...")
        try:
            from ..generation import QwenGenerator
            from ..retrieval import JinaReranker

            # Share embedder and vector store with chat
            chat.chat_state.embedder = state.embedder
            chat.chat_state.vector_store = state.vector_store
            logger.info(f"Chat state embedder set: {chat.chat_state.embedder is not None}")
            logger.info(f"Chat state vector_store set: {chat.chat_state.vector_store is not None}")

            # Initialize generator (lazy loading, won't actually load model until first use)
            logger.info("Creating QwenGenerator (lazy loading)...")
            chat.chat_state.generator = QwenGenerator()
            logger.info("Generator initialized")

            # Initialize reranker (lazy loading) if reranking is enabled
            if chat.chat_state.rag_config.enable_reranking:
                logger.info("Creating JinaReranker (lazy loading)...")
                chat.chat_state.reranker = JinaReranker(
                    model_name=chat.chat_state.rag_config.rerank_model
                )
                logger.info("Reranker initialized (model will load on first use)")

            # Start session cleanup task
            await chat.chat_state.session_manager.start_cleanup_task()
            logger.info("Session cleanup task started")

            logger.info("=" * 60)
            logger.info("CHAT MODULE READY")
            logger.info("=" * 60)

        except Exception as e:
            import traceback
            logger.error(f"Chat module initialization failed: {e}")
            logger.error(traceback.format_exc())

    # Mount chat router
    app.include_router(chat.router)

    # Mount admin endpoints for profiles, checkpoints, and system management
    app.include_router(endpoints_admin.router)

    @app.get("/api/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            embeddings_loaded=state.embedder is not None,
        )

    @app.get("/api/stats", response_model=StatsResponse)
    async def get_stats() -> StatsResponse:
        if state.vector_store is None:
            raise HTTPException(status_code=500, detail="Vector store not initialized")

        collections = state.vector_store.list_collections()
        total_embeddings = sum(
            state.vector_store.get_collection_stats(col.name).count for col in collections
        )

        return StatsResponse(collections=len(collections), total_embeddings=total_embeddings)

    @app.get("/api/collections", response_model=CollectionsResponse)
    async def list_collections() -> CollectionsResponse:
        if state.vector_store is None:
            raise HTTPException(status_code=500, detail="Vector store not initialized")

        collections = state.vector_store.list_collections()
        collection_infos = []

        for col in collections:
            stats = state.vector_store.get_collection_stats(col.name)
            collection_infos.append(
                CollectionInfo(
                    name=col.name, count=stats.count, metadata=col.metadata or {}
                )
            )

        return CollectionsResponse(collections=collection_infos)

    @app.post("/api/collections/create")
    async def create_collection(collection_name: str = Form(...)) -> Dict[str, Any]:
        if state.vector_store is None:
            raise HTTPException(status_code=500, detail="Vector store not initialized")
        if state.collection_manager is None:
            raise HTTPException(status_code=500, detail="Collection manager not initialized")

        if not collection_name or not collection_name.strip():
            raise HTTPException(status_code=400, detail="Collection name cannot be empty")

        collection_name = collection_name.strip()

        try:
            # Check if collection already exists
            existing_collections = state.vector_store.list_collections()
            if any(col.name == collection_name for col in existing_collections):
                raise HTTPException(status_code=409, detail=f"Collection '{collection_name}' already exists")

            # Create organized directory structure with precision-first defaults
            collection_dir = state.collection_manager.create_collection_structure(
                collection_name=collection_name,
                config=None,  # Use default precision-first config
            )

            # Create collection in vector store
            # Jina v4 produces 2048-dimensional embeddings
            state.vector_store.create_collection(
                name=collection_name,
                embedding_dimension=2048,
                metadata={"description": "Collection for RAG"}
            )

            return {
                "collection_name": collection_name,
                "status": "created",
                "directory": str(collection_dir),
                "config": "precision-first defaults (layout analysis enabled)",
            }
        except Exception as e:
            if "already exists" in str(e):
                raise HTTPException(status_code=409, detail=f"Collection '{collection_name}' already exists")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/search", response_model=SearchResponse)
    async def search(request: SearchRequest) -> SearchResponse:
        if state.embedder is None:
            raise HTTPException(status_code=500, detail="Embedder not initialized")
        if state.vector_store is None:
            raise HTTPException(status_code=500, detail="Vector store not initialized")

        cache_key = f"{request.collection_name}:{request.query}:{request.top_k}:{request.distance_metric}"

        if cache_key in state.query_cache:
            cached_result, timestamp = state.query_cache[cache_key]
            if time.time() - timestamp < state.cache_ttl:
                return cached_result

        try:
            config = EmbeddingConfig.for_query()
            query_embedding = state.embedder.embed_with_config([request.query], config)[0]
            query_embedding_list = query_embedding.tolist()

            results = state.vector_store.similarity_search(
                collection_name=request.collection_name,
                query_embedding=query_embedding_list,
                top_k=request.top_k,
                metadata_filter=request.metadata_filter,
            )

            search_results = []
            for result in results:
                # Determine result type from metadata
                result_type = result.metadata.get("modality", "text") if result.metadata else "text"

                # Build image metadata if this is an image result
                image_metadata = None
                if result_type == "image" and result.metadata:
                    image_path = result.metadata.get("image_path", "")
                    thumbnail_path = result.metadata.get("thumbnail_path", "")
                    doc_id = result.metadata.get("document_id", "")
                    collection = request.collection_name

                    if doc_id:
                        thumbnail_url = f"/api/images/thumbnail/{collection}/{doc_id}"
                        full_image_url = f"/api/images/full/{collection}/{doc_id}"

                        # Reconstruct mean_rgb from separate fields
                        mean_rgb = [
                            result.metadata.get("mean_r", 0.0),
                            result.metadata.get("mean_g", 0.0),
                            result.metadata.get("mean_b", 0.0),
                        ]

                        image_metadata = ImageMetadata(
                            width=result.metadata.get("width", 0),
                            height=result.metadata.get("height", 0),
                            format=result.metadata.get("format", "unknown"),
                            file_size=result.metadata.get("file_size", 0),
                            thumbnail_url=thumbnail_url,
                            full_image_url=full_image_url,
                            mean_rgb=mean_rgb,
                        )

                search_results.append(
                    SearchResult(
                        id=result.id,
                        score=result.score,
                        document=result.document,
                        metadata=result.metadata or {},
                        result_type=result_type,
                        image_metadata=image_metadata,
                    )
                )

            response = SearchResponse(
                results=search_results,
                query=request.query,
                collection=request.collection_name,
                total_results=len(search_results),
            )

            state.query_cache[cache_key] = (response, time.time())

            return response

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/ingest/supported-formats", response_model=SupportedFormatsResponse)
    async def get_supported_formats() -> SupportedFormatsResponse:
        return SupportedFormatsResponse(
            formats=SUPPORTED_FORMATS,
            max_file_size_mb=MAX_FILE_SIZE_MB,
        )

    @app.post("/api/ingest/upload", response_model=IngestionResponse)
    async def upload_documents(
        files: List[UploadFile] = File(...),
        collection_name: str = Form(...),
    ) -> IngestionResponse:
        if state.task_manager is None:
            raise HTTPException(status_code=500, detail="Task manager not initialized")

        file_statuses = []

        for file in files:
            original_name = file.filename or "upload"
            safe_name = Path(original_name).name or ""
            if not safe_name.strip():
                safe_name = f"upload_{uuid.uuid4().hex}"
            file_ext = Path(safe_name).suffix.lower()

            if file_ext not in SUPPORTED_FORMATS:
                file_statuses.append(
                    FileStatus(
                        name=safe_name,
                        status=IngestionStatus.FAILED,
                        size=0,
                        error=f"Unsupported file format: {file_ext}",
                    )
                )
                continue

            # Validate MIME type for images
            is_image = file_ext in IMAGE_FORMATS
            if is_image and file.content_type:
                expected_mime_types = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif", "image/bmp"]
                if not any(file.content_type.startswith(mime) for mime in expected_mime_types):
                    file_statuses.append(
                        FileStatus(
                            name=safe_name,
                            status=IngestionStatus.FAILED,
                            size=0,
                            error=f"Invalid MIME type for image: {file.content_type}",
                        )
                    )
                    continue

            content = await file.read()
            file_size = len(content)

            # Apply different size limits for images vs documents
            max_size = MAX_IMAGE_SIZE_MB if is_image else MAX_FILE_SIZE_MB
            if file_size > max_size * 1024 * 1024:
                file_statuses.append(
                    FileStatus(
                        name=safe_name,
                        status=IngestionStatus.FAILED,
                        size=file_size,
                        error=f"File exceeds maximum size of {max_size}MB",
                    )
                )
                continue

            unique_temp_name = f"{uuid.uuid4().hex}_{safe_name}"
            temp_path = state.task_manager.temp_dir / unique_temp_name
            print(f"[DEBUG] Writing file for {safe_name} to: {temp_path}", flush=True)
            print(f"[DEBUG] File size: {file_size} bytes", flush=True)

            # Write file with proper sync to ensure it's fully written to disk
            try:
                temp_path.write_bytes(content)
                print(f"[DEBUG] File write completed for: {safe_name}", flush=True)
            except Exception as e:
                print(f"[ERROR] Failed to write file {safe_name}: {e}", flush=True)
                raise HTTPException(status_code=500, detail=f"Failed to write file: {safe_name}: {e}")

            # Ensure file is fully written before proceeding
            if not temp_path.exists():
                print(f"[ERROR] File does not exist after write: {temp_path}", flush=True)
                raise HTTPException(status_code=500, detail=f"Failed to write file: {safe_name}")

            # Verify file size matches to ensure complete write
            actual_size = temp_path.stat().st_size
            print(f"[DEBUG] File written: {temp_path}, size: {actual_size} bytes (expected: {file_size})", flush=True)
            if actual_size != file_size:
                print(f"[ERROR] File size mismatch: expected {file_size}, got {actual_size}", flush=True)
                temp_path.unlink()  # Clean up partial file
                raise HTTPException(status_code=500, detail=f"File write incomplete: {safe_name}")

            file_statuses.append(
                FileStatus(
                    name=safe_name,
                    status=IngestionStatus.QUEUED,
                    size=file_size,
                    temp_name=unique_temp_name,
                )
            )

        task = state.task_manager.create_task(file_statuses, collection_name)

        # Longer delay to ensure all files are fully written and visible to task processor
        # This prevents race conditions where task starts before files are accessible
        await asyncio.sleep(0.5)
        state.task_manager.start_task(task.task_id)

        return IngestionResponse(task_id=task.task_id, files=file_statuses)

    @app.get("/api/ingest/status/{task_id}", response_model=IngestionStatusResponse)
    async def get_ingestion_status(task_id: str) -> IngestionStatusResponse:
        if state.task_manager is None:
            raise HTTPException(status_code=500, detail="Task manager not initialized")

        task = state.task_manager.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        return IngestionStatusResponse(
            task_id=task.task_id,
            status=task.status,
            progress=task.progress,
            current_file=task.current_file,
            processed_files=task.processed_files,
            total_files=task.total_files,
            errors=task.errors,
        )

    @app.post("/api/search/image", response_model=SearchResponse)
    async def search_by_image(
        image: UploadFile = File(...),
        collection_name: str = Form(...),
        top_k: int = Form(default=5),
        modality_filter: Optional[str] = Form(default=None),
    ) -> SearchResponse:
        """Search using an image query (image-to-image or image-to-text search)."""
        if state.embedder is None:
            raise HTTPException(status_code=500, detail="Embedder not initialized")
        if state.vector_store is None:
            raise HTTPException(status_code=500, detail="Vector store not initialized")

        try:
            # Read image content
            content = await image.read()

            # Load image with PIL
            from PIL import Image as PILImage
            import io

            pil_image = PILImage.open(io.BytesIO(content))

            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Generate embedding using vision encoder
            query_embedding = state.embedder.encode_image(pil_image, task="retrieval")
            query_embedding_list = query_embedding.tolist()

            # Build metadata filter for modality if specified
            metadata_filter = {}
            if modality_filter and modality_filter in ["image", "text"]:
                metadata_filter["modality"] = modality_filter

            # Perform similarity search
            results = state.vector_store.similarity_search(
                collection_name=collection_name,
                query_embedding=query_embedding_list,
                top_k=top_k,
                metadata_filter=metadata_filter if metadata_filter else None,
            )

            # Build search results with image metadata
            search_results = []
            for result in results:
                result_type = result.metadata.get("modality", "text") if result.metadata else "text"

                image_metadata = None
                if result_type == "image" and result.metadata:
                    doc_id = result.metadata.get("document_id", "")

                    if doc_id:
                        thumbnail_url = f"/api/images/thumbnail/{collection_name}/{doc_id}"
                        full_image_url = f"/api/images/full/{collection_name}/{doc_id}"

                        # Reconstruct mean_rgb from separate fields
                        mean_rgb = [
                            result.metadata.get("mean_r", 0.0),
                            result.metadata.get("mean_g", 0.0),
                            result.metadata.get("mean_b", 0.0),
                        ]

                        image_metadata = ImageMetadata(
                            width=result.metadata.get("width", 0),
                            height=result.metadata.get("height", 0),
                            format=result.metadata.get("format", "unknown"),
                            file_size=result.metadata.get("file_size", 0),
                            thumbnail_url=thumbnail_url,
                            full_image_url=full_image_url,
                            mean_rgb=mean_rgb,
                        )

                search_results.append(
                    SearchResult(
                        id=result.id,
                        score=result.score,
                        document=result.document,
                        metadata=result.metadata or {},
                        result_type=result_type,
                        image_metadata=image_metadata,
                    )
                )

            return SearchResponse(
                results=search_results,
                query=f"Image query: {image.filename}",
                collection=collection_name,
                total_results=len(search_results),
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")

    @app.get("/api/images/thumbnail/{collection}/{image_id}")
    async def get_thumbnail(collection: str, image_id: str):
        """Retrieve thumbnail image for a given image ID."""
        thumbnail_path = Path(f"./uploads/{collection}/thumbnails/{image_id}_thumb.jpg")

        if not thumbnail_path.exists():
            raise HTTPException(status_code=404, detail="Thumbnail not found")

        return FileResponse(
            thumbnail_path,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
                "ETag": f'"{image_id}"',
            },
        )

    @app.get("/api/images/full/{collection}/{image_id}")
    async def get_full_image(collection: str, image_id: str):
        """Retrieve full-size image for a given image ID."""
        # Check all possible image formats
        images_dir = Path(f"./uploads/{collection}/images")

        for ext in IMAGE_FORMATS:
            image_path = images_dir / f"{image_id}{ext}"
            if image_path.exists():
                # Determine MIME type from extension
                mime_types = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".webp": "image/webp",
                    ".gif": "image/gif",
                    ".bmp": "image/bmp",
                }
                media_type = mime_types.get(ext, "application/octet-stream")

                return FileResponse(
                    image_path,
                    media_type=media_type,
                    headers={
                        "Cache-Control": "public, max-age=31536000",
                        "ETag": f'"{image_id}"',
                    },
                )

        raise HTTPException(status_code=404, detail="Image not found")

    @app.get("/api/documents/{collection}/{filename}")
    async def get_document(collection: str, filename: str):
        """Retrieve document file for citation viewing."""
        from .chat import safe_filename

        # Validate filename to prevent path traversal
        safe_name = safe_filename(filename)
        if not safe_name:
            raise HTTPException(status_code=400, detail="Invalid filename")

        # Build safe path
        documents_dir = Path(f"./uploads/{collection}/documents")
        document_path = documents_dir / safe_name

        # Check if file exists
        if not document_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Document not found. This document may have been uploaded before persistent storage was enabled."
            )

        # Determine Content-Type from extension
        mime_types = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".py": "text/x-python",
            ".json": "application/json",
            ".csv": "text/csv",
        }
        ext = document_path.suffix.lower()
        media_type = mime_types.get(ext, "application/octet-stream")

        return FileResponse(
            document_path,
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
                "ETag": f'"{safe_name}"',
                "Content-Disposition": "inline",  # Preview in browser
            },
        )

    @app.websocket("/ws/progress/{task_id}")
    async def websocket_progress(websocket: WebSocket, task_id: str) -> None:
        await websocket.accept()

        if state.task_manager is None:
            await websocket.close(code=1011, reason="Task manager not initialized")
            return

        task = state.task_manager.get_task(task_id)
        if task is None:
            await websocket.close(code=1008, reason="Task not found")
            return

        queue: asyncio.Queue = asyncio.Queue()
        task.add_listener(queue)

        try:
            await websocket.send_json(task.to_dict())

            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    await websocket.send_json(message)
                    
                    if message.get("type") in ["complete", "error"]:
                        break
                except asyncio.TimeoutError:
                    await websocket.send_json({"type": "ping"})
                except WebSocketDisconnect:
                    break

        except Exception:
            pass
        finally:
            task.remove_listener(queue)
            try:
                await websocket.close()
            except Exception:
                pass

    @app.get("/api/config/rag", response_model=RAGConfigResponse)
    async def get_rag_config() -> RAGConfigResponse:
        """Get current RAG configuration settings."""
        from ..generation import RAGConfig

        # Get current config from chat module
        if hasattr(chat.chat_state, 'rag_config') and chat.chat_state.rag_config:
            rag_config = chat.chat_state.rag_config
        else:
            # Return default config
            rag_config = RAGConfig()

        return RAGConfigResponse(
            config=RAGConfigModel(
                initial_retrieval_k=rag_config.initial_retrieval_k,
                rerank_top_n=rag_config.rerank_top_n,
                enable_reranking=rag_config.enable_reranking,
                rerank_model=rag_config.rerank_model,
                enable_hybrid_search=rag_config.enable_hybrid_search,
                hybrid_alpha=rag_config.hybrid_alpha,
                citation_style=rag_config.citation_style,
                include_relevance_scores=rag_config.include_relevance_scores,
            )
        )

    @app.post("/api/config/rag", response_model=RAGConfigResponse)
    async def update_rag_config(config: RAGConfigModel) -> RAGConfigResponse:
        """Update RAG configuration settings at runtime."""
        from ..generation import RAGConfig

        # Validate configuration
        new_config = RAGConfig(
            initial_retrieval_k=config.initial_retrieval_k,
            rerank_top_n=config.rerank_top_n,
            enable_reranking=config.enable_reranking,
            rerank_model=config.rerank_model,
            enable_hybrid_search=config.enable_hybrid_search,
            hybrid_alpha=config.hybrid_alpha,
            citation_style=config.citation_style,
            include_relevance_scores=config.include_relevance_scores,
        )

        try:
            new_config.validate()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")

        # Update chat module configuration
        chat.chat_state.rag_config = new_config

        # If reranker model changed and reranking is enabled, reinitialize reranker
        if config.enable_reranking and hasattr(chat.chat_state, 'reranker'):
            try:
                from ..retrieval import JinaReranker
                chat.chat_state.reranker = JinaReranker(model_name=config.rerank_model)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize reranker with model {config.rerank_model}: {str(e)}"
                )

        return RAGConfigResponse(
            config=RAGConfigModel(
                initial_retrieval_k=new_config.initial_retrieval_k,
                rerank_top_n=new_config.rerank_top_n,
                enable_reranking=new_config.enable_reranking,
                rerank_model=new_config.rerank_model,
                enable_hybrid_search=new_config.enable_hybrid_search,
                hybrid_alpha=new_config.hybrid_alpha,
                citation_style=new_config.citation_style,
                include_relevance_scores=new_config.include_relevance_scores,
            )
        )

    # ========================================================================
    # Embedding Configuration Endpoints
    # ========================================================================

    @app.get("/api/config/embeddings", response_model=EmbeddingConfigResponse)
    async def get_embedding_config() -> EmbeddingConfigResponse:
        """Get current embedding configuration."""
        if state.config_manager is None:
            raise HTTPException(status_code=500, detail="Config manager not initialized")

        try:
            embedding_config = state.config_manager.get_embedding_config()
            return EmbeddingConfigResponse(
                config=embedding_config,
                preset="custom"  # In Phase 1, always return "custom" (no preset tracking yet)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve config: {str(e)}")

    @app.post("/api/config/embeddings", response_model=EmbeddingConfigResponse)
    async def update_embedding_config(config: EmbeddingConfigModel) -> EmbeddingConfigResponse:
        """Update embedding configuration globally.

        Configuration changes will take effect for the next document upload/embedding generation.
        """
        if state.config_manager is None:
            raise HTTPException(status_code=500, detail="Config manager not initialized")

        try:
            # Log before/after values for audit trail
            old_config = state.config_manager.get_embedding_config()
            logger.info(
                f"Updating embedding config - "
                f"task: {old_config.task} → {config.task}, "
                f"dimensions: {old_config.dimensions} → {config.dimensions}, "
                f"late_chunking: {old_config.late_chunking} → {config.late_chunking}, "
                f"format: {old_config.embedding_format} → {config.embedding_format}"
            )

            # Validate and update configuration
            state.config_manager.set_embedding_config(config)
            logger.info(f"✓ Embedding config updated successfully")

            return EmbeddingConfigResponse(
                config=config,
                preset="custom"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")

    @app.get("/api/config/embeddings/presets", response_model=List[PresetInfo])
    async def get_embedding_presets() -> List[PresetInfo]:
        """List available embedding presets with descriptions and performance characteristics."""
        return [
            PresetInfo(
                name="for_query",
                display_name="Query Optimized",
                description="Fast single-shot queries, optimized for speed without late chunking",
                performance_characteristics={
                    "speed": "Fast",
                    "dimensions": "1024",
                    "storage": "8 KB/embedding",
                    "quality": "Good for simple queries"
                }
            ),
            PresetInfo(
                name="for_documents",
                display_name="Document Optimized",
                description="Late chunking for better context preservation, ideal for document indexing",
                performance_characteristics={
                    "speed": "Standard",
                    "dimensions": "1024",
                    "storage": "8 KB/embedding",
                    "quality": "Excellent for context"
                }
            ),
            PresetInfo(
                name="fast",
                display_name="Fast (4× faster)",
                description="4× faster with lower dimensions, best for speed-critical applications",
                performance_characteristics={
                    "speed": "4× faster",
                    "dimensions": "512",
                    "storage": "2 KB/embedding",
                    "quality": "Good (reduced dimensions)"
                }
            ),
            PresetInfo(
                name="storage_optimized",
                display_name="Storage Optimized (8× smaller)",
                description="8× smaller storage with binary format, best for resource-constrained systems",
                performance_characteristics={
                    "speed": "Standard",
                    "dimensions": "512",
                    "storage": "64 bytes/embedding",
                    "quality": "Good (binary format)"
                }
            ),
            PresetInfo(
                name="memory_constrained",
                display_name="Memory Constrained",
                description="Auto-scaled for systems with limited memory",
                performance_characteristics={
                    "speed": "Variable",
                    "dimensions": "Auto-selected",
                    "storage": "Auto-scaled",
                    "quality": "Variable"
                }
            ),
        ]

    # ========================================================================
    # OCR Configuration Endpoints
    # ========================================================================

    @app.get("/api/config/ocr", response_model=OCRConfigResponse)
    async def get_ocr_config() -> OCRConfigResponse:
        """Get current OCR configuration."""
        if state.config_manager is None:
            raise HTTPException(status_code=500, detail="Config manager not initialized")

        try:
            ocr_config = state.config_manager.get_ocr_config()
            return OCRConfigResponse(
                config=ocr_config,
                preset="custom"  # In Phase 1, always return "custom" (no preset tracking yet)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve config: {str(e)}")

    @app.post("/api/config/ocr", response_model=OCRConfigResponse)
    async def update_ocr_config(config: OCRConfigModel) -> OCRConfigResponse:
        """Update OCR configuration globally.

        Configuration changes will take effect for the next document upload with OCR processing.
        """
        if state.config_manager is None:
            raise HTTPException(status_code=500, detail="Config manager not initialized")

        try:
            # Log before/after values for audit trail
            old_config = state.config_manager.get_ocr_config()
            logger.info(
                "Updating OCR config - "
                f"batch_size: {old_config.batch_size} → {config.batch_size}, "
                f"render_workers: {old_config.render_workers} → {config.render_workers}, "
                f"analysis_workers: {old_config.analysis_workers} → {config.analysis_workers}, "
                f"resolution_mode: {old_config.resolution_mode} → {config.resolution_mode}, "
                f"grounding: {old_config.enable_grounding} → {config.enable_grounding}, "
                f"compression: {old_config.enable_compression} → {config.enable_compression}, "
                f"use_vllm: {old_config.use_vllm} → {config.use_vllm}"
            )

            # Validate and update configuration
            state.config_manager.set_ocr_config(config)
            logger.info(f"✓ OCR config updated successfully")

            return OCRConfigResponse(
                config=config,
                preset="custom"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")

    @app.get("/api/config/ocr/presets", response_model=List[PresetInfo])
    async def get_ocr_presets() -> List[PresetInfo]:
        """List available OCR presets with descriptions and performance characteristics."""
        return [
            PresetInfo(
                name="deepseek_tiny",
                display_name="Deepseek Tiny",
                description="Fastest Deepseek mode (512×512) for simple text-heavy documents",
                performance_characteristics={
                    "speed": "Fastest",
                    "resolution": "512×512",
                    "grounding": "Disabled",
                    "compression": "Enabled"
                }
            ),
            PresetInfo(
                name="deepseek_small",
                display_name="Deepseek Small",
                description="Speed/quality balance (640×640) for mixed but moderate complexity documents",
                performance_characteristics={
                    "speed": "Faster",
                    "resolution": "640×640",
                    "grounding": "Enabled",
                    "compression": "Enabled"
                }
            ),
            PresetInfo(
                name="deepseek_balanced",
                display_name="Deepseek Balanced",
                description="Default Deepseek quality (1024×1024) for general-purpose educational documents",
                performance_characteristics={
                    "speed": "Baseline",
                    "resolution": "1024×1024",
                    "grounding": "Enabled",
                    "compression": "Enabled"
                }
            ),
            PresetInfo(
                name="deepseek_high_quality",
                display_name="Deepseek High Quality",
                description="High fidelity (1280×1280) for dense tables, equations, and diagrams",
                performance_characteristics={
                    "speed": "Slower",
                    "resolution": "1280×1280",
                    "grounding": "Enabled",
                    "compression": "Enabled"
                }
            ),
            PresetInfo(
                name="deepseek_gundam",
                display_name="Deepseek Gundam",
                description="Dynamic multi-resolution pipeline for complex or mixed-layout documents",
                performance_characteristics={
                    "speed": "Adaptive",
                    "resolution": "Dynamic 640×640 + 1024×1024",
                    "grounding": "Enabled",
                    "compression": "Enabled"
                }
            ),
            PresetInfo(
                name="deepseek_production",
                display_name="Deepseek Production (vLLM)",
                description="High-throughput preset using vLLM backend for large-scale ingestion",
                performance_characteristics={
                    "speed": "5-10× faster with A100",
                    "resolution": "Dynamic (Gundam)",
                    "grounding": "Enabled",
                    "compression": "Enabled",
                    "inference": "vLLM required"
                }
            ),
        ]

    @app.get("/api/collections/{collection_name}/config", response_model=CollectionConfig)
    async def get_collection_config(collection_name: str) -> CollectionConfig:
        """Get configuration for a specific collection."""
        if state.collection_manager is None:
            raise HTTPException(status_code=500, detail="Collection manager not initialized")

        try:
            config = state.collection_manager.get_config(collection_name)
            return config
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve config: {str(e)}")

    @app.put("/api/collections/{collection_name}/config", response_model=CollectionConfig)
    async def update_collection_config(
        collection_name: str,
        config: CollectionConfig
    ) -> CollectionConfig:
        """Update configuration for a specific collection.

        Note: Configuration changes only affect future document uploads.
        Existing documents in the collection are not reprocessed.
        """
        if state.collection_manager is None:
            raise HTTPException(status_code=500, detail="Collection manager not initialized")

        try:
            # Validate config by attempting to convert to dict
            config.to_dict()

            # Update the configuration
            state.collection_manager.update_config(collection_name, config)

            # Return the updated config
            return state.collection_manager.get_config(collection_name)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")

    # Metrics and monitoring endpoints
    @app.get("/api/metrics/summary")
    async def get_metrics_summary():
        """Get summary statistics for processing performance."""
        from ..monitoring.metrics import get_metrics_collector

        collector = get_metrics_collector()
        return collector.get_summary_stats()

    @app.get("/api/metrics/performance")
    async def get_performance_metrics():
        """Get detailed performance metrics by method and file type."""
        from ..monitoring.metrics import get_metrics_collector

        collector = get_metrics_collector()
        return {
            "by_method": collector.get_performance_by_method(),
            "by_file_type": collector.get_performance_by_file_type(),
        }

    @app.get("/api/metrics/events")
    async def get_recent_events(limit: int = 20):
        """Get recent processing events.

        Args:
            limit: Maximum number of events to return (default: 20, max: 100)
        """
        from ..monitoring.metrics import get_metrics_collector

        limit = min(limit, 100)  # Cap at 100
        collector = get_metrics_collector()
        return collector.get_recent_events(limit=limit)

    @app.get("/api/metrics/system")
    async def get_system_metrics(limit: int = 10):
        """Get recent system metrics snapshots.

        Args:
            limit: Maximum number of snapshots to return (default: 10, max: 50)
        """
        from ..monitoring.metrics import get_metrics_collector

        limit = min(limit, 50)  # Cap at 50
        collector = get_metrics_collector()
        return collector.get_system_metrics(limit=limit)

    @app.get("/api/metrics/queues")
    async def get_queue_metrics():
        """Get RQ queue statistics if distributed processing is enabled."""
        from ..monitoring.metrics import get_metrics_collector

        collector = get_metrics_collector()
        stats = collector.get_rq_stats()

        if stats is None:
            return {
                "enabled": False,
                "message": "Distributed processing is not enabled"
            }

        return {
            "enabled": True,
            "queues": stats
        }

    @app.get("/api/metrics/all")
    async def get_all_metrics():
        """Get comprehensive metrics including all categories."""
        from ..monitoring.metrics import get_metrics_collector

        collector = get_metrics_collector()
        return collector.get_all_metrics()

    # Lesson Plan Generation endpoint
    @app.post("/api/lesson-plan/generate")
    async def generate_lesson_plan(request: "GenerateLessonRequest") -> "LessonMarkdownResponse":
        """
        Generate a lesson plan using RAG + LLM.

        This endpoint retrieves relevant educational materials and uses an LLM
        to generate a complete lesson plan with:
        - YAML frontmatter metadata
        - Learning objectives with citations
        - Embedded images with source attribution
        - Complete lesson flow (Engagement, Instruction, Practice, Closure)
        - Assessment strategies and differentiation
        - Sources Referenced section

        Args:
            request: Lesson generation request with topic, objective, grade, etc.

        Returns:
            Markdown lesson plan with metadata, source citations, and images

        Raises:
            HTTPException: If generation fails or no materials found
        """
        from ..generation import LessonPlanner, LessonGenerationError, QwenGenerator
        from ..generation.config import GenerationConfig
        from ..retrieval.educational import EducationalRetriever
        from dataclasses import asdict
        import time as time_module

        # Verify dependencies are available
        if state.embedder is None:
            raise HTTPException(
                status_code=500,
                detail="Embeddings model not loaded. Please restart the server."
            )

        if state.vector_store is None:
            raise HTTPException(
                status_code=500,
                detail="Vector store not available. Please restart the server."
            )

        # Initialize components for lesson generation
        try:
            # Create retriever
            retriever = EducationalRetriever(
                vector_store=state.vector_store,
                embedder=state.embedder,
                text_collection="educational_content",  # Default collection name
                image_collection="educational_images",   # Default image collection
            )

            # Create generator with config
            gen_config = GenerationConfig(
                max_tokens=4096,  # Longer output for lesson plans
                temperature=0.7,  # Slightly creative
                enable_thinking=False,  # Disable thinking for cleaner output
            )
            generator = QwenGenerator(config=gen_config)

            # Create planner
            planner = LessonPlanner(
                retriever=retriever,
                generator=generator,
                text_top_k=5,
                image_top_k=3,
            )

            # Generate lesson
            start_time = time_module.time()

            lesson = await planner.generate_lesson(
                topic=request.topic,
                learning_objective=request.learning_objective,
                grade=request.grade_level,
                subject=request.subject,
                duration=request.duration_minutes,
                teaching_style=request.teaching_style,
            )

            generation_time = time_module.time() - start_time

            # Generate unique lesson ID and cache for export
            import uuid
            lesson_id = str(uuid.uuid4())
            state.lesson_cache[lesson_id] = lesson.markdown_content

            # Convert lesson to response
            return LessonMarkdownResponse(
                lesson_id=lesson_id,
                markdown=lesson.markdown_content,
                metadata=asdict(lesson.metadata),
                sources_count=lesson.sources_count,
                images_count=lesson.images_count,
                generation_time_seconds=round(generation_time, 2),
            )

        except LessonGenerationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate lesson: {str(e)}"
            )
        except Exception as e:
            import logging
            logger = logging.getLogger("uvicorn")
            logger.error(f"Lesson generation error: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error during lesson generation: {str(e)}"
            )

    # Lesson Plan Export endpoint (Phase 2)
    @app.get("/api/lesson-plan/export/{lesson_id}")
    async def export_lesson_plan(
        lesson_id: str,
        format: str = "markdown",
        style: str = "color"
    ):
        """
        Export a previously generated lesson plan in various formats.

        Supports:
        - markdown: Original markdown content
        - pdf: Professional PDF with styling (color or bw)
        - json: Structured JSON data

        Args:
            lesson_id: UUID of the lesson to export
            format: Export format (markdown, pdf, or json)
            style: PDF style (color or bw) - only applies to pdf format

        Returns:
            File response with appropriate content type

        Raises:
            HTTPException: If lesson not found or export fails
        """
        from ..generation import LessonExporter, LessonExportError
        from fastapi.responses import Response
        import json as json_module

        # Validate format
        if format not in ["markdown", "pdf", "json"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format '{format}'. Must be one of: markdown, pdf, json"
            )

        # Validate style
        if style not in ["color", "bw"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid style '{style}'. Must be one of: color, bw"
            )

        # Check if lesson exists in cache
        if lesson_id not in state.lesson_cache:
            raise HTTPException(
                status_code=404,
                detail=f"Lesson '{lesson_id}' not found. It may have expired from cache."
            )

        markdown_content = state.lesson_cache[lesson_id]

        try:
            exporter = LessonExporter()

            if format == "markdown":
                # Return markdown as text file
                return Response(
                    content=markdown_content,
                    media_type="text/markdown",
                    headers={
                        "Content-Disposition": f'attachment; filename="lesson_{lesson_id[:8]}.md"'
                    }
                )

            elif format == "pdf":
                # Convert to PDF (color or B&W style)
                pdf_bytes = exporter.markdown_to_pdf(markdown_content, style=style)
                # Add style indicator to filename for B&W
                filename_suffix = "_bw" if style == "bw" else ""
                return Response(
                    content=pdf_bytes,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f'attachment; filename="lesson_{lesson_id[:8]}{filename_suffix}.pdf"'
                    }
                )

            elif format == "json":
                # Convert to JSON
                lesson_json = exporter.markdown_to_json(markdown_content)
                json_str = json_module.dumps(lesson_json, indent=2)
                return Response(
                    content=json_str,
                    media_type="application/json",
                    headers={
                        "Content-Disposition": f'attachment; filename="lesson_{lesson_id[:8]}.json"'
                    }
                )

        except LessonExportError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to export lesson: {str(e)}"
            )
        except Exception as e:
            import logging
            logger = logging.getLogger("uvicorn")
            logger.error(f"Lesson export error: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error during lesson export: {str(e)}"
            )

    # ========================================================================
    # Phase 3: Simple Lesson Persistence (Single-User App)
    # ========================================================================

    from fastapi import Depends
    from sqlalchemy.orm import Session
    from ..database import init_db, get_db, Lesson

    # Initialize database on startup
    @app.on_event("startup")
    async def init_database():
        """Initialize database tables on startup."""
        init_db()

    # Save Lesson
    @app.post("/api/lessons/save", response_model=LessonDetailResponse, status_code=201)
    async def save_lesson(
        request: SaveLessonRequest,
        db: Session = Depends(get_db)
    ):
        """Save a generated lesson to the library."""
        if request.lesson_id not in state.lesson_cache:
            raise HTTPException(
                status_code=404,
                detail=f"Lesson '{request.lesson_id}' not found in cache."
            )

        markdown_content = state.lesson_cache[request.lesson_id]

        # Parse metadata
        from ..generation import LessonExporter
        exporter = LessonExporter()
        lesson_json = exporter.markdown_to_json(markdown_content)

        # Save to database
        new_lesson = Lesson(
            lesson_id=request.lesson_id,
            title=lesson_json["metadata"].get("title", "Untitled Lesson"),
            markdown_content=markdown_content,
            grade=lesson_json["metadata"].get("grade", ""),
            subject=lesson_json["metadata"].get("subject", ""),
            topic=lesson_json["metadata"].get("topic", ""),
            learning_objective=lesson_json["metadata"].get("learning_objective", ""),
            duration_minutes=lesson_json["metadata"].get("duration", 50),
            teaching_style=lesson_json["metadata"].get("teaching_style", "balanced"),
            metadata_json=lesson_json["metadata"],
            sources_count=len(lesson_json.get("citations", [])),
            images_count=lesson_json["metadata"].get("images_count", 0),
        )

        db.add(new_lesson)
        db.commit()
        db.refresh(new_lesson)

        # Remove from cache
        del state.lesson_cache[request.lesson_id]

        return LessonDetailResponse(
            id=new_lesson.id,
            lesson_id=new_lesson.lesson_id,
            title=new_lesson.title,
            markdown_content=new_lesson.markdown_content,
            grade=new_lesson.grade,
            subject=new_lesson.subject,
            topic=new_lesson.topic,
            learning_objective=new_lesson.learning_objective,
            duration_minutes=new_lesson.duration_minutes,
            teaching_style=new_lesson.teaching_style,
            metadata_json=new_lesson.metadata_json,
            sources_count=new_lesson.sources_count,
            images_count=new_lesson.images_count,
            is_favorite=new_lesson.is_favorite,
            created_at=new_lesson.created_at.isoformat(),
            updated_at=new_lesson.updated_at.isoformat(),
        )

    # List Lessons
    @app.get("/api/lessons", response_model=List[LessonListItem])
    async def list_lessons(
        limit: int = 20,
        offset: int = 0,
        grade: Optional[str] = None,
        subject: Optional[str] = None,
        favorites_only: bool = False,
        db: Session = Depends(get_db)
    ):
        """Get all saved lessons with optional filters."""
        query = db.query(Lesson).filter(Lesson.is_archived == False)

        if grade:
            query = query.filter(Lesson.grade == grade)
        if subject:
            query = query.filter(Lesson.subject == subject)
        if favorites_only:
            query = query.filter(Lesson.is_favorite == True)

        query = query.order_by(Lesson.created_at.desc())
        lessons = query.offset(offset).limit(limit).all()

        return [
            LessonListItem(
                id=lesson.id,
                lesson_id=lesson.lesson_id,
                title=lesson.title,
                grade=lesson.grade,
                subject=lesson.subject,
                topic=lesson.topic,
                duration_minutes=lesson.duration_minutes,
                teaching_style=lesson.teaching_style,
                sources_count=lesson.sources_count,
                images_count=lesson.images_count,
                is_favorite=lesson.is_favorite,
                created_at=lesson.created_at.isoformat(),
                updated_at=lesson.updated_at.isoformat(),
            )
            for lesson in lessons
        ]

    # Get Lesson by ID
    @app.get("/api/lessons/{lesson_id}", response_model=LessonDetailResponse)
    async def get_lesson(
        lesson_id: int,
        db: Session = Depends(get_db)
    ):
        """Get a specific lesson by ID."""
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        return LessonDetailResponse(
            id=lesson.id,
            lesson_id=lesson.lesson_id,
            title=lesson.title,
            markdown_content=lesson.markdown_content,
            grade=lesson.grade,
            subject=lesson.subject,
            topic=lesson.topic,
            learning_objective=lesson.learning_objective,
            duration_minutes=lesson.duration_minutes,
            teaching_style=lesson.teaching_style,
            metadata_json=lesson.metadata_json,
            sources_count=lesson.sources_count,
            images_count=lesson.images_count,
            is_favorite=lesson.is_favorite,
            created_at=lesson.created_at.isoformat(),
            updated_at=lesson.updated_at.isoformat(),
        )

    # Toggle Favorite
    @app.post("/api/lessons/{lesson_id}/favorite")
    async def toggle_favorite(
        lesson_id: int,
        db: Session = Depends(get_db)
    ):
        """Toggle favorite status for a lesson."""
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        lesson.is_favorite = not lesson.is_favorite
        db.commit()

        return {"status": "toggled", "is_favorite": lesson.is_favorite}

    # Delete Lesson
    @app.delete("/api/lessons/{lesson_id}")
    async def delete_lesson(
        lesson_id: int,
        db: Session = Depends(get_db)
    ):
        """Delete a lesson."""
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        db.delete(lesson)
        db.commit()

        return {"status": "deleted"}

    # Update Lesson
    @app.patch("/api/lessons/{lesson_id}", response_model=LessonDetailResponse)
    async def update_lesson(
        lesson_id: int,
        request: UpdateLessonRequest,
        db: Session = Depends(get_db)
    ):
        """
        Update an existing lesson with partial updates.

        This endpoint allows updating lesson content and metadata. Only the fields
        provided in the request will be updated. The `updated_at` timestamp is
        automatically set.

        **Editable fields:**
        - `markdown_content`: Lesson content in markdown format (1-100,000 chars)
        - `title`: Lesson title (1-500 chars)
        - `duration_minutes`: Lesson duration (20-90 minutes)
        - `teaching_style`: Teaching approach (balanced, direct, inquiry, project)
        - `learning_objective`: Learning objective (1-500 chars)

        **Non-editable fields:**
        - `grade`, `subject`, `topic` (core identifiers)
        - `sources_count`, `images_count` (derived from generation)
        - `created_at` (immutable)

        **Example request:**
        ```json
        {
            "title": "Updated Lesson Title",
            "duration_minutes": 60
        }
        ```

        **Status codes:**
        - 200: Success
        - 400: No fields to update
        - 404: Lesson not found
        - 422: Validation error
        """
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        update_data = request.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        for key, value in update_data.items():
            setattr(lesson, key, value)

        db.commit()
        db.refresh(lesson)

        return LessonDetailResponse(
            id=lesson.id,
            lesson_id=lesson.lesson_id,
            title=lesson.title,
            markdown_content=lesson.markdown_content,
            grade=lesson.grade,
            subject=lesson.subject,
            topic=lesson.topic,
            learning_objective=lesson.learning_objective,
            duration_minutes=lesson.duration_minutes,
            teaching_style=lesson.teaching_style,
            metadata_json=lesson.metadata_json,
            sources_count=lesson.sources_count,
            images_count=lesson.images_count,
            is_favorite=lesson.is_favorite,
            created_at=lesson.created_at.isoformat(),
            updated_at=lesson.updated_at.isoformat()
        )

    frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    frontend_assets = frontend_dist / "assets"

    # Only mount frontend if both dist and assets directories exist
    if frontend_dist.exists() and frontend_assets.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_assets)), name="assets")

        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            if full_path and not full_path.startswith("api") and not full_path.startswith("ws"):
                file_path = frontend_dist / full_path
                if file_path.exists() and file_path.is_file():
                    return FileResponse(file_path)
            return FileResponse(frontend_dist / "index.html")

    return app


# Initialize app with default components for direct usage
try:
    from ..embeddings import JinaEmbeddingsV4
    from ..storage import ChromaVectorStore

    embedder = JinaEmbeddingsV4()
    vector_store = ChromaVectorStore()
    app = create_app(embedder=embedder, vector_store=vector_store)
except Exception:
    # Fallback: create minimal app if components fail to load
    app = create_app()
