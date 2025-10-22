"""
SQLAlchemy models for Phase 3: Simple lesson persistence (single-user app).
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Index,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Lesson(Base):
    """Lesson model for storing generated lesson plans."""

    __tablename__ = "lessons"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Lesson identification
    lesson_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID from generation

    # Lesson content
    title = Column(String(500), nullable=False, index=True)
    markdown_content = Column(Text, nullable=False)

    # Educational metadata
    grade = Column(String(50), nullable=False, index=True)
    subject = Column(String(100), nullable=False, index=True)
    topic = Column(String(500), nullable=False)
    learning_objective = Column(Text, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    teaching_style = Column(String(50), nullable=False)

    # Additional metadata as JSON
    metadata_json = Column(JSON, nullable=True)

    # Statistics
    sources_count = Column(Integer, default=0)
    images_count = Column(Integer, default=0)
    generation_time_seconds = Column(Integer, nullable=True)

    # Flags
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes for common queries
    __table_args__ = (
        Index('ix_lessons_grade_subject', 'grade', 'subject'),
        Index('ix_lessons_favorite', 'is_favorite', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<Lesson(id={self.id}, title='{self.title}', grade='{self.grade}', subject='{self.subject}')>"
