#!/usr/bin/env python3
"""RQ worker startup script.

This script starts RQ workers that process jobs from the queues.
Workers can be started on the same machine or on separate machines.

Usage:
    # Start worker for all queues
    python worker.py

    # Start worker for specific queues
    python worker.py --queues high default

    # Start worker with custom name
    python worker.py --name worker-01

    # Start worker with burst mode (exit when queues are empty)
    python worker.py --burst
"""

import argparse
import logging
import sys
from pathlib import Path

from redis import Redis
from rq import Worker, Queue

from .config import RQConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def start_worker(
    queue_names: list[str],
    worker_name: str | None = None,
    burst: bool = False,
):
    """Start an RQ worker.

    Args:
        queue_names: List of queue names to process
        worker_name: Optional worker name for identification
        burst: If True, worker exits when queues are empty
    """
    logger.info(f"Starting RQ worker for queues: {', '.join(queue_names)}")

    # Connect to Redis
    try:
        redis_conn = Redis.from_url(RQConfig.REDIS_URL)
        redis_conn.ping()
        logger.info(f"Connected to Redis at {RQConfig.REDIS_URL}")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)

    # Create queues
    queues = [Queue(name, connection=redis_conn) for name in queue_names]

    # Create and start worker
    worker = Worker(
        queues,
        connection=redis_conn,
        name=worker_name,
    )

    logger.info(f"Worker '{worker.name}' started")
    logger.info(f"Processing queues (in order): {', '.join(queue_names)}")

    try:
        worker.work(burst=burst, with_scheduler=True)
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
    finally:
        logger.info("Worker shutting down")


def main():
    """Parse arguments and start worker."""
    parser = argparse.ArgumentParser(description="Start RQ worker for distributed processing")
    parser.add_argument(
        "--queues",
        nargs="+",
        default=RQConfig.ALL_QUEUES,
        help=f"Queues to process (default: {', '.join(RQConfig.ALL_QUEUES)})"
    )
    parser.add_argument(
        "--name",
        help="Worker name for identification"
    )
    parser.add_argument(
        "--burst",
        action="store_true",
        help="Exit when all queues are empty (useful for testing)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    start_worker(
        queue_names=args.queues,
        worker_name=args.name,
        burst=args.burst,
    )


if __name__ == "__main__":
    main()
