"""Session management for chat conversations."""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import ImageMetadata
from ..generation.config import GenerationConfig


@dataclass
class Session:
    """Chat session with conversation history and image tracking."""

    session_id: str
    collection_name: str
    config: GenerationConfig
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    image_references: Dict[str, ImageMetadata] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        self.last_accessed = datetime.now(timezone.utc)

    def track_image(self, document_id: str, metadata: ImageMetadata) -> None:
        """Track an image reference for this session."""
        self.image_references[document_id] = metadata
        self.last_accessed = datetime.now(timezone.utc)

    def get_recent_history(self, max_turns: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history (last N turns)."""
        # Each turn = user + assistant message, so max_messages = max_turns * 2
        max_messages = max_turns * 2
        return self.conversation_history[-max_messages:]

    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "collection_name": self.collection_name,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "message_count": len(self.conversation_history),
            "image_references_count": len(self.image_references),
        }


class SessionManager:
    """Manage chat sessions with TTL-based cleanup."""

    def __init__(self, default_ttl: int = 1800):
        """
        Initialize session manager.

        Args:
            default_ttl: Session TTL in seconds (default 30 minutes)
        """
        self.sessions: Dict[str, Session] = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup expired sessions."""
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            await self.cleanup_expired_sessions()

    def create_session(
        self, collection_name: str, config: Optional[GenerationConfig] = None
    ) -> Session:
        """
        Create a new chat session.

        Args:
            collection_name: Name of collection to query
            config: Generation configuration

        Returns:
            Created session
        """
        session_id = str(uuid.uuid4())
        config = config or GenerationConfig()

        session = Session(
            session_id=session_id, collection_name=collection_name, config=config
        )

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found, None otherwise
        """
        session = self.sessions.get(session_id)
        if session:
            session.last_accessed = datetime.now(timezone.utc)
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def track_image_reference(
        self, session_id: str, document_id: str, metadata: ImageMetadata
    ) -> None:
        """
        Track an image reference in a session.

        Args:
            session_id: Session identifier
            document_id: Image document ID
            metadata: Image metadata
        """
        session = self.get_session(session_id)
        if session:
            session.track_image(document_id, metadata)

    def get_image_references(self, session_id: str) -> Dict[str, ImageMetadata]:
        """
        Get all image references for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dict mapping document_id to ImageMetadata
        """
        session = self.get_session(session_id)
        return session.image_references if session else {}

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions based on TTL.

        Returns:
            Number of sessions cleaned up
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            expired = []

            for session_id, session in self.sessions.items():
                age = (now - session.last_accessed).total_seconds()
                if age > self.default_ttl:
                    expired.append(session_id)

            for session_id in expired:
                del self.sessions[session_id]

            if expired:
                print(f"Cleaned up {len(expired)} expired sessions")

            return len(expired)

    def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        return len(self.sessions)

    def get_all_sessions(self) -> List[Dict]:
        """Get info for all active sessions."""
        return [session.to_dict() for session in self.sessions.values()]
