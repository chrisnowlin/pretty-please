# Pretty Please - RAG Pipeline: Comprehensive Codebase Structure Analysis

**Analysis Date:** October 21, 2025
**Project Version:** 2.0.0
**Status:** Production-Ready with DeepseekOCR

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Frontend/Backend Separation](#frontendbackend-separation)
3. [Key Directories and Purposes](#key-directories-and-purposes)
4. [RAG Pipeline Architecture](#rag-pipeline-architecture)
5. [Frontend-Backend Communication](#frontend-backend-communication)
6. [Configuration Files](#configuration-files)
7. [Recent Changes & RAG Pipeline Enhancements](#recent-changes--rag-pipeline-enhancements)

---

## Project Overview

**Pretty Please** is a production-ready Retrieval-Augmented Generation (RAG) pipeline built with:

- **Backend:** FastAPI (Python) running on port 8000
- **Frontend:** React/TypeScript (Vite) running on port 5173
- **Vector Database:** ChromaDB (persistent, local-first)
- **Embeddings:** Jina Embeddings v4 (2048-dimensional, optimized for Apple Silicon)
- **OCR Engine:** DeepseekOCR with GUNDAM mode (dynamic multi-resolution)
- **LLM Integration:** Qwen generator for lesson plan generation
- **Database:** SQLAlchemy with SQLite (Phase 3 lesson persistence)

**Core Features:**
- Document ingestion with OCR and semantic chunking
- Real-time embedding generation and vector storage
- Semantic similarity search (text and image-based)
- RAG-powered lesson plan generation for educational content
- Lesson library persistence and management
- Configuration management for OCR and embeddings
- WebSocket-based progress tracking for async operations
- Distributed processing support via RQ (optional)

---

## Frontend/Backend Separation

### Clear Separation of Concerns

The project maintains a clean separation between frontend and backend:

```
project_root/
├── src/                          # Backend (Python)
│   └── jina_rag_pipeline/        # Main package
├── frontend/                     # Frontend (TypeScript/React)
│   └── src/
└── tests/                        # Backend tests
```

### Communication Protocol

- **API Base URL:** `/api` (relative, proxied in development)
- **WebSocket Endpoint:** `/ws/progress/{task_id}`
- **Static Files:** Frontend dist mounted at `/` and `/assets`
- **Development:** Vite dev server on 5173, FastAPI on 8000
- **Production:** Frontend built to `dist/`, served by FastAPI

---

## Key Directories and Purposes

### Backend Structure: `/src/jina_rag_pipeline/`

```
src/jina_rag_pipeline/
├── api/                          # REST API & Web Framework Layer
│   ├── app.py                   # Main FastAPI application (1636 lines)
│   ├── models.py                # Pydantic request/response models (25k)
│   ├── tasks.py                 # Task manager for async ingestion (55k)
│   ├── config_manager.py        # Dynamic config persistence
│   ├── collection_manager.py    # Collection organization
│   ├── chat.py                  # RAG chat endpoints
│   ├── session.py               # Session management
│   ├── endpoints_admin.py       # Admin/checkpoint endpoints
│   └── task_db.py               # Task persistence DB
│
├── embeddings/                   # Jina Embeddings v4 Implementation
│   ├── jina_v4.py               # Core embedding model
│   ├── config.py                # Embedding config (task, dimensions, late_chunking)
│   ├── batch_processor.py       # Batch processing with streaming
│   ├── multivector.py           # Multi-vector embeddings
│   └── format_converter.py      # Format conversion (binary, int8, etc.)
│
├── ingestion/                    # Document Processing Pipeline
│   ├── pipeline.py              # DocumentProcessor class
│   ├── loaders.py               # Format-specific loaders (PDF, PPTX, etc.)
│   ├── deepseek_loader.py       # DeepseekOCR integration
│   ├── deepseek_layout.py       # Layout analysis (37k) - GUNDAM mode
│   ├── ocr_config.py            # OCR configuration presets
│   ├── unified_ocr_loader.py   # Unified OCR loader abstraction
│   ├── chunking.py              # Chunking strategies
│   ├── semantic_chunking.py     # Semantic region preservation
│   ├── semantic_region.py       # Region extraction
│   ├── markdown_parser.py       # Markdown parsing
│   ├── document_renderer.py     # PDF rendering for DeepseekOCR
│   ├── analysis_pipeline.py     # Analysis orchestration
│   └── educational/             # Educational content metadata
│       └── metadata_hints.py    # Subject/topic hints
│
├── storage/                      # Vector Store Abstraction
│   ├── base.py                  # Abstract storage interface
│   └── chroma_store.py          # ChromaDB implementation
│
├── retrieval/                    # RAG Retrieval & Ranking
│   ├── educational.py           # Educational retriever
│   ├── reranker.py              # Jina reranker
│   └── metrics.py               # Retrieval metrics
│
├── generation/                   # Text Generation
│   ├── config.py                # Generation configuration
│   ├── qwen_generator.py        # Qwen LLM wrapper
│   ├── lesson_planner.py        # Lesson plan generation
│   ├── prompts.py               # System prompts
│   └── lesson_exporter.py       # Export to PDF/JSON/Markdown
│
├── database/                     # ORM & Persistence
│   ├── database.py              # SQLAlchemy setup
│   ├── models.py                # SQLAlchemy models (Lesson, etc.)
│   └── __init__.py              # DB initialization
│
├── monitoring/                   # Metrics & Observability
│   ├── metrics.py               # Metrics collector
│   └── (private - permissions restricted)
│
├── multimodal/                   # Multi-Modal Processing
│   └── thumbnails.py            # Thumbnail generation
│
├── workers/                      # Distributed Processing (RQ)
│   ├── queue.py                 # Job queue manager
│   └── config.py                # RQ configuration
│
└── batch/                        # Batch Processing
    └── (Processing utilities)

```

### Frontend Structure: `/frontend/src/`

```
frontend/src/
├── pages/                        # Page Components (6 main pages)
│   ├── SearchPage.tsx           # Semantic search UI
│   ├── IngestionPage.tsx        # Document upload & progress
│   ├── CollectionsPage.tsx      # Collection management
│   ├── ChatPage.tsx             # RAG chat interface
│   ├── LessonPlansPage.tsx      # Lesson generation UI
│   └── SettingsPage.tsx         # Configuration UI
│
├── components/                   # Reusable UI Components
│   ├── search/                  # Search-specific components
│   ├── ingestion/               # Upload & progress components
│   ├── chat/                    # Chat interface components
│   ├── collections/             # Collection management
│   ├── lessonPlan/              # Lesson generation components
│   ├── settings/                # Settings components
│   └── common/                  # Shared components
│       ├── Navigation.tsx       # Main navigation
│       └── Layout.tsx           # Page layout
│
├── services/                     # API Client & WebSocket
│   ├── api.ts                   # APIClient class (280 lines)
│   └── websocket.ts             # WebSocket utilities
│
├── hooks/                        # React Hooks
│   └── (Custom hooks for state management)
│
├── contexts/                     # React Context
│   └── ThemeContext.tsx         # Theme management
│
├── types/                        # TypeScript Type Definitions
│   └── (API response types, etc.)
│
├── styles/                       # CSS & Styling
│   └── theme.ts                 # Theme configuration
│
├── constants/                    # App Constants
│   └── (Configuration constants)
│
├── App.tsx                       # Root component
├── index.tsx                     # React entry point
└── vite.config.ts               # Vite configuration

```

---

## RAG Pipeline Architecture

### End-to-End Document Processing Flow

```
User Upload (Frontend)
    ↓
    ├─→ POST /api/ingest/upload
    │   └─→ TaskManager.create_task() → task_id returned
    │
    ├─→ WebSocket /ws/progress/{task_id}
    │   └─→ Real-time progress updates
    │
    └─→ Backend Processing Pipeline:
        
        Stage 1: Document Reception & Validation
        ├─→ Check file format, size, MIME type
        └─→ Write to temp directory
        
        Stage 2: OCR Ingestion (DeepseekOCR)
        ├─→ Detect format (PDF, image, PPTX, etc.)
        ├─→ Load via UnifiedOCRLoader
        ├─→ Apply GUNDAM mode (dynamic resolution)
        │   ├─→ 640×640 for simple content
        │   └─→ 1024×1024 for complex layouts
        ├─→ Extract text with bounding boxes
        ├─→ Apply optical compression
        └─→ Generate semantic regions
        
        Stage 3: Document Processing
        ├─→ Parse markdown/structure
        ├─→ Extract metadata (source, OCR model)
        └─→ Generate thumbnails for images
        
        Stage 4: Semantic Chunking
        ├─→ Split by semantic boundaries
        ├─→ Create chunks (1000 chars, 200 char overlap)
        ├─→ Attach source metadata
        └─→ Filter empty chunks
        
        Stage 5: Embedding Generation
        ├─→ Load Jina Embeddings v4 model
        ├─→ Batch process chunks (32-token batches)
        ├─→ Generate 2048-dim vectors (or configured size)
        ├─→ Apply task-specific optimization (retrieval.passage)
        └─→ Log metrics
        
        Stage 6: Vector Storage
        ├─→ Create ChromaDB collection (if needed)
        ├─→ Store vectors with metadata
        ├─→ Persist to disk (.chroma_db/)
        └─→ Index for similarity search
        
        Stage 7: Artifact Organization
        ├─→ Store original documents in uploads/collection/documents/
        ├─→ Store extracted images in uploads/collection/images/
        └─→ Store thumbnails in uploads/collection/thumbnails/
```

### Key Processing Components

#### 1. **Unified OCR Loader** (`unified_ocr_loader.py`)
- Abstracts multiple OCR backends
- Primary: DeepseekOCR (GUNDAM mode)
- Fallback: PaddleOCR (removed in recent update)
- Returns: Document with text, metadata, and regions

#### 2. **DeepseekOCR Layout Engine** (`deepseek_layout.py` - 37k)
- **GUNDAM Mode:** Dynamic multi-resolution pipeline
  - Analyzes page complexity
  - Applies 640×640 for simple pages
  - Applies 1024×1024 for dense content
  - Adaptive based on layout analysis
- **Grounding:** Bounding boxes for detected text
- **Compression:** Optical compression for faster processing
- **Attention:** SDPA (Scaled Dot Product Attention) on MPS

#### 3. **Semantic Chunking** (`chunking.py`)
- Preserves semantic boundaries
- Configurable chunk size (default: 1000 characters)
- Overlap for context (default: 200 characters)
- Removes empty chunks

#### 4. **Task Manager** (`tasks.py` - 55k)
- Async task orchestration
- Progress tracking via WebSocket
- Optional distributed processing via RQ
- Metrics collection
- Task persistence to database

#### 5. **Embedding Configuration** (`embeddings/config.py`)
- **Presets:**
  - `for_query`: Query optimization (fast)
  - `for_documents`: Document indexing with context
  - `fast`: 4× faster, 512-dim
  - `storage_optimized`: Binary format, 8× smaller
  - `memory_constrained`: Auto-scaling

---

## Frontend-Backend Communication

### API Endpoints Reference

#### Collection Management
```
GET  /api/collections              # List all collections
POST /api/collections/create       # Create new collection
GET  /api/collections/{name}/config
PUT  /api/collections/{name}/config
```

#### Document Ingestion
```
POST /api/ingest/upload            # Upload files (returns task_id)
GET  /api/ingest/status/{task_id}  # Check ingestion status
GET  /api/ingest/supported-formats # Get file format info
```

#### WebSocket Progress
```
WebSocket /ws/progress/{task_id}   # Real-time task progress
```

#### Search & Retrieval
```
POST /api/search                   # Text similarity search
POST /api/search/image             # Image-based search
GET  /api/images/thumbnail/{collection}/{id}
GET  /api/images/full/{collection}/{id}
GET  /api/documents/{collection}/{filename}
```

#### RAG Chat
```
POST /api/chat/stream              # Stream RAG responses
POST /api/chat/save-session        # Save chat session
GET  /api/chat/sessions            # List sessions
```

#### Lesson Plans
```
POST /api/lesson-plan/generate     # Generate lesson plan
GET  /api/lesson-plan/export/{id}  # Export (markdown/pdf/json)
POST /api/lessons/save             # Persist lesson
GET  /api/lessons                  # List lessons
GET  /api/lessons/{id}             # Get lesson detail
PATCH /api/lessons/{id}            # Update lesson
DELETE /api/lessons/{id}           # Delete lesson
POST /api/lessons/{id}/favorite    # Toggle favorite
```

#### Configuration
```
GET  /api/config/embeddings        # Get embedding config
POST /api/config/embeddings        # Update embedding config
GET  /api/config/embeddings/presets
GET  /api/config/ocr               # Get OCR config
POST /api/config/ocr               # Update OCR config
GET  /api/config/ocr/presets
GET  /api/config/rag               # Get RAG config
POST /api/config/rag               # Update RAG config
```

#### Monitoring & Health
```
GET  /api/health                   # Health check
GET  /api/stats                    # Basic stats
GET  /api/metrics/summary          # Metrics summary
GET  /api/metrics/performance      # Performance breakdown
GET  /api/metrics/system           # System metrics
GET  /api/metrics/all              # All metrics
```

### Frontend API Client (`frontend/src/services/api.ts`)

The `APIClient` class provides a TypeScript wrapper:

```typescript
class APIClient {
  // Search operations
  search(request: SearchRequest): Promise<SearchResponse>
  searchByImage(image: File, collectionName: string, topK?: number): Promise<SearchResponse>
  
  // Collections
  getCollections(): Promise<CollectionsResponse>
  
  // Ingestion
  uploadDocuments(files: File[], collectionName: string): Promise<IngestionResponse>
  getIngestionStatus(taskId: string): Promise<IngestionStatusResponse>
  getSupportedFormats(): Promise<SupportedFormatsResponse>
  
  // Configuration
  getCollectionConfig(collectionName: string): Promise<CollectionConfig>
  updateCollectionConfig(collectionName: string, config: CollectionConfig): Promise<CollectionConfig>
  
  // Lessons
  getLesson(lessonId: number): Promise<LessonDetailResponse>
  updateLesson(lessonId: number, updates: UpdateLessonRequest): Promise<LessonDetailResponse>
  
  // Image retrieval
  getThumbnailUrl(collection: string, imageId: string): string
  getFullImageUrl(collection: string, imageId: string): string
}
```

### WebSocket Progress Tracking

**Connection Point:** `WebSocket /ws/progress/{task_id}`

**Message Flow:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45.5,
  "current_file": "document_1.pdf",
  "processed_files": 2,
  "total_files": 5,
  "errors": [
    { "file": "bad_file.ppt", "error": "Unsupported format" }
  ]
}
```

**Message Types:**
- `processing`: Active processing
- `complete`: Task finished successfully
- `error`: Task failed
- `ping`: Keep-alive (every 30 seconds)

### React Query Integration

The frontend uses TanStack React Query for:
- Automatic caching of API responses
- Background refetching
- Optimistic updates
- Error boundary handling

```typescript
const { data: collections, refetch: refetchCollections } = useQuery({
  queryKey: ['collections'],
  queryFn: () => apiClient.getCollections(),
});
```

---

## Configuration Files

### Backend Configuration

#### `pyproject.toml` - Project Metadata & Dependencies
```toml
[project]
name = "jina-rag-pipeline"
version = "2.0.0"
requires-python = ">=3.10"

[project.optional-dependencies]
dev = [...]           # Testing & development tools
distributed = [...]   # RQ for distributed processing
deepseek = [...]      # GPU acceleration (Linux only)
production = [...]    # vLLM for high-throughput inference
paddleocr = [...]     # Removed but retained for compatibility
```

#### Embedding Configuration (`src/jina_rag_pipeline/embeddings/config.py`)
```python
@dataclass
class EmbeddingConfig:
    task: str                    # "retrieval.query" or "retrieval.passage"
    dimensions: int              # 512, 1024, or 2048
    late_chunking: bool          # Preserve context across chunks
    embedding_format: str        # "float", "int8", "binary"
    
    @classmethod
    def for_query(cls) -> 'EmbeddingConfig':
        return cls(task="retrieval.query", dimensions=1024, late_chunking=False)
    
    @classmethod
    def for_documents(cls) -> 'EmbeddingConfig':
        return cls(task="retrieval.passage", dimensions=1024, late_chunking=True)
```

#### OCR Configuration (`src/jina_rag_pipeline/ingestion/ocr_config.py`)
```python
@dataclass
class OCRConfig:
    batch_size: int              # Pages per batch
    render_workers: int          # PDF rendering threads
    analysis_workers: int        # Layout analysis threads
    resolution_mode: str         # "tiny", "small", "balanced", "high_quality", "gundam"
    enable_grounding: bool       # Bounding boxes
    enable_compression: bool     # Optical compression
    use_vllm: bool              # GPU acceleration
    
    @classmethod
    def deepseek_gundam(cls) -> 'OCRConfig':
        """Dynamic multi-resolution pipeline for complex documents."""
        return cls(
            resolution_mode="gundam",
            enable_grounding=True,
            enable_compression=True,
        )
```

#### Runtime Config Directory (`./data/`)
- `embedding_config.json`: Current embedding settings
- `ocr_config.json`: Current OCR settings
- `collection_configs/`: Per-collection configurations

### Frontend Configuration

#### `frontend/vite.config.ts`
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
});
```

#### `.env` (Not committed, created at runtime)
```
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

#### Theme Configuration (`frontend/src/styles/theme.ts`)
```typescript
export const THEMES = {
  light: {
    bg: { primary: '#ffffff', secondary: '#f8fafc', tertiary: '#e2e8f0' },
    text: { primary: '#1e293b', secondary: '#64748b' },
    accent: '#3b82f6',
  },
  dark: { ... },
};
```

---

## Recent Changes & RAG Pipeline Enhancements

### Recent Commits

1. **Commit 7049fe81b** (Latest)
   - Title: `docs(e2e-test): Add comprehensive end-to-end pipeline test results analysis`
   - Files: Test result documentation

2. **Commit 0c840cafc**
   - Title: `feat(e2e-test): Complete end-to-end RAG pipeline test with DeepseekOCR GUNDAM`
   - **Impact:** Full pipeline validation with 30.74s execution
   - Stages: OCR → Chunking → Embeddings → Storage → Retrieval → Generation

3. **Commit 18763b3c4**
   - Title: `refactor(ocr): Remove PaddleOCR support, standardize on DeepseekOCR + GUNDAM`
   - **Impact:** Unified OCR strategy
   - Removed: PaddleOCR backend
   - Added: GUNDAM dynamic multi-resolution mode

4. **Commit c8e7bd4ce**
   - Title: `docs(analysis): Add comprehensive PaddleOCR vs Gundam comparison analysis`
   - Comparison: Quality metrics, performance benchmarks

5. **Commit d7c2ae0ac**
   - Title: `feat(ocr): Add OCR comparison testing and fix Deepseek attention implementation`
   - Fixes: Attention mechanism (SDPA) on MPS

### Key Enhancements in RAG Pipeline

#### 1. **Unified OCR Strategy** (DeepseekOCR)
- **Single Backend:** Eliminated PaddleOCR
- **GUNDAM Mode:** Dynamic resolution per page
  - Analyzes content complexity
  - Applies 640×640 for simple pages
  - Applies 1024×1024 for dense content
- **Optimization:** Optical compression enabled
- **Hardware:** MPS (Apple Silicon) with SDPA attention

#### 2. **Improved Document Processing**
- Better semantic region extraction
- Metadata preservation (OCR model, resolution, regions)
- Image extraction with thumbnails
- Document artifact organization

#### 3. **Enhanced Configuration Management**
- Runtime OCR config updates
- Runtime embedding config updates
- Per-collection configuration support
- Config persistence to disk

#### 4. **Production-Ready Monitoring**
- Task persistence across restarts
- Metrics collection (performance, file types)
- Real-time progress tracking
- RQ distributed processing support (optional)

#### 5. **Lesson Plan Generation Pipeline**
- **Retriever:** EducationalRetriever for targeted queries
- **Generator:** Qwen LLM with custom prompts
- **Exporter:** PDF, Markdown, JSON formats
- **Persistence:** Lesson library with favorites

---

## Data Flow Diagrams

### Ingestion Flow
```
Frontend (Upload Form)
         ↓
POST /api/ingest/upload (multipart/form-data)
         ↓
TaskManager.create_task()
         ↓
TaskManager.start_task() → asyncio.create_task()
         ↓
DocumentProcessor.load_document()
         ├─→ Format detection
         ├─→ UnifiedOCRLoader.load()
         ├─→ DeepseekOCR.process() [GUNDAM mode]
         └─→ Returns Document with text + regions
         ↓
Semantic chunking (1000 chars, 200 overlap)
         ↓
Jina Embeddings v4.embed()
         ├─→ Batch processing (32 tokens)
         ├─→ 2048-dimensional vectors
         └─→ Config-based optimization
         ↓
ChromaVectorStore.add_embeddings()
         ├─→ Create collection (if needed)
         ├─→ Store vectors + metadata
         └─→ Persist to disk
         ↓
WebSocket /ws/progress/{task_id}
         ├─→ "complete" message
         └─→ Frontend updates UI
```

### Search Flow
```
Frontend (Search Query)
         ↓
POST /api/search
         ├─→ Query text
         ├─→ Collection name
         ├─→ Top-k results
         └─→ Optional metadata filter
         ↓
Generate query embedding (Jina v4, task="retrieval.query")
         ↓
ChromaVectorStore.similarity_search()
         ├─→ Cosine distance calculation
         ├─→ Top-k retrieval
         └─→ Metadata enrichment
         ↓
Build SearchResponse
         ├─→ Result ID
         ├─→ Similarity score
         ├─→ Document/image content
         ├─→ Metadata
         └─→ Result type (text/image)
         ↓
Frontend renders results
         └─→ Shows similarity scores
         └─→ Links to source images/documents
```

### Lesson Generation Flow
```
Frontend (Lesson Request)
         ↓
POST /api/lesson-plan/generate
         ├─→ Topic, objective, grade, subject
         ├─→ Duration, teaching style
         └─→ Request body
         ↓
EducationalRetriever.retrieve()
         ├─→ Text retrieval (top-5)
         ├─→ Image retrieval (top-3)
         └─→ From default collections
         ↓
QwenGenerator.generate()
         ├─→ System prompt with RAG context
         ├─→ Curriculum alignment
         ├─→ Generates lesson markdown
         └─→ YAML frontmatter metadata
         ↓
LessonPlanner.format_lesson()
         ├─→ Parse markdown
         ├─→ Extract metadata
         ├─→ Embed images
         └─→ Add citations
         ↓
Cache lesson (state.lesson_cache)
         ├─→ UUID lesson_id
         └─→ Markdown content
         ↓
Response: LessonMarkdownResponse
         ├─→ lesson_id (for export/save)
         ├─→ markdown content
         ├─→ metadata (sources, images)
         └─→ generation_time_seconds
         ↓
Frontend can:
         ├─→ Display preview
         ├─→ Export to PDF/JSON
         └─→ Save to library
```

---

## Key Connection Points Between Frontend and Backend

### 1. **Upload Orchestration**
- Frontend: `IngestionPage` → `UploadZone` → `ProgressTracker`
- Backend: `POST /api/ingest/upload` → Task creation → `TaskManager` → `DocumentProcessor`
- Real-time sync via WebSocket

### 2. **Configuration Management**
- Frontend: `SettingsPage` shows current configs
- Backend: `ConfigManager` persists to `./data/` directory
- Updates take effect immediately for next operation

### 3. **Search Results**
- Frontend: `SearchPage` displays `SearchResult` components
- Backend: `SearchResponse` includes metadata for image/document links
- Image URLs: `/api/images/thumbnail/{collection}/{id}`

### 4. **Lesson Generation**
- Frontend: `LessonPlansPage` → Generation form → Preview → Export
- Backend: `GenerateLessonRequest` → RAG pipeline → Lesson saved to DB
- Caching: `state.lesson_cache` for temporary storage

### 5. **Collection Management**
- Frontend: `CollectionsPage` lists and creates collections
- Backend: `CollectionManager` manages directory structure
- Config sync: Per-collection settings in `uploads/{collection}/config.json`

---

## Summary

Pretty Please is a well-architected RAG pipeline with:

1. **Clean Separation:** Independent frontend (React) and backend (FastAPI)
2. **Scalability:** Support for distributed processing via RQ
3. **Configuration:** Runtime-updatable OCR and embedding configs
4. **Monitoring:** Comprehensive metrics and progress tracking
5. **Production-Ready:** Task persistence, error handling, WebSocket updates
6. **Educational Focus:** Lesson plan generation with vector retrieval
7. **Multi-Modal:** Text and image search with semantic embeddings
8. **Local-First:** All processing on device (MPS for Apple Silicon)

The recent refactoring (commits 0c840cafc, 18763b3c4) has established **DeepseekOCR with GUNDAM mode as the standard**, removing PaddleOCR and consolidating the OCR strategy for better reliability and performance.

