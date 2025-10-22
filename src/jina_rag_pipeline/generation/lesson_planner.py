"""Lesson plan generator integrating retrieval and LLM generation."""

import logging
import re
from typing import Optional, List, Dict, Any
from dataclasses import asdict

from ..models.educational import (
    LessonPlan,
    LessonMetadata,
    RetrievedMaterial,
    ImageReference,
    DEFAULT_DURATION,
)
from ..retrieval.educational import EducationalRetriever
from .qwen_generator import QwenGenerator
from .educational_prompts import (
    LESSON_SYSTEM_PROMPT,
    format_lesson_prompt,
)

logger = logging.getLogger(__name__)


class LessonGenerationError(Exception):
    """Error during lesson generation."""
    pass


class LessonPlanner:
    """
    Generate lesson plans using RAG + LLM.

    Integrates EducationalRetriever for content and QwenGenerator for
    lesson plan creation with proper citations and images.
    """

    def __init__(
        self,
        retriever: EducationalRetriever,
        generator: QwenGenerator,
        text_top_k: int = 5,
        image_top_k: int = 3,
    ):
        """
        Initialize lesson planner.

        Args:
            retriever: EducationalRetriever for fetching materials
            generator: QwenGenerator for LLM-based generation
            text_top_k: Number of text materials to retrieve (default: 5)
            image_top_k: Number of images to retrieve (default: 3)
        """
        self.retriever = retriever
        self.generator = generator
        self.text_top_k = text_top_k
        self.image_top_k = image_top_k

    async def generate_lesson(
        self,
        topic: str,
        learning_objective: str,
        grade: str,
        subject: str,
        duration: int = DEFAULT_DURATION,
        teaching_style: str = "balanced",
    ) -> LessonPlan:
        """
        Generate a complete lesson plan with citations and images.

        Args:
            topic: Lesson topic
            learning_objective: Learning objective
            grade: Grade level (abbreviated: "K", "3", "6-8", etc.)
            subject: Subject area
            duration: Duration in minutes (default: 50)
            teaching_style: Teaching style ("balanced", "direct", "inquiry", "project")

        Returns:
            LessonPlan with markdown content, sources, and images

        Raises:
            LessonGenerationError: If generation fails
        """
        logger.info(
            f"Generating lesson: topic='{topic}', grade={grade}, subject={subject}, "
            f"duration={duration}min, style={teaching_style}"
        )

        try:
            # Step 1: Retrieve relevant materials
            logger.info("Retrieving materials...")
            materials = self.retriever.retrieve_combined(
                topic=topic,
                grade=grade,
                subject=subject,
                text_top_k=self.text_top_k,
                image_top_k=self.image_top_k,
            )

            text_materials = materials["text"]
            image_materials = materials["images"]

            logger.info(
                f"Retrieved {len(text_materials)} text materials, "
                f"{len(image_materials)} images"
            )

            if not text_materials:
                raise LessonGenerationError(
                    "No relevant materials found. Please ensure educational content "
                    "has been uploaded to the system."
                )

            # Step 2: Format prompt with numbered sources
            logger.info("Formatting prompt with numbered sources...")
            user_prompt = format_lesson_prompt(
                topic=topic,
                learning_objective=learning_objective,
                grade=grade,
                subject=subject,
                duration=duration,
                teaching_style=teaching_style,
                text_materials=text_materials,
                image_materials=image_materials,
            )

            # Step 3: Generate lesson with LLM
            logger.info("Calling LLM to generate lesson...")
            messages = [
                {"role": "system", "content": LESSON_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            # Stream and collect response
            markdown_content = await self._generate_complete_response(messages)

            logger.info(f"Generated {len(markdown_content)} characters of markdown")

            # Step 4: Parse and validate output
            logger.info("Parsing and validating output...")
            lesson_plan = self._parse_lesson_output(
                markdown_content=markdown_content,
                text_materials=text_materials,
                image_materials=image_materials,
                topic=topic,
                grade=grade,
                subject=subject,
                duration=duration,
                teaching_style=teaching_style,
            )

            logger.info(
                f"Lesson generated successfully: {lesson_plan.sources_count} sources, "
                f"{lesson_plan.images_count} images"
            )

            return lesson_plan

        except Exception as e:
            logger.error(f"Lesson generation failed: {e}", exc_info=True)
            raise LessonGenerationError(f"Failed to generate lesson: {e}") from e

    async def _generate_complete_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate complete response by consuming stream.

        Args:
            messages: Chat messages
            max_tokens: Maximum tokens to generate

        Returns:
            Complete generated text
        """
        tokens = []
        async for token in self.generator.generate_stream(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,  # Slightly creative but focused
        ):
            tokens.append(token)

        return "".join(tokens)

    def _parse_lesson_output(
        self,
        markdown_content: str,
        text_materials: List[RetrievedMaterial],
        image_materials: List[RetrievedMaterial],
        topic: str,
        grade: str,
        subject: str,
        duration: int,
        teaching_style: str,
    ) -> LessonPlan:
        """
        Parse LLM output into LessonPlan object.

        Extracts YAML frontmatter, validates citations, and builds
        source reference list.

        Args:
            markdown_content: Generated markdown from LLM
            text_materials: Retrieved text materials
            image_materials: Retrieved image materials
            topic: Lesson topic
            grade: Grade level
            subject: Subject area
            duration: Duration in minutes
            teaching_style: Teaching style

        Returns:
            Parsed and validated LessonPlan

        Raises:
            LessonGenerationError: If parsing fails
        """
        # Extract YAML frontmatter if present
        frontmatter_match = re.match(
            r'^---\s*\n(.*?)\n---\s*\n(.*)$',
            markdown_content,
            re.DOTALL
        )

        if frontmatter_match:
            frontmatter_yaml = frontmatter_match.group(1)
            content_without_frontmatter = frontmatter_match.group(2)

            # Parse title from frontmatter (simple regex parsing)
            title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', frontmatter_yaml, re.MULTILINE)
            title = title_match.group(1).strip('"\'') if title_match else topic
        else:
            # No frontmatter, use content as-is
            content_without_frontmatter = markdown_content
            title = topic

        # Create metadata
        metadata = LessonMetadata(
            title=title,
            grade=grade,
            subject=subject,
            duration=duration,
            teaching_style=teaching_style,
        )

        # Add YAML frontmatter to content if not present
        if not frontmatter_match:
            markdown_with_frontmatter = (
                metadata.to_yaml_frontmatter() + "\n\n" + markdown_content
            )
        else:
            # Replace existing frontmatter with our metadata
            markdown_with_frontmatter = (
                metadata.to_yaml_frontmatter() + "\n\n" + content_without_frontmatter
            )

        # Extract image references from markdown
        images = self._extract_image_references(
            markdown_content=markdown_with_frontmatter,
            image_materials=image_materials,
        )

        # Create lesson plan
        lesson_plan = LessonPlan(
            metadata=metadata,
            markdown_content=markdown_with_frontmatter,
            sources=text_materials + image_materials,
            images=images,
        )

        # Validate citations are present
        self._validate_citations(markdown_with_frontmatter, text_materials, image_materials)

        return lesson_plan

    def _extract_image_references(
        self,
        markdown_content: str,
        image_materials: List[RetrievedMaterial],
    ) -> List[ImageReference]:
        """
        Extract image references from markdown.

        Looks for markdown image syntax: ![alt](path)
        And captions: *Figure N: caption [Source: [IMG-N]]*

        Args:
            markdown_content: Markdown content with images
            image_materials: Retrieved image materials

        Returns:
            List of ImageReference objects
        """
        images = []

        # Pattern: ![alt](path)\n*Figure N: caption [Source: [IMG-N]]*
        # More relaxed pattern to handle variations
        image_pattern = re.compile(
            r'!\[([^\]]*)\]\(([^)]+)\)\s*\*?(?:Figure\s+(\d+):?\s*)?([^\[]*?)(?:\[Source:\s*\[IMG-(\d+)\]\])?\*?',
            re.MULTILINE
        )

        for match in image_pattern.finditer(markdown_content):
            alt_text = match.group(1) or "Image"
            path = match.group(2)
            figure_number = match.group(3)
            caption = match.group(4).strip() if match.group(4) else alt_text
            source_num = match.group(5)

            # Determine source citation number
            if source_num:
                citation_num = int(source_num)
            else:
                # No explicit source, try to infer from position
                citation_num = len(images) + 1

            images.append(
                ImageReference(
                    path=path,
                    alt_text=alt_text,
                    caption=caption,
                    source_citation=citation_num,
                    figure_number=f"Figure {figure_number}" if figure_number else None,
                )
            )

        logger.info(f"Extracted {len(images)} image references from markdown")
        return images

    def _validate_citations(
        self,
        markdown_content: str,
        text_materials: List[RetrievedMaterial],
        image_materials: List[RetrievedMaterial],
    ) -> None:
        """
        Validate that citations are present in the lesson.

        Logs warnings if citations are missing but does not fail generation.

        Args:
            markdown_content: Markdown content to check
            text_materials: Text materials (should be cited)
            image_materials: Image materials (should be cited)
        """
        # Check for text citations [1], [2], [3]...
        text_citations_found = []
        for i in range(1, len(text_materials) + 1):
            if f"[{i}]" in markdown_content:
                text_citations_found.append(i)

        # Check for image citations [IMG-1], [IMG-2]...
        image_citations_found = []
        for i in range(1, len(image_materials) + 1):
            if f"[IMG-{i}]" in markdown_content or f"![" in markdown_content:
                image_citations_found.append(i)

        # Log warnings for missing citations
        missing_text = set(range(1, len(text_materials) + 1)) - set(text_citations_found)
        missing_images = set(range(1, len(image_materials) + 1)) - set(image_citations_found)

        if missing_text:
            logger.warning(
                f"Some text sources not cited: {missing_text}. "
                f"Total text sources: {len(text_materials)}, "
                f"Citations found: {len(text_citations_found)}"
            )

        if missing_images and image_materials:
            logger.warning(
                f"Some images not cited: {missing_images}. "
                f"Total images: {len(image_materials)}, "
                f"Citations found: {len(image_citations_found)}"
            )

        # Check if "Sources Referenced" section exists
        if "## Sources Referenced" not in markdown_content and "# Sources Referenced" not in markdown_content:
            logger.warning("No 'Sources Referenced' section found in generated lesson")
        else:
            logger.info("'Sources Referenced' section found in lesson")
