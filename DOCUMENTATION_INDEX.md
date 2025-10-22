# Pretty Please Codebase Documentation Index

This index provides a guide to all the comprehensive documentation created for the Pretty Please RAG pipeline project.

## Documentation Files

### 1. CODEBASE_STRUCTURE_ANALYSIS.md (27 KB, 765 lines)
**Comprehensive technical architecture documentation**

Primary audience: Architects, senior developers, technical leads

Contains:
- Detailed project overview and feature list
- Frontend/backend separation patterns
- Complete directory structures with file-by-file descriptions
- 7-stage RAG pipeline architecture with flow diagrams
- All 50+ API endpoints documented with request/response specs
- Backend module reference guide
- Configuration system documentation
- Frontend component map and state management
- Recent commits and recent changes analysis
- Data flow diagrams (Ingestion, Search, Lesson Generation)
- Key connection points between frontend and backend

**Start here if you need:** Deep understanding of architecture, module relationships, data flow

### 2. QUICK_REFERENCE.md (14 KB, 550 lines)
**Practical development and operations guide**

Primary audience: Developers, DevOps engineers, API integrators

Contains:
- Quick start (make start, service URLs, logs)
- 50+ curl examples for all API endpoints
- Frontend component organization and routing
- Backend module API reference with Python code examples
- Database schema documentation
- Environment variables configuration
- Common tasks with step-by-step examples
- Troubleshooting section with solutions
- File locations and important directories
- Service management commands

**Start here if you need:** How to run the system, API examples, common tasks, quick answers

### 3. ANALYSIS_SUMMARY.txt (8 KB)
**Executive summary and high-level overview**

Primary audience: Project managers, stakeholders, new team members

Contains:
- One-page architecture overview
- Key findings from analysis
- Frontend/backend separation summary
- Main module descriptions
- RAG pipeline flow at a glance
- Recent improvements (last 5 commits)
- Configuration system overview
- API endpoint categories
- Performance metrics from tests
- Strengths of current architecture
- Next steps for developers

**Start here if you need:** Quick understanding of project status and architecture

---

## Quick Navigation

### For Different Roles

**I'm a new developer joining the project:**
1. Read ANALYSIS_SUMMARY.txt (5 min overview)
2. Follow Quick Start in QUICK_REFERENCE.md
3. Run `make start` to see it in action
4. Review CODEBASE_STRUCTURE_ANALYSIS.md sections as needed

**I'm working on the frontend:**
1. Check "Frontend Component Map" in QUICK_REFERENCE.md
2. Review pages and components in CODEBASE_STRUCTURE_ANALYSIS.md
3. Look at frontend-specific API calls in QUICK_REFERENCE.md

**I'm working on the backend:**
1. Study "Backend Module Reference" in CODEBASE_STRUCTURE_ANALYSIS.md
2. Check "Backend Module Reference" examples in QUICK_REFERENCE.md
3. Review specific ingestion/embeddings/storage module docs
4. Use `/docs` endpoint for live API documentation

**I need to debug an issue:**
1. Check "Troubleshooting" section in QUICK_REFERENCE.md
2. Look at file locations for logs
3. Review relevant module in CODEBASE_STRUCTURE_ANALYSIS.md
4. Check recent commits for context

**I'm integrating with the API:**
1. Read API reference in QUICK_REFERENCE.md (curl examples)
2. Review full endpoint specs in CODEBASE_STRUCTURE_ANALYSIS.md
3. Visit http://localhost:8000/docs for interactive documentation
4. Check data models in CODEBASE_STRUCTURE_ANALYSIS.md

**I'm deploying or managing the system:**
1. Read Configuration section in CODEBASE_STRUCTURE_ANALYSIS.md
2. Check "Common Tasks" and "Troubleshooting" in QUICK_REFERENCE.md
3. Review File Locations section
4. Check Environment Variables section

---

## Key Concepts Explained

### Frontend/Backend Communication
**Location:** CODEBASE_STRUCTURE_ANALYSIS.md, Section "Frontend-Backend Communication"

The system uses:
- RESTful API for most operations (base URL: `/api`)
- WebSocket for real-time progress (`/ws/progress/{task_id}`)
- Static file serving for production deployment

### RAG Pipeline Architecture
**Location:** CODEBASE_STRUCTURE_ANALYSIS.md, Section "RAG Pipeline Architecture"

7-stage processing pipeline:
1. Document upload and validation
2. OCR ingestion (DeepseekOCR + GUNDAM mode)
3. Document processing and parsing
4. Semantic chunking
5. Embedding generation (Jina v4)
6. Vector storage (ChromaDB)
7. Artifact organization

### Configuration System
**Location:** CODEBASE_STRUCTURE_ANALYSIS.md, Section "Configuration Files"

Runtime-updatable configurations for:
- Embeddings (task, dimensions, format)
- OCR (resolution, grounding, compression)
- RAG (retrieval, reranking, citation)
- Per-collection settings

### API Endpoints
**Location:** CODEBASE_STRUCTURE_ANALYSIS.md, Section "API Endpoints Reference"

50+ endpoints organized by:
- Collection Management (3)
- Document Ingestion (3)
- Search & Retrieval (4)
- RAG Chat (3)
- Lesson Plans (7)
- Configuration (10)
- Monitoring (7)
- Admin/System (5+)

---

## File Organization

```
/Users/cnowlin/Developer/pretty_please/
├── CODEBASE_STRUCTURE_ANALYSIS.md      # Technical deep dive
├── QUICK_REFERENCE.md                  # Practical guide
├── ANALYSIS_SUMMARY.txt                # Executive summary
├── DOCUMENTATION_INDEX.md              # This file
├── src/jina_rag_pipeline/              # Backend code
│   ├── api/                            # FastAPI application
│   ├── embeddings/                     # Jina v4
│   ├── ingestion/                      # OCR, chunking, etc.
│   ├── storage/                        # ChromaDB
│   ├── retrieval/                      # Search, ranking
│   ├── generation/                     # LLM, lesson planning
│   ├── database/                       # ORM, persistence
│   └── ...
├── frontend/src/                       # Frontend code
│   ├── pages/                          # 6 main pages
│   ├── components/                     # UI components
│   ├── services/                       # API client
│   └── ...
└── ...
```

---

## Architecture at a Glance

```
Browser                          Server                         Storage
┌──────────────────┐            ┌──────────────────┐           ┌──────────┐
│   React/TypeScript│            │   FastAPI        │           │ChromaDB  │
│   - SearchPage    │◄───────────┤ - /api/search    │──────────►│ - Vectors│
│   - IngestionPage │   HTTP/JSON├─ /api/ingest/*  │           │ - Metadata
│   - ChatPage      │            │ - /api/lessons   │           └──────────┘
│   - LessonPlans   │            │ - /api/config/*  │
│   - SettingsPage  │            └──────────────────┘           ┌──────────┐
└──────────────────┘                     │                      │  SQLite  │
         │                                │                      │ - Lessons│
         │                         OCR Engine                    │ - Sessions
      WebSocket◄──────────────────────────┤                      └──────────┘
      Progress                    DeepseekOCR                    
                              ┌──────────────────┐              ┌──────────┐
                              │  Embeddings      │              │  Uploads │
                              │  Jina v4 (2048d)│              │- Docs    │
                              │  Apple Silicon   │              │- Images  │
                              │  MPS/CPU         │              │- Thumbs  │
                              └──────────────────┘              └──────────┘
```

---

## Recent Updates

### Latest Commits (from git log)
1. **Commit 7049fe81b** - `docs(e2e-test): Comprehensive pipeline test analysis`
2. **Commit 0c840cafc** - `feat(e2e-test): Complete RAG pipeline with GUNDAM`
3. **Commit 18763b3c4** - `refactor(ocr): Remove PaddleOCR, standardize DeepseekOCR`
4. **Commit c8e7bd4ce** - `docs(analysis): PaddleOCR vs Gundam comparison`
5. **Commit d7c2ae0ac** - `feat(ocr): Fix Deepseek attention + add comparisons`

### Key Status
- Status: Production-Ready
- OCR Engine: DeepseekOCR with GUNDAM mode
- Embeddings: Jina v4 (2048-dim)
- Pipeline: Fully tested (30.74s end-to-end)
- All stages: Passing validation

---

## Documentation Maintenance

These documents were generated through automated codebase analysis on October 21, 2025.

**Note:** For the most up-to-date information:
- Check git commits: `git log --oneline`
- Visit API docs: `http://localhost:8000/docs` (when server running)
- Review source code: `/src/jina_rag_pipeline/`
- Check test files: `/tests/`

---

## Related Documentation in Project

Additional documentation in the project:
- `README.md` - Project overview and quick start
- `docs/guides/` - Configuration guides and tutorials
- `docs/architecture/` - System architecture documents
- `pyproject.toml` - Project dependencies and metadata
- `Makefile` - Service management commands
- API docs: Available at `/docs` when server is running

---

## Questions? Check Here First

| Question | Location |
|----------|----------|
| How do I start the system? | QUICK_REFERENCE.md > Quick Start |
| What are the API endpoints? | QUICK_REFERENCE.md > API Quick Reference or CODEBASE_STRUCTURE_ANALYSIS.md > API Endpoints |
| How does document processing work? | CODEBASE_STRUCTURE_ANALYSIS.md > RAG Pipeline Architecture |
| How do frontend and backend communicate? | CODEBASE_STRUCTURE_ANALYSIS.md > Frontend-Backend Communication |
| Where are configuration files? | QUICK_REFERENCE.md > File Locations or CODEBASE_STRUCTURE_ANALYSIS.md > Configuration Files |
| What's the current status? | ANALYSIS_SUMMARY.txt |
| How do I upload documents? | QUICK_REFERENCE.md > Common Tasks |
| How do I troubleshoot an issue? | QUICK_REFERENCE.md > Troubleshooting |
| What are the recent changes? | ANALYSIS_SUMMARY.txt > Recent Improvements or git log |
| How is the codebase organized? | CODEBASE_STRUCTURE_ANALYSIS.md > Key Directories and Purposes |

---

**Documentation Generated:** October 21, 2025  
**Analysis Tool:** Automated codebase analysis  
**Project Version:** 2.0.0  
**Status:** Production-Ready with DeepseekOCR
