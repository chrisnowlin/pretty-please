"""Administrative API endpoints for profiles, checkpoints, and system management."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from ..config import get_profile, get_profile_summary, PROFILES, auto_detect_profile
from ..ingestion import CheckpointManager
from .task_db import TaskDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Initialize managers
checkpoint_manager = CheckpointManager()
task_db = TaskDatabase()


@router.get("/profile")
async def get_current_profile():
    """Get current processing profile information."""
    try:
        profile = get_profile()

        return {
            "name": profile.name,
            "description": profile.description,
            "configuration": {
                "render_batch_size": profile.render_batch_size,
                "embedding_batch_size": profile.embedding_batch_size,
                "max_render_workers": profile.max_render_workers,
                "max_analysis_workers": profile.max_analysis_workers,
                "max_memory_gb": profile.max_memory_gb,
                "memory_target_gb": profile.memory_target_gb,
                "pre_render_batches": profile.pre_render_batches,
                "checkpoint_interval_pages": profile.checkpoint_interval_pages,
                "aggressive_mode": profile.aggressive_mode,
            },
            "summary": get_profile_summary(profile)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles")
async def list_profiles():
    """List all available processing profiles."""
    return {
        "profiles": {
            name: {
                "name": profile.name,
                "description": profile.description,
                "render_batch_size": profile.render_batch_size,
                "max_render_workers": profile.max_render_workers,
                "max_analysis_workers": profile.max_analysis_workers,
                "max_memory_gb": profile.max_memory_gb,
                "aggressive_mode": profile.aggressive_mode,
            }
            for name, profile in PROFILES.items()
        },
        "current": auto_detect_profile()
    }


@router.get("/checkpoints")
async def list_checkpoints(
    collection_name: Optional[str] = Query(None, description="Filter by collection")
):
    """List all active checkpoints."""
    try:
        checkpoints = checkpoint_manager.list_checkpoints(collection_name)
        return {
            "checkpoints": checkpoints,
            "count": len(checkpoints)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/checkpoints/{checkpoint_id}")
async def delete_checkpoint(checkpoint_id: str):
    """Delete a specific checkpoint."""
    try:
        # Parse checkpoint_id to get collection and file_hash
        parts = checkpoint_id.split("_", 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid checkpoint_id format")

        collection_name, file_hash = parts

        checkpoint_path = (
            checkpoint_manager.base_dir / collection_name / file_hash / "checkpoint.json"
        )

        if not checkpoint_path.exists():
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        checkpoint_path.unlink()
        logger.info(f"Deleted checkpoint: {checkpoint_id}")

        return {"message": f"Checkpoint {checkpoint_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checkpoints/cleanup")
async def cleanup_expired_checkpoints():
    """Clean up expired checkpoints."""
    try:
        cleaned = checkpoint_manager.cleanup_expired()
        return {
            "message": f"Cleaned up {cleaned} expired checkpoints",
            "cleaned_count": cleaned
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    collection_name: Optional[str] = Query(None, description="Filter by collection"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum tasks to return")
):
    """List tasks from persistent storage."""
    try:
        tasks = task_db.list_tasks(
            status=status,
            collection_name=collection_name,
            limit=limit
        )
        return {
            "tasks": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str):
    """Get detailed information about a specific task."""
    try:
        task = task_db.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        files = task_db.get_task_files(task_id)

        return {
            "task": task,
            "files": files
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task from persistent storage."""
    try:
        task = task_db.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task_db.delete_task(task_id)

        return {"message": f"Task {task_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/cleanup")
async def cleanup_old_tasks(
    days: int = Query(7, ge=1, le=365, description="Delete tasks older than this many days")
):
    """Clean up old completed/failed tasks."""
    try:
        cleaned = task_db.cleanup_old_tasks(days=days)
        return {
            "message": f"Cleaned up {cleaned} old tasks",
            "cleaned_count": cleaned
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_system_statistics():
    """Get system statistics and health information."""
    try:
        import psutil
        from pathlib import Path

        # Memory stats
        mem = psutil.virtual_memory()

        # Task database stats
        db_stats = task_db.get_statistics()

        # Checkpoint stats
        checkpoints = checkpoint_manager.list_checkpoints()

        # Disk usage
        checkpoint_dir_size = sum(
            f.stat().st_size
            for f in checkpoint_manager.base_dir.rglob("*")
            if f.is_file()
        ) / (1024 * 1024)  # MB

        return {
            "memory": {
                "total_gb": mem.total / (1024**3),
                "available_gb": mem.available / (1024**3),
                "used_gb": mem.used / (1024**3),
                "percent": mem.percent
            },
            "tasks": db_stats,
            "checkpoints": {
                "active_count": len(checkpoints),
                "disk_usage_mb": checkpoint_dir_size
            },
            "profile": {
                "current": get_profile().name,
                "aggressive_mode": get_profile().aggressive_mode
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
