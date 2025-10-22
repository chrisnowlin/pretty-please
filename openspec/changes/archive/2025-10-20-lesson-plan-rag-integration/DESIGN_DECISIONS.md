# Design Decisions: Lesson Plan Generation

**Change ID**: `lesson-plan-rag-integration`
**Date**: 2025-10-18
**Status**: Confirmed

## Core Requirements (Confirmed)

### 1. Source Citations - REQUIRED ✅

**Decision**: Every generated lesson MUST include citations to source materials used.

**Implementation**:
- Track which retrieved documents contributed to each lesson section
- Include citations inline: "As shown in [1]..." or at end of sections
- Provide full source list at bottom of lesson with document names and pages

**Example**:
```markdown
# Materials Needed

- Fraction circles (manipulatives) [1]
- Student worksheet: "Parts of a Whole" [2]
- Visual aids showing pizza/pie diagrams [1]

## Sources Referenced

[1] Chapter 3: Introduction to Fractions (Textbook_Math_Grade3.pdf, pages 45-52)
[2] Fraction Activities Workbook (Activities_Fractions.docx)
[3] Visual Learning Aids (Diagrams_Fractions.pptx, slide 5)
```

**Rationale**:
- Teachers need to know where information came from
- Builds trust in AI-generated content
- Helps teachers verify and expand on materials
- Educational integrity and attribution

---

### 2. Image/Diagram Inclusion - REQUIRED ✅

**Decision**: Automatically include relevant images and diagrams found in uploaded materials.

**Implementation**:
- Use existing multimodal RAG capabilities (already supports image embeddings)
- Retrieve relevant images alongside text chunks
- Include images in markdown using standard syntax
- Reference images in lesson flow where appropriate

**Example**:
```markdown
## Direct Instruction (15 minutes)

1. **Introduce fraction notation** (5 min)
   - Show fraction as numerator/denominator
   - Use visual model:

   ![Fraction circle showing 1/4](images/fraction_circle_quarters.png)
   *Figure 1: Circle divided into fourths [Source: Visual_Aids.pdf]*

2. **Demonstrate multiple representations** (10 min)
   - Circles, bars, number lines

   ![Three representations of 1/2](images/half_representations.png)
   *Figure 2: Different ways to show one-half [Source: Teaching_Fractions.pptx, slide 12]*
```

**Technical Notes**:
- Images stored in `uploads/lesson-images/` directory
- Markdown references relative paths or base64-encoded inline images
- Image retrieval ranked by semantic relevance to lesson topic
- Max 3-5 images per lesson (avoid cluttering)

**Rationale**:
- Visual aids critical for student learning, especially in math and science
- Teachers expect visual materials in lessons
- Leverages existing multimodal RAG investment
- Reduces teacher effort to find/create diagrams

---

### 3. Grade Level Format - ABBREVIATED ✅

**Decision**: Use abbreviated grade level indicators, not full names.

**Format**:
- **PreK** - Prekindergarten
- **K** - Kindergarten
- **1, 2, 3, 4, 5** - Elementary grades
- **6, 7, 8** - Middle school grades
- **9, 10, 11, 12** - High school grades
- **College** - Higher education

**Ranges** (when applicable):
- **K-2** - Early elementary
- **3-5** - Upper elementary
- **6-8** - Middle school
- **9-12** - High school

**Example YAML Frontmatter**:
```yaml
---
title: "Understanding Fractions"
grade: "3"              # Single grade
subject: "Mathematics"
duration: 50
---
```

or

```yaml
---
title: "Introduction to Ecosystems"
grade: "6-8"            # Grade range
subject: "Science"
duration: 50
---
```

**Rationale**:
- Concise and standard in education
- Easy to parse programmatically
- Matches how teachers think/talk about grades
- Consistent with most educational databases

---

### 4. Default Lesson Duration - 50 MINUTES ✅

**Decision**: Default lesson duration is **50 minutes** (typical class period).

**Configuration**:
```python
# src/jina_rag_pipeline/generation/config.py
DEFAULT_LESSON_DURATION_MINUTES = 50

# Frontend default
const DEFAULT_DURATION = 50;
```

**Allowed Range**: 20-90 minutes
- **20-30 min**: Mini-lesson, single topic
- **40-50 min**: Standard class period
- **60-75 min**: Block schedule
- **90 min**: Extended block or workshop

**Duration Breakdown Template (50 min)**:
```
Engagement:     5 min  (10%)
Instruction:    15 min (30%)
Practice:       25 min (50%)
Closure:        5 min  (10%)
```

**Rationale**:
- 50 minutes is typical middle/high school period
- Elementary can adjust down to 30-40 min
- Block schedules adjust up to 75-90 min
- Provides realistic, achievable timing

---

## Implementation Priorities

### Phase 1 (POC) - MUST HAVE:
1. ✅ **Source citations** - Every lesson includes sources
2. ✅ **Image inclusion** - Retrieve and embed relevant images
3. ✅ **Abbreviated grades** - Use K, 1-12, College format
4. ✅ **50-min default** - Configurable default duration

### Phase 2 (Enhanced) - NICE TO HAVE:
- Interactive image preview in frontend
- Image editing/replacement in lesson editor
- Citation management (edit, add, remove sources)
- Duration templates for common formats

---

## Technical Implementation Notes

### Source Citation Tracking

**During Retrieval**:
```python
@dataclass
class RetrievedMaterial:
    content: str
    document_name: str
    page_number: Optional[int]
    chunk_id: str
    relevance_score: float
    source_type: str  # "text", "image", "table"
```

**During Generation**:
- Pass source metadata to Qwen3 in prompt context
- Instruct LLM to cite sources: "When using information, cite as [N]"
- Parse citations from output
- Build source reference list

**Prompt Example**:
```
You are generating a lesson plan. You MUST cite sources for all materials and information.

Available sources:
[1] Chapter 3: Fractions (Textbook_Math_Grade3.pdf, pages 45-52)
[2] Fraction Activities (Activities_Workbook.docx)
[3] Visual Learning Aids (Diagrams_Fractions.pptx, slide 5)

When referencing materials or information, cite the source like this:
- "Use fraction circles [1] to demonstrate..."
- "The diagram shows [3]..."

At the end of the lesson, include a "Sources Referenced" section listing all sources used.
```

---

### Image Retrieval and Embedding

**Retrieval**:
```python
# Retrieve both text and images
text_results = retriever.retrieve_text(topic, grade, top_k=5)
image_results = retriever.retrieve_images(topic, grade, top_k=3)

# Combine and rank
combined_materials = combine_and_rank(text_results, image_results)
```

**Markdown Generation**:
```python
# Include images in markdown
def format_image_markdown(image: RetrievedImage) -> str:
    return f"""
![{image.alt_text}]({image.path})
*Figure {image.number}: {image.caption} [Source: {image.source_document}]*
"""
```

**Storage**:
- Images extracted during ingestion → stored in `uploads/lesson-images/`
- Unique filenames: `{lesson_id}_{image_hash}.{ext}`
- Markdown references: relative paths or base64 inline

---

### Grade Level Handling

**Frontend Dropdown**:
```typescript
const GRADE_LEVELS = [
  { value: "PreK", label: "PreK" },
  { value: "K", label: "Kindergarten (K)" },
  { value: "1", label: "Grade 1" },
  { value: "2", label: "Grade 2" },
  // ... 3-12
  { value: "College", label: "College" },

  // Ranges
  { value: "K-2", label: "K-2 (Early Elementary)" },
  { value: "3-5", label: "3-5 (Upper Elementary)" },
  { value: "6-8", label: "6-8 (Middle School)" },
  { value: "9-12", label: "9-12 (High School)" },
];
```

**Metadata Filtering**:
```python
# Match grade ranges
def matches_grade(material_grade: str, query_grade: str) -> bool:
    """
    Examples:
    - material_grade="3", query_grade="3" → True
    - material_grade="3-5", query_grade="4" → True
    - material_grade="K-2", query_grade="1" → True
    """
    # Implementation handles ranges and single grades
```

---

### Duration Configuration

**API Request**:
```python
@dataclass
class GenerateLessonRequest:
    topic: str
    learning_objective: str
    grade_level: str
    subject: str
    duration_minutes: int = 50  # Default
    teaching_style: str = "balanced"
```

**Validation**:
```python
MIN_DURATION = 20
MAX_DURATION = 90

if not MIN_DURATION <= duration <= MAX_DURATION:
    raise ValueError(f"Duration must be between {MIN_DURATION}-{MAX_DURATION} minutes")
```

---

## Example Complete Lesson Output

```markdown
---
title: "Understanding Fractions as Parts of a Whole"
grade: "3"
subject: "Mathematics"
duration: 50
teaching_style: "balanced"
generated: "2025-10-18T14:30:00Z"
---

# Learning Objectives

By the end of this lesson, students will be able to:
- Define a fraction as a part of a whole [1]
- Represent fractions using visual models [1][3]
- Identify the numerator and denominator in fraction notation [1]

# Materials Needed

- Fraction circles (manipulatives) [1]
- Student worksheet: "Parts of a Whole" [2]
- Whiteboard and markers
- Visual aids (see figures below) [3]

# Lesson Flow

## Engagement (5 minutes)

**Hook Question**: "If I cut a pizza into 4 equal pieces and eat 1 piece, what part of the pizza did I eat?"

Students turn-and-talk with a partner, then share whole-group.

![Pizza diagram showing 4 equal slices](images/pizza_quarters.png)
*Figure 1: Pizza divided into fourths [Source: Visual_Aids.pptx, slide 3]*

## Direct Instruction (15 minutes)

### Introduce Fraction Notation (7 minutes)

Explain fraction as part/whole relationship [1]:
- **Numerator** (top number): parts we have
- **Denominator** (bottom number): total equal parts

Use the fraction circle manipulatives to demonstrate 1/4 [1].

![Fraction circle showing 1/4 shaded](images/fraction_circle_quarters.png)
*Figure 2: One-fourth represented with fraction circles [Source: Math_Manipulatives.pdf, page 12]*

### Multiple Representations (8 minutes)

Show that fractions can be represented in different ways [3]:
- Circles
- Bars/rectangles
- Number lines

![Three representations of 1/2](images/half_representations.png)
*Figure 3: Different visual models for one-half [Source: Visual_Aids.pptx, slide 5]*

## Guided Practice (25 minutes)

### Activity 1: Paper Folding (12 minutes)

Students fold paper to create halves, thirds, and fourths [2].
- Fold once → halves (1/2)
- Fold into thirds → thirds (1/3)
- Fold into fourths → fourths (1/4)

Students label each section and shade one part.

### Activity 2: Fraction Matching Game (13 minutes)

Using worksheet from [2], students match:
- Visual models ↔ Fraction notation
- Real-world examples ↔ Fractions

Work in pairs, teacher circulates to check understanding.

## Closure (5 minutes)

**Exit Ticket**: Draw a model showing 1/3 and write the fraction below it.

Quick gallery walk: 3-4 students share their work under document camera.

# Assessments

**Formative**:
- Observation during paper folding activity (checklist)
- Partner discussions (listening for accurate fraction language)
- Exit ticket review (collect and check for understanding)

**Summative**:
- End-of-unit fraction assessment (planned for Week 3)

# Differentiation

**For Struggling Learners**:
- Pre-cut fraction models available [1]
- Small group instruction during guided practice
- Simplified worksheet with larger visual models [2]

**For Advanced Learners**:
- Challenge: Which is larger, 1/3 or 1/4? Explain why.
- Introduce equivalent fractions concept (2/4 = 1/2)
- Extension activity: Create your own fraction story problem

**For ELL Students**:
- Visual vocabulary cards: fraction, numerator, denominator [3]
- Sentence frames: "This shows ___ out of ___ equal parts."
- Partner with strong English speaker for discussions

# Notes for Teacher

- Emphasize **equal parts** - this is key to fraction understanding
- Common misconception: bigger denominator = bigger fraction (address proactively)
- Have extra manipulatives ready for hands-on learners
- Timing is flexible - adjust practice time based on student needs

---

## Sources Referenced

[1] **Chapter 3: Introduction to Fractions**
    Math Textbook - Grade 3 (Textbook_Math_Grade3.pdf, pages 45-52)

[2] **Fraction Activities and Worksheets**
    Teacher Resource Guide (Fraction_Activities_Workbook.docx)

[3] **Visual Learning Aids: Fractions**
    Visual Teaching Materials (Diagrams_Fractions.pptx, slides 3, 5, 12)

---

*This lesson plan was AI-generated using materials from your teaching collection. Please review and adjust for your specific classroom needs.*
```

---

## Summary of Confirmed Decisions

| Decision | Value | Implementation Priority |
|----------|-------|------------------------|
| **Source Citations** | Required, inline + reference list | Phase 1 (POC) |
| **Image Inclusion** | Auto-include relevant images | Phase 1 (POC) |
| **Grade Format** | Abbreviated (K, 1-12, College) | Phase 1 (POC) |
| **Default Duration** | 50 minutes (range: 20-90) | Phase 1 (POC) |

All four requirements are **MUST HAVE** for Phase 1 POC.

---

**Status**: ✅ Confirmed and ready for implementation
