# Pretty Please - Quick Reference Guides

## Quick Start

### Starting Services
```bash
# Start everything
make start

# Or start services separately
make backend      # Port 8000
make frontend     # Port 5173
```

**Access Points:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Stopping Services
```bash
make stop
make logs              # View all logs
make logs-backend      # Backend logs only
```

---

## API Quick Reference

### Collections
```bash
# List collections
curl http://localhost:8000/api/collections

# Create collection
curl -X POST http://localhost:8000/api/collections/create \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "collection_name=my_collection"

# Get collection config
curl http://localhost:8000/api/collections/my_collection/config

# Update collection config
curl -X PUT http://localhost:8000/api/collections/my_collection/config \
  -H "Content-Type: application/json" \
  -d '{"enable_layout_analysis": true}'
```

### Document Upload
```bash
# Upload documents
curl -X POST http://localhost:8000/api/ingest/upload \
  -F "files=@document1.pdf" \
  -F "files=@document2.txt" \
  -F "collection_name=my_collection"

# Response includes task_id - use for progress tracking

# Check ingestion status
curl http://localhost:8000/api/ingest/status/{task_id}
```

### Search
```bash
# Text search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "collection_name": "my_collection",
    "top_k": 5
  }'

# Image search
curl -X POST http://localhost:8000/api/search/image \
  -F "image=@photo.jpg" \
  -F "collection_name=my_collection" \
  -F "top_k=5"
```

### Configuration
```bash
# Get current OCR config
curl http://localhost:8000/api/config/ocr

# Update OCR config
curl -X POST http://localhost:8000/api/config/ocr \
  -H "Content-Type: application/json" \
  -d '{
    "resolution_mode": "gundam",
    "enable_grounding": true,
    "enable_compression": true,
    "batch_size": 20
  }'

# Get embedding config
curl http://localhost:8000/api/config/embeddings

# Update embedding config
curl -X POST http://localhost:8000/api/config/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "task": "retrieval.passage",
    "dimensions": 1024,
    "late_chunking": true,
    "embedding_format": "float"
  }'
```

### Lesson Plans
```bash
# Generate lesson plan
curl -X POST http://localhost:8000/api/lesson-plan/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Photosynthesis",
    "learning_objective": "Understand how plants convert light to energy",
    "grade_level": "9-12",
    "subject": "Biology",
    "duration_minutes": 45,
    "teaching_style": "balanced"
  }'

# Export lesson (returns PDF/Markdown/JSON)
curl http://localhost:8000/api/lesson-plan/export/{lesson_id}?format=pdf

# Save lesson to library
curl -X POST http://localhost:8000/api/lessons/save \
  -H "Content-Type: application/json" \
  -d '{"lesson_id": "550e8400-e29b-41d4-a716-446655440000"}'

# List saved lessons
curl http://localhost:8000/api/lessons?limit=20

# Get lesson detail
curl http://localhost:8000/api/lessons/1

# Update lesson
curl -X PATCH http://localhost:8000/api/lessons/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title", "duration_minutes": 50}'
```

### WebSocket Progress Tracking
```bash
# Connect to WebSocket and stream progress
websocat ws://localhost:8000/ws/progress/{task_id}

# Receives messages like:
# {"task_id": "...", "status": "processing", "progress": 45.5, "current_file": "doc1.pdf", ...}
```

---

## Frontend Component Map

### Page Components
| Component | Route | Purpose |
|-----------|-------|---------|
| SearchPage | / | Text/image semantic search |
| IngestionPage | /ingest | Upload documents, track progress |
| CollectionsPage | /collections | Create/manage collections |
| ChatPage | /chat | RAG-powered conversational interface |
| LessonPlansPage | /lesson-plans | Generate educational lesson plans |
| SettingsPage | /settings | Configure OCR/embeddings |

### Key Components
| Component | Path | Exports |
|-----------|------|---------|
| Navigation | common/Navigation | Main navigation bar |
| UploadZone | ingestion/UploadZone | File drag-drop upload |
| ProgressTracker | ingestion/ProgressTracker | Real-time progress display |
| SearchResult | search/SearchResult | Individual search result |
| CollectionSelector | collections/CollectionSelector | Pick/create collections |

### Context Providers
| Context | Usage |
|---------|-------|
| ThemeContext | Theme switching (light/dark) |
| QueryClientProvider | React Query cache management |

---

## Backend Module Reference

### Embeddings Module (`src/jina_rag_pipeline/embeddings/`)

**Key Class: JinaEmbeddingsV4**
```python
from jina_rag_pipeline.embeddings import JinaEmbeddingsV4
from jina_rag_pipeline.embeddings.config import EmbeddingConfig

# Initialize
embedder = JinaEmbeddingsV4(device="mps")  # or "cpu", "cuda"

# Generate embeddings
config = EmbeddingConfig.for_documents()
embeddings = embedder.embed_with_config(texts, config)  # Shape: (n, 2048)

# Or use preset
embeddings = embedder.encode_text("Hello world", task="retrieval.query")
```

**Configuration Presets:**
```python
EmbeddingConfig.for_query()          # Fast query embeddings
EmbeddingConfig.for_documents()      # Full document embeddings with context
EmbeddingConfig.fast()               # 4x faster, 512-dim
EmbeddingConfig.storage_optimized()  # Binary format, 8x smaller
```

### Ingestion Module (`src/jina_rag_pipeline/ingestion/`)

**Key Class: DocumentProcessor**
```python
from jina_rag_pipeline.ingestion import DocumentProcessor

processor = DocumentProcessor()
document = processor.load_document(Path("file.pdf"))
chunks = processor.chunk_document(document)  # List[Chunk]
```

**OCR Configuration:**
```python
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig

# Preset configurations
config = OCRConfig.deepseek_balanced()      # Default, 1024x1024
config = OCRConfig.deepseek_gundam()        # Dynamic resolution
config = OCRConfig.deepseek_production()    # vLLM acceleration (GPU)

# Custom
config = OCRConfig(
    resolution_mode="gundam",
    enable_grounding=True,
    enable_compression=True,
    batch_size=20
)
```

### Storage Module (`src/jina_rag_pipeline/storage/`)

**Key Class: ChromaVectorStore**
```python
from jina_rag_pipeline.storage import ChromaVectorStore

store = ChromaVectorStore(persist_directory=".chroma_db")

# Create collection
store.create_collection(
    name="documents",
    embedding_dimension=2048,
    metadata={"description": "My documents"}
)

# Add embeddings
ids = store.add_embeddings(
    collection_name="documents",
    embeddings=[[...], [...]],  # List of embedding vectors
    documents=["text1", "text2"],
    metadatas=[{"source": "doc1"}, {"source": "doc2"}]
)

# Search
results = store.similarity_search(
    collection_name="documents",
    query_embedding=[...],  # Query vector
    top_k=5,
    metadata_filter={"source": "doc1"}
)

# List collections
collections = store.list_collections()
stats = store.get_collection_stats(collection_name)
```

### Retrieval Module (`src/jina_rag_pipeline/retrieval/`)

**Key Class: EducationalRetriever**
```python
from jina_rag_pipeline.retrieval.educational import EducationalRetriever

retriever = EducationalRetriever(
    vector_store=store,
    embedder=embedder,
    text_collection="educational_content",
    image_collection="educational_images"
)

# Retrieve for lesson planning
results = await retriever.retrieve(
    topic="Photosynthesis",
    subject="Biology",
    grade_level="9-12",
    text_top_k=5,
    image_top_k=3
)
```

### Generation Module (`src/jina_rag_pipeline/generation/`)

**Key Class: QwenGenerator**
```python
from jina_rag_pipeline.generation import QwenGenerator

generator = QwenGenerator(config=GenerationConfig(
    max_tokens=2048,
    temperature=0.7,
    enable_thinking=False
))

response = await generator.generate(
    prompt="Generate a lesson plan...",
    system_prompt="You are an educational expert..."
)
```

**Key Class: LessonPlanner**
```python
from jina_rag_pipeline.generation import LessonPlanner

planner = LessonPlanner(
    retriever=retriever,
    generator=generator,
    text_top_k=5,
    image_top_k=3
)

lesson = await planner.generate_lesson(
    topic="Photosynthesis",
    learning_objective="...",
    grade="9-12",
    subject="Biology",
    duration=45,
    teaching_style="inquiry"
)
```

---

## Database Schema

### Lesson Model (SQLAlchemy)
```python
class Lesson:
    id: int                          # Primary key
    lesson_id: str                   # UUID
    title: str
    markdown_content: str            # Full lesson markdown
    grade: str                       # Grade level
    subject: str                     # Subject area
    topic: str                       # Topic name
    learning_objective: str          # Learning goal
    duration_minutes: int            # Lesson duration
    teaching_style: str              # balanced, direct, inquiry, project
    metadata_json: Dict              # Extra metadata
    sources_count: int               # Number of cited sources
    images_count: int                # Number of embedded images
    is_favorite: bool                # Bookmark status
    is_archived: bool                # Soft delete
    created_at: datetime             # Creation timestamp
    updated_at: datetime             # Last update timestamp
```

---

## Environment Variables

### Backend
```bash
# OCR configuration
DEEPSEEK_OCR_ENABLED=true           # Enable/disable OCR
DEEPSEEK_BATCH_SIZE=20              # Pages per batch
DEEPSEEK_RENDER_WORKERS=2           # PDF rendering threads

# Distributed processing
RQ_ENABLED=false                    # Enable Redis Queue
REDIS_URL=redis://localhost:6379

# Model paths
EMBEDDINGS_MODEL=jinaai/jina-embeddings-v4
OCR_MODEL_PATH=path/to/model
```

### Frontend
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

---

## Common Tasks

### Add a New Collection
```python
# Frontend UI or via API
POST /api/collections/create?collection_name=my_new_collection

# Creates:
# - ChromaDB collection
# - Directory: uploads/my_new_collection/
#   - documents/
#   - images/
#   - thumbnails/
#   - config.json
```

### Bulk Upload Documents
```bash
# Upload multiple files
curl -X POST http://localhost:8000/api/ingest/upload \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf" \
  -F "files=@doc3.txt" \
  -F "collection_name=my_collection"

# Track with WebSocket
websocat ws://localhost:8000/ws/progress/{task_id}
```

### Generate Lesson Plan
```python
# Python
import httpx

response = httpx.post(
    "http://localhost:8000/api/lesson-plan/generate",
    json={
        "topic": "Photosynthesis",
        "learning_objective": "Understand plant energy conversion",
        "grade_level": "9-12",
        "subject": "Biology",
        "duration_minutes": 45,
        "teaching_style": "inquiry"
    }
)

lesson = response.json()
lesson_id = lesson["lesson_id"]

# Export to PDF
export = httpx.get(
    f"http://localhost:8000/api/lesson-plan/export/{lesson_id}?format=pdf"
)
pdf_bytes = export.content
```

### Search with Filters
```bash
# Search with metadata filtering
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "photosynthesis",
    "collection_name": "biology_resources",
    "top_k": 10,
    "metadata_filter": {
      "grade_level": "9-12",
      "resource_type": "textbook"
    }
  }'
```

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
make logs-backend

# Restart services
make restart

# Check port 8000 is available
lsof -i :8000

# Kill any lingering processes
pkill -f "uvicorn.*8000"
```

### WebSocket connection fails
```bash
# Check WebSocket endpoint
websocat ws://localhost:8000/health

# Verify task_id exists
curl http://localhost:8000/api/ingest/status/{task_id}

# Check CORS if using different domain
# Backend has CORS enabled in app.py
```

### Ingestion hangs
```bash
# Check task status
curl http://localhost:8000/api/ingest/status/{task_id}

# Monitor backend logs
tail -f /tmp/pretty_please_backend.log

# Check disk space (OCR can be memory intensive)
df -h
```

### Model loading slow
```bash
# First load caches model in ~/.cache/huggingface
# Subsequent loads are faster

# Check available memory
python -c "import psutil; print(psutil.virtual_memory())"

# Use lighter embedding config for faster loading
curl -X POST http://localhost:8000/api/config/embeddings \
  -d '{"dimensions": 512}'  # 512 instead of 2048
```

---

## File Locations

### Important Directories
```
project_root/
├── .chroma_db/                      # Vector database
├── data/                            # Configuration files
│   ├── embedding_config.json
│   ├── ocr_config.json
│   └── collection_configs/
├── uploads/                         # Document storage
│   └── {collection_name}/
│       ├── documents/
│       ├── images/
│       ├── thumbnails/
│       └── config.json
├── tasks.db                         # Task persistence
├── lesson_plans.db                  # Lesson library
└── frontend/dist/                   # Built frontend (production)
```

### Log Files
```
/tmp/pretty_please_backend.log       # Backend logs
/tmp/pretty_please_frontend.log      # Frontend logs
```

