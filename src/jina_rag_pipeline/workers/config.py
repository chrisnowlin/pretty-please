"""Configuration for RQ (Redis Queue) distributed workers.

This module provides configuration for distributed task processing using RQ.
RQ is a simple job queue for Python that uses Redis as a message broker.

Features:
- Job queueing and execution
- Multiple worker support
- Job status tracking
- Failed job recovery
"""

import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RQConfig:
    """Configuration for RQ distributed worker system."""

    # Redis connection settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Queue settings
    DEFAULT_QUEUE: str = "default"
    HIGH_PRIORITY_QUEUE: str = "high"
    LOW_PRIORITY_QUEUE: str = "low"

    # All queues for monitoring
    ALL_QUEUES = [DEFAULT_QUEUE, HIGH_PRIORITY_QUEUE, LOW_PRIORITY_QUEUE]

    # Job settings
    DEFAULT_JOB_TIMEOUT: int = 3600  # 1 hour
    LARGE_FILE_JOB_TIMEOUT: int = 7200  # 2 hours
    DEFAULT_RESULT_TTL: int = 500  # Result stored for 500 seconds
    DEFAULT_FAILURE_TTL: int = 86400  # Failed job info stored for 1 day

    # Worker settings
    DEFAULT_WORKERS: int = int(os.getenv("RQ_WORKERS", "2"))

    # Enable/disable distributed processing
    DISTRIBUTED_PROCESSING_ENABLED: bool = (
        os.getenv("DISTRIBUTED_PROCESSING_ENABLED", "false").lower() in ("true", "1", "yes")
    )

    # File size threshold for distributed processing (MB)
    LARGE_FILE_THRESHOLD_MB: float = float(os.getenv("LARGE_FILE_THRESHOLD_MB", "10.0"))

    # Job retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 60  # seconds

    # Monitoring
    ENABLE_JOB_MONITORING: bool = (
        os.getenv("ENABLE_JOB_MONITORING", "true").lower() in ("true", "1", "yes")
    )


class JobConfig:
    """Configuration for individual job execution."""

    # Job type routing
    JOB_TYPE_DEEPSEEK_PDF = "deepseek_pdf"
    JOB_TYPE_DEEPSEEK_PPTX = "deepseek_pptx"
    JOB_TYPE_PROCESS_CHUNKS = "process_chunks"
    JOB_TYPE_PROCESS_REGIONS = "process_regions"

    # Priority levels
    PRIORITY_HIGH = 10
    PRIORITY_NORMAL = 5
    PRIORITY_LOW = 1

    @staticmethod
    def get_job_queue(file_size_mb: float) -> str:
        """Determine which queue a job should go to based on file size.

        Args:
            file_size_mb: File size in megabytes

        Returns:
            Queue name (high, default, or low)
        """
        if file_size_mb > 50:  # Large files
            return RQConfig.HIGH_PRIORITY_QUEUE
        elif file_size_mb > 10:  # Medium files
            return RQConfig.DEFAULT_QUEUE
        else:  # Small files
            return RQConfig.LOW_PRIORITY_QUEUE

    @staticmethod
    def get_job_timeout(file_size_mb: float) -> int:
        """Determine job timeout based on file size.

        Args:
            file_size_mb: File size in megabytes

        Returns:
            Timeout in seconds
        """
        if file_size_mb > 50:
            return RQConfig.LARGE_FILE_JOB_TIMEOUT
        else:
            return RQConfig.DEFAULT_JOB_TIMEOUT


def get_redis_connection():
    """Get Redis connection using configured settings.

    Returns:
        Redis connection object

    Raises:
        ImportError: If redis-py is not installed
        ConnectionError: If Redis server is unreachable
    """
    try:
        import redis
    except ImportError:
        raise ImportError(
            "redis-py is required for distributed processing. "
            "Install with: pip install redis"
        )

    try:
        conn = redis.Redis(
            host=RQConfig.REDIS_HOST,
            port=RQConfig.REDIS_PORT,
            db=RQConfig.REDIS_DB,
            decode_responses=True,
        )
        # Test connection
        conn.ping()
        logger.info(f"Connected to Redis at {RQConfig.REDIS_HOST}:{RQConfig.REDIS_PORT}")
        return conn
    except Exception as e:
        raise ConnectionError(
            f"Failed to connect to Redis: {e}"
        )
