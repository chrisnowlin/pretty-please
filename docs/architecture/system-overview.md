# System Architecture

## Overview

Pretty Please is a multimodal RAG (Retrieval-Augmented Generation) pipeline designed for processing complex documents including PDFs, PowerPoint presentations, images, tables, and equations. The system uses Jina Embeddings v4 with semantic layout analysis powered by Nanonets OCR.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Frontend (React)                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐         │
│  │ Upload UI  │  │ Search UI  │  │  Chat UI   │         │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘         │
│        │                │                │                │
│        └────────────────┴────────────────┘                │
│                         │                                 │
│                    WebSocket/HTTP                         │
└─────────────────────────┼─────────────────────────────────┘
                          │
┌─────────────────────────┼─────────────────────────────────┐
│                    FastAPI Backend                        │
│  ┌──────────────────────┴───────────────────────────┐    │
│  │              API Endpoints                       │    │
│  │  /api/ingest  /api/search  /api/chat  /ws       │    │
│  └──────────────────┬───────────────────────────────┘    │
│                     │                                     │
│  ┌──────────────────┼───────────────────────────────┐    │
│  │          Task Processing Layer                   │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │    │
│  │  │ ThreadPool│  │ RQ Queue │  │ Progress     │   │    │
│  │  │ (small)   │  │ (large)  │  │ Tracking     │   │    │
│  │  └──────────┘  └──────────┘  └──────────────┘   │    │
│  └──────────────────┬───────────────────────────────┘    │
│                     │                                     │
│  ┌──────────────────┼───────────────────────────────┐    │
│  │           Ingestion Pipeline                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │    │
│  │  │   Loaders   │→ │  Nanonets   │→ │ Markdown │ │    │
│  │  │  (PDF/PPTX) │  │   Analyzer  │  │  Parser  │ │    │
│  │  └─────────────┘  └─────────────┘  └──────────┘ │    │
│  └──────────────────┬───────────────────────────────┘    │
│                     │                                     │
│  ┌──────────────────┼───────────────────────────────┐    │
│  │         Embedding & Storage Layer                │    │
│  │  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │ Jina Embed v4│→ │   ChromaDB   │             │    │
│  │  │   (MPS)      │  │ Vector Store │             │    │
│  │  └──────────────┘  └──────────────┘             │    │
│  └──────────────────┬───────────────────────────────┘    │
│                     │                                     │
│  ┌──────────────────┼───────────────────────────────┐    │
│  │            Retrieval & Generation                │    │
│  │  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │  Reranker    │→ │ Qwen 2.5 VL  │             │    │
│  │  │   (ColBERT)  │  │  Generator   │             │    │
│  │  └──────────────┘  └──────────────┘             │    │
│  └──────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────┘
```

## Component Overview

### 1. Frontend (React + TypeScript)

**Technology Stack**:
- React 18 with TypeScript
- Bun for fast builds and bundling
- React Query for server state management
- Tailwind CSS for styling

**Key Features**:
- Real-time upload progress via WebSocket
- Interactive search with faceted filters
- Chat interface with citation links
- Collection management
- Dark mode support

**Location**: `frontend/src/`

### 2. API Layer (FastAPI)

**Endpoints**:
- **Ingestion**: `/api/ingest/upload` - Upload and process documents
- **Collections**: `/api/collections/*` - Manage collections
- **Search**: `/api/search/query` - Vector similarity search
- **Chat**: `/api/chat/query` - RAG-based chatbot
- **WebSocket**: `/ws/tasks/{task_id}` - Real-time progress updates
- **Health**: `/api/health` - Service health check
- **Metrics**: `/api/metrics/*` - System metrics

**Location**: `src/jina_rag_pipeline/api/`

### 3. Ingestion Pipeline

#### Document Loaders

**Supported Formats**:
- **Text**: .txt, .md
- **PDF**: .pdf (with layout analysis)
- **PowerPoint**: .pptx, .ppt
- **Images**: .png, .jpg, .jpeg, .webp, .gif, .bmp
- **Documents**: .docx, .doc

**Loader Architecture**:
```python
DocumentLoader (ABC)
    ├── TextLoader
    ├── MarkdownLoader
    ├── PDFLoader
    ├── PowerPointLoader
    ├── DocxLoader
    └── ImageLoader

LoaderFactory
    └── get_loader(file_path) → DocumentLoader
```

**Location**: `src/jina_rag_pipeline/ingestion/loaders.py`

#### Layout Analysis (Nanonets)

**Nanonets-OCR2-3B** Vision-Language Model:
- **Tables**: Full HTML structure with rows/columns/headers
- **Equations**: LaTeX representation
- **Images**: Natural language descriptions with classification
- **Text**: Headings, paragraphs, lists with hierarchy
- **Multilingual**: Superior CJK and RTL language support

**Location**: `src/jina_rag_pipeline/ingestion/nanonets_layout.py`

#### Markdown Parser

Converts Nanonets markdown output into structured semantic regions:
- Extracts 6 region types: text, title, list, table, image, equation
- Preserves semantic metadata
- Handles table structure, equation LaTeX, image descriptions

**Location**: `src/jina_rag_pipeline/ingestion/markdown_parser.py`

### 4. Embeddings (Jina v4)

**Model**: `jinaai/jina-embeddings-v4`
- **Dimensions**: 2048
- **Max Sequence Length**: 8192 tokens
- **Tasks**: retrieval, text-matching, classification, separation, clustering
- **Acceleration**: MPS (Apple Silicon), CUDA (NVIDIA), CPU fallback

**Features**:
- Matryoshka embeddings (truncatable dimensions)
- Task-specific optimization
- Batch processing for efficiency

**Location**: `src/jina_rag_pipeline/embeddings/jina_v4.py`

### 5. Vector Database (ChromaDB)

**Storage**: Persistent vector database with metadata
- **Collections**: Namespace isolation
- **Metadata**: Rich filtering and faceting
- **Similarity**: Cosine similarity search
- **Persistence**: Disk-backed storage

**Client Modes**:
- **Embedded**: Default, local file storage
- **Client/Server**: Distributed deployments

**Location**: `src/jina_rag_pipeline/storage/chroma_store.py`

### 6. Retrieval & Reranking

**Two-Stage Retrieval**:

1. **Initial Retrieval** (ChromaDB):
   - Fast vector similarity search
   - Returns top-k candidates (k=20-50)
   - Uses Jina embeddings

2. **Reranking** (ColBERT):
   - Fine-grained relevance scoring
   - Returns top-n results (n=5-10)
   - Improves precision

**Location**: `src/jina_rag_pipeline/retrieval/reranker.py`

### 7. Generation (Qwen 2.5 VL)

**Model**: Qwen/Qwen2.5-VL-7B-Instruct
- **Capabilities**: Multimodal (text + images)
- **Context Window**: 32K tokens
- **Streaming**: Token-by-token generation
- **Citations**: Automatic source attribution

**Prompt Engineering**:
- Context formatting with retrieved chunks
- Image integration for visual documents
- Citation marker insertion

**Location**: `src/jina_rag_pipeline/generation/qwen_generator.py`

---

## Data Flow

### Ingestion Flow

```
1. User uploads document.pdf
   ↓
2. API validates file format and size
   ↓
3. TaskManager routes to appropriate worker
   │
   ├─ Small file (<10MB) → ThreadPool
   └─ Large file (>10MB) → RQ Worker
   ↓
4. Loader extracts content
   │  PDFLoader.load(document.pdf)
   ↓
5. Nanonets analyzes layout
   │  NanonetsLayoutAnalyzer.extract_regions()
   │  → Returns markdown with semantic tags
   ↓
6. Markdown parser creates semantic regions
   │  MarkdownParser.parse_markdown_to_regions()
   │  → Returns SemanticRegion objects
   ↓
7. Document processor chunks regions
   │  ChunkingStrategy.chunk(regions)
   │  → Returns text chunks with metadata
   ↓
8. Embedder generates vectors
   │  JinaEmbeddingsV4.encode_text(chunks)
   │  → Returns 2048-dim embeddings
   ↓
9. Vector store persists data
   │  ChromaStore.add_embeddings(embeddings, metadata)
   ↓
10. WebSocket notifies completion
    → Frontend shows success message
```

### Search Flow

```
1. User enters query: "What is machine learning?"
   ↓
2. Query embedding generated
   │  JinaEmbeddingsV4.encode_text(query, task="retrieval")
   ↓
3. Vector similarity search
   │  ChromaStore.query(embedding, top_k=20)
   │  → Returns 20 candidate chunks
   ↓
4. Reranking (optional)
   │  Reranker.rerank(query, candidates)
   │  → Returns top 5 most relevant
   ↓
5. Results formatted and returned
   │  Include: content, source, score, metadata
   ↓
6. Frontend displays results
   → User views snippets with scores
```

### Chat Flow

```
1. User asks: "Explain the key concepts"
   ↓
2. Query embedding generated
   │  JinaEmbeddingsV4.encode_text(query, task="retrieval")
   ↓
3. Vector search retrieves context
   │  ChromaStore.query(embedding, top_k=10)
   ↓
4. Context formatter creates prompt
   │  ContextFormatter.format_multimodal_context()
   │  → Inserts citation markers [1], [2], [IMG-1]
   ↓
5. LLM generates response
   │  QwenGenerator.generate(prompt, context)
   │  → Streams tokens with citations
   ↓
6. Citation map sent to frontend
   │  WebSocket sends citation metadata
   │  → {[1]: {source, url, score}, ...}
   ↓
7. Frontend renders response
   │  ReactMarkdown + CitationLink components
   │  → User can click citations to view sources
```

---

## Async Processing Architecture

### ThreadPool (Phase 1)

**Purpose**: Non-blocking processing for small/medium files

```python
ThreadPoolExecutor(max_workers=2)
    ↓
asyncio.run_in_executor(executor, blocking_function)
    ↓
Event loop remains responsive
```

**Benefits**:
- API stays responsive during processing
- Health checks work during heavy loads
- Multiple uploads can be queued

**Limitations**:
- Limited to single machine
- 2 concurrent files max
- Not suitable for very large files

### RQ Workers (Phase 2)

**Purpose**: Distributed processing for large files

```
FastAPI Server
    ↓
TaskManager routes to RQ
    ↓
Redis Queue (job queue)
    ↓
RQ Worker 1, Worker 2, Worker 3...
    ↓
Results stored in database
```

**Configuration**:
- Files >10MB automatically routed to RQ
- Priority queues: high, default, low
- Job timeouts: 1-2 hours for large PDFs
- Redis pub/sub for progress updates

**Benefits**:
- Horizontal scaling across machines
- No API blocking
- Graceful failure handling

### Production Deployment (Phase 3)

**Multi-Worker Setup**:

```
Nginx Load Balancer
    ├─ Sticky sessions for WebSockets (IP hash)
    └─ Round-robin for HTTP
    ↓
Uvicorn Worker 1, Worker 2, Worker 3, Worker 4
    ↓
Redis (shared state)
    ├─ Task status
    ├─ WebSocket pub/sub
    └─ Session data
    ↓
Shared Storage
    ├─ ChromaDB (NFS or client/server)
    ├─ File uploads (NFS or S3)
    └─ Metrics database
```

**See**: [Async Processing Guide](../guides/async-processing.md) for details

---

## Storage Architecture

### File Storage

```
uploads/
├── {collection_name}/
│   ├── documents/
│   │   └── {uuid}.pdf
│   ├── images/
│   │   ├── thumbnails/
│   │   │   └── {image_id}_thumb.jpg
│   │   └── full/
│   │       └── {image_id}.jpg
│   └── metadata.json
```

**Access**:
- Documents: `/api/documents/{collection}/{file_id}`
- Images: `/api/images/thumbnail/{collection}/{image_id}`
- Images: `/api/images/full/{collection}/{image_id}`

### Vector Database Schema

**Collection Structure**:
```python
{
    "name": "my_collection",
    "metadata": {
        "description": "Research papers",
        "created_at": "2025-01-15T10:00:00Z"
    },
    "embeddings": [
        [0.123, 0.456, ...],  # 2048 dimensions
        [0.789, 0.012, ...]
    ],
    "documents": [
        "Text chunk 1 content...",
        "Text chunk 2 content..."
    ],
    "metadatas": [
        {
            "source": "document.pdf",
            "page": 1,
            "chunk_id": 0,
            "region_type": "text",
            "document_path": "uploads/collection/uuid.pdf"
        }
    ],
    "ids": [
        "uuid-1",
        "uuid-2"
    ]
}
```

---

## Performance Characteristics

### Benchmarks (M4 Max, 48GB RAM)

| Operation | Time | Notes |
|-----------|------|-------|
| **Upload (5-page PDF)** | 0.2s | API response time |
| **Nanonets OCR (per page)** | 8-16s | Layout analysis |
| **Embedding (512 tokens)** | 0.1-0.3s | MPS accelerated |
| **Vector search (10k docs)** | 50-100ms | ChromaDB |
| **Reranking (20 candidates)** | 200-500ms | ColBERT |
| **LLM generation (streaming)** | 20-40 tokens/s | Qwen 2.5 VL |

### Throughput (Distributed Setup, 3 Workers)

- **PDFs (10-20MB)**: 10-15 documents/minute
- **PowerPoint (20+ slides)**: 5-8 presentations/minute
- **Concurrent users**: 50-100 (with proper caching)

---

## Security Considerations

### Authentication & Authorization
- API keys for programmatic access
- Session-based auth for web UI
- Collection-level access control

### Input Validation
- File type whitelisting
- File size limits (default: 100MB)
- Filename sanitization (path traversal prevention)
- Content validation (malware scanning recommended)

### Data Privacy
- Local-first architecture (no cloud dependencies)
- Encrypted storage at rest (optional)
- TLS/HTTPS for transport security

### Citation Security
- Path traversal prevention in document serving
- Collection-scoped access (can't access other collections)
- UUID-based filenames (no guessing attacks)

---

## Monitoring & Observability

### Health Checks

```bash
curl http://localhost:8000/api/health
```

Returns:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "chroma": "ok",
    "redis": "ok"
  }
}
```

### Metrics

```bash
curl http://localhost:8000/api/metrics/summary
```

Provides:
- Total documents indexed
- Total collections
- Average query latency
- System resource usage

### Logging

- **Backend**: Structured JSON logs with levels (DEBUG, INFO, WARN, ERROR)
- **Frontend**: Console logging for development
- **Workers**: RQ job logs with timestamps

---

## Scaling Strategies

### Vertical Scaling
- Increase worker count (`GUNICORN_WORKERS`)
- Increase RQ workers (`RQ_WORKERS`)
- Add more RAM for larger models

### Horizontal Scaling
- Add more RQ worker machines
- Use ChromaDB client/server mode
- Use shared file storage (NFS, S3)

### Caching
- Embedding cache for repeated queries
- Model cache (avoid reloading)
- HTTP cache for static resources

---

## Related Documentation

- [Getting Started Guide](../guides/getting-started.md)
- [Async Processing Guide](../guides/async-processing.md)
- [Nanonets Migration Guide](../guides/nanonets-migration.md)
- [Citations Feature](../features/citations.md)
