"""Job queue manager for distributed RQ workers."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry

from .config import RQConfig
from .tasks import process_pdf, process_pptx, process_chunks

logger = logging.getLogger(__name__)


class JobQueueManager:
    """Manages RQ job queues for distributed processing."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize queue manager with Redis connection."""
        self.redis_url = redis_url or RQConfig.REDIS_URL
        self.redis_conn = Redis.from_url(self.redis_url)

        # Create queues with priority levels
        self.high_queue = Queue(RQConfig.HIGH_PRIORITY_QUEUE, connection=self.redis_conn)
        self.default_queue = Queue(RQConfig.DEFAULT_QUEUE, connection=self.redis_conn)
        self.low_queue = Queue(RQConfig.LOW_PRIORITY_QUEUE, connection=self.redis_conn)

        logger.info(f"JobQueueManager initialized with Redis at {self.redis_url}")

    def submit_pdf_job(
        self,
        file_path: Path,
        document_id: str,
        priority: str = "default",
        batch_size: int = 5,
        timeout: Optional[int] = None,
    ) -> Job:
        """Submit PDF processing job to queue."""
        queue = self._get_queue(priority)
        timeout = timeout or RQConfig.LARGE_FILE_JOB_TIMEOUT

        job = queue.enqueue(
            process_pdf,
            str(file_path),
            document_id,
            batch_size=batch_size,
            job_timeout=timeout,
            result_ttl=3600,  # Keep results for 1 hour
            meta={
                "file_path": str(file_path),
                "document_id": document_id,
                "file_type": "pdf",
            }
        )

        logger.info(f"Submitted PDF job {job.id} for document {document_id}")
        return job

    def submit_pptx_job(
        self,
        file_path: Path,
        document_id: str,
        priority: str = "default",
        timeout: Optional[int] = None,
    ) -> Job:
        """Submit PowerPoint processing job to queue."""
        queue = self._get_queue(priority)
        timeout = timeout or RQConfig.DEFAULT_JOB_TIMEOUT

        job = queue.enqueue(
            process_pptx,
            str(file_path),
            document_id,
            job_timeout=timeout,
            result_ttl=3600,
            meta={
                "file_path": str(file_path),
                "document_id": document_id,
                "file_type": "pptx",
            }
        )

        logger.info(f"Submitted PPTX job {job.id} for document {document_id}")
        return job

    def submit_chunk_processing_job(
        self,
        chunks: List[str],
        document_id: str,
        priority: str = "low",
        timeout: Optional[int] = None,
    ) -> Job:
        """Submit chunk processing job to queue."""
        queue = self._get_queue(priority)
        timeout = timeout or RQConfig.DEFAULT_JOB_TIMEOUT

        job = queue.enqueue(
            process_chunks,
            chunks,
            document_id,
            job_timeout=timeout,
            result_ttl=3600,
            meta={
                "document_id": document_id,
                "chunk_count": len(chunks),
                "job_type": "chunks",
            }
        )

        logger.info(f"Submitted chunk processing job {job.id} for document {document_id}")
        return job

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status and metadata for a job."""
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)

            return {
                "job_id": job.id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "result": job.result,
                "exc_info": job.exc_info,
                "meta": job.meta,
                "progress": job.meta.get("progress", 0),
            }
        except Exception as e:
            logger.error(f"Error fetching job {job_id}: {e}")
            return {
                "job_id": job_id,
                "status": "not_found",
                "error": str(e),
            }

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued or running job."""
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            job.cancel()
            logger.info(f"Cancelled job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics for all queues."""
        stats = {}

        for queue_name, queue in [
            ("high", self.high_queue),
            ("default", self.default_queue),
            ("low", self.low_queue),
        ]:
            stats[queue_name] = {
                "queued": len(queue),
                "started": len(StartedJobRegistry(queue=queue)),
                "finished": len(FinishedJobRegistry(queue=queue)),
                "failed": len(FailedJobRegistry(queue=queue)),
            }

        return stats

    def _get_queue(self, priority: str) -> Queue:
        """Get queue by priority level."""
        if priority == "high":
            return self.high_queue
        elif priority == "low":
            return self.low_queue
        else:
            return self.default_queue

    def should_use_distributed_queue(self, file_size_mb: float, file_ext: str) -> bool:
        """Determine if file should be processed via distributed queue."""
        if not RQConfig.DISTRIBUTED_PROCESSING_ENABLED:
            return False

        # Use distributed queue for large PDFs/PPTX
        if file_ext in [".pdf", ".pptx"]:
            return file_size_mb > RQConfig.LARGE_FILE_THRESHOLD_MB

        return False
