"""Semantic region representation for document layout analysis.

This module defines the SemanticRegion dataclass for representing semantic
content regions extracted from document layout analysis. Unlike spatial regions
(bounding boxes), semantic regions focus on content understanding and structured
extraction.

With Deepseek-OCR integration, regions can now include optional spatial grounding
via BoundingBox coordinates.
"""

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional, List, Union, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import json


@dataclass
class BoundingBox:
    """Normalized bounding box for spatial grounding.

    All coordinates are normalized to [0, 1] range relative to page dimensions.
    Origin (0, 0) is top-left corner, (1, 1) is bottom-right.

    Attributes:
        x_min: Left boundary (0-1)
        y_min: Top boundary (0-1)
        x_max: Right boundary (0-1)
        y_max: Bottom boundary (0-1)
        confidence: Optional confidence score (0-1)

    Example:
        >>> bbox = BoundingBox(x_min=0.1, y_min=0.2, x_max=0.9, y_max=0.8)
        >>> bbox.area()
        0.48
        >>> bbox.contains(BoundingBox(0.2, 0.3, 0.8, 0.7))
        True
    """

    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: Optional[float] = None

    def __post_init__(self):
        """Validate bounding box coordinates."""
        if not (0 <= self.x_min <= 1 and 0 <= self.x_max <= 1):
            raise ValueError(f"x coordinates must be in [0, 1]: x_min={self.x_min}, x_max={self.x_max}")
        if not (0 <= self.y_min <= 1 and 0 <= self.y_max <= 1):
            raise ValueError(f"y coordinates must be in [0, 1]: y_min={self.y_min}, y_max={self.y_max}")
        if self.x_min >= self.x_max:
            raise ValueError(f"x_min must be < x_max: {self.x_min} >= {self.x_max}")
        if self.y_min >= self.y_max:
            raise ValueError(f"y_min must be < y_max: {self.y_min} >= {self.y_max}")
        if self.confidence is not None and not (0 <= self.confidence <= 1):
            raise ValueError(f"confidence must be in [0, 1]: {self.confidence}")

    def area(self) -> float:
        """Calculate normalized area (0-1)."""
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)

    def width(self) -> float:
        """Calculate normalized width (0-1)."""
        return self.x_max - self.x_min

    def height(self) -> float:
        """Calculate normalized height (0-1)."""
        return self.y_max - self.y_min

    def center(self) -> tuple[float, float]:
        """Calculate center point (x, y)."""
        return (
            (self.x_min + self.x_max) / 2,
            (self.y_min + self.y_max) / 2
        )

    def iou(self, other: 'BoundingBox') -> float:
        """Calculate Intersection over Union with another bounding box.

        Args:
            other: Another BoundingBox

        Returns:
            IoU score (0-1), where 1 is perfect overlap
        """
        # Calculate intersection
        x_min_inter = max(self.x_min, other.x_min)
        y_min_inter = max(self.y_min, other.y_min)
        x_max_inter = min(self.x_max, other.x_max)
        y_max_inter = min(self.y_max, other.y_max)

        # Check if boxes overlap
        if x_min_inter >= x_max_inter or y_min_inter >= y_max_inter:
            return 0.0

        intersection_area = (x_max_inter - x_min_inter) * (y_max_inter - y_min_inter)
        union_area = self.area() + other.area() - intersection_area

        return intersection_area / union_area if union_area > 0 else 0.0

    def contains(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box fully contains another.

        Args:
            other: Another BoundingBox

        Returns:
            True if other is fully contained within this box
        """
        return (
            self.x_min <= other.x_min and
            self.y_min <= other.y_min and
            self.x_max >= other.x_max and
            self.y_max >= other.y_max
        )

    def overlaps(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box overlaps with another.

        Args:
            other: Another BoundingBox

        Returns:
            True if boxes overlap
        """
        return not (
            self.x_max <= other.x_min or
            other.x_max <= self.x_min or
            self.y_max <= other.y_min or
            other.y_max <= self.y_min
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'x_min': self.x_min,
            'y_min': self.y_min,
            'x_max': self.x_max,
            'y_max': self.y_max,
            'confidence': self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoundingBox':
        """Create from dictionary (deserialization)."""
        return cls(**data)


@dataclass
class SemanticRegion:
    """Represents a semantic region extracted from document layout analysis.

    Unlike spatial regions (bounding boxes), semantic regions focus on content
    understanding and structured extraction.

    With Deepseek-OCR integration, regions can optionally include spatial grounding
    via the bbox field.

    Attributes:
        region_id: Unique identifier for this region
        region_type: Type of content (text, table, image, equation, list, title)
        region_sequence: Order of region in document (0-indexed)
        page_number: Source page number (1-indexed)
        content: Main content (text string or Path to image)
        raw_markdown: Original markdown representation
        semantic_tags: Content classification tags (e.g., "financial", "technical")
        markdown_level: Heading level if applicable (1-6 for H1-H6)
        bbox: Optional spatial bounding box (for Deepseek grounding)
        table_html: HTML representation for tables
        table_rows: Number of rows for tables
        table_cols: Number of columns for tables
        image_description: Generated description for images
        image_type: Classification for images (chart, logo, diagram, photo)
        equation_latex: LaTeX representation for equations
        equation_type: Inline or display equation
        extraction_timestamp: When region was extracted
        model: Model used for extraction (default: "deepseek-ocr")
    """

    region_id: str
    region_type: Literal["text", "table", "image", "equation", "list", "title"]
    region_sequence: int
    page_number: int
    content: Union[str, Path]
    raw_markdown: str

    # Optional semantic metadata
    semantic_tags: List[str] = field(default_factory=list)
    markdown_level: Optional[int] = None

    # Spatial grounding (Deepseek-OCR)
    bbox: Optional[BoundingBox] = None

    # Table-specific fields
    table_html: Optional[str] = None
    table_rows: Optional[int] = None
    table_cols: Optional[int] = None

    # Image-specific fields
    image_description: Optional[str] = None
    image_type: Optional[Literal["chart", "logo", "diagram", "photo", "unknown"]] = None

    # Equation-specific fields
    equation_latex: Optional[str] = None
    equation_type: Optional[Literal["inline", "display"]] = None

    # Metadata
    extraction_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model: str = "deepseek-ocr"  # Can be overridden by PaddleOCR
    detected_language: Optional[str] = None
    chart_type: Optional[str] = None
    confidence_score: Optional[float] = None
    bounding_box: Optional[Tuple[int, int, int, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert Path to string
        content_value = data.get("content")
        if isinstance(content_value, Path):
            data["content"] = str(content_value)
        # Convert BoundingBox to dict (asdict handles this, but be explicit)
        if data.get('bbox') is not None and isinstance(data['bbox'], BoundingBox):
            data['bbox'] = data['bbox']  # Already converted by asdict

        # Remove None values for compact storage while preserving falsy values like 0 or ""
        return {key: value for key, value in data.items() if value is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticRegion':
        """Create from dictionary (deserialization)."""
        # Convert string paths back to Path objects if needed
        if 'content' in data and isinstance(data['content'], str):
            # Check if it looks like a file path
            if data['content'].startswith('/') or data['content'].startswith('./'):
                data['content'] = Path(data['content'])

        # Convert bbox dict back to BoundingBox object
        if 'bbox' in data and data['bbox'] is not None and isinstance(data['bbox'], dict):
            data['bbox'] = BoundingBox.from_dict(data['bbox'])

        # Handle bounding_box field from PaddleOCR
        if 'bounding_box' in data and isinstance(data['bounding_box'], list):
            bbox = data['bounding_box']
            if len(bbox) == 4:
                data['bounding_box'] = tuple(int(v) for v in bbox)

        return cls(**data)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'SemanticRegion':
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
