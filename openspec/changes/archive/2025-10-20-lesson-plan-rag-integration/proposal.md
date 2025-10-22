# Proposal: Lesson Plan Generation via RAG

**Change ID**: `lesson-plan-rag-integration`
**Status**: Open for Review
**Created**: 2025-10-18
**Version**: 1.0

## Executive Summary

This proposal transforms the general-purpose Jina RAG system into a **specialized lesson plan generation engine** for K-12 educators. By layering educational-specific capabilities on top of the existing RAG foundation, teachers can input learning objectives, grade levels, and topics—then retrieve aligned curriculum materials and generate structured lesson plans in minutes.

## Problem Statement

### Current State
- Teachers spend 5-10 hours planning a single comprehensive lesson
- Planning requires manual research across multiple disconnected sources (textbooks, online resources, past lessons, activity banks)
- Materials are scattered across file systems, bookmarks, and physical binders
- No easy way to synthesize diverse materials into cohesive lesson plans

### Desired State
- Teachers upload their own teaching materials (PDFs, docs, slides, images) → RAG indexes everything
- Teachers input a learning objective + topic → system retrieves relevant materials from their collection
- System generates ready-to-use lesson outlines in clean markdown format
- Lessons can be edited in any text editor and exported to other formats later
- Works for ANY grade level and subject matter without pre-configuration

## Scope

### In Scope: Core Capabilities (Phase 1 POC)
1. **Material-agnostic ingestion**: Accept any teaching materials (PDFs, Word docs, slides, images, markdown) and index them
2. **Intelligent retrieval**: Retrieve relevant materials based on topic, grade level, and learning objective
3. **Structured lesson generation**: Create lessons with objectives, materials, procedures, activities, and assessments
4. **Markdown-first export**: Clean, readable markdown that can be edited and converted to other formats
5. **Grade/subject flexibility**: Works for K-12, college, any subject without pre-configuration
6. **Teacher customization**: Adjust duration, teaching style, and target audience

### Out of Scope: Future Phases
- **Standards alignment** (Common Core, state standards) — Phase 2
- **Multi-format export** (PDF, JSON, DOCX) — Phase 2 (markdown can be converted)
- Student-facing features (assignment tracking, grading, reporting)
- Integration with external LMS (Canvas, Schoology, Google Classroom)
- Multi-language support
- Real-time collaborative editing
- Advanced analytics or learning outcome tracking

## Key Capabilities

### Capability 1: Material-Agnostic Content Ingestion
- Accept any educational materials (PDF, DOCX, PPTX, images, markdown, etc.)
- Extract text and visual content using existing RAG pipeline
- Auto-detect metadata where possible (grade level hints, subject keywords)
- Index everything in ChromaDB with semantic embeddings
- Support teacher-uploaded custom materials (their own lessons, activities, worksheets)

**Rationale**: Teachers have diverse materials in different formats. The RAG system should make sense of whatever they have, not require pre-structured content.

### Capability 2: Smart Contextual Retrieval
- Retrieve materials by learning objective, topic, and grade level
- Semantic search using Jina embeddings (what you already have)
- Combine with metadata filtering (grade, subject) when available
- Return results with relevance scores
- Works even with minimal metadata (purely semantic matching)

**Rationale**: Teachers need materials that match their topic and grade level. Pure semantic search already provides most of this; light metadata filtering improves precision.

### Capability 3: Markdown Lesson Plan Generation
- Generate lesson components: objectives, materials, duration, procedures, activities, assessments
- Output as **clean, readable markdown** (easy to edit, version control, convert)
- Support multiple teaching styles (direct instruction, inquiry-based, project-based)
- Include activity sequences with timing
- Format for readability and easy conversion to other formats

**Rationale**: Markdown is universal, editable in any text editor, version-controllable with Git, and convertible to PDF/DOCX/HTML later. Teachers can immediately use and modify lessons.

### Capability 4: Teacher Customization & Control
- Specify target grade level, duration, student population
- Choose assessment style (formative, summative, performance-based)
- Adjust complexity and pacing
- Regenerate components on demand

**Rationale**: One-size-fits-all lessons don't work in education. Teachers need fine-grained control.

### Capability 5: Clean Markdown Output (Future: Multi-format)
- Generate lessons as clean, well-structured markdown
- Use standard markdown conventions (headers, lists, emphasis)
- Include metadata as YAML frontmatter (grade, subject, duration)
- Format for easy conversion to PDF/DOCX/HTML using pandoc or similar tools
- **Future phases**: Direct PDF/JSON export, but POC proves markdown works

**Rationale**: Start simple. Markdown is readable, editable, and convertible. Proves the concept before adding export complexity.

## Design Approach

This proposal builds incrementally on the existing RAG system:

1. **Layer 1**: Extend ingestion to parse standards documents → Educational content types
2. **Layer 2**: Add specialized retrieval logic → Educational retrieval engine
3. **Layer 3**: Create lesson plan prompt templates → Lesson generation module
4. **Layer 4**: Build teacher UI and customization controls → Frontend forms
5. **Layer 5**: Export pipeline for multiple formats → Export service

**Why this approach?**
- Reuses mature RAG foundation (no need to rebuild embeddings, storage, async infrastructure)
- Keeps components independent and testable
- Allows parallel frontend/backend work
- Enables iterative teacher feedback
- Reduces risk by validating each layer before moving to the next

## Technical Architecture (High-Level)

```
┌─────────────────────────────────────────────┐
│  Teacher Frontend (React)                    │
│  - Input form: objective, grade, duration   │
│  - Customization controls                   │
│  - Lesson preview & export                  │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Lesson Plan Generation API (FastAPI)        │
│  - /lesson-plan/generate                    │
│  - /lesson-plan/customize                   │
│  - /lesson-plan/export                      │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│  Lesson Generation Engine                           │
│  ┌────────────────────────────────────────────────┐ │
│  │ Educational Retrieval (specialized RAG)       │ │
│  │ - Semantic search + standards alignment       │ │
│  │ - Activity retrieval                          │ │
│  │ - Assessment bank retrieval                   │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │ Lesson Template Engine                        │ │
│  │ - Fill templates from retrieved materials     │ │
│  │ - Generate structured lesson JSON             │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │ Customization & Refinement                    │ │
│  │ - Apply grade/duration/format preferences     │ │
│  │ - Regenerate components on demand             │ │
│  └────────────────────────────────────────────────┘ │
└──────────────┬───────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│  Existing RAG Infrastructure                        │
│  - Jina Embeddings v4                              │
│  - ChromaDB Storage                                │
│  - Async Processing & Workers                      │
│  - Monitoring & Metrics                            │
└──────────────────────────────────────────────────────┘
```

## Phased Rollout

### Phase 1: Proof of Concept (1-2 weeks)
- Material upload and ingestion (uses existing RAG pipeline)
- Semantic retrieval with optional grade/subject filtering
- Markdown lesson plan generation from templates
- Simple frontend form for input

**Output**: Teachers upload materials → input objective + grade → get markdown lesson they can edit

### Phase 2: Enhanced Features (2-3 weeks)
- Lesson customization (duration, teaching style, differentiation)
- Multi-format export (PDF, JSON from markdown)
- Standards alignment (optional metadata)
- Improved UI with editing and preview

**Output**: Teachers can customize lessons and export to multiple formats

### Phase 3: Polish & Scale (2-3 weeks)
- Performance optimization for large standards documents
- Advanced retrieval (multi-standard queries, cross-curricular)
- Frontend refinements (drag-and-drop editing, templates)
- Initial teacher feedback incorporation

**Output**: Production-ready system ready for classroom pilot testing

## Success Criteria

### Phase 1 (POC)
- [ ] Can ingest diverse teaching materials (PDFs, slides, docs, images)
- [ ] Retrieves 5+ relevant materials for a given topic/objective
- [ ] Generates clean markdown lesson plan
- [ ] Works end-to-end via API and simple frontend
- [ ] Lessons are immediately usable by teachers (editable markdown)

### Phase 2 (Enhanced)
- [ ] Customization features work (duration, style, differentiation)
- [ ] Can convert markdown to PDF and JSON
- [ ] System handles 100+ concurrent requests
- [ ] Performance: lesson generation in <30 seconds for typical query
- [ ] Optional standards alignment for those who want it

### Phase 3 (Polish)
- [ ] Handles large material collections (1000s of documents) efficiently
- [ ] Advanced retrieval (cross-curricular, multi-topic)
- [ ] UI allows inline editing and component regeneration
- [ ] Teachers report 50%+ time savings vs. manual planning
- [ ] Works reliably for diverse grade levels and subjects

## Known Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Teacher adoption low | ROI uncertainty | Early feedback loop, iterate on UI |
| Quality of generated lessons poor | System unusable | Comprehensive testing with educators, iterative prompt refinement |
| Diverse materials don't index well | Retrieval failures | Leverage existing multimodal RAG (already handles PDFs, images, etc.) |
| Performance degrades with large collections | UX poor | Use existing async processing and distributed workers |
| LLM generates educationally unsound content | Reputational risk | Teacher review workflow, clear "AI-generated" labeling |
| Markdown output too simple | Limited adoption | Show teachers how easy it is to convert (pandoc, etc.) |

## Dependencies & Assumptions

### Dependencies
- Existing RAG foundation (embeddings, storage, async workers)
- Jina Embeddings v4 already deployed and working
- ChromaDB already configured and operational
- Qwen3-14B-4bit model loaded for generation

### Assumptions
- Teachers have educational materials in digital formats (PDFs, docs, slides)
- Existing RAG ingestion pipeline handles their materials (it already supports many formats)
- Markdown output is acceptable (can be converted later)
- Teachers want to keep control and edit lessons (not fully automated)
- Teachers will provide feedback for iterative improvements

## Effort Estimates (Simplified POC-First Approach)

- **Design & Spec Writing**: 0.5 days (already mostly done)
- **Phase 1 Implementation (POC)**: 5-7 engineering days
- **Phase 2 Implementation**: 8-10 engineering days
- **Phase 3 Implementation**: 6-8 engineering days
- **Testing & QA**: 3-5 days (ongoing)
- **Total**: ~25-35 engineering days over 5-8 weeks

**Key Simplifications**:
- No standards parsing → -3 days
- Markdown-only export → -2 days
- Uses existing RAG ingestion → -2 days
- Simpler metadata extraction → -3 days

## Next Steps

1. **Review & Feedback** (1-2 days): Stakeholder review of this proposal
2. **Detailed Design** (1 day): Create detailed specs for each capability
3. **Phase 1 Start** (Week 1): Begin educational ingestion module
4. **Continuous Integration**: Add frontend work and user testing in parallel
5. **Iterate**: Gather teacher feedback after each phase

## Success Definition

The project is successful when:
- Teachers can generate a usable lesson plan in <5 minutes
- Generated lessons require <10 minutes of teacher editing before use
- Teachers report improved lesson planning consistency
- System handles at least 100 concurrent users in production
