# Lesson Plan Generation via RAG - OpenSpec Proposal

## Overview

This OpenSpec proposal transforms your production-ready Jina RAG system into a **specialized lesson plan generation engine** for K-12 educators. The proposal is organized into complete, actionable documents that cover the architecture, design, specifications, and implementation roadmap.

## What You'll Find Here

```
lesson-plan-rag-integration/
├── README.md (this file)
├── proposal.md              # Executive proposal with scope and rationale
├── design.md                # Architectural design and component details
├── tasks.md                 # Phase-by-phase implementation tasks
└── specs/
    ├── educational-content-ingestion/spec.md
    ├── lesson-plan-generation/spec.md
    └── teacher-customization/spec.md
```

## Key Documents

### 1. **proposal.md** - Start Here
- **Read this first** to understand the full vision
- Problem statement: Teachers spend 5-10 hours planning a lesson manually
- Solution: Teachers input objective → system generates standards-aligned lesson
- Phased approach: POC (2-3 wks) → Core (3-4 wks) → Polish (2-3 wks)
- Success criteria and risk mitigation

**Key insight**: This builds on your existing RAG foundation—no need to rebuild embeddings, storage, or async infrastructure. We layer educational-specific capabilities on top.

### 2. **design.md** - Architecture & Decisions
- High-level architecture showing how lesson generation fits into existing RAG
- 5 new component modules:
  1. **Educational Content Ingestion**: Parse standards, extract metadata
  2. **Educational Retrieval**: Standards-aware semantic search
  3. **Lesson Template Engine**: Generate structured lesson JSON
  4. **Customization & Refinement**: Let teachers adjust generated lessons
  5. **Export Service**: Output in markdown, PDF, JSON formats

- Data flow diagram showing end-to-end generation pipeline
- Database schema for educational metadata
- Performance targets and optimization strategies

### 3. **tasks.md** - Implementation Roadmap
- **130+ specific tasks** organized by phase
- Phase 1 (2-3 weeks): Proof of concept, basic generation
- Phase 2 (3-4 weeks): Multi-format export, customization controls
- Phase 3 (2-3 weeks): Performance optimization, polish

Each task includes:
- Clear acceptance criteria
- Files to create/modify
- Definition of done
- Dependencies

### 4. **Capability Specifications** - The Details
- `specs/educational-content-ingestion/spec.md`: Parse standards, extract metadata
- `specs/lesson-plan-generation/spec.md`: Generate lessons, align to standards
- `specs/teacher-customization/spec.md`: Customize, share, export lessons

Each spec includes:
- ADDED requirements with scenarios and acceptance criteria
- Implementation notes and data structures
- Performance targets
- Testing strategy

## Quick Summary

### What This Enables (Phase 1 POC)
✅ Teachers upload their own materials (any format the RAG system supports)
✅ Teachers input: "Grade 3 Math, Understanding fractions, 45 minutes"
✅ System retrieves: Relevant materials from teacher's collection
✅ System generates: Clean markdown lesson with objectives, materials, activities, assessments
✅ Teacher downloads: Editable .md file (works in any text editor, version control)
✅ Phase 2+: Customization, PDF/JSON export, optional standards alignment

### Architecture at a Glance
```
Teacher uploads materials → Existing RAG ingestion pipeline
    ↓
Materials indexed in ChromaDB (already working)
    ↓
Teacher → Frontend Form (topic, grade, subject, duration)
    ↓
API: POST /api/lesson-plan/generate
    ↓
Educational Retrieval (semantic search + optional metadata)
    ↓
Lesson Generation (Qwen3 + markdown templates)
    ↓
Clean markdown with YAML frontmatter
    ↓
Download .md file (future: PDF/JSON export)
```

### Effort Estimate (Simplified Approach)
- **Phase 1 (POC)**: 5-7 days → Markdown lessons working end-to-end
- **Phase 2 (Enhanced)**: 8-10 days → Customization, PDF/JSON export
- **Phase 3 (Polish)**: 6-8 days → Production-ready, performant
- **Total**: ~25-35 engineering days over 5-8 weeks

**Faster than original** by removing standards parsing complexity and starting markdown-only.

### Why This Works
1. **Reuses existing RAG pipeline**: Material ingestion already handles PDFs, PPTX, images, docs
2. **No pre-structured content needed**: Works with whatever materials teachers have
3. **Markdown-first**: Simple, editable, convertible—proves concept before adding complexity
4. **Grade/subject agnostic**: No pre-configuration or standards documents required
5. **Fastest path to validation**: Get teacher feedback in 1-2 weeks instead of 2-3 months

## Next Steps

### For Review (You)
1. ✅ Read `proposal.md` - understand the vision and scope
2. ✅ Review `design.md` - validate architectural approach
3. ✅ Skim `tasks.md` - see level of detail in implementation plan
4. ✅ Check one spec (`lesson-plan-generation/spec.md`) - see requirement format

### Feedback Points
- Is the scope right for Phase 1? Too much? Too little?
- Do you want to start with standards-aligned lessons or more general lesson planning?
- Should we prioritize multi-format export (Phase 2) or more customization options?
- Do you have teacher contacts who can provide feedback early?

### To Begin Implementation
1. Initialize OpenSpec with `openspec init` (interactive setup)
2. Start with Phase 1, Task 1.1: Define educational data models
3. Build incrementally, getting feedback after each task
4. Each phase has a "milestone" checkpoint for teacher review

## File Structure Reference

### New Python Modules (To Be Created)
```
src/jina_rag_pipeline/
├── models/
│   └── educational.py                    # Data models for content
├── ingestion/educational/
│   ├── __init__.py
│   ├── standards_parser.py              # Parse standards documents
│   └── educational_chunker.py           # Smart chunking
├── retrieval/
│   └── educational.py                    # Standards-aware retrieval
├── generation/
│   ├── educational_prompts.py           # Lesson-specific prompts
│   ├── lesson_planner.py                # Generate lessons
│   ├── lesson_customizer.py             # Customize components
│   ├── lesson_exporter.py               # Export to multiple formats
│   └── lesson_templates.py              # Export templates
└── api/
    └── [modifications to app.py, models.py for new endpoints]
```

### New Frontend Components (To Be Created)
```
frontend/src/
├── pages/
│   └── LessonPlans.tsx                  # Main lesson planning page
├── components/
│   ├── LessonPlanForm.tsx               # Input form
│   ├── LessonPlanPreview.tsx            # Display generated lesson
│   ├── LessonCustomizationPanel.tsx     # Customization controls
│   ├── LessonPlanEditor.tsx             # Edit lesson components
│   └── ExportDropdown.tsx               # Export options
└── [integration with existing API calls]
```

## Key Decisions Made in This Proposal

1. **Markdown-first output** (Phase 1): Lessons are clean markdown, not JSON/PDF initially
   - Reason: Markdown is universal, editable, convertible. Proves concept before complexity.

2. **Material-agnostic**: No standards parsing or pre-structured content required
   - Reason: Works with whatever teachers have. Lowers barrier to entry.

3. **Optional metadata extraction**: Best-effort grade/subject detection
   - Reason: Improves retrieval when possible, but doesn't fail without it.

4. **Semantic search + light filtering**: Leverage existing Jina embeddings
   - Reason: Already working, performant, and "good enough" for POC.

5. **Phased rollout**: POC (markdown) → Enhanced (PDF/JSON/customization) → Polish
   - Reason: Faster validation, lower risk, teacher-driven iteration.

6. **Teacher control**: Editable markdown, not black-box automation
   - Reason: Education requires human judgment; AI is assistant, not replacement.

## Success Metrics

### Phase 1 (POC) Success
- System generates usable lesson outlines end-to-end
- No critical bugs in core workflow
- Lessons are importable into teacher workflow

### Phase 2 (Core) Success
- Export works in all formats perfectly
- Teachers report 30% time savings vs. manual planning
- System handles 100 concurrent users

### Phase 3 (Polish) Success
- Teachers report 50% time savings
- System stability: 99.9% uptime over 30 days
- Teacher satisfaction: ≥4.2/5 rating

## Getting Started

1. **Understand the scope**: Read `proposal.md` (15 minutes)
2. **Validate the approach**: Review `design.md` (20 minutes)
3. **Plan the work**: Skim `tasks.md` (10 minutes)
4. **Go deep on one area**: Read `specs/lesson-plan-generation/spec.md` (10 minutes)
5. **Make a decision**: Start Phase 1 or iterate on proposal?

## Questions or Clarifications?

- **Scope too broad?** Focus on Phase 1 only initially (POC)
- **Need more detail on X?** Check the detailed spec for that capability
- **Want to adjust approach?** Modify `design.md` with your preferences
- **Need code examples?** Implementation starts in Phase 1, Task 1.1

---

## Appendix: Existing RAG System You're Building On

Your current system already has:
- ✅ Jina Embeddings v4 (2048-D, Apple Silicon optimized)
- ✅ ChromaDB vector storage with similarity search
- ✅ Async processing with ThreadPool + RQ workers
- ✅ Real-time progress tracking via WebSocket
- ✅ Multi-format document ingestion (PDF, PPTX, images, markdown)
- ✅ Multimodal support (text + image embeddings)
- ✅ Metrics and monitoring dashboard
- ✅ Production-ready deployment (Docker, Kubernetes)
- ✅ Qwen3-14B-4bit model for generation

**This proposal leverages all of the above** by adding educational-specific layers on top. No rebuilding needed.

---

**Proposal Version**: 1.0
**Date**: 2025-10-18
**Status**: Ready for Review
