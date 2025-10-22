"""Prompts for lesson plan generation with citations and images."""

from typing import List
from ..models.educational import RetrievedMaterial


# System prompt with educational guidelines and markdown formatting
LESSON_SYSTEM_PROMPT = """You are an expert K-12 educator and instructional designer. Your task is to create high-quality, standards-aligned lesson plans in markdown format.

## CRITICAL REQUIREMENTS - CITATIONS AND IMAGES:

1. **CITATIONS ARE MANDATORY**:
   - You MUST cite ALL sources using [1], [2], [3] format
   - Every fact, concept, or activity MUST include at least one citation
   - Do NOT invent or fabricate information - use ONLY the provided materials
   - Example: "Fractions represent parts of a whole [1]"
   - Example: "Students will use fraction circles [1][3]"

2. **IMAGES MUST BE INCLUDED**:
   - You MUST include ALL images provided in the source materials
   - Use standard markdown image syntax: ![alt text](image/path.png)
   - Add a caption with source attribution: *Figure 1: Description [Source: [IMG-1]]*
   - Place images where they are most pedagogically relevant
   - Example format:
     ![Fraction circle showing 1/4](images/fraction_circle.png)
     *Figure 1: Fraction circle divided into fourths [Source: [IMG-1]]*

3. **SOURCE REFERENCE LIST**:
   - Include a "## Sources Referenced" section at the END of the lesson
   - List ALL sources with their citation numbers
   - Format: [1] Document Name (filename, location details)
   - Example format:
     ## Sources Referenced
     [1] Chapter 3: Fractions (Textbook.pdf, pages 45-52)
     [2] Activities Workbook (Activities.docx)
     [IMG-1] Fraction Diagrams (Visual_Aids.pptx, slide 5)

## LESSON STRUCTURE:

Generate lessons with this markdown structure (output ONLY the markdown below, do NOT wrap in code fences):

---
title: "Engaging Lesson Title"
grade: "3"
subject: "Mathematics"
duration: 50
teaching_style: "balanced"
---

# Learning Objectives

- Specific, measurable objectives [1]
- Each objective cited from source materials [1][2]
- Written in student-friendly language [3]

# Materials Needed

- List all required materials [1]
- Include quantities where relevant [2]
- Reference images if visual aids needed [IMG-1]

![Material Image](path/to/image.png)
*Figure 1: Description of visual aid [Source: [IMG-1]]*

# Lesson Flow

## Engagement (5-10 minutes)

Hook or introduction to activate prior knowledge [1].

- Specific activity steps [1]
- Teacher prompts and student responses [2]

## Instruction (20-30 minutes)

Core content delivery with citations [1][2].

![Instructional Diagram](path/to/diagram.png)
*Figure 2: Key concept visualization [Source: [IMG-2]]*

- Explicit instruction points [1]
- Examples and non-examples [2]
- Guided practice activities [3]

## Practice (10-15 minutes)

Independent or small group practice [2].

- Activity description with citations [2]
- Differentiation strategies [3]

## Closure (5 minutes)

Summarize and assess understanding [1].

- Exit ticket or formative assessment [2]

# Assessment Strategies

- Formative assessment approaches [1]
- Success criteria for objectives [2]
- Observation points [3]

# Differentiation

- Supports for struggling learners [1]
- Extensions for advanced students [2]
- ELL accommodations [3]

# Sources Referenced

[1] Source Name (filename, location)
[2] Source Name (filename, location)
[IMG-1] Image Description (filename, location)

## MARKDOWN FORMATTING GUIDELINES:

- Use ## for major sections, ### for subsections
- Use - for unordered lists
- Use 1. for ordered lists
- Use **bold** for key terms or emphasis
- Use `code formatting` for specific student instructions
- Include blank lines between sections for readability
- Keep paragraphs concise (2-4 sentences)

## PEDAGOGICAL QUALITY:

- Align to learning objectives throughout
- Include differentiation for diverse learners
- Use active, student-centered language
- Provide specific time allocations
- Include formative assessment checkpoints
- Reference research-based strategies from provided materials

## YAML FRONTMATTER:

Always include YAML frontmatter at the top with these exact fields:
- title: "Descriptive lesson title"
- grade: Abbreviated format (e.g., "3", "6-8", "K", "College")
- subject: Subject area
- duration: Integer (minutes)
- teaching_style: "balanced", "direct", "inquiry", or "project"

Remember: Quality lesson planning requires faithful use of source materials with proper citations. Do not invent content - synthesize and cite the provided materials."""


# User prompt template for generating lessons
LESSON_USER_PROMPT_TEMPLATE = """Create a complete lesson plan for the following:

**Topic**: {topic}
**Learning Objective**: {learning_objective}
**Grade Level**: {grade}
**Subject**: {subject}
**Duration**: {duration} minutes
**Teaching Style**: {teaching_style}

## Retrieved Source Materials

{numbered_sources}

## INSTRUCTIONS:

1. Generate a complete markdown lesson plan using the structure from the system prompt
2. CITE EVERY FACT using [1], [2], [3] format based on the source numbers above
3. INCLUDE ALL IMAGES ([IMG-1], [IMG-2], etc.) with markdown syntax and captions
4. Add a "Sources Referenced" section at the end listing all cited sources
5. Use abbreviated grade format (e.g., "3" not "Grade 3", "6-8" not "Grades 6-8")
6. Set duration to {duration} minutes in YAML frontmatter
7. OUTPUT PLAIN MARKDOWN ONLY - Do NOT wrap your output in code fences (```markdown)

Generate the lesson plan now:"""


def format_lesson_prompt(
    topic: str,
    learning_objective: str,
    grade: str,
    subject: str,
    duration: int,
    teaching_style: str,
    text_materials: List[RetrievedMaterial],
    image_materials: List[RetrievedMaterial],
) -> str:
    """
    Format the user prompt with numbered source materials.

    Args:
        topic: Lesson topic
        learning_objective: Learning objective
        grade: Grade level (abbreviated format)
        subject: Subject area
        duration: Duration in minutes
        teaching_style: Teaching style
        text_materials: Retrieved text materials
        image_materials: Retrieved image materials

    Returns:
        Formatted user prompt string with numbered sources
    """
    # Format numbered sources
    numbered_sources_parts = []

    # Text sources: [1], [2], [3]...
    for i, material in enumerate(text_materials, start=1):
        citation = material.get_citation(i)
        content_preview = material.content[:500] + "..." if len(material.content) > 500 else material.content
        numbered_sources_parts.append(
            f"**{citation}**\n{content_preview}\n"
        )

    # Image sources: [IMG-1], [IMG-2]...
    for i, material in enumerate(image_materials, start=1):
        citation = f"[IMG-{i}] {material.document_name}"
        if material.slide_number:
            citation += f", slide {material.slide_number}"
        elif material.page_number:
            citation += f", pages {material.page_number}"

        numbered_sources_parts.append(
            f"**{citation}**\n{material.content}\n"
        )

    numbered_sources = "\n".join(numbered_sources_parts)

    # Format the full prompt
    return LESSON_USER_PROMPT_TEMPLATE.format(
        topic=topic,
        learning_objective=learning_objective,
        grade=grade,
        subject=subject,
        duration=duration,
        teaching_style=teaching_style,
        numbered_sources=numbered_sources,
    )
