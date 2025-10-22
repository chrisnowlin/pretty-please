"""Educational data models for lesson plan generation."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class RetrievedMaterial:
    """
    Material retrieved from the RAG system for lesson planning.

    Attributes:
        content: The text or description of the material
        document_name: Name of the source document
        page_number: Page number in source document (if applicable)
        chunk_id: Unique identifier for the chunk in ChromaDB
        relevance_score: Similarity score from retrieval (0.0-1.0)
        source_type: Type of material ("text", "image", "table")
        slide_number: Slide number for presentation files (if applicable)
    """
    content: str
    document_name: str
    chunk_id: str
    relevance_score: float
    source_type: str  # "text", "image", "table"
    page_number: Optional[int] = None
    slide_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def get_citation(self, citation_number: int) -> str:
        """
        Generate citation string for this material.

        Args:
            citation_number: The number to use for citation (e.g., [1], [2])

        Returns:
            Formatted citation string
        """
        location = ""
        if self.page_number:
            location = f", pages {self.page_number}"
        elif self.slide_number:
            location = f", slide {self.slide_number}"

        return f"[{citation_number}] {self.document_name}{location}"


@dataclass
class ImageReference:
    """
    Reference to an image included in a lesson plan.

    Attributes:
        path: Relative path to the image file
        alt_text: Alt text description for accessibility
        caption: Caption to display under the image
        source_citation: Citation number for the source document
        figure_number: Figure number in the lesson (e.g., "Figure 1")
    """
    path: str
    alt_text: str
    caption: str
    source_citation: int
    figure_number: Optional[str] = None

    def to_markdown(self) -> str:
        """
        Generate markdown representation of the image.

        Returns:
            Markdown string with image and caption
        """
        md = f"![{self.alt_text}]({self.path})\n"
        if self.caption:
            md += f"*{self.figure_number or 'Figure'}: {self.caption} [Source: [{self.source_citation}]]*"
        return md

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class LessonMetadata:
    """
    Metadata for a lesson plan.

    Attributes:
        title: Lesson title
        grade: Grade level (abbreviated: "K", "1", "3-5", "6-8", etc.)
        subject: Subject area (Math, Science, ELA, etc.)
        duration: Lesson duration in minutes (default: 50)
        teaching_style: Teaching approach ("balanced", "direct", "inquiry", "project")
        generated_at: Timestamp when lesson was generated
        generated_by_model: Name of the LLM model used
    """
    title: str
    grade: str
    subject: str
    duration: int = 50
    teaching_style: str = "balanced"
    generated_at: Optional[str] = None
    generated_by_model: str = "Qwen3-14B-4bit"

    def __post_init__(self):
        """Set generated_at timestamp if not provided."""
        if self.generated_at is None:
            self.generated_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def to_yaml_frontmatter(self) -> str:
        """
        Generate YAML frontmatter for markdown lesson.

        Returns:
            YAML frontmatter block
        """
        return f"""---
title: "{self.title}"
grade: "{self.grade}"
subject: "{self.subject}"
duration: {self.duration}
teaching_style: "{self.teaching_style}"
generated: "{self.generated_at}"
---"""


@dataclass
class LessonPlan:
    """
    Complete lesson plan with all components.

    Attributes:
        metadata: Lesson metadata (title, grade, subject, etc.)
        markdown_content: Full lesson content in markdown format
        sources: List of source materials used (with citations)
        images: List of images included in the lesson
        sources_count: Number of unique sources cited
        images_count: Number of images included
    """
    metadata: LessonMetadata
    markdown_content: str
    sources: List[RetrievedMaterial] = field(default_factory=list)
    images: List[ImageReference] = field(default_factory=list)

    @property
    def sources_count(self) -> int:
        """Get count of unique source materials."""
        return len(self.sources)

    @property
    def images_count(self) -> int:
        """Get count of images in lesson."""
        return len(self.images)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for API responses.

        Returns:
            Dictionary representation
        """
        return {
            "metadata": self.metadata.to_dict(),
            "markdown_content": self.markdown_content,
            "sources": [source.to_dict() for source in self.sources],
            "images": [img.to_dict() for img in self.images],
            "sources_count": self.sources_count,
            "images_count": self.images_count,
        }

    def to_full_markdown(self) -> str:
        """
        Get complete markdown with frontmatter.

        Returns:
            Full markdown document
        """
        return f"{self.metadata.to_yaml_frontmatter()}\n\n{self.markdown_content}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LessonPlan":
        """
        Create LessonPlan from dictionary.

        Args:
            data: Dictionary with lesson plan data

        Returns:
            LessonPlan instance
        """
        metadata = LessonMetadata(**data["metadata"])
        sources = [RetrievedMaterial(**s) for s in data.get("sources", [])]
        images = [ImageReference(**i) for i in data.get("images", [])]

        return cls(
            metadata=metadata,
            markdown_content=data["markdown_content"],
            sources=sources,
            images=images,
        )


@dataclass
class RetrievalContext:
    """
    Context passed to the lesson generator with retrieved materials.

    Attributes:
        topic: Lesson topic
        learning_objective: Learning objective for the lesson
        grade: Target grade level
        subject: Subject area
        duration: Lesson duration in minutes
        teaching_style: Teaching approach
        text_materials: Retrieved text materials (top-5)
        image_materials: Retrieved images (top-3)
    """
    topic: str
    learning_objective: str
    grade: str
    subject: str
    duration: int
    teaching_style: str
    text_materials: List[RetrievedMaterial] = field(default_factory=list)
    image_materials: List[RetrievedMaterial] = field(default_factory=list)

    @property
    def all_materials(self) -> List[RetrievedMaterial]:
        """Get all materials (text + images) combined."""
        return self.text_materials + self.image_materials

    def get_numbered_sources(self) -> str:
        """
        Format materials as numbered sources for prompt context.

        Returns:
            Formatted string with numbered sources
        """
        lines = []

        # Number text sources
        for i, material in enumerate(self.text_materials, start=1):
            location = ""
            if material.page_number:
                location = f", pages {material.page_number}"
            elif material.slide_number:
                location = f", slide {material.slide_number}"

            lines.append(f"[{i}] {material.document_name}{location}")
            lines.append(f"    Content: {material.content[:200]}...")  # First 200 chars
            lines.append("")

        # Number image sources
        for i, material in enumerate(self.image_materials, start=1):
            location = ""
            if material.page_number:
                location = f", page {material.page_number}"
            elif material.slide_number:
                location = f", slide {material.slide_number}"

            lines.append(f"[IMG-{i}] {material.document_name}{location}")
            lines.append(f"    Description: {material.content}")
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "topic": self.topic,
            "learning_objective": self.learning_objective,
            "grade": self.grade,
            "subject": self.subject,
            "duration": self.duration,
            "teaching_style": self.teaching_style,
            "text_materials": [m.to_dict() for m in self.text_materials],
            "image_materials": [m.to_dict() for m in self.image_materials],
        }


# Constants for validation
VALID_GRADE_LEVELS = [
    "PreK", "K",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
    "K-2", "3-5", "6-8", "9-12",
    "College"
]

VALID_SUBJECTS = [
    "Mathematics", "Science", "English Language Arts", "Social Studies",
    "Arts & Design", "Physical Education", "World Languages", "Technology",
    "Career & Technical Education", "Other"
]

VALID_TEACHING_STYLES = ["balanced", "direct", "inquiry", "project"]

MIN_DURATION = 20
MAX_DURATION = 90
DEFAULT_DURATION = 50
