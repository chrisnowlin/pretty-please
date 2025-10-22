# Specification: Lesson Plan Generation

**Change ID**: `lesson-plan-rag-integration`
**Capability**: Lesson Plan Generation
**Phase**: 1
**Status**: Draft

## Overview

The system generates structured, standards-aligned lesson plans from learning objectives. Using retrieval-augmented generation with educational context, the system produces lessons with learning objectives, materials, activities, assessments, and differentiation strategies.

## ADDED Requirements

#### Requirement: Generate Structured Lesson Plans
**Description**: System generates complete lessons as structured JSON with all required components.

**Scenario**: Teacher enters: "Grade 3 Math, Understanding fractions, 45 minutes". System:
1. Retrieves fraction-related standards and materials
2. Generates lesson with:
   - Learning objectives (aligned to standards)
   - Materials needed
   - Lesson phases (engagement, instruction, practice, closure)
   - Activities with timing
   - Formative and summative assessments
   - Differentiation for diverse learners
3. Returns as validated JSON

**Acceptance Criteria**:
- [ ] Generated lessons include all required components
- [ ] JSON validates against schema
- [ ] Performance: generation in <30 seconds
- [ ] Multiple lessons for same objective vary (not identical)
- [ ] Sample lessons are pedagogically sound

#### Requirement: Align Lessons to Standards
**Description**: Generated lessons explicitly reference and align to learning standards.

**Scenario**: Generated lesson for "photosynthesis" includes:
```json
{
  "aligned_standards": [
    {
      "code": "NGSS.3-LS1-1",
      "description": "Develop models to describe...",
      "practice": "Developing and Using Models"
    }
  ]
}
```

**Acceptance Criteria**:
- [ ] Every lesson has aligned standards
- [ ] Standards are from the ingested collection
- [ ] Standard codes are correct
- [ ] Standards describe learning in lesson

#### Requirement: Support Multiple Teaching Styles
**Description**: Lesson generation adapts to different pedagogical approaches.

**Scenario**: Same objective generates different lessons based on style:
- **Direct Instruction**: Teacher-led demonstration, guided practice, independent work
- **Inquiry-Based**: Question → investigation → analysis → conclusion
- **Project-Based**: Real-world problem → teamwork → deliverable
- **Balanced**: Mix of approaches

**Acceptance Criteria**:
- [ ] Each style produces distinct activities
- [ ] Activities match stated pedagogical approach
- [ ] Teacher resources align to style
- [ ] Assessments match style (e.g., project-based for PBL)

#### Requirement: Integrate Retrieved Materials
**Description**: Generated lessons incorporate retrieved educational materials appropriately.

**Scenario**: Retrieval returns 5 relevant documents on ecosystems. Generation:
1. Selects most relevant materials
2. Cites sources in lesson
3. Incorporates examples from documents
4. Uses document activities as starting point

**Acceptance Criteria**:
- [ ] Retrieved materials appear in lesson
- [ ] No more than top-5 materials per lesson (avoid clutter)
- [ ] Materials cited in activities section
- [ ] Quality of materials reflected in lesson quality

#### Requirement: Generate Age-Appropriate Content
**Description**: All lesson content matches target grade level cognitively.

**Scenario**: Grade 3 lesson uses:
- Simple vocabulary appropriate for 8-9 year olds
- Activities doable in one sitting
- No advanced prerequisite knowledge assumed
- Concrete examples, not abstract concepts

Grade 10 lesson uses:
- More complex vocabulary and ideas
- Multi-day projects appropriate
- Builds on prior high school learning
- Some abstract reasoning encouraged

**Acceptance Criteria**:
- [ ] Vocabulary grade level matches target grade
- [ ] Complexity appropriate for grade
- [ ] Time allocation realistic for grade
- [ ] Teacher feedback: activities are age-appropriate

#### Requirement: Include Realistic Timing
**Description**: All lesson components include realistic time estimates.

**Scenario**: 45-minute lesson breakdown:
```json
{
  "phases": [
    {"phase": "engagement", "duration_minutes": 5},
    {"phase": "direct_instruction", "duration_minutes": 10},
    {"phase": "practice", "duration_minutes": 25},
    {"phase": "closure", "duration_minutes": 5}
  ]
}
```
Total: 45 minutes (no phase exceeds parent duration)

**Acceptance Criteria**:
- [ ] All phase durations sum to total lesson duration
- [ ] Individual activity durations realistic (<20 min each)
- [ ] Timing allows buffer for transitions (~5%)
- [ ] Teachers can execute timing as written

#### Requirement: Provide Multiple Assessment Types
**Description**: Lessons include varied assessment approaches.

**Scenario**: Lesson includes:
- **Formative**: Observation during practice, think-pair-share, exit ticket
- **Summative**: End-of-unit quiz or project
- **Performance**: Student demonstration or portfolio piece

**Acceptance Criteria**:
- [ ] Every lesson has both formative and summative elements
- [ ] At least 2 different assessment methods
- [ ] Assessments align to learning objectives
- [ ] Assessment rubrics or answer keys included

#### Requirement: Include Differentiation Strategies
**Description**: Lessons provide modifications for diverse learners.

**Scenario**: Lesson for "multiplication" includes modifications for:
- **Advanced**: Multi-digit by multi-digit, algebraic patterns
- **On-level**: Two-digit by one-digit, repeated groups
- **Struggling**: Arrays with manipulatives, skip counting
- **ELL**: Simplified vocabulary, visual aids, word bank

**Acceptance Criteria**:
- [ ] Modifications for at least 3 student groups
- [ ] Modifications are practical for classroom
- [ ] Scaffolding strategies evidence-based
- [ ] Teachers can implement without additional resources

#### Requirement: Export to Multiple Formats
**Description**: Generated lessons can be exported in markdown, PDF, and JSON formats.

**Scenario**: After generation, teacher can:
- Download as `.md` (edit in any text editor)
- Download as `.pdf` (print or share)
- Copy as `.json` (integrate with other tools)

**Acceptance Criteria**:
- [ ] Markdown exports are readable and well-formatted
- [ ] PDF exports are professional and print-friendly
- [ ] JSON exports are valid and complete
- [ ] All formats include all lesson components
- [ ] Export in <5 seconds per format

## MODIFIED Requirements

*(No modifications to existing requirements)*

## REMOVED Requirements

*(No removals)*

## Implementation Notes

### Lesson Plan JSON Schema

```python
@dataclass
class LessonPlan:
    """Structured lesson plan output."""

    metadata: LessonMetadata
    learning_objectives: List[LearningObjective]
    materials_and_resources: List[Resource]
    lesson_flow: List[LessonPhase]
    assessments: List[Assessment]
    differentiation: List[DifferentiationStrategy]

@dataclass
class LessonMetadata:
    title: str
    grade_level: str
    subject: str
    duration_minutes: int
    teaching_style: str
    aligned_standards: List[str]
    created_at: str
    generated_by_model: str = "Qwen3-14B-4bit"

@dataclass
class LearningObjective:
    objective: str                 # "Students will understand..."
    bloom_level: str              # remember, understand, apply, analyze, evaluate, create
    aligned_standard: str         # Standard code

@dataclass
class LessonPhase:
    phase: str                    # engagement, instruction, practice, closure
    duration_minutes: int
    description: str
    activities: List[str]
    materials_needed: List[str]

@dataclass
class Assessment:
    type: str                     # formative, summative, diagnostic
    timing: str                   # during_engagement, during_instruction, etc.
    method: str                   # "Exit ticket", "Observation checklist", etc.
    description: str

@dataclass
class DifferentiationStrategy:
    student_group: str            # advanced, on_level, struggling, ell
    modifications: List[str]      # Specific changes for this group
```

### Generation Pipeline

```
Teacher Input
    ↓
Query Expansion (Qwen3)
    ↓
Educational Retrieval (top-5 materials)
    ↓
Format Context (retrieved materials → prompt)
    ↓
Prompt Engineering (apply lesson generation prompt)
    ↓
Qwen3 Streaming Generation
    ↓
Response Parsing (extract JSON)
    ↓
Validation (all fields present and valid)
    ↓
Structure Conversion (JSON → LessonPlan object)
    ↓
Return to User (JSON or export)
```

### Prompt Engineering

Lesson generation uses carefully crafted prompts:

1. **System Prompt**: Establishes role, constraints, pedagogical principles
2. **Context Injection**: Retrieved materials formatted as context
3. **Lesson Prompt**: Specifies structure, required components, format
4. **Style Prompt**: Varies based on teaching style selected

### Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Query expansion | <1s | Qwen3 synonym generation |
| Educational retrieval | <1s | ChromaDB lookup |
| Lesson generation | 10-20s | Qwen3 streaming |
| Response parsing | <1s | JSON extraction |
| **Total end-to-end** | **<30s** | Typical request |

### Error Handling

- **Malformed LLM output**: Retry with stricter prompt
- **Missing required fields**: Fill with templates, flag for review
- **Invalid standards reference**: Log warning, generate without alignment
- **Timeout**: Return partial lesson or cached template

## Testing Strategy

### Unit Tests
- [ ] Lesson schema validation: all types work
- [ ] Metadata extraction: correctness
- [ ] Component generation: each part independently

### Integration Tests
- [ ] End-to-end generation: objective → complete lesson
- [ ] Multi-style generation: each style produces different results
- [ ] Export all formats: markdown, PDF, JSON work
- [ ] Performance: meets <30s target

### Acceptance Tests
- [ ] Generated lessons are pedagogically sound (teacher review)
- [ ] Standards alignment is accurate
- [ ] Age-appropriateness verified
- [ ] Differentiation strategies are practical

## Related Capabilities

- **Educational Content Ingestion**: Provides materials for context
- **Educational Retrieval**: Fetches aligned standards/materials
- **Teacher Customization**: Allows refinement after generation
- **Multi-format Export**: Supports output in different formats

## Future Enhancements

- Support more teaching styles (flipped classroom, station rotation)
- Include LMS integration (Canvas, Google Classroom export)
- Student-facing generated materials (handouts, slides)
- Cross-curricular connections (recommend related lessons)

## Version History

- **v1.0** (2025-10-18): Initial specification
