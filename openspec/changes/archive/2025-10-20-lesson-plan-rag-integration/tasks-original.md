# Implementation Tasks: Lesson Plan Generation via RAG

**Change ID**: `lesson-plan-rag-integration`
**Estimated Duration**: 8-12 weeks across 3 phases
**Effort**: ~40-50 engineering days

## Phase 1: Proof of Concept (2-3 weeks)

Goal: End-to-end working system with basic lesson generation

### 1.1 Educational Content Types & Metadata (1 day)

**Tasks**:
- [ ] Define Python dataclasses for educational content
  - `StandardsRecord`: Standards with grade levels, subject, code
  - `CurriculumChunk`: Lesson/activity with metadata
  - `LessonPlan`: Structured lesson output
- [ ] Add metadata extraction functions
- [ ] Write unit tests for data structures

**Files**:
- `src/jina_rag_pipeline/models/educational.py` (new)
- `tests/test_educational_models.py` (new)

**Definition of Done**:
- All dataclasses defined with docstrings
- Unit tests pass
- Serialization to/from JSON works

---

### 1.2 Standards Parser (1-2 days)

**Tasks**:
- [ ] Create standards parser module
  - Parse JSON format (structured standards documents)
  - Extract: grade level, subject, standard code, description
  - Handle hierarchy (domain → cluster → standard)
- [ ] Handle Common Core format:
  ```json
  {
    "domain": "Operations and Algebraic Thinking",
    "cluster": "Represent and solve problems",
    "standard": {
      "code": "CCSS.Math.3.OA.A.1",
      "grade": "3",
      "description": "Interpret..."
    }
  }
  ```
- [ ] Create sample standards documents for testing
- [ ] Write integration test with real standards file

**Files**:
- `src/jina_rag_pipeline/ingestion/educational/standards_parser.py` (new)
- `tests/test_standards_parser.py` (new)
- `tests/fixtures/sample_standards.json` (new)

**Definition of Done**:
- Parses sample Common Core JSON correctly
- Extracts all metadata fields
- Handles edge cases (missing fields, empty clusters)
- Integration test passes with realistic file

---

### 1.3 Educational Content Ingestion Pipeline (1.5 days)

**Tasks**:
- [ ] Extend `IngestionPipeline` to support educational content type
- [ ] Create educational chunker: chunk by learning objective, not tokens
  - Preserve metadata through chunking
  - Associate chunks with parent standard
  - Example chunk: "Grade 3 Math - CCSS.3.OA.1: Interpret multiplication..."
- [ ] Add to `TaskManager`: support educational content type detection
- [ ] Test with sample curriculum document

**Files**:
- `src/jina_rag_pipeline/ingestion/educational/__init__.py` (new)
- `src/jina_rag_pipeline/ingestion/educational/educational_chunker.py` (new)
- `tests/test_educational_ingestion.py` (new)

**Definition of Done**:
- Chunking preserves metadata relationships
- ChromaDB stores chunks with educational metadata
- Retrieval uses metadata filters correctly

---

### 1.4 Educational Retriever (1.5 days)

**Tasks**:
- [ ] Create `EducationalRetriever` class
  - Semantic search (use existing embeddings)
  - Grade level filtering
  - Subject filtering
  - Combined scoring (semantic + metadata)
- [ ] Implement ranking function:
  ```
  score = 0.5 × semantic_sim + 0.3 × grade_match + 0.2 × subject_match
  ```
- [ ] Add method: `retrieve_by_objective(objective, grade, subject) → List[Result]`
- [ ] Test with sample queries

**Files**:
- `src/jina_rag_pipeline/retrieval/educational.py` (new)
- `tests/test_educational_retriever.py` (new)

**Definition of Done**:
- Retrieves relevant materials for sample objectives
- Metadata filters work correctly
- Returns ranked results with scores
- Performance: <1 second for typical query

---

### 1.5 Lesson Plan Generation Prompt (1 day)

**Tasks**:
- [ ] Create educational generation prompts
  - System prompt: educational guidelines, pedagogical principles
  - Lesson generation prompt: structure, timing, standards alignment
  - Activity generation prompt: learning objectives, scaffolding
  - Assessment prompt: alignment, variety, rigor
- [ ] Design JSON output schema for lessons
- [ ] Test prompts with manual LLM calls
- [ ] Document prompt engineering decisions

**Files**:
- `src/jina_rag_pipeline/generation/educational_prompts.py` (new)
- `docs/PROMPT_ENGINEERING.md` (new)

**Definition of Done**:
- Prompts generate valid JSON output
- Output includes all required fields
- Sample generations are pedagogically sound
- Prompts are documented with examples

---

### 1.6 Lesson Plan Generator (1.5 days)

**Tasks**:
- [ ] Create `LessonPlanner` class
  - Method: `generate_lesson(objective, grade, duration, style="balanced") → LessonPlan`
  - Use `EducationalRetriever` to fetch materials
  - Format retrieved materials into prompt context
  - Call Qwen3 generator with lesson prompt
  - Parse response JSON into `LessonPlan` object
  - Validate all required fields present
- [ ] Error handling: malformed LLM output, missing fields
- [ ] Add logging and monitoring

**Files**:
- `src/jina_rag_pipeline/generation/lesson_planner.py` (new)
- `tests/test_lesson_planner.py` (new)

**Definition of Done**:
- Generates complete lesson plans end-to-end
- Output passes validation
- Handles errors gracefully
- Performance: <30 seconds for typical lesson
- Sample generated lessons are usable by teachers

---

### 1.7 Lesson Export - Markdown (1 day)

**Tasks**:
- [ ] Create `LessonExporter` class
  - Method: `to_markdown(lesson: LessonPlan) → str`
  - Generate readable markdown with:
    - Title, grade level, subject, duration
    - Standards alignment
    - Learning objectives
    - Materials list
    - Lesson phases with timing and activities
    - Assessments
    - Differentiation notes
- [ ] Format as human-readable, well-structured markdown
- [ ] Test export: visual inspection of output

**Files**:
- `src/jina_rag_pipeline/generation/lesson_exporter.py` (new)
- `tests/test_lesson_exporter.py` (new)

**Definition of Done**:
- Markdown output is well-formatted and readable
- All lesson components included
- Can be opened in text editor or preview
- Sample exports suitable for teacher use

---

### 1.8 API Endpoints - Lesson Generation (1 day)

**Tasks**:
- [ ] Add to `app.py`:
  ```python
  @app.post("/api/lesson-plan/generate")
  async def generate_lesson(request: GenerateLessonRequest) -> LessonPlanResponse
  ```
- [ ] Create request/response models
- [ ] Integrate with `TaskManager` for async processing
- [ ] Add error handling and validation
- [ ] Write API integration test

**Files**:
- Modify: `src/jina_rag_pipeline/api/app.py`
- Modify: `src/jina_rag_pipeline/api/models.py` (add request/response types)
- `tests/test_api_lesson_generation.py` (new)

**Definition of Done**:
- Endpoint works end-to-end via HTTP
- Accepts valid requests, returns lesson JSON
- Rejects invalid input with proper error messages
- Performance acceptable (<30s for typical request)

---

### 1.9 Basic Frontend Form (React) (1.5 days)

**Tasks**:
- [ ] Create React component: `LessonPlanForm.tsx`
  - Input fields: objective, grade level, subject, duration
  - Submit button
  - Loading state while generating
- [ ] Create component: `LessonPlanPreview.tsx`
  - Display generated lesson JSON
  - Show all sections (objectives, materials, activities, assessments)
- [ ] Connect to backend API
- [ ] Add error state and messaging
- [ ] Style with Tailwind CSS

**Files**:
- `frontend/src/pages/LessonPlans.tsx` (new)
- `frontend/src/components/LessonPlanForm.tsx` (new)
- `frontend/src/components/LessonPlanPreview.tsx` (new)
- Modify: `frontend/src/App.tsx` (add route)

**Definition of Done**:
- Form submits data to backend
- Shows loading state during generation
- Displays generated lesson
- Error messages appear on failure
- All sections visible and readable

---

### 1.10 Integration Test: End-to-End (0.5 days)

**Tasks**:
- [ ] Create integration test script
  - Upload sample standards document
  - Generate lesson from objective
  - Export as markdown
  - Verify output quality
- [ ] Run end-to-end scenario manually
- [ ] Document any issues found
- [ ] Create POC summary document

**Files**:
- `tests/test_e2e_lesson_generation.py` (new)
- `docs/POC_SUMMARY.md` (new)

**Definition of Done**:
- End-to-end flow works without errors
- Generated lessons are usable
- No blocking issues found
- POC validated with stakeholders

**Phase 1 Milestone**: Proof of concept complete, ready for teacher feedback

---

## Phase 2: Core Features (3-4 weeks)

Goal: Production-ready system with multi-format export and customization

### 2.1 Export - PDF (1 day)

**Tasks**:
- [ ] Implement `to_pdf(lesson: LessonPlan) → bytes`
- [ ] Use library: `weasyprint` or `pdfkit`
- [ ] Create professional template
- [ ] Include: header with standards, footer with page numbers
- [ ] Handle images if lesson includes them
- [ ] Test: visual inspection of PDF output

**Files**:
- Modify: `src/jina_rag_pipeline/generation/lesson_exporter.py`
- Modify: `src/jina_rag_pipeline/generation/lesson_templates.py` (new)
- Add: PDF template CSS

**Definition of Done**:
- PDF export works without errors
- Output is print-friendly and professional
- All content included and readable
- Performance: <5 seconds per export

---

### 2.2 Export - JSON (0.5 days)

**Tasks**:
- [ ] Implement `to_json(lesson: LessonPlan) → str`
- [ ] Ensure all fields serializable
- [ ] Pretty-print with indentation
- [ ] Document JSON schema

**Files**:
- Modify: `src/jina_rag_pipeline/generation/lesson_exporter.py`

**Definition of Done**:
- JSON output valid per schema
- Parseable by external tools
- Includes all lesson data

---

### 2.3 Lesson Customizer - Duration Adjustment (1 day)

**Tasks**:
- [ ] Create `LessonCustomizer` class
  - Method: `adjust_duration(lesson: LessonPlan, new_duration: int) → LessonPlan`
  - Proportionally adjust activity durations
  - Consolidate/expand phases as needed
  - Regenerate activities if needed for new duration
- [ ] Test with various duration changes

**Files**:
- `src/jina_rag_pipeline/generation/lesson_customizer.py` (new)
- `tests/test_lesson_customizer.py` (new)

**Definition of Done**:
- Duration adjustment maintains pedagogical flow
- Total activity time matches new duration
- Regenerated content is relevant

---

### 2.4 Lesson Customizer - Teaching Style (1 day)

**Tasks**:
- [ ] Extend customizer: change teaching style
  - Styles: "direct", "inquiry", "project", "balanced"
  - Regenerate activities matching style
  - Adjust assessment approach
- [ ] Create style-specific prompts
- [ ] Test: generate lessons in each style

**Files**:
- Modify: `src/jina_rag_pipeline/generation/lesson_customizer.py`
- Modify: `src/jina_rag_pipeline/generation/educational_prompts.py`

**Definition of Done**:
- Each style produces distinct, appropriate activities
- Assessment methods match teaching style
- Generated content is pedagogically sound

---

### 2.5 Lesson Customizer - Differentiation (1 day)

**Tasks**:
- [ ] Extend customizer: add differentiation options
  - Student groups: "advanced", "on_level", "struggling", "ell"
  - Regenerate activities/assessments for each group
  - Include scaffolding and support strategies
- [ ] Test with various differentiation requests

**Files**:
- Modify: `src/jina_rag_pipeline/generation/lesson_customizer.py`
- Add: differentiation strategies in prompts

**Definition of Done**:
- Each student group gets appropriate modifications
- Scaffolding strategies are evidence-based
- Modifications are practical for teachers

---

### 2.6 API Endpoints - Customization & Export (1 day)

**Tasks**:
- [ ] Add endpoints:
  ```python
  POST /api/lesson-plan/{id}/customize
  GET /api/lesson-plan/{id}/export?format=markdown|pdf|json
  POST /api/lesson-plan/{id}/regenerate-component
  ```
- [ ] Implement lesson storage (cache in database or memory)
- [ ] Add error handling for missing lessons

**Files**:
- Modify: `src/jina_rag_pipeline/api/app.py`
- Modify: `src/jina_rag_pipeline/api/models.py`

**Definition of Done**:
- All endpoints work end-to-end
- Export in all formats works
- Customization regenerates correctly

---

### 2.7 Frontend - Customization Controls (1.5 days)

**Tasks**:
- [ ] Create component: `LessonCustomizationPanel.tsx`
  - Duration slider (20-90 minutes)
  - Teaching style selector (buttons)
  - Differentiation checkboxes
  - Regenerate button
- [ ] Add component: `ExportDropdown.tsx`
  - Export as Markdown, PDF, JSON
  - Show loading while exporting
- [ ] Integrate with backend APIs
- [ ] Error handling and messaging

**Files**:
- Modify: `frontend/src/components/LessonPlanPreview.tsx`
- `frontend/src/components/LessonCustomizationPanel.tsx` (new)
- `frontend/src/components/ExportDropdown.tsx` (new)

**Definition of Done**:
- Customization controls work end-to-end
- Export downloads correct file format
- UX is intuitive and responsive

---

### 2.8 Lesson Caching & Performance (1 day)

**Tasks**:
- [ ] Add caching layer for generated lessons
  - Key: hash of (objective, grade, duration, style)
  - TTL: 24 hours
  - Cache hit check before regeneration
- [ ] Add metrics tracking for cache hits/misses
- [ ] Performance optimization: reduce LLM calls via caching

**Files**:
- Modify: `src/jina_rag_pipeline/api/app.py`
- Add: cache config

**Definition of Done**:
- Cache hits return results instantly
- Cache misses regenerate correctly
- Cache reduces API response time by ~90%

---

### 2.9 Teacher Testing & Feedback (1 week)

**Tasks**:
- [ ] Deploy Phase 2 system to test environment
- [ ] Recruit 5-10 teachers for feedback
- [ ] Collect feedback on:
  - Lesson quality and usefulness
  - Time savings vs. manual planning
  - Features they need most
  - UI usability
- [ ] Document feedback and prioritize improvements
- [ ] Make high-priority fixes

**Files**:
- `docs/TEACHER_FEEDBACK_PHASE2.md` (new)

**Definition of Done**:
- Feedback collected and documented
- High-priority issues fixed
- Teachers report positive experience

---

## Phase 3: Polish & Scale (2-3 weeks)

Goal: Production-ready, optimized system

### 3.1 Large Standards Document Handling (1 day)

**Tasks**:
- [ ] Test with 1000+ page standards documents
- [ ] Optimize ChromaDB queries for large collections
- [ ] Implement pagination/batching if needed
- [ ] Performance testing: ensure <1s retrieval with large docs

**Files**:
- `tests/test_large_standards_performance.py` (new)

**Definition of Done**:
- System handles large standards efficiently
- Retrieval performance maintained
- Memory usage stays constant

---

### 3.2 Multi-Standard Queries (1 day)

**Tasks**:
- [ ] Extend retriever: handle "cross-curricular" queries
  - Example: "Integrate math and science concepts"
  - Retrieve materials from both standards
  - Identify cross-disciplinary connections
- [ ] Create prompts for cross-curricular lessons

**Files**:
- Modify: `src/jina_rag_pipeline/retrieval/educational.py`
- Modify: `src/jina_rag_pipeline/generation/educational_prompts.py`

**Definition of Done**:
- Multi-standard queries return appropriate materials
- Generated lessons show clear connections
- Integration is pedagogically sound

---

### 3.3 Lesson Plan Editing Interface (1.5 days)

**Tasks**:
- [ ] Create component: `LessonPlanEditor.tsx`
  - Expandable sections for each lesson component
  - Edit text, update times, modify activities
  - "Regenerate this component" button
  - Save edits locally
- [ ] Integrate with backend
- [ ] Handle version history (optional: save versions)

**Files**:
- `frontend/src/components/LessonPlanEditor.tsx` (new)
- `frontend/src/components/EditableSection.tsx` (new)

**Definition of Done**:
- Teachers can edit all lesson components
- Changes persist
- Can regenerate components after editing
- Version history optional but nice-to-have

---

### 3.4 Quality Assurance & Testing (1.5 days)

**Tasks**:
- [ ] Create comprehensive test suite:
  - Unit tests for all educational modules (target: 80%+ coverage)
  - Integration tests for full workflows
  - Performance tests with realistic data
  - Load tests: 100 concurrent users
- [ ] Manual QA: test common teacher workflows
- [ ] Security testing: validate input, check for injection

**Files**:
- `tests/test_coverage_report.md` (new)

**Definition of Done**:
- Test coverage >80%
- All workflows pass integration tests
- Performance meets targets
- Security issues addressed

---

### 3.5 Documentation & Deployment Guide (1 day)

**Tasks**:
- [ ] Create user documentation
  - Getting started guide
  - Feature walkthrough
  - Tips for best results
- [ ] Create admin documentation
  - Deploying with standards documents
  - Configuration options
  - Monitoring and maintenance
- [ ] Create developer documentation
  - Architecture overview
  - Adding new education types (STEAM, CTE)
  - Customizing prompts

**Files**:
- `docs/USER_GUIDE.md` (new)
- `docs/ADMIN_GUIDE.md` (new)
- `docs/DEVELOPER_GUIDE.md` (new)
- `docs/DEPLOYMENT.md` (new)

**Definition of Done**:
- Docs are comprehensive and clear
- New users can get started in <30 minutes
- Admins can deploy and configure system
- Developers understand architecture

---

### 3.6 Production Deployment (1 day)

**Tasks**:
- [ ] Deploy to production environment
- [ ] Configure auto-scaling if needed
- [ ] Set up monitoring and alerts
- [ ] Create runbooks for common issues
- [ ] Perform final load testing
- [ ] Monitor first week post-deployment

**Files**:
- `ops/DEPLOYMENT_RUNBOOK.md` (new)
- `ops/TROUBLESHOOTING_GUIDE.md` (new)

**Definition of Done**:
- System deployed and stable
- All endpoints responding normally
- Monitoring active
- Team confident in support

---

### 3.7 Extended Teacher Testing (1-2 weeks)

**Tasks**:
- [ ] Expand teacher testing to 20-50 teachers
- [ ] Collect usage metrics
- [ ] Gather feedback on:
  - Which features are most used
  - Pain points and issues
  - Feature requests
- [ ] Iterate on UI/features based on feedback
- [ ] Track adoption metrics

**Files**:
- `docs/TEACHER_FEEDBACK_PHASE3.md` (new)
- `docs/USAGE_METRICS.md` (new)

**Definition of Done**:
- Large-scale testing completed
- High teacher satisfaction (>4/5 rating)
- System handles production load
- Clear roadmap for Phase 4

---

## Cross-Phase Activities

### Testing & Validation
- **Unit Tests**: Add throughout all phases (target: 80%+ coverage)
- **Integration Tests**: Add after each feature completion
- **Teacher Testing**: Continuous feedback loop starting Phase 1

### Documentation
- **API Documentation**: Update as endpoints added
- **Architecture Docs**: Update in design.md as changes made
- **User Guides**: Create during Phase 2, refine during Phase 3
- **Prompt Library**: Document all prompts as they're created

### Dependencies & Blockers
- **Dependency**: Requires working RAG system (✅ already deployed)
- **Dependency**: Requires Qwen3 model loaded (✅ already deployed)
- **Blocker**: If retrieval quality poor, generation quality suffers (mitigation: extensive testing)

## Success Metrics

### Phase 1 (POC)
- System generates usable lesson outlines end-to-end
- Teachers can import output into their workflow
- No critical bugs in core flow

### Phase 2 (Core)
- Export in all formats works perfectly
- Customization features are actually used by teachers
- System handles 100 concurrent users
- Teachers report 30% time savings

### Phase 3 (Polish)
- Large standards documents handled efficiently
- Teachers report 50% time savings
- System stability: 99.9% uptime over 30 days
- Teacher feedback score: ≥4.2/5

---

## Ongoing Maintenance & Support

After Phase 3 (weeks 9-12+):
- Monitor system for issues and performance degradation
- Gather ongoing teacher feedback
- Plan Phase 4 enhancements based on usage data
- Support teacher onboarding and training
