# Implementation Tasks: Lesson Plan Generation (Simplified POC-First)

**Change ID**: `lesson-plan-rag-integration`
**Approach**: Material-agnostic, markdown-first, grade/subject flexible
**Estimated Duration**: 5-8 weeks across 3 phases
**Effort**: ~25-35 engineering days

## Phase 1: Proof of Concept (1-2 weeks, 5-7 days)

Goal: Teachers upload materials → generate markdown lesson plans

### 1.1 Educational Data Models (0.5 days)

**Tasks**:
- [ ] Define Python dataclass for `LessonPlan`
  - Metadata: title, grade, subject, duration (default: 50 min)
  - Components: objectives, materials, activities, assessments
  - **Sources**: list of source citations
  - **Images**: list of embedded images with captions
- [ ] Define `RetrievedMaterial` dataclass
  - content, document_name, page_number, chunk_id
  - relevance_score, source_type ("text", "image", "table")
- [ ] Define `RetrievalContext` for passing materials to generator
- [ ] Write unit tests for serialization

**Files**:
- `src/jina_rag_pipeline/models/educational.py` (new)
- `tests/test_educational_models.py` (new)

**Definition of Done**:
- All dataclasses defined with clear docstrings
- Source citation tracking built into models
- Image metadata included
- Can serialize to/from dict (for API responses)
- Unit tests pass

---

### 1.2 Simple Metadata Extraction (0.5 days)

**Tasks**:
- [ ] Add optional metadata extractor for uploaded files
  - Detect grade level keywords ("grade 3", "kindergarten", "high school")
  - Detect subject keywords ("math", "science", "reading", "history")
  - Store as ChromaDB metadata when detected
- [ ] No required metadata - system works without it
- [ ] Test with diverse file types

**Files**:
- `src/jina_rag_pipeline/ingestion/educational/metadata_hints.py` (new)
- `tests/test_metadata_extraction.py` (new)

**Definition of Done**:
- Metadata extraction is best-effort (doesn't fail if missing)
- Works on PDFs, DOCX, PPTX, markdown
- Stores metadata in ChromaDB chunks

---

### 1.3 Educational Retrieval Module (1.5 days)

**Tasks**:
- [ ] Create `EducationalRetriever` class
  - Uses existing `ChromaVectorStore`
  - Adds optional metadata filtering (grade, subject)
  - Falls back to pure semantic search if no metadata
  - Method: `retrieve_for_lesson(topic, grade=None, subject=None, top_k=5)`
  - **NEW**: Method: `retrieve_images(topic, grade=None, top_k=3)`
- [ ] Implement combined text + image retrieval
  - Retrieve top-5 text chunks
  - Retrieve top-3 images (using existing multimodal RAG)
  - Return `RetrievedMaterial` objects with full source metadata
- [ ] Track source attribution for each retrieved item
  - Document name, page number, chunk location
  - Store for citation generation
- [ ] Test with sample materials including images

**Files**:
- `src/jina_rag_pipeline/retrieval/educational.py` (new)
- `tests/test_educational_retriever.py` (new)

**Definition of Done**:
- Retrieves both text and images using semantic search
- Source metadata captured for all materials
- Metadata filtering works when present
- Performance: <1 second for typical query
- Returns RetrievedMaterial objects with citations

---

### 1.4 Lesson Generation Prompts (0.5 days)

**Tasks**:
- [ ] Create markdown lesson template prompt
  - System prompt: educational guidelines, markdown formatting
  - **Citation instructions**: "MUST cite sources as [1], [2], etc."
  - **Image instructions**: "Include images with ![alt](path) syntax"
  - Lesson prompt: structure with headers, lists, timing
  - Output format: markdown with YAML frontmatter
- [ ] Design markdown structure:
  ```markdown
  ---
  title: "Understanding Fractions"
  grade: "3"
  subject: "Mathematics"
  duration: 50
  ---

  # Learning Objectives
  - Define fractions [1]
  - Use visual models [1][3]

  # Materials Needed
  - Fraction circles [1]
  - Worksheet [2]

  ![Fraction diagram](images/fractions.png)
  *Figure 1: Fraction representations [Source: Visual_Aids.pdf]*

  # Lesson Flow
  ## Engagement (5 minutes)
  ...

  ## Sources Referenced
  [1] Chapter 3: Fractions (Textbook.pdf, pages 45-52)
  [2] Activities Workbook (Activities.docx)
  [3] Visual Aids (Diagrams.pptx, slide 5)
  ```
- [ ] Test prompts manually with Qwen3
- [ ] Verify citations and images appear in output

**Files**:
- `src/jina_rag_pipeline/generation/educational_prompts.py` (new)
- `docs/LESSON_MARKDOWN_FORMAT.md` (new - template spec with citation examples)

**Definition of Done**:
- Prompts generate valid markdown with citations
- Images included with proper markdown syntax
- Source reference list at end of lesson
- Output is clean and readable
- Sample generations include all required elements
- Documented with citation and image examples

---

### 1.5 Lesson Plan Generator (2 days)

**Tasks**:
- [ ] Create `LessonPlanner` class
  - Method: `generate_lesson(topic, objective, grade, duration=50, teaching_style="balanced")`
  - Uses `EducationalRetriever` to fetch:
    - Top-5 text materials
    - Top-3 images
  - **Format context with source numbers**:
    ```
    [1] Chapter 3: Fractions (Textbook.pdf, pages 45-52)
        Content: "A fraction represents..."
    [2] Activities Workbook (Activities.docx)
        Content: "Paper folding activity..."
    [IMG-1] Fraction diagram (Visual_Aids.pptx, slide 5)
        Description: Circle divided into fourths
    ```
  - Calls Qwen3 with lesson prompt + numbered sources
  - Parses markdown output
  - Validates citations present
  - Extracts image references and paths
  - Builds source reference list
- [ ] Image handling:
  - Copy referenced images to lesson-specific directory
  - Update markdown paths to correct locations
  - Generate image captions with source attribution
- [ ] Error handling for malformed output
- [ ] Add logging and monitoring
- [ ] Parse YAML frontmatter from output

**Files**:
- `src/jina_rag_pipeline/generation/lesson_planner.py` (new)
- `src/jina_rag_pipeline/generation/citation_builder.py` (new - helper)
- `tests/test_lesson_planner.py` (new)

**Definition of Done**:
- Generates complete markdown lessons with citations
- Images embedded with proper syntax and attribution
- Source reference list at end of lesson
- All retrieved materials cited at least once
- Output validates as proper markdown
- YAML frontmatter includes grade (abbreviated format)
- Default duration: 50 minutes
- Performance: <30 seconds typical
- Sample lessons are usable and properly attributed

---

### 1.6 API Endpoint - Generate Lesson (1 day)

**Tasks**:
- [ ] Add to `app.py`:
  ```python
  @app.post("/api/lesson-plan/generate")
  async def generate_lesson(request: GenerateLessonRequest) -> LessonMarkdownResponse
  ```
- [ ] Request model:
  ```python
  class GenerateLessonRequest:
      topic: str
      learning_objective: str
      grade_level: str  # "K", "1", "2", "3-5", "6-8", "9-12", "College"
      subject: str
      duration_minutes: int = 50  # DEFAULT CHANGED TO 50
      teaching_style: str = "balanced"
  ```
- [ ] Response model:
  ```python
  class LessonMarkdownResponse:
      markdown: str
      metadata: dict  # title, grade, subject, duration
      sources_count: int
      images_count: int
  ```
- [ ] Validation:
  - Grade level in allowed list
  - Duration: 20-90 minutes
  - Teaching style in allowed values
- [ ] Integrate with TaskManager for async processing (optional for POC)
- [ ] Error handling and validation

**Files**:
- Modify: `src/jina_rag_pipeline/api/app.py`
- Modify: `src/jina_rag_pipeline/api/models.py`
- `tests/test_api_lesson_generation.py` (new)

**Definition of Done**:
- Endpoint works via HTTP POST
- Returns markdown lesson with citations and images
- Default duration is 50 minutes
- Grade format is abbreviated (K, 1-12, College)
- Rejects invalid input with clear errors
- Performance acceptable (<30s)
- Response includes counts of sources and images

---

### 1.7 Frontend - Lesson Plan Form (1 day)

**Tasks**:
- [ ] Create React page: `LessonPlans.tsx`
- [ ] Create component: `LessonPlanForm.tsx`
  - Input: topic, objective
  - **Grade dropdown**: K, 1-12, College, ranges (K-2, 3-5, 6-8, 9-12)
  - Subject dropdown: Math, Science, ELA, Social Studies, etc.
  - **Duration slider**: 20-90 min, default 50
  - Teaching style: Direct, Inquiry, Project, Balanced
  - Submit button → API call
  - Loading state while generating
- [ ] Create component: `LessonMarkdownPreview.tsx`
  - Display markdown with syntax highlighting
  - **Show embedded images** (render from markdown)
  - **Highlight citations** (make [1], [2] stand out)
  - Copy to clipboard button
  - Download as .md file button
  - **Show metadata**: sources count, images count
- [ ] Basic styling with Tailwind CSS

**Files**:
- `frontend/src/pages/LessonPlans.tsx` (new)
- `frontend/src/components/LessonPlanForm.tsx` (new)
- `frontend/src/components/LessonMarkdownPreview.tsx` (new)
- Modify: `frontend/src/App.tsx` (add route)
- `frontend/src/constants/educationOptions.ts` (new - grade/subject lists)

**Definition of Done**:
- Form submits to backend API with default duration = 50
- Grade dropdown uses abbreviated format
- Loading state shows during generation
- Markdown displays with preview
- **Images render inline from markdown**
- **Citations highlighted/clickable**
- Can download .md file (with images included as references)
- Error messages on failure
- Shows "3 sources, 2 images" count

---

### 1.8 Integration Test - End to End (0.5 days)

**Tasks**:
- [ ] Upload sample teaching materials (3-5 PDFs/docs with images)
- [ ] Generate lesson for "Grade 3 Math - Understanding Fractions"
  - **Verify**: Citations present (at least 3 sources)
  - **Verify**: Images embedded (at least 1 image)
  - **Verify**: Source reference list at end
  - **Verify**: Grade format is "3" (abbreviated)
  - **Verify**: Duration is 50 minutes
- [ ] Generate lesson for "High School Biology - Photosynthesis"
  - **Verify**: Different sources retrieved
  - **Verify**: Grade format is "9-12"
  - **Verify**: Subject-appropriate materials
- [ ] Test with different durations (30, 50, 75 minutes)
- [ ] Verify image paths work and images display
- [ ] Document any issues
- [ ] Create POC demo video/screenshots

**Files**:
- `tests/test_e2e_lesson_generation.py` (new)
- `tests/fixtures/sample_materials/` (sample PDFs, images)
- `docs/POC_DEMO.md` (new - with screenshots showing citations and images)

**Definition of Done**:
- End-to-end flow works without errors
- **All lessons include source citations**
- **Images appear in generated lessons**
- **Default duration is 50 minutes**
- **Grade format is abbreviated**
- Generated lessons are readable and usable
- Works for multiple grade levels and subjects
- No blocking issues
- POC validated and documented with visual examples

**Phase 1 Milestone**: Working POC with citations and images, ready for teacher feedback

---

## Phase 2: Enhanced Features (2-3 weeks, 8-10 days)

Goal: Customization, format conversion, optional standards

### 2.1 Lesson Customization - Duration (1 day)

**Tasks**:
- [ ] Create `LessonCustomizer` class
  - Method: `adjust_duration(lesson_markdown, new_duration)`
  - Parse markdown, adjust activity timings
  - Regenerate with new constraints
- [ ] Test with various duration changes (20-90 minutes)

**Files**:
- `src/jina_rag_pipeline/generation/lesson_customizer.py` (new)
- `tests/test_lesson_customizer.py` (new)

**Definition of Done**:
- Duration adjustments maintain lesson quality
- Activities scale proportionally
- Total time matches new duration

---

### 2.2 Lesson Customization - Teaching Style (1 day)

**Tasks**:
- [ ] Extend customizer: change teaching style
  - Styles: "direct", "inquiry", "project", "balanced"
  - Different prompt templates per style
  - Regenerate activities matching style
- [ ] Test: same topic, different styles

**Files**:
- Modify: `src/jina_rag_pipeline/generation/lesson_customizer.py`
- Modify: `src/jina_rag_pipeline/generation/educational_prompts.py`

**Definition of Done**:
- Each style produces distinct activities
- Pedagogically appropriate for style
- Performance: <20s regeneration

---

### 2.3 Export - Markdown to PDF (1 day)

**Tasks**:
- [ ] Add PDF conversion using `weasyprint` or `pandoc`
- [ ] Create professional PDF template
- [ ] Method: `markdown_to_pdf(markdown_content) -> bytes`
- [ ] Include proper styling (headers, lists, page breaks)

**Files**:
- `src/jina_rag_pipeline/generation/lesson_exporter.py` (new)
- Add: PDF template CSS

**Definition of Done**:
- PDF conversion works reliably
- Output is professional and print-friendly
- Performance: <5 seconds per conversion

---

### 2.4 Export - Markdown to JSON (0.5 days)

**Tasks**:
- [ ] Parse markdown to structured JSON
- [ ] Extract YAML frontmatter → metadata
- [ ] Parse sections → JSON objects
- [ ] Method: `markdown_to_json(markdown_content) -> dict`

**Files**:
- Modify: `src/jina_rag_pipeline/generation/lesson_exporter.py`

**Definition of Done**:
- JSON output is valid and complete
- Preserves all lesson data
- Can round-trip: JSON → markdown

---

### 2.5 Optional Standards Alignment (1 day)

**Tasks**:
- [ ] Add optional standards metadata field
- [ ] If teacher uploads standards docs, index with type="standard"
- [ ] Retrieval can filter for standards when requested
- [ ] Lesson can include standards section if available
- [ ] NOT required - fully optional enhancement

**Files**:
- Modify: `src/jina_rag_pipeline/ingestion/educational/metadata_hints.py`
- Modify: `src/jina_rag_pipeline/generation/educational_prompts.py`

**Definition of Done**:
- Standards indexing works when docs provided
- Lessons include standards when available
- System works fine without any standards

---

### 2.6 API Endpoints - Customization & Export (1 day)

**Tasks**:
- [ ] Add endpoints:
  ```python
  POST /api/lesson-plan/customize
  GET /api/lesson-plan/export?format=pdf|json
  ```
- [ ] Store generated lessons temporarily (in-memory cache or Redis)
- [ ] Error handling

**Files**:
- Modify: `src/jina_rag_pipeline/api/app.py`
- Modify: `src/jina_rag_pipeline/api/models.py`

**Definition of Done**:
- All endpoints work end-to-end
- Export in PDF and JSON works
- Customization regenerates correctly

---

### 2.7 Frontend - Customization & Export UI (1.5 days)

**Tasks**:
- [ ] Add customization panel to lesson preview
  - Duration slider
  - Teaching style buttons
  - Regenerate button
- [ ] Add export dropdown
  - Download as PDF
  - Download as JSON
  - Copy markdown
- [ ] Show loading states during operations

**Files**:
- `frontend/src/components/LessonCustomizationPanel.tsx` (new)
- `frontend/src/components/ExportDropdown.tsx` (new)
- Modify: `frontend/src/components/LessonMarkdownPreview.tsx`

**Definition of Done**:
- Customization controls work
- Export downloads correct format
- UX is smooth and intuitive

---

### 2.8 Teacher Testing & Feedback (1 week)

**Tasks**:
- [ ] Deploy Phase 2 to test environment
- [ ] Recruit 3-5 teachers for testing
- [ ] Collect feedback on:
  - Lesson quality
  - UI usability
  - Missing features
- [ ] Document feedback and prioritize fixes

**Files**:
- `docs/TEACHER_FEEDBACK_PHASE2.md` (new)

**Definition of Done**:
- Feedback collected and documented
- Critical issues fixed
- Teachers report positive experience

---

## Phase 3: Polish & Scale (2-3 weeks, 6-8 days)

Goal: Production-ready, performant, polished UX

### 3.1 Performance Optimization (1 day)

**Tasks**:
- [ ] Add caching for generated lessons
  - Key: hash of (topic, grade, subject, duration, style)
  - TTL: 24 hours
- [ ] Test with large material collections (100+ documents)
- [ ] Optimize ChromaDB queries
- [ ] Performance testing: 100 concurrent users

**Files**:
- `tests/test_performance.py` (new)

**Definition of Done**:
- Cache reduces response time by ~80%
- System handles 100 concurrent users
- Large collections perform well

---

### 3.2 Inline Editing (1.5 days)

**Tasks**:
- [ ] Create markdown editor component
  - Syntax highlighting
  - Live preview
  - Save edited version
- [ ] "Regenerate section" buttons
  - Regenerate just one section
  - Keep rest of lesson intact

**Files**:
- `frontend/src/components/MarkdownEditor.tsx` (new)

**Definition of Done**:
- Teachers can edit markdown inline
- Changes persist
- Can regenerate individual sections

---

### 3.3 Lesson Library & Management (1 day)

**Tasks**:
- [ ] Save generated lessons to database
- [ ] List view of past lessons
- [ ] Search/filter saved lessons
- [ ] Delete/archive lessons

**Files**:
- `src/jina_rag_pipeline/api/lesson_storage.py` (new)
- `frontend/src/components/LessonLibrary.tsx` (new)

**Definition of Done**:
- Teachers can save and organize lessons
- Search works effectively
- Performance with 100+ saved lessons

---

### 3.4 Quality Assurance & Testing (1.5 days)

**Tasks**:
- [ ] Comprehensive test suite:
  - Unit tests: 80%+ coverage
  - Integration tests for workflows
  - Load testing
- [ ] Manual QA with diverse materials
- [ ] Security testing (input validation)

**Files**:
- `tests/test_coverage_report.md` (new)

**Definition of Done**:
- Test coverage >80%
- All workflows tested
- Security validated

---

### 3.5 Documentation (1 day)

**Tasks**:
- [ ] User guide: getting started, best practices
- [ ] Admin guide: deployment, configuration
- [ ] Developer guide: architecture, extending

**Files**:
- `docs/USER_GUIDE.md` (new)
- `docs/ADMIN_GUIDE.md` (new)
- `docs/DEVELOPER_GUIDE.md` (new)

**Definition of Done**:
- Docs comprehensive and clear
- New users can get started easily

---

### 3.6 Production Deployment (1 day)

**Tasks**:
- [ ] Deploy to production
- [ ] Configure monitoring and alerts
- [ ] Final load testing
- [ ] Create runbooks

**Files**:
- `ops/DEPLOYMENT_RUNBOOK.md` (new)

**Definition of Done**:
- System deployed and stable
- Monitoring active
- Team confident in support

---

## Summary of Changes from Original

**Removed** (moved to Phase 2+):
- ❌ Standards document parsing (10 tasks, ~3 days)
- ❌ Multi-format export initially (PDF/JSON come in Phase 2)
- ❌ Complex metadata extraction (simplified to keyword hints)
- ❌ Standards-specific retrieval logic

**Kept & Simplified**:
- ✅ Material ingestion (uses existing RAG pipeline directly)
- ✅ Semantic retrieval (with optional metadata filtering)
- ✅ Lesson generation (markdown-first, clean templates)
- ✅ Basic frontend (input form + markdown preview)

**Result**:
- Phase 1: **1-2 weeks** instead of 2-3 weeks
- Total effort: **25-35 days** instead of 40-50 days
- Faster to validate with teachers
- Simpler to maintain and extend

## Success Metrics

### Phase 1 (POC)
- Teachers can upload materials and generate lessons end-to-end
- Markdown output is immediately usable
- Works for any grade level and subject
- Teachers report lessons save time vs. manual planning

### Phase 2 (Enhanced)
- Customization features actually used
- PDF/JSON exports work perfectly
- Optional standards alignment adds value

### Phase 3 (Polish)
- 99.9% uptime over 30 days
- Teachers report 50% time savings
- Satisfaction: ≥4.2/5
