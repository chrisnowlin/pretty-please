# Design: Lesson Plan Generation via RAG

**Change ID**: `lesson-plan-rag-integration`
**Date**: 2025-10-18

## Architectural Overview

The lesson plan generation system layers educational domain knowledge on top of the existing Jina RAG foundation. Rather than building a separate system, we extend the current architecture with specialized components.

### Core Philosophy
- **Reuse, don't rebuild**: The embeddings, storage, and async infrastructure are already proven and stable
- **Domain specialization**: Add educational-specific layers (ingestion parsers, retrieval logic, generation prompts)
- **Separation of concerns**: Keep educational logic separate from generic RAG logic
- **Progressive enhancement**: Add capabilities incrementally without breaking existing chat functionality

## Component Design

### 1. Educational Content Ingestion Layer

**Purpose**: Parse, structure, and index educational content (standards, curricula, activities)

**Design Decision**: Extend the existing ingestion pipeline rather than create a separate one

```python
# New module: src/jina_rag_pipeline/ingestion/educational/
├── standards_parser.py      # Parse Common Core, state standards, IB, AP formats
├── curriculum_parser.py     # Parse district curricula, textbooks
├── metadata_extractor.py    # Extract grade levels, subjects, learning objectives
└── educational_chunker.py   # Smart chunking for educational content
```

**Key Features**:
1. **Standards Parsing**:
   - Input: Standards document (PDF, JSON, XML)
   - Extract: Standards hierarchy (domain → cluster → standard), grade bands
   - Output: Structured records with metadata (code, grade level, subject)

2. **Curriculum Chunking**:
   - Don't chunk by fixed token count (loses semantic meaning)
   - Chunk by educational units: lesson, learning objective, activity
   - Preserve hierarchical relationships in metadata
   - Example chunks: "Grade 3 Math: Multi-digit addition (CCSS.Math.3.NBT.A.2)"

3. **Metadata Extraction**:
   - Grade level (K, 1-2, 3-5, 6-8, 9-10, 11-12, college, etc.)
   - Subject (Math, Science, ELA, Social Studies, Arts, etc.)
   - Topic/learning domain
   - Content type (standard, activity, assessment, resource)
   - Estimated time to teach
   - Prerequisites and connections

### 2. Educational Retrieval Engine

**Purpose**: Retrieve standards-aligned, grade-appropriate materials

**Design Decision**: Create specialized retrieval that combines semantic similarity + metadata filtering

```python
# New module: src/jina_rag_pipeline/retrieval/educational.py
class EducationalRetriever:
    """Retrieves content aligned to learning objectives and standards."""

    async def retrieve_by_objective(
        self,
        objective: str,  # e.g., "Students will understand photosynthesis"
        grade_level: str,
        subject: str,
        top_k: int = 10,
    ) -> List[RetrievalResult]:
        """
        Semantic search + metadata filtering + standards alignment scoring.
        Returns materials ranked by relevance and alignment.
        """
```

**Retrieval Strategy**:
1. **Semantic Query Expansion**:
   - Input: Learning objective
   - Expand: Add related terminology, synonyms, related concepts
   - Example: "photosynthesis" → ["photosynthesis", "plant energy", "light reactions", "Calvin cycle"]
   - Use Qwen3 to intelligently expand if needed

2. **Multi-Factor Ranking**:
   ```
   Final Score =
       0.4 × semantic_similarity +
       0.3 × standards_alignment +
       0.2 × grade_level_match +
       0.1 × content_type_relevance
   ```

3. **Filtering Logic**:
   - Filter by grade level (allow ±1 grade band)
   - Filter by subject match
   - Exclude low-confidence alignments
   - Sort by combined relevance score

### 3. Lesson Template Engine

**Purpose**: Generate structured lesson plans from retrieved materials

**Design Decision**: Template-based generation with structured output (JSON)

```python
# New module: src/jina_rag_pipeline/generation/lesson_planner.py
class LessonPlanner:
    """Generates structured lesson plans from retrieved educational materials."""

    async def generate_lesson(
        self,
        learning_objective: str,
        grade_level: str,
        duration_minutes: int,
        teaching_style: str = "balanced",  # direct, inquiry, project, balanced
        customizations: Dict[str, Any] = None,
    ) -> LessonPlan:
        """
        Generate complete lesson plan as structured JSON.
        """
```

**Lesson Plan Structure** (JSON):
```json
{
  "metadata": {
    "title": "Understanding Photosynthesis",
    "grade_level": "3-5",
    "subject": "Science",
    "duration_minutes": 45,
    "aligned_standards": ["CCSS.Science.3-5.LS1.A", "...]
  },
  "learning_objectives": [
    {
      "objective": "Students will...",
      "verbs": ["understand", "identify"],
      "aligned_standard": "CCSS.Science..."
    }
  ],
  "materials_and_resources": [
    {
      "name": "Plant diagram",
      "type": "visual",
      "source": "retrieved_document_1"
    }
  ],
  "lesson_flow": [
    {
      "phase": "engagement",
      "duration_minutes": 5,
      "activities": ["Hook question: Why do plants need light?"]
    },
    {
      "phase": "direct_instruction",
      "duration_minutes": 10,
      "activities": ["Explain photosynthesis process", "Show diagram"]
    },
    {
      "phase": "practice",
      "duration_minutes": 20,
      "activities": ["Label diagram activity", "Think-pair-share discussion"]
    },
    {
      "phase": "closure",
      "duration_minutes": 5,
      "activities": ["Reflection: What did you learn?"]
    }
  ],
  "assessments": [
    {
      "type": "formative",
      "timing": "during_practice",
      "method": "Observation checklist"
    },
    {
      "type": "summative",
      "timing": "closure",
      "method": "Exit ticket with 3 questions"
    }
  ],
  "differentiation": [
    {
      "student_group": "advanced",
      "modifications": ["Research cellular respiration connection"]
    },
    {
      "student_group": "struggling",
      "modifications": ["Simplified diagram with labels"]
    }
  ]
}
```

### 4. Customization & Refinement Module

**Purpose**: Allow teachers to adjust generated lessons

**Design Decision**: Modular regeneration of individual components

```python
# New module: src/jina_rag_pipeline/generation/lesson_customizer.py
class LessonCustomizer:
    """Allows targeted customization and regeneration of lesson components."""

    async def customize_lesson(
        self,
        lesson: LessonPlan,
        customization_request: CustomizationRequest,
    ) -> LessonPlan:
        """
        Regenerate specific components based on teacher preferences.
        Examples: adjust duration, change teaching style, add differentiation.
        """

    async def regenerate_component(
        self,
        lesson: LessonPlan,
        component: str,  # "activities", "assessments", "differentiation"
        constraint: Dict[str, Any],  # e.g., {"duration_minutes": 30}
    ) -> Any:
        """
        Regenerate a single component while keeping others fixed.
        """
```

**Customization Options**:
1. **Duration**: Compress/expand lesson to fit available time
2. **Teaching Style**: Switch between direct instruction, inquiry, project-based
3. **Grade Level Adjustment**: Simplify or advance content
4. **Assessment Type**: Formative, summative, performance-based, multiple choice
5. **Differentiation**: Modify for ELL, special education, advanced learners
6. **Activity Swaps**: Replace specific activities with alternatives

### 5. Export Service

**Purpose**: Convert lessons to multiple formats

**Design Decision**: Separate export logic from generation logic

```python
# New module: src/jina_rag_pipeline/generation/lesson_exporter.py
class LessonExporter:
    """Export lessons in multiple formats."""

    def to_markdown(self, lesson: LessonPlan) -> str:
        """Export as readable markdown."""

    def to_pdf(self, lesson: LessonPlan) -> bytes:
        """Export as printable PDF."""

    def to_json(self, lesson: LessonPlan) -> str:
        """Export as machine-readable JSON."""

    def to_html(self, lesson: LessonPlan) -> str:
        """Export as interactive HTML for online preview."""
```

**Format Details**:
- **Markdown**: Clean, Git-friendly, editable in any text editor
- **PDF**: Print-ready, suitable for staff meetings and sharing
- **JSON**: Programmatic access, integrable with other tools
- **HTML**: Interactive preview with collapsible sections

## Data Flow Diagram

```
Teacher Input
│
├─ Learning Objective
├─ Grade Level
├─ Duration
├─ Teaching Style
└─ Subject

        │
        ▼

1. Query Expansion
   └─ Qwen3: expand objective to key concepts

        │
        ▼

2. Educational Retrieval
   ├─ Semantic search for materials
   ├─ Filter by grade & subject
   ├─ Score standards alignment
   └─ Return top-k results

        │
        ▼

3. Lesson Generation
   ├─ Prompt: objective + retrieved materials
   ├─ Qwen3: generate lesson structure
   ├─ Parse: extract JSON components
   └─ Validate: ensure all sections present

        │
        ▼

4. Customization (Optional)
   ├─ Teacher adjusts parameters
   └─ Regenerate affected components

        │
        ▼

5. Export
   ├─ Format selection (MD/PDF/JSON)
   └─ Generate output

        │
        ▼

Teacher Output (ready to use, or edit further)
```

## API Endpoints (Phase 1)

```
POST /api/lesson-plan/generate
  Input: {
    "learning_objective": str,
    "grade_level": str,
    "subject": str,
    "duration_minutes": int,
    "teaching_style"?: str = "balanced",
    "customizations"?: Dict[str, Any]
  }
  Output: LessonPlan JSON

GET /api/lesson-plan/{lesson_id}
  Output: LessonPlan JSON

POST /api/lesson-plan/{lesson_id}/customize
  Input: CustomizationRequest
  Output: Updated LessonPlan JSON

GET /api/lesson-plan/{lesson_id}/export
  Query params: format (markdown|pdf|json)
  Output: File (markdown/PDF) or JSON
```

## Database Schema Changes

**New Collections**:
1. `standards` - Standards documents and hierarchies
2. `curricula` - Curriculum materials and lesson resources
3. `lesson_plans` - Generated lesson plans (cache)

**Metadata Fields Added to Existing Chunks**:
```python
{
  "content_type": "standard" | "activity" | "assessment" | "resource",
  "grade_level": str,  # "K", "1", "2-3", "6-8", "9-12", "college"
  "subject": str,  # "math", "science", "ela", "social_studies"
  "learning_domain": str,  # e.g., "algebraic_thinking", "life_cycles"
  "estimated_duration_minutes": int,
  "alignment_confidence": float,  # 0.0-1.0
  "prerequisites": List[str],
  "connections": List[str],  # Related topics/standards
  "source_document": str,  # Which document this came from
  "page_number": int,
}
```

## Prompt Engineering Approach

**Educational Generation Prompts**:

The system will use specialized prompts that guide Qwen3 to generate pedagogically sound lessons:

1. **Lesson Structure Prompt**:
   - Enforce 5E model (Engage, Explore, Explain, Elaborate, Evaluate)
   - Require explicit alignment to standards
   - Specify realistic timeframes

2. **Activity Generation Prompt**:
   - Use Bloom's taxonomy to vary cognitive levels
   - Suggest scaffolding for diverse learners
   - Include formative assessment checkpoints

3. **Assessment Prompt**:
   - Ensure alignment to learning objectives
   - Mix formative and summative assessments
   - Include rubrics or answer keys

See: `src/jina_rag_pipeline/generation/educational_prompts.py` (to be created)

## Performance Considerations

### Optimization Strategy

1. **Embedding Reuse**:
   - Standards documents pre-embedded once, not per query
   - Store embedding vectors in ChromaDB for instant retrieval
   - Expected: 100-500ms retrieval time for 1000-entry standards document

2. **Caching**:
   - Cache generated lessons by (objective, grade, duration, style) hash
   - TTL: 24 hours
   - Hit rate expected: 30-40% for repeated planning

3. **Async Processing**:
   - Use existing ThreadPool for non-blocking generation
   - For large standards documents (>1000 pages): use RQ workers
   - Expected: lesson generation in <30 seconds

4. **Prompt Optimization**:
   - Keep prompts concise (don't include all retrieved materials in prompt)
   - Use top-5 most relevant materials instead of top-10
   - Use structured prompting (JSON format for output) instead of free text

### Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Retrieve standards for objective | 100-500ms | ChromaDB lookup |
| Generate lesson outline | 5-15 seconds | Qwen3 streaming |
| Customize component | 3-10 seconds | Targeted regeneration |
| Export to PDF | 1-3 seconds | wkhtmltopdf or similar |
| Cache hit (regenerate) | <100ms | Direct JSON return |

## Security & Privacy Considerations

1. **Content Validation**:
   - Validate all teacher-uploaded standards documents
   - Scan for malicious content before indexing
   - Limit file size to 50MB

2. **Data Isolation**:
   - Each teacher/school gets separate ChromaDB collection
   - Standards documents are not shared across instances
   - Generated lesson plans are teacher-owned

3. **Output Validation**:
   - Check generated lessons for factual accuracy
   - Flag lessons that might contain harmful content
   - Include "Teacher Review Recommended" warning for novel material

## Testing Strategy

### Unit Tests
- Metadata extraction correctness
- Ranking algorithm logic
- Export format validation
- Customization parameter handling

### Integration Tests
- End-to-end: objective → retrieval → generation → export
- Multi-format export consistency
- Async operation correctness

### Acceptance Tests (with educators)
- Lesson pedagogical soundness
- Standards alignment accuracy
- Time savings vs. manual planning
- UI usability

## Rollback Plan

If issues arise during production rollout:

1. **Disable lesson generation**: Keep RAG chat working, disable lesson API
2. **Revert standards indexing**: Use previous ChromaDB snapshot
3. **Cache clearing**: Wipe generated lesson cache to force regeneration with fixes
4. **Graceful degradation**: Return error instead of bad lessons

## Future Extensions (Not in Scope)

1. **Multi-language support**: Generate lessons in Spanish, French, etc.
2. **LMS integration**: Export directly to Canvas, Google Classroom
3. **Adaptive paths**: Recommend lesson sequences based on learner profiles
4. **Peer sharing**: Teachers share and rate lesson plans
5. **Analytics**: Track which lesson components are most used/edited
6. **A/B testing**: Test different generation prompts with educators
