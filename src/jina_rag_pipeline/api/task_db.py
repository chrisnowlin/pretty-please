"""SQLite-based task persistence for crash recovery and server restart resilience.

Provides persistent storage for ingestion tasks, allowing them to survive
server restarts and crashes.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TaskDatabase:
    """SQLite database for task persistence.

    Features:
    - WAL mode for concurrent access
    - Automatic schema initialization
    - Task expiration and cleanup
    - File-level progress tracking
    """

    def __init__(self, db_path: Path = Path("./tasks.db")):
        """Initialize task database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
        logger.info(f"Task database initialized: {db_path}")

    def _init_database(self):
        """Initialize database schema with tables and indexes."""
        with self._get_connection() as conn:
            # Enable WAL mode for concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")

            # Tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    collection_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0,
                    total_files INTEGER DEFAULT 0,
                    processed_files INTEGER DEFAULT 0,
                    current_file TEXT,
                    errors TEXT,  -- JSON array of errors
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Task files table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    status TEXT NOT NULL,
                    size INTEGER,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                )
            """)

            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status
                ON tasks(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_collection
                ON tasks(collection_name)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_updated
                ON tasks(updated_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_files_task
                ON task_files(task_id)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_task(
        self,
        task_id: str,
        collection_name: str,
        files: List[Dict[str, Any]]
    ) -> None:
        """Create a new task in the database.

        Args:
            task_id: Unique task identifier
            collection_name: Name of target collection
            files: List of file information dicts
        """
        with self._get_connection() as conn:
            # Insert task
            conn.execute("""
                INSERT INTO tasks (
                    task_id, collection_name, status, total_files
                ) VALUES (?, ?, ?, ?)
            """, (task_id, collection_name, "queued", len(files)))

            # Insert files
            for file_info in files:
                conn.execute("""
                    INSERT INTO task_files (
                        task_id, filename, status, size
                    ) VALUES (?, ?, ?, ?)
                """, (
                    task_id,
                    file_info.get("name"),
                    file_info.get("status", "pending"),
                    file_info.get("size", 0)
                ))

            conn.commit()
            logger.info(f"Created task in database: {task_id} ({len(files)} files)")

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        current_file: Optional[str] = None,
        processed_files: Optional[int] = None,
        errors: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """Update task status and progress.

        Args:
            task_id: Task identifier
            status: New status
            progress: Progress percentage (0-100)
            current_file: Currently processing file
            processed_files: Number of processed files
            errors: List of error dicts
        """
        with self._get_connection() as conn:
            updates = ["updated_at = CURRENT_TIMESTAMP"]
            params = []

            if status is not None:
                updates.append("status = ?")
                params.append(status)

            if progress is not None:
                updates.append("progress = ?")
                params.append(progress)

            if current_file is not None:
                updates.append("current_file = ?")
                params.append(current_file)

            if processed_files is not None:
                updates.append("processed_files = ?")
                params.append(processed_files)

            if errors is not None:
                updates.append("errors = ?")
                params.append(json.dumps(errors))

            params.append(task_id)

            conn.execute(f"""
                UPDATE tasks
                SET {', '.join(updates)}
                WHERE task_id = ?
            """, params)

            conn.commit()

    def update_file_status(
        self,
        task_id: str,
        filename: str,
        status: str,
        error: Optional[str] = None
    ) -> None:
        """Update status of a specific file.

        Args:
            task_id: Task identifier
            filename: Name of file
            status: New status
            error: Error message if failed
        """
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE task_files
                SET status = ?, error = ?, updated_at = CURRENT_TIMESTAMP
                WHERE task_id = ? AND filename = ?
            """, (status, error, task_id, filename))

            conn.commit()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task information.

        Args:
            task_id: Task identifier

        Returns:
            Task dict or None if not found
        """
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM tasks WHERE task_id = ?
            """, (task_id,)).fetchone()

            if not row:
                return None

            task = dict(row)

            # Parse errors JSON
            if task.get("errors"):
                try:
                    task["errors"] = json.loads(task["errors"])
                except json.JSONDecodeError:
                    task["errors"] = []
            else:
                task["errors"] = []

            return task

    def get_task_files(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all files for a task.

        Args:
            task_id: Task identifier

        Returns:
            List of file dicts
        """
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM task_files
                WHERE task_id = ?
                ORDER BY id
            """, (task_id,)).fetchall()

            return [dict(row) for row in rows]

    def list_tasks(
        self,
        status: Optional[str] = None,
        collection_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filters.

        Args:
            status: Filter by status
            collection_name: Filter by collection
            limit: Maximum number of tasks to return

        Returns:
            List of task dicts
        """
        with self._get_connection() as conn:
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if collection_name:
                query += " AND collection_name = ?"
                params.append(collection_name)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()

            tasks = []
            for row in rows:
                task = dict(row)
                if task.get("errors"):
                    try:
                        task["errors"] = json.loads(task["errors"])
                    except json.JSONDecodeError:
                        task["errors"] = []
                else:
                    task["errors"] = []
                tasks.append(task)

            return tasks

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active (non-completed) tasks.

        Returns:
            List of active task dicts
        """
        return self.list_tasks(status="processing")

    def delete_task(self, task_id: str) -> None:
        """Delete a task and its files.

        Args:
            task_id: Task identifier
        """
        with self._get_connection() as conn:
            conn.execute("DELETE FROM task_files WHERE task_id = ?", (task_id,))
            conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            conn.commit()
            logger.info(f"Deleted task from database: {task_id}")

    def cleanup_old_tasks(self, days: int = 7) -> int:
        """Delete tasks older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of tasks deleted
        """
        cutoff = datetime.now() - timedelta(days=days)

        with self._get_connection() as conn:
            # Get tasks to delete
            rows = conn.execute("""
                SELECT task_id FROM tasks
                WHERE status IN ('completed', 'failed')
                AND updated_at < ?
            """, (cutoff.isoformat(),)).fetchall()

            task_ids = [row[0] for row in rows]

            if task_ids:
                placeholders = ','.join('?' * len(task_ids))
                conn.execute(
                    f"DELETE FROM task_files WHERE task_id IN ({placeholders})",
                    task_ids
                )
                conn.execute(
                    f"DELETE FROM tasks WHERE task_id IN ({placeholders})",
                    task_ids
                )
                conn.commit()

                logger.info(f"Cleaned up {len(task_ids)} old tasks")

            return len(task_ids)

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dict with statistics
        """
        with self._get_connection() as conn:
            stats = {}

            # Task counts by status
            rows = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM tasks
                GROUP BY status
            """).fetchall()

            stats["tasks_by_status"] = {row[0]: row[1] for row in rows}

            # Total tasks
            stats["total_tasks"] = conn.execute(
                "SELECT COUNT(*) FROM tasks"
            ).fetchone()[0]

            # Total files
            stats["total_files"] = conn.execute(
                "SELECT COUNT(*) FROM task_files"
            ).fetchone()[0]

            # Active tasks (last 24 hours)
            cutoff = (datetime.now() - timedelta(days=1)).isoformat()
            stats["active_last_24h"] = conn.execute("""
                SELECT COUNT(*) FROM tasks
                WHERE updated_at > ?
            """, (cutoff,)).fetchone()[0]

            # Database size
            stats["db_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)

            return stats
