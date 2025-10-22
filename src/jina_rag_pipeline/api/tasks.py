import asyncio
import uuid
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import logging
import os

from PIL import Image

from ..embeddings import JinaEmbeddingsV4
from ..embeddings.config import EmbeddingConfig
from ..ingestion import DocumentProcessor
from ..ingestion.ocr_config import OCRConfig
from ..multimodal.thumbnails import ThumbnailGenerator
from ..storage import ChromaVectorStore
from .models import FileStatus, IngestionStatus
from .config_manager import ConfigManager
from ..monitoring.metrics import get_metrics_collector

# Optional RQ support for distributed processing
try:
    from ..workers.queue import JobQueueManager
    from ..workers.config import RQConfig
    RQ_AVAILABLE = True
except ImportError:
    RQ_AVAILABLE = False
    JobQueueManager = None
    RQConfig = None

# Image formats that should use vision encoder
IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

logger = logging.getLogger(__name__)

# Thread pool for offloading I/O-bound Deepseek rendering
# Using ThreadPoolExecutor since PDF rendering is I/O bound but GIL-blocked
_executor = ThreadPoolExecutor(max_workers=2)


class IngestionTask:
    def __init__(
        self,
        task_id: str,
        files: List[FileStatus],
        collection_name: str,
        temp_dir: Path,
    ) -> None:
        self.task_id = task_id
        self.files = files
        self.collection_name = collection_name
        self.temp_dir = temp_dir
        self.status = IngestionStatus.QUEUED
        self.progress = 0.0
        self.current_file: Optional[str] = None
        self.processed_files = 0
        self.total_files = len(files)
        self.errors: List[Dict[str, str]] = []
        self.listeners: List[asyncio.Queue] = []

    def add_listener(self, queue: asyncio.Queue) -> None:
        self.listeners.append(queue)

    def remove_listener(self, queue: asyncio.Queue) -> None:
        if queue in self.listeners:
            self.listeners.remove(queue)

    async def notify_listeners(self, message: Dict[str, Any]) -> None:
        for queue in self.listeners:
            try:
                await queue.put(message)
            except Exception:
                pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "progress": self.progress,
            "current_file": self.current_file,
            "processed_files": self.processed_files,
            "total_files": self.total_files,
            "errors": self.errors,
        }


class TaskManager:
    def __init__(
        self,
        embedder: JinaEmbeddingsV4,
        vector_store: ChromaVectorStore,
        temp_dir: Path,
        collection_manager: Optional[Any] = None,
        config_manager: Optional[ConfigManager] = None,
        enable_task_persistence: bool = True,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.tasks: Dict[str, IngestionTask] = {}
        self.processor = DocumentProcessor()
        self.thumbnail_generator = ThumbnailGenerator()
        self.collection_manager = collection_manager
        self.config_manager = config_manager
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        self._executor = _executor

        # Initialize RQ queue manager if available and enabled
        self.queue_manager = None
        if RQ_AVAILABLE and RQConfig and RQConfig.DISTRIBUTED_PROCESSING_ENABLED:
            try:
                self.queue_manager = JobQueueManager()
                logger.info("Distributed processing enabled via RQ")
            except Exception as e:
                logger.warning(f"Failed to initialize RQ queue manager: {e}")
                self.queue_manager = None

        # Initialize metrics collector
        self.metrics = get_metrics_collector()

        # Initialize task persistence
        self.task_db = None
        if enable_task_persistence:
            try:
                from .task_db import TaskDatabase
                self.task_db = TaskDatabase()
                logger.info("Task persistence enabled")
                # Restore active tasks from database
                self._restore_tasks_from_db()
            except Exception as e:
                logger.warning(f"Failed to initialize task persistence: {e}")
                self.task_db = None

    def _restore_tasks_from_db(self):
        """Restore active tasks from database on startup."""
        if not self.task_db:
            return

        try:
            active_tasks = self.task_db.get_active_tasks()
            for task_data in active_tasks:
                task_id = task_data["task_id"]
                collection_name = task_data["collection_name"]

                # Get files for this task
                files_data = self.task_db.get_task_files(task_id)

                # Recreate FileStatus objects
                files = []
                for file_data in files_data:
                    file_status = FileStatus(
                        name=file_data["filename"],
                        size=file_data["size"] or 0,
                        status=IngestionStatus(file_data["status"]),
                        error=file_data.get("error")
                    )
                    files.append(file_status)

                # Recreate task
                task = IngestionTask(task_id, files, collection_name, self.temp_dir)
                task.status = IngestionStatus(task_data["status"])
                task.progress = task_data["progress"]
                task.current_file = task_data.get("current_file")
                task.processed_files = task_data["processed_files"]
                task.errors = task_data.get("errors") or []

                self.tasks[task_id] = task

            logger.info(f"Restored {len(active_tasks)} active tasks from database")
        except Exception as e:
            logger.error(f"Failed to restore tasks from database: {e}")

    def _get_embedding_config(self) -> EmbeddingConfig:
        """Get embedding configuration from ConfigManager or use default.

        Returns:
            EmbeddingConfig: Current embedding configuration with fallback to default.
        """
        if not self.config_manager:
            logger.debug("ConfigManager not available, using default EmbeddingConfig.for_documents()")
            return EmbeddingConfig.for_documents()

        try:
            config_model = self.config_manager.get_embedding_config()
            logger.debug(f"Loaded embedding config: task={config_model.task}, dimensions={config_model.dimensions}")

            # Convert Pydantic model to EmbeddingConfig dataclass
            # The dataclass constructor accepts the same fields as the Pydantic model
            return EmbeddingConfig(
                task=config_model.task,
                dimensions=config_model.dimensions,
                late_chunking=config_model.late_chunking,
                return_multivector=config_model.return_multivector,
                embedding_format=config_model.embedding_format,
                batch_size=config_model.batch_size,
                max_tokens_per_batch=config_model.max_tokens_per_batch,
            )
        except Exception as e:
            logger.warning(f"Failed to load embedding config from ConfigManager: {e}. Using default.")
            return EmbeddingConfig.for_documents()

    def _get_ocr_config(self) -> OCRConfig:
        """Get OCR configuration from ConfigManager or use default.

        Returns:
            OCRConfig: Current OCR configuration with fallback to auto-detected default.
        """
        default_config = self._default_ocr_config()

        if not self.config_manager:
            logger.debug("ConfigManager not available, using default Deepseek OCR config")
            return default_config

        try:
            config_model = self.config_manager.get_ocr_config()
            logger.debug(
                "Loaded OCR config: batch_size=%s, render_workers=%s, analysis_workers=%s, "
                "resolution_mode=%s, grounding=%s, compression=%s, use_vllm=%s",
                config_model.batch_size,
                config_model.render_workers,
                config_model.analysis_workers,
                config_model.resolution_mode,
                config_model.enable_grounding,
                config_model.enable_compression,
                config_model.use_vllm,
            )

            return OCRConfig(
                batch_size=config_model.batch_size,
                render_workers=config_model.render_workers,
                analysis_workers=config_model.analysis_workers,
                pre_render_batches=config_model.pre_render_batches,
                checkpoint_enabled=config_model.checkpoint_enabled,
                resolution_mode=config_model.resolution_mode,
                enable_grounding=config_model.enable_grounding,
                enable_compression=config_model.enable_compression,
                use_vllm=config_model.use_vllm,
            )
        except Exception as e:
            logger.warning("Failed to load OCR config from ConfigManager: %s. Using default.", e)
            return default_config

    @staticmethod
    def _default_ocr_config() -> OCRConfig:
        """Select default Deepseek OCR configuration based on platform."""
        import platform

        is_apple_silicon = (
            platform.system() == "Darwin"
            and platform.machine().lower().startswith("arm")
        )
        return OCRConfig.deepseek_small() if is_apple_silicon else OCRConfig.deepseek_balanced()

    def create_task(
        self, files: List[FileStatus], collection_name: str
    ) -> IngestionTask:
        task_id = str(uuid.uuid4())
        task = IngestionTask(task_id, files, collection_name, self.temp_dir)
        self.tasks[task_id] = task

        # Persist to database
        if self.task_db:
            try:
                files_data = [
                    {"name": f.name, "size": f.size, "status": f.status.value}
                    for f in files
                ]
                self.task_db.create_task(task_id, collection_name, files_data)
            except Exception as e:
                logger.error(f"Failed to persist task to database: {e}")

        return task

    def get_task(self, task_id: str) -> Optional[IngestionTask]:
        return self.tasks.get(task_id)

    def _should_use_distributed_queue(self, file_path: Path) -> bool:
        """Determine if file should be processed via distributed RQ instead of ThreadPool."""
        if not self.queue_manager:
            return False

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        file_ext = file_path.suffix.lower()

        return self.queue_manager.should_use_distributed_queue(file_size_mb, file_ext)

    async def process_task(self, task_id: str) -> None:
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = IngestionStatus.PROCESSING
        await task.notify_listeners(
            {"type": "status", "status": "processing", "progress": 0}
        )

        # Update database
        if self.task_db:
            try:
                self.task_db.update_task(task_id, status="processing")
            except Exception as e:
                logger.error(f"Failed to update task in database: {e}")

        # Load collection configuration (Task 3.4)
        collection_config = None
        if self.collection_manager:
            try:
                collection_config = self.collection_manager.get_config(task.collection_name)
            except Exception:
                # Use defaults if config loading fails
                from .models import CollectionConfig
                collection_config = CollectionConfig.get_default()
        else:
            # No collection manager - use precision-first defaults
            from .models import CollectionConfig
            collection_config = CollectionConfig.get_default()

        # Extract layout analysis settings
        enable_layout_analysis = collection_config.enable_layout_analysis if collection_config else True

        try:
            for i, file_status in enumerate(task.files):
                task.current_file = file_status.name
                temp_name = getattr(file_status, "temp_name", None) or file_status.name
                file_path = task.temp_dir / temp_name

                print(f"[DEBUG] Processing file: {file_status.name}", flush=True)
                print(f"[DEBUG] Looking for file at: {file_path}", flush=True)
                print(f"[DEBUG] File exists: {file_path.exists()}", flush=True)

                if not file_path.exists():
                    error_msg = f"File not found: {file_path}"
                    print(f"[ERROR] File not found: {file_path}", flush=True)
                    print(f"[ERROR] Temp dir contents: {list(task.temp_dir.iterdir())}", flush=True)
                    task.errors.append({"file": file_status.name, "error": error_msg})
                    file_status.status = IngestionStatus.FAILED
                    file_status.error = error_msg
                    task.processed_files += 1
                    continue

                try:
                    file_status.status = IngestionStatus.PROCESSING

                    # Generate unique identifiers for this document instance
                    document_id = str(uuid.uuid4())
                    upload_timestamp = datetime.now(timezone.utc).isoformat()

                    # Check if this is an image file
                    file_ext = file_path.suffix.lower()
                    is_image = file_ext in IMAGE_FORMATS

                    # Start metrics tracking
                    file_size_mb = file_path.stat().st_size / (1024 * 1024)
                    metric_task_id = f"{task.task_id}_{i}"
                    processing_method = "unknown"  # Will be updated based on actual path taken

                    if is_image:
                        # Process image file
                        processing_method = "vision_encoder"
                        self.metrics.start_processing(
                            metric_task_id, file_status.name, file_size_mb, file_ext, processing_method
                        )

                        from ..ingestion.loaders import ImageLoader

                        loader = ImageLoader()
                        document = loader.load(file_path)

                        # Create permanent storage directory for this collection
                        images_dir = Path(f"./uploads/{task.collection_name}/images")
                        images_dir.mkdir(parents=True, exist_ok=True)

                        # Move image to permanent storage with UUID-based name
                        image_filename = f"{document_id}{file_path.suffix}"
                        permanent_image_path = images_dir / image_filename
                        file_path.rename(permanent_image_path)

                        # Generate thumbnail
                        thumbnails_dir = Path(f"./uploads/{task.collection_name}/thumbnails")
                        thumbnails_dir.mkdir(parents=True, exist_ok=True)

                        thumbnail_filename = f"{document_id}_thumb.jpg"
                        thumbnail_path = thumbnails_dir / thumbnail_filename
                        self.thumbnail_generator.generate_thumbnail(permanent_image_path, thumbnail_path)

                        # Load PIL Image for embedding
                        pil_image = Image.open(permanent_image_path)

                        # Generate embedding using vision encoder
                        embedding = self.embedder.encode_image(pil_image, task="retrieval")
                        embedding_list = embedding.tolist()

                        # Prepare metadata with file paths
                        # Convert list fields to scalar values for ChromaDB compatibility
                        base_metadata = document.metadata.copy()

                        # Convert mean_rgb list to separate scalar fields
                        if "mean_rgb" in base_metadata and isinstance(base_metadata["mean_rgb"], (list, tuple)):
                            mean_rgb = base_metadata.pop("mean_rgb")
                            base_metadata["mean_r"] = float(mean_rgb[0]) if len(mean_rgb) > 0 else 0.0
                            base_metadata["mean_g"] = float(mean_rgb[1]) if len(mean_rgb) > 1 else 0.0
                            base_metadata["mean_b"] = float(mean_rgb[2]) if len(mean_rgb) > 2 else 0.0

                        # Convert std_rgb list to separate scalar fields
                        if "std_rgb" in base_metadata and isinstance(base_metadata["std_rgb"], (list, tuple)):
                            std_rgb = base_metadata.pop("std_rgb")
                            base_metadata["std_r"] = float(std_rgb[0]) if len(std_rgb) > 0 else 0.0
                            base_metadata["std_g"] = float(std_rgb[1]) if len(std_rgb) > 1 else 0.0
                            base_metadata["std_b"] = float(std_rgb[2]) if len(std_rgb) > 2 else 0.0

                        metadata = {
                            "source": file_status.name,
                            "document_id": document_id,
                            "upload_timestamp": upload_timestamp,
                            "image_path": str(permanent_image_path),
                            "thumbnail_path": str(thumbnail_path),
                            **base_metadata,
                        }

                        # Store with empty document content (embeddings are from visual features)
                        self.vector_store.add_embeddings(
                            collection_name=task.collection_name,
                            embeddings=[embedding_list],
                            documents=[document.content],
                            metadatas=[metadata],
                        )
                    else:
                        # Process text document
                        # Check if this should be routed through Deepseek OCR (PDFs, PPTX, images)
                        from ..ingestion.loaders import LoaderFactory
                        from ..ingestion.deepseek_loader import DeepseekLoader
                        import os

                        file_ext = file_path.suffix.lower()
                        deepseek_flag = os.getenv("DEEPSEEK_OCR_ENABLED", "true")
                        deepseek_enabled = deepseek_flag.lower() in ("true", "1", "yes")
                        is_deepseek_format = file_ext in [".pdf", ".pptx", ".ppt", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]

                        document = None
                        if deepseek_enabled and is_deepseek_format:
                            # Determine whether to use RQ distributed queue or ThreadPool
                            use_rq = self._should_use_distributed_queue(file_path)

                            if use_rq:
                                # Route through RQ distributed worker queue for large files
                                processing_method = "rq"
                                self.metrics.start_processing(
                                    metric_task_id, file_status.name, file_size_mb, file_ext, processing_method
                                )
                                try:
                                    logger.info(f"Loading {file_status.name} via RQ distributed Deepseek OCR (large file)")
                                    document = await self._load_deepseek_document_via_rq(
                                        task, file_path, file_status, file_ext, document_id
                                    )
                                except Exception as e:
                                    # Fall back to ThreadPool if RQ fails
                                    logger.warning(f"RQ processing failed for {file_status.name}, falling back to ThreadPool: {e}")
                                    try:
                                        document = await self._load_deepseek_document_async(task, file_path, file_status, file_ext)
                                    except Exception as e2:
                                        logger.warning(f"ThreadPool processing also failed, falling back to traditional loader: {e2}")
                                        document = None
                            else:
                                # Route through ThreadPool for normal-sized files
                                processing_method = "threadpool"
                                self.metrics.start_processing(
                                    metric_task_id, file_status.name, file_size_mb, file_ext, processing_method
                                )
                                try:
                                    logger.info(f"Loading {file_status.name} via Deepseek OCR (ThreadPool async)")
                                    document = await self._load_deepseek_document_async(task, file_path, file_status, file_ext)
                                except Exception as e:
                                    # Fall back to traditional loaders
                                    logger.warning(f"Deepseek OCR failed for {file_status.name}, falling back to traditional loader: {e}")
                                    document = None

                        # If Deepseek OCR didn't work, try traditional loaders
                        if document is None:
                            loader_factory = LoaderFactory()
                            loader = loader_factory.get_loader(file_path)
                            if loader:
                                document = loader.load(file_path)
                            else:
                                # No loader found, try chunking
                                chunks = self.processor.process(file_path, skip_if_processed=False)
                                if chunks:
                                    await self._process_chunks(
                                        task=task,
                                        file_status=file_status,
                                        file_path=file_path,
                                        chunks=chunks,
                                        document_id=document_id,
                                        upload_timestamp=upload_timestamp,
                                    )
                                else:
                                    raise ValueError(f"No chunks generated for {file_status.name} (no loader found)")
                                document = None  # Mark as processed

                        # Process the loaded document
                        if document is not None:
                            print(f"[DEBUG] Document loaded, metadata keys: {list(document.metadata.keys())}", flush=True)
                            print(f"[DEBUG] extraction_method: {document.metadata.get('extraction_method')}", flush=True)
                            try:
                                # Check if document has regions (from layout analysis)
                                if "regions" in document.metadata and document.metadata["regions"]:
                                    # Region-based processing (Task 3.2)
                                    await self._process_regions(
                                        task=task,
                                        file_status=file_status,
                                        file_path=file_path,
                                        document=document,
                                        document_id=document_id,
                                        upload_timestamp=upload_timestamp,
                                    )
                                elif document.metadata.get("extraction_method") == "deepseek-ocr":
                                    # Deepseek OCR: content already extracted, process directly
                                    from ..ingestion.chunking import Chunk
                                    chunks = [
                                        Chunk(
                                            content=document.content,
                                            metadata={
                                                **document.metadata,
                                                "chunk_index": 0,
                                                "start_index": 0,
                                                "end_index": len(document.content),
                                            },
                                            source=document.source,
                                        )
                                    ]
                                    await self._process_chunks(
                                        task=task,
                                        file_status=file_status,
                                        file_path=file_path,
                                        chunks=chunks,
                                        document_id=document_id,
                                        upload_timestamp=upload_timestamp,
                                    )
                                else:
                                    # Fall back to chunking-based processing
                                    chunks = self.processor.process(file_path, skip_if_processed=False)
                                    if chunks:
                                        await self._process_chunks(
                                            task=task,
                                            file_status=file_status,
                                            file_path=file_path,
                                            chunks=chunks,
                                            document_id=document_id,
                                            upload_timestamp=upload_timestamp,
                                        )
                                    else:
                                        raise ValueError(f"No chunks generated for {file_status.name}")
                            except Exception as e:
                                print(f"[ERROR] Exception during document processing: {type(e).__name__}: {e}", flush=True)
                                import traceback
                                print(f"[ERROR] Traceback: {traceback.format_exc()}", flush=True)
                                # Fall back to chunking if processing fails
                                chunks = self.processor.process(file_path, skip_if_processed=False)
                                if chunks:
                                    await self._process_chunks(
                                        task=task,
                                        file_status=file_status,
                                        file_path=file_path,
                                        chunks=chunks,
                                        document_id=document_id,
                                        upload_timestamp=upload_timestamp,
                                    )
                                else:
                                    raise ValueError(f"No chunks generated for {file_status.name} (fallback from processing error: {e})")

                    file_status.status = IngestionStatus.COMPLETED
                    task.processed_files += 1
                    task.progress = (task.processed_files / task.total_files) * 100

                    # Update database
                    if self.task_db:
                        try:
                            self.task_db.update_file_status(
                                task_id, file_status.name, "completed"
                            )
                            self.task_db.update_task(
                                task_id,
                                progress=task.progress,
                                processed_files=task.processed_files
                            )
                        except Exception as e:
                            logger.error(f"Failed to update database: {e}")

                    # Track successful processing
                    page_count = document.metadata.get("page_count") if document else None
                    self.metrics.end_processing(
                        metric_task_id,
                        success=True,
                        page_count=page_count
                    )

                    await task.notify_listeners(
                        {
                            "type": "progress",
                            "progress": task.progress,
                            "current_file": file_status.name,
                            "processed_files": task.processed_files,
                        }
                    )

                except Exception as e:
                    error_msg = str(e)
                    task.errors.append({"file": file_status.name, "error": error_msg})
                    file_status.status = IngestionStatus.FAILED
                    file_status.error = error_msg
                    task.processed_files += 1

                    # Update database
                    if self.task_db:
                        try:
                            self.task_db.update_file_status(
                                task_id, file_status.name, "failed", error_msg
                            )
                            self.task_db.update_task(
                                task_id,
                                processed_files=task.processed_files,
                                errors=task.errors
                            )
                        except Exception as e:
                            logger.error(f"Failed to update database: {e}")

                    # Track failed processing
                    self.metrics.end_processing(
                        metric_task_id,
                        success=False,
                        error=error_msg
                    )

                finally:
                    # Only delete temp file if it still exists (wasn't renamed to permanent storage)
                    try:
                        if file_path.exists():
                            file_path.unlink()
                    except Exception:
                        pass

            task.status = IngestionStatus.COMPLETED
            task.progress = 100.0
            task.current_file = None

            # Update database
            if self.task_db:
                try:
                    self.task_db.update_task(
                        task_id,
                        status="completed",
                        progress=100.0,
                        current_file=None
                    )
                except Exception as e:
                    logger.error(f"Failed to update database: {e}")

            await task.notify_listeners(
                {
                    "type": "complete",
                    "progress": 100,
                    "processed_files": task.processed_files,
                    "errors": task.errors,
                }
            )

        except Exception as e:
            task.status = IngestionStatus.FAILED
            task.errors.append({"file": "system", "error": str(e)})

            # Update database
            if self.task_db:
                try:
                    self.task_db.update_task(
                        task_id,
                        status="failed",
                        errors=task.errors
                    )
                except Exception as e:
                    logger.error(f"Failed to update database: {e}")

            await task.notify_listeners(
                {"type": "error", "error": str(e), "progress": task.progress}
            )

    async def _process_chunks(
        self,
        task: IngestionTask,
        file_status: FileStatus,
        file_path: Path,
        chunks: List[Any],
        document_id: str,
        upload_timestamp: str,
    ) -> None:
        """Process document using traditional chunking approach.

        Args:
            task: The ingestion task
            file_status: Status of the file being processed
            file_path: Path to the file
            chunks: List of text chunks
            document_id: Unique document identifier
            upload_timestamp: Timestamp of upload
        """
        # Create permanent storage directory for this collection
        documents_dir = Path(f"./uploads/{task.collection_name}/documents")
        documents_dir.mkdir(parents=True, exist_ok=True)

        # Move document to permanent storage with UUID-based name
        document_filename = f"{document_id}{file_path.suffix}"
        permanent_document_path = documents_dir / document_filename
        file_path.rename(permanent_document_path)

        # Prepare chunk texts and metadata
        texts = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "source": file_status.name,
                "document_id": document_id,
                "upload_timestamp": upload_timestamp,
                "modality": "text",
                "document_path": str(permanent_document_path),
                **(chunk.metadata or {}),
            }
            for chunk in chunks
        ]

        # Generate embeddings using text encoder with aggressive batch size
        # Use profile-based batch size for optimal throughput
        try:
            from ..config import get_profile
            profile = get_profile()
            batch_size = profile.embedding_batch_size
        except ImportError:
            batch_size = 64  # Fallback to reasonable default

        config = self._get_embedding_config()
        embeddings = self.embedder.embed_with_config(
            texts,
            config
        )
        embeddings_list = [emb.tolist() for emb in embeddings]

        # Store embeddings in vector database
        self.vector_store.add_embeddings(
            collection_name=task.collection_name,
            embeddings=embeddings_list,
            documents=texts,
            metadatas=metadatas,
        )

    async def _process_regions(
        self,
        task: IngestionTask,
        file_status: FileStatus,
        file_path: Path,
        document: Any,
        document_id: str,
        upload_timestamp: str,
    ) -> None:
        """Process document regions with maximum precision and granularity.

        Each region is processed independently with the appropriate encoder
        (text regions → text encoder, image regions → vision encoder).
        All regions are linked to the source document via document_id.

        Args:
            task: The ingestion task
            file_status: Status of the file being processed
            file_path: Path to the file
            document: Document object with regions metadata
            document_id: Unique document identifier
            upload_timestamp: Timestamp of upload
        """
        from ..ingestion.semantic_region import SemanticRegion

        # Create organized persistent storage directories
        documents_dir = Path(f"./uploads/{task.collection_name}/documents")
        extracted_images_dir = Path(f"./uploads/{task.collection_name}/extracted_images")
        tables_dir = Path(f"./uploads/{task.collection_name}/tables")
        thumbnails_dir = Path(f"./uploads/{task.collection_name}/thumbnails")
        metadata_dir = Path(f"./uploads/{task.collection_name}/metadata")

        for directory in [documents_dir, extracted_images_dir, tables_dir, thumbnails_dir, metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Move original document to permanent storage
        document_filename = f"{document_id}{file_path.suffix}"
        permanent_document_path = documents_dir / document_filename
        file_path.rename(permanent_document_path)

        # Parse regions from metadata
        regions_data = document.metadata.get("regions", [])

        # Track all embeddings to be stored
        all_embeddings = []
        all_documents = []
        all_metadatas = []

        for region_data in regions_data:
            # Reconstruct SemanticRegion object from dict
            region = SemanticRegion.from_dict(region_data) if isinstance(region_data, dict) else region_data

            # Prepare base metadata for this region
            base_metadata = {
                "source": file_status.name,
                "document_id": document_id,
                "upload_timestamp": upload_timestamp,
                "document_path": str(permanent_document_path),
                "region_id": region.region_id,
                "region_type": region.region_type,
                "region_sequence": region.region_sequence,
                "page_number": region.page_number,
                "extraction_timestamp": region.extraction_timestamp,
                "model": region.model,
            }

            # Add semantic tags if present
            if region.semantic_tags:
                base_metadata["semantic_tags"] = region.semantic_tags

            # Add markdown level for titles
            if region.markdown_level is not None:
                base_metadata["markdown_level"] = region.markdown_level

            # Process based on region type
            if region.region_type in ["text", "title", "list"]:
                # Text region - use text encoder
                text_content = str(region.content)

                config = self._get_embedding_config()
                embedding = self.embedder.embed_with_config([text_content], config)[0]
                embedding_list = embedding.tolist()

                metadata = {
                    **base_metadata,
                    "modality": "text",
                }

                all_embeddings.append(embedding_list)
                all_documents.append(text_content)
                all_metadatas.append(metadata)

            elif region.region_type in ["image"]:
                # Image region - use vision encoder + text description

                # If we have an image description, create a text embedding too
                if region.image_description:
                    # Create text embedding for image description
                    config = self._get_embedding_config()
                    desc_embedding = self.embedder.embed_with_config([region.image_description], config)[0]
                    desc_metadata = {
                        **base_metadata,
                        "modality": "image_description",
                        "image_type": region.image_type,
                    }

                    all_embeddings.append(desc_embedding.tolist())
                    all_documents.append(f"[Image: {region.image_type or 'unknown'}] {region.image_description}")
                    all_metadatas.append(desc_metadata)

                # If region content is a Path to an extracted image, also create vision embedding
                if isinstance(region.content, (str, Path)):
                    image_path = Path(region.content)

                    if image_path.exists():
                        # Save extracted image to organized persistent storage
                        image_filename = f"{document_id}_page{region.page_number}_region{region.region_sequence}_{region.region_type}{image_path.suffix}"
                        permanent_image_path = extracted_images_dir / image_filename

                        # Copy image to permanent storage
                        import shutil
                        shutil.copy2(image_path, permanent_image_path)

                        # Generate thumbnail
                        thumbnail_filename = f"{document_id}_page{region.page_number}_region{region.region_sequence}_thumb.jpg"
                        thumbnail_path = thumbnails_dir / thumbnail_filename
                        self.thumbnail_generator.generate_thumbnail(permanent_image_path, thumbnail_path)

                        # Load PIL Image and generate vision embedding
                        pil_image = Image.open(permanent_image_path)
                        embedding = self.embedder.encode_image(pil_image, task="retrieval")

                        metadata = {
                            **base_metadata,
                            "modality": "image",
                            "image_path": str(permanent_image_path),
                            "thumbnail_path": str(thumbnail_path),
                            "image_description": region.image_description,
                            "image_type": region.image_type,
                        }

                        all_embeddings.append(embedding.tolist())
                        all_documents.append(f"[Image: {region.image_type or 'unknown'}]")
                        all_metadatas.append(metadata)

            elif region.region_type == "table":
                # Table region - use text encoder with both markdown and HTML

                # Prefer table HTML if available, fall back to content
                table_content = region.table_html or str(region.content)

                # Save table structure
                if region.table_rows and region.table_cols:
                    table_filename = f"{document_id}_page{region.page_number}_region{region.region_sequence}_table.json"
                    table_path = tables_dir / table_filename

                    import json
                    table_metadata_file = {
                        "content": table_content,
                        "markdown": str(region.content),
                        "html": region.table_html,
                        "row_count": region.table_rows,
                        "column_count": region.table_cols,
                    }

                    with open(table_path, "w", encoding="utf-8") as f:
                        json.dump(table_metadata_file, f, indent=2, ensure_ascii=False)

                # Use text encoder for table content
                config = self._get_embedding_config()
                embedding = self.embedder.embed_with_config([table_content], config)[0]

                metadata = {
                    **base_metadata,
                    "modality": "table",
                    "table_html": region.table_html,
                }

                if region.table_rows:
                    metadata["table_rows"] = region.table_rows
                if region.table_cols:
                    metadata["table_cols"] = region.table_cols

                all_embeddings.append(embedding.tolist())
                all_documents.append(table_content)
                all_metadatas.append(metadata)

            elif region.region_type == "equation":
                # Equation region - use text encoder with LaTeX
                equation_content = region.equation_latex or str(region.content)

                # Use text encoder for LaTeX content
                config = self._get_embedding_config()
                embedding = self.embedder.embed_with_config([equation_content], config)[0]

                metadata = {
                    **base_metadata,
                    "modality": "equation",
                    "equation_latex": region.equation_latex,
                    "equation_type": region.equation_type,  # inline or display
                }

                all_embeddings.append(embedding.tolist())
                all_documents.append(f"[Equation: {region.equation_type or 'unknown'}] {equation_content}")
                all_metadatas.append(metadata)

        # Save per-document region metadata for debugging and re-processing
        metadata_filename = f"{document_id}_regions.json"
        metadata_path = metadata_dir / metadata_filename

        import json
        # Convert SemanticRegion objects to dictionaries for JSON serialization
        regions_as_dicts = [
            region.to_dict() if isinstance(region, SemanticRegion) else region
            for region in regions_data
        ]

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "document_id": document_id,
                    "source": file_status.name,
                    "upload_timestamp": upload_timestamp,
                    "total_regions": len(regions_data),
                    "regions": regions_as_dicts,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        # Store all region embeddings in vector database
        if all_embeddings:
            self.vector_store.add_embeddings(
                collection_name=task.collection_name,
                embeddings=all_embeddings,
                documents=all_documents,
                metadatas=all_metadatas,
            )

    async def _load_deepseek_document_via_rq(
        self,
        task: IngestionTask,
        file_path: Path,
        file_status: FileStatus,
        file_ext: str,
        document_id: str
    ) -> Any:
        """Load document via RQ distributed queue for large files.

        This method submits the job to an RQ worker and polls for completion.
        Used for very large PDFs/PPTX files that exceed the threshold.

        Args:
            task: Current ingestion task
            file_path: Path to the document file
            file_status: Status tracking for the file
            file_ext: File extension (e.g., ".pdf", ".pptx")
            document_id: Unique document identifier

        Returns:
            Document object loaded via Deepseek OCR on a distributed worker
        """
        if not self.queue_manager:
            raise RuntimeError("RQ queue manager not available")

        logger.info(f"Submitting {file_status.name} to RQ distributed queue")

        # Submit job to RQ based on file type
        if file_ext == ".pdf":
            job = self.queue_manager.submit_pdf_job(
                file_path=file_path,
                document_id=document_id,
                priority="high" if file_path.stat().st_size > 50 * 1024 * 1024 else "default"
            )
        elif file_ext in [".pptx", ".ppt"]:
            job = self.queue_manager.submit_pptx_job(
                file_path=file_path,
                document_id=document_id,
                priority="default"
            )
        else:
            raise ValueError(f"Unsupported file type for RQ: {file_ext}")

        logger.info(f"Job {job.id} submitted for {file_status.name}")

        # Poll job status
        while True:
            job_status = self.queue_manager.get_job_status(job.id)
            status = job_status.get("status")

            if status == "finished":
                logger.info(f"RQ job {job.id} completed successfully")
                result = job_status.get("result")
                if not result:
                    raise RuntimeError(f"RQ job {job.id} returned no result")

                # Load the document from the result (simplified - actual implementation would reconstruct Document object)
                from ..ingestion.deepseek_loader import DeepseekLoader
                ocr_config = self._get_ocr_config()
                loader = DeepseekLoader(config=ocr_config)
                document = loader.load(file_path)
                return document

            elif status == "failed":
                error_msg = job_status.get("exc_info", "Unknown error")
                logger.error(f"RQ job {job.id} failed: {error_msg}")
                raise RuntimeError(f"RQ job failed: {error_msg}")

            elif status in ["queued", "started"]:
                # Send progress update
                progress = job_status.get("progress", 0)
                await task.notify_listeners({
                    "type": "rq_progress",
                    "message": f"Processing via distributed queue: {progress}%",
                    "current_file": file_status.name,
                    "progress_percent": progress,
                    "job_id": job.id,
                })
                await asyncio.sleep(2)  # Poll every 2 seconds

            else:
                # Unknown status, wait and retry
                await asyncio.sleep(2)

    async def _load_deepseek_document_async(
        self,
        task: IngestionTask,
        file_path: Path,
        file_status: FileStatus,
        file_ext: str
    ) -> Any:
        """Load document via Deepseek OCR using thread pool to avoid blocking.

        This method is offloaded to a thread pool executor to keep the event loop
        responsive during heavy PDF rendering and OCR processing. It also reports
        per-page/per-slide progress via the task's listener queue in real-time.

        Args:
            task: Current ingestion task
            file_path: Path to the document file
            file_status: Status tracking for the file
            file_ext: File extension (e.g., ".pdf", ".pptx")

        Returns:
            Document object loaded via Deepseek OCR
        """
        from queue import Queue

        loop = asyncio.get_event_loop()
        progress_queue: Queue = Queue()
        last_notified_page = 0

        def progress_callback(current: int, total: int, message: str):
            """Thread-safe callback for progress updates (runs in thread pool)."""
            progress_queue.put({
                "current": current,
                "total": total,
                "message": message,
                "file": file_status.name,
                "timestamp": time.time(),
            })

        def _load_in_thread():
            from ..ingestion.deepseek_loader import DeepseekLoader
            print(f"[DEBUG THREAD] Starting Deepseek processing for {file_status.name} in thread pool", flush=True)
            print(f"[DEBUG THREAD] File path: {file_path}", flush=True)
            print(f"[DEBUG THREAD] File exists in thread: {file_path.exists()}", flush=True)
            if not file_path.exists():
                print(f"[ERROR THREAD] File not found in thread! Checking parent dir...", flush=True)
                print(f"[ERROR THREAD] Parent dir contents: {list(file_path.parent.iterdir())}", flush=True)
            ocr_config = self._get_ocr_config()
            loader = DeepseekLoader(config=ocr_config)
            print(f"[DEBUG] About to call loader.load() with file: {file_path}", flush=True)
            result = loader.load(
                file_path,
                progress_callback=progress_callback,
                collection_name=task.collection_name,
                resume=False  # Disable checkpoint/resume to fix file not found issue
            )
            print(f"[DEBUG] loader.load() completed successfully", flush=True)
            return result

        # Start the blocking load operation in the thread pool
        load_future = loop.run_in_executor(self._executor, _load_in_thread)

        # Poll progress queue while document is loading
        logger.info(f"Monitoring Deepseek progress for {file_status.name}")
        while not load_future.done():
            try:
                # Check for progress updates (non-blocking)
                while True:
                    try:
                        update = progress_queue.get_nowait()
                        current = update["current"]
                        total = update["total"]

                        # Send progress update if it's for a new page/slide
                        if current > last_notified_page:
                            last_notified_page = current
                            doc_type = "page" if file_ext == ".pdf" else "slide"
                            await task.notify_listeners({
                                "type": "page_progress",
                                "message": f"Processing {doc_type} {current}/{total}: {update['message']}",
                                "current_file": file_status.name,
                                "page_number": current,
                                "total_pages": total,
                                "progress_percent": (current / total * 100) if total > 0 else 0,
                            })
                            logger.debug(f"{file_status.name}: {update['message']} ({current}/{total})")
                    except:
                        # Queue is empty
                        break

                # Brief sleep to avoid busy-waiting
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                logger.warning(f"Progress monitoring cancelled for {file_status.name}")
                raise

        # Get the completed document
        document = await load_future

        # Report final completion with page/slide counts
        page_count = document.metadata.get("page_count")
        slide_count = document.metadata.get("slide_count")

        if page_count:
            logger.info(f"Deepseek completed for {file_status.name}: {page_count} pages extracted")
            await task.notify_listeners({
                "type": "progress_detail",
                "message": f"✓ Deepseek OCR completed: {page_count} pages extracted from {file_status.name}",
                "current_file": file_status.name,
                "pages_processed": page_count,
            })
        elif slide_count:
            logger.info(f"Deepseek completed for {file_status.name}: {slide_count} slides extracted")
            await task.notify_listeners({
                "type": "progress_detail",
                "message": f"✓ Deepseek OCR completed: {slide_count} slides extracted from {file_status.name}",
                "current_file": file_status.name,
                "slides_processed": slide_count,
            })

        return document

    def start_task(self, task_id: str) -> None:
        if task_id not in self._processing_tasks:
            task_coro = self.process_task(task_id)
            self._processing_tasks[task_id] = asyncio.create_task(task_coro)

    async def cleanup_completed_tasks(self, max_age_seconds: int = 3600) -> None:
        to_remove = []
        for task_id, task in self.tasks.items():
            if task.status in [IngestionStatus.COMPLETED, IngestionStatus.FAILED]:
                to_remove.append(task_id)

        for task_id in to_remove:
            self.tasks.pop(task_id, None)
            self._processing_tasks.pop(task_id, None)
