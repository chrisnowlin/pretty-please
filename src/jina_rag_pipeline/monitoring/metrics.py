"""Metrics collection and tracking for monitoring system performance."""

import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional
import psutil


@dataclass
class ProcessingMetric:
    """Single processing event metric."""
    file_name: str
    file_size_mb: float
    file_type: str
    processing_method: str  # "threadpool", "rq", "traditional"
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    page_count: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class SystemMetrics:
    """System-level metrics snapshot."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    active_tasks: int
    queued_tasks: int


class MetricsCollector:
    """Collects and aggregates processing metrics for monitoring."""

    def __init__(self, max_history: int = 1000):
        """Initialize metrics collector.

        Args:
            max_history: Maximum number of processing events to retain in memory
        """
        self.max_history = max_history
        self._lock = threading.Lock()

        # Processing metrics
        self._processing_events: Deque[ProcessingMetric] = deque(maxlen=max_history)
        self._active_processing: Dict[str, ProcessingMetric] = {}

        # Counters
        self._total_processed = 0
        self._total_failed = 0
        self._total_bytes_processed = 0

        # Performance tracking
        self._processing_times_by_method: Dict[str, List[float]] = defaultdict(list)
        self._processing_times_by_type: Dict[str, List[float]] = defaultdict(list)

        # System metrics history
        self._system_snapshots: Deque[SystemMetrics] = deque(maxlen=100)

    def start_processing(
        self,
        task_id: str,
        file_name: str,
        file_size_mb: float,
        file_type: str,
        processing_method: str
    ) -> None:
        """Record the start of a processing event.

        Args:
            task_id: Unique task identifier
            file_name: Name of the file being processed
            file_size_mb: File size in megabytes
            file_type: File extension (e.g., ".pdf", ".pptx")
            processing_method: Processing method ("threadpool", "rq", "traditional")
        """
        with self._lock:
            metric = ProcessingMetric(
                file_name=file_name,
                file_size_mb=file_size_mb,
                file_type=file_type,
                processing_method=processing_method,
                start_time=time.time()
            )
            self._active_processing[task_id] = metric

    def end_processing(
        self,
        task_id: str,
        success: bool = True,
        error: Optional[str] = None,
        page_count: Optional[int] = None
    ) -> None:
        """Record the end of a processing event.

        Args:
            task_id: Unique task identifier
            success: Whether processing succeeded
            error: Error message if failed
            page_count: Number of pages/slides processed
        """
        with self._lock:
            if task_id not in self._active_processing:
                return

            metric = self._active_processing.pop(task_id)
            metric.end_time = time.time()
            metric.duration_seconds = metric.end_time - metric.start_time
            metric.success = success
            metric.error = error
            metric.page_count = page_count

            # Store completed metric
            self._processing_events.append(metric)

            # Update counters
            if success:
                self._total_processed += 1
                self._total_bytes_processed += int(metric.file_size_mb * 1024 * 1024)

                # Track performance by method and type
                if metric.duration_seconds:
                    self._processing_times_by_method[metric.processing_method].append(
                        metric.duration_seconds
                    )
                    self._processing_times_by_type[metric.file_type].append(
                        metric.duration_seconds
                    )
            else:
                self._total_failed += 1

    def capture_system_snapshot(self, active_tasks: int = 0, queued_tasks: int = 0) -> None:
        """Capture current system metrics snapshot.

        Args:
            active_tasks: Number of currently active tasks
            queued_tasks: Number of queued tasks
        """
        memory = psutil.virtual_memory()

        snapshot = SystemMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            active_tasks=active_tasks,
            queued_tasks=queued_tasks
        )

        with self._lock:
            self._system_snapshots.append(snapshot)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all processing events."""
        with self._lock:
            recent_events = list(self._processing_events)
            active_count = len(self._active_processing)

        if not recent_events:
            return {
                "total_processed": self._total_processed,
                "total_failed": self._total_failed,
                "active_processing": active_count,
                "total_bytes_processed": self._total_bytes_processed,
                "average_processing_time_seconds": 0,
                "success_rate_percent": 0,
            }

        # Calculate averages
        successful_events = [e for e in recent_events if e.success and e.duration_seconds]
        avg_time = (
            sum(e.duration_seconds for e in successful_events) / len(successful_events)
            if successful_events else 0
        )

        success_count = sum(1 for e in recent_events if e.success)
        success_rate = (success_count / len(recent_events) * 100) if recent_events else 0

        return {
            "total_processed": self._total_processed,
            "total_failed": self._total_failed,
            "active_processing": active_count,
            "total_bytes_processed": self._total_bytes_processed,
            "average_processing_time_seconds": round(avg_time, 2),
            "success_rate_percent": round(success_rate, 2),
            "recent_events_count": len(recent_events),
        }

    def get_performance_by_method(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics grouped by processing method."""
        with self._lock:
            stats = {}
            for method, times in self._processing_times_by_method.items():
                if times:
                    stats[method] = {
                        "count": len(times),
                        "average_seconds": round(sum(times) / len(times), 2),
                        "min_seconds": round(min(times), 2),
                        "max_seconds": round(max(times), 2),
                    }
            return stats

    def get_performance_by_file_type(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics grouped by file type."""
        with self._lock:
            stats = {}
            for file_type, times in self._processing_times_by_type.items():
                if times:
                    stats[file_type] = {
                        "count": len(times),
                        "average_seconds": round(sum(times) / len(times), 2),
                        "min_seconds": round(min(times), 2),
                        "max_seconds": round(max(times), 2),
                    }
            return stats

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent processing events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events as dictionaries
        """
        with self._lock:
            events = list(self._processing_events)[-limit:]

        return [
            {
                "file_name": e.file_name,
                "file_size_mb": round(e.file_size_mb, 2),
                "file_type": e.file_type,
                "processing_method": e.processing_method,
                "duration_seconds": round(e.duration_seconds, 2) if e.duration_seconds else None,
                "page_count": e.page_count,
                "success": e.success,
                "error": e.error,
                "timestamp": datetime.fromtimestamp(e.start_time, tz=timezone.utc).isoformat(),
            }
            for e in events
        ]

    def get_system_metrics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent system metrics snapshots.

        Args:
            limit: Maximum number of snapshots to return

        Returns:
            List of system metrics as dictionaries
        """
        with self._lock:
            snapshots = list(self._system_snapshots)[-limit:]

        return [
            {
                "timestamp": s.timestamp,
                "cpu_percent": round(s.cpu_percent, 2),
                "memory_percent": round(s.memory_percent, 2),
                "memory_used_mb": round(s.memory_used_mb, 2),
                "memory_available_mb": round(s.memory_available_mb, 2),
                "active_tasks": s.active_tasks,
                "queued_tasks": s.queued_tasks,
            }
            for s in snapshots
        ]

    def get_rq_stats(self) -> Optional[Dict[str, Any]]:
        """Get RQ queue statistics if available."""
        try:
            from ..workers.queue import JobQueueManager
            from ..workers.config import RQConfig

            if not RQConfig.DISTRIBUTED_PROCESSING_ENABLED:
                return None

            manager = JobQueueManager()
            return manager.get_queue_stats()
        except Exception:
            return None

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics including all categories."""
        return {
            "summary": self.get_summary_stats(),
            "performance_by_method": self.get_performance_by_method(),
            "performance_by_file_type": self.get_performance_by_file_type(),
            "recent_events": self.get_recent_events(limit=20),
            "system_metrics": self.get_system_metrics(limit=10),
            "rq_queues": self.get_rq_stats(),
        }


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
