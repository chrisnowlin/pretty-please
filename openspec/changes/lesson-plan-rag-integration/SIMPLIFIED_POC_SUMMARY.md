# Simplified POC Summary: Material-Agnostic Lesson Planning

## What Changed Based on Your Feedback

You requested:
1. ✅ **Handle any grade or subject equally** - No pre-configuration needed
2. ✅ **Material-agnostic RAG** - Upload any teaching materials, system makes sense of them
3. ✅ **Markdown-first export** - Simple format, easily convertible to other formats later

## Updated Approach

### Phase 1 POC (1-2 weeks, 5-7 days)

**What it does:**
```
Teacher uploads materials (PDFs, PowerPoints, docs, images, worksheets)
    ↓
Existing RAG pipeline indexes everything (already working!)
    ↓
Teacher fills form: Topic, objective, grade, subject, duration
    ↓
System retrieves top-5 relevant materials using semantic search
    ↓
Qwen3 generates clean markdown lesson plan
    ↓
Teacher downloads .md file (editable in any text editor)
```

**Example markdown output:**
```markdown
---
title: "Understanding Fractions"
grade: "3"
subject: "Mathematics"
duration: 45
generated: "2025-10-18"
---

# Learning Objectives

By the end of this lesson, students will be able to:
- Identify fractions as parts of a whole
- Represent fractions using visual models
- Compare simple fractions (1/2, 1/3, 1/4)

# Materials Needed

- Fraction circles (manipulatives)
- Paper for folding activities
- Whiteboard and markers
- Student worksheets (see resources)

# Lesson Flow

## Engagement (5 minutes)

Hook question: "If I cut a pizza into 4 equal pieces and eat 1 piece, how much did I eat?"

Students share ideas with a partner, then whole-class discussion.

## Direct Instruction (15 minutes)

1. Introduce fraction notation (numerator/denominator)
2. Demonstrate with physical fraction circles
3. Show multiple representations: circles, bars, number lines

## Guided Practice (20 minutes)

Activity 1: Paper folding (10 min)
- Students fold paper to create halves, thirds, fourths
- Label each section
- Compare sizes

Activity 2: Fraction matching (10 min)
- Match visual models to fraction notation
- Work in pairs

## Closure (5 minutes)

Exit ticket: Draw a model showing 1/3 and write the fraction.

Quick gallery walk: students share their work.

# Assessments

**Formative:**
- Observation during paper folding activity
- Partner discussions
- Exit ticket review

**Summative:**
- End-of-unit fraction quiz (future lesson)

# Differentiation

**For struggling learners:**
- Pre-cut fraction models available
- Work with teacher in small group during practice

**For advanced learners:**
- Challenge: Compare 1/3 and 1/4 - which is larger? Why?
- Extend to equivalent fractions (future topic preview)

**For ELL students:**
- Visual vocabulary cards (numerator, denominator, fraction)
- Sentence frames for discussions

---

*This lesson plan was AI-generated using materials from your teaching collection. Review and adjust as needed for your classroom.*
```

## What's Removed (Moved to Phase 2+)

❌ **Standards parsing** - No Common Core, state standards processing initially
❌ **Multi-format export** - Just markdown for POC (PDF/JSON in Phase 2)
❌ **Complex metadata** - Simple keyword hints only
❌ **Standards alignment** - Optional in Phase 2 for teachers who want it

## What's Simplified

✅ **Material ingestion** - Uses existing RAG pipeline (already handles PDFs, PPTX, images)
✅ **Retrieval** - Pure semantic search + optional metadata (grade/subject if detected)
✅ **Generation** - Clean markdown templates (no complex JSON schemas)
✅ **Frontend** - Simple form + markdown preview + download button

## Phase 1 Tasks Breakdown (5-7 days)

1. **Educational data models** (0.5 days) - Simple Python dataclasses
2. **Metadata extraction** (0.5 days) - Best-effort keyword detection
3. **Educational retriever** (1 day) - Wrapper around existing ChromaDB
4. **Lesson prompts** (0.5 days) - Markdown template prompts
5. **Lesson generator** (1.5 days) - Qwen3 integration
6. **API endpoint** (1 day) - POST /api/lesson-plan/generate
7. **Frontend form** (1 day) - React form + markdown preview
8. **Integration test** (0.5 days) - End-to-end validation

## Effort Saved

| Task Removed | Days Saved |
|--------------|------------|
| Standards parsing | 1.5 |
| Complex metadata extraction | 1 |
| PDF/JSON export | 1 |
| Standards-specific retrieval | 1 |
| **Total saved** | **~4.5 days** |

Original Phase 1: 10-12 days → New Phase 1: **5-7 days**

## Why This is Better for POC

1. **Faster validation** - Get teacher feedback in 1-2 weeks
2. **Lower complexity** - Fewer moving parts = fewer bugs
3. **Material flexibility** - Works with whatever teachers have
4. **Incremental value** - Each phase adds clear value
5. **Easier to pivot** - Based on teacher feedback, adjust Phase 2 priorities

## What Teachers Get (Phase 1)

✅ Upload teaching materials (any format)
✅ Generate lesson plans in seconds
✅ Download editable markdown files
✅ Works for any grade level or subject
✅ No setup or configuration required

## What Comes Later (Phase 2+)

📋 Customization (duration, teaching style, differentiation)
📋 PDF and JSON export
📋 Optional standards alignment (for those who want it)
📋 Inline editing and component regeneration
📋 Lesson library and management

## Success Criteria for Phase 1

- [ ] Teachers upload 5+ teaching materials → indexed successfully
- [ ] Generate lesson for "Grade 3 Math - Fractions" → usable markdown output
- [ ] Generate lesson for "High School Biology - Photosynthesis" → usable markdown output
- [ ] Performance: <30 seconds end-to-end
- [ ] Teacher feedback: "This saves me time" (qualitative)

## Next Steps

1. **Review this approach** - Does it match your vision?
2. **Validate assumptions** - Do you have sample teaching materials to test with?
3. **Start Phase 1 Task 1.1** - Define educational data models
4. **Iterate based on feedback** - Get teachers testing early and often

## Example Materials Teachers Might Upload

- Textbook chapters (PDF)
- Lesson plans from previous years (DOCX)
- Activity worksheets (PDF)
- PowerPoint presentations
- Images of diagrams or charts
- Curriculum guides (PDF)
- Assessment banks (DOCX)
- Online article screenshots
- Video transcripts

**All handled by existing RAG pipeline!** No special processing needed.

## Conversion Path (Later)

Once you have markdown lessons, teachers can easily convert:

```bash
# Markdown to PDF (using pandoc)
pandoc lesson.md -o lesson.pdf

# Markdown to DOCX
pandoc lesson.md -o lesson.docx

# Markdown to HTML
pandoc lesson.md -o lesson.html
```

Or we build it into Phase 2 with proper styling and templates.

## Confirmed Design Decisions ✅

All questions answered! See [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md) for full details.

1. **Source citations**: ✅ **REQUIRED** - Every lesson MUST include inline citations [1][2] and source reference list
2. **Image inclusion**: ✅ **REQUIRED** - Automatically include relevant images/diagrams from materials
3. **Grade level format**: ✅ **Abbreviated** - Use K, 1, 2, 3-5, 6-8, 9-12, College
4. **Default duration**: ✅ **50 minutes** - Configurable range: 20-90 minutes

All four are **MUST HAVE** for Phase 1 POC.
