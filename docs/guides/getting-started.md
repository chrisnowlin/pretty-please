# Getting Started with Pretty Please

## Overview

Pretty Please is a production-ready RAG (Retrieval-Augmented Generation) pipeline using Jina Embeddings v4, optimized for Apple Silicon with advanced document processing capabilities including PDFs, PowerPoint presentations, and multimodal content.

## Features

- **Jina Embeddings v4**: State-of-the-art 2048-dimensional embeddings with MPS acceleration
- **Vector Database**: ChromaDB integration for persistent storage and similarity search
- **Multimodal Support**: Process PDFs, PowerPoint, images, tables, and equations
- **Semantic Analysis**: Rich metadata extraction with Nanonets OCR
- **Async Processing**: Non-blocking document processing with WebSocket progress updates
- **Distributed Workers**: Scale horizontally with Redis Queue (RQ)
- **Local-First**: No cloud dependencies, complete data privacy
- **RAG Chat**: Interactive chatbot with source citations

## Installation

### Prerequisites

- Python 3.10+
- macOS with Apple Silicon (M1/M2/M3/M4) or Linux/Windows
- 10GB+ RAM recommended
- Redis (optional, for distributed processing)

### Basic Installation

```bash
# Create virtual environment with Python 3.10+
uv venv --python 3.10
source .venv/bin/activate

# Install package with dependencies
uv pip install -e .

# Install dev dependencies (for testing)
uv pip install -e ".[dev]"
```

### Optional: Distributed Processing

```bash
# Install Redis and RQ for distributed workers
uv pip install redis>=5.0.0 rq>=1.15.0
```

### Verify Installation

```bash
python3 -c "import jina_rag_pipeline; print('✓ Installation successful')"
```

## Quick Start

### 1. Start the Backend API

```bash
uvicorn jina_rag_pipeline.api.app:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### 2. Start the Frontend (Development)

```bash
cd frontend
bun install
bun run dev
```

The frontend will be available at `http://localhost:3000`.

### 3. Upload Your First Document

#### Via Web UI

1. Open `http://localhost:3000` in your browser
2. Navigate to the **Ingestion** page
3. Select or create a collection
4. Upload a PDF, PowerPoint, or image file
5. Monitor the progress in real-time

#### Via API (cURL)

```bash
curl -X POST "http://localhost:8000/api/ingest/upload" \
  -F "files=@/path/to/document.pdf" \
  -F "collection_name=my_collection"
```

#### Via Python

```python
import requests

url = "http://localhost:8000/api/ingest/upload"
files = {"files": open("document.pdf", "rb")}
data = {"collection_name": "my_collection"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### 4. Search Your Documents

#### Via Web UI

1. Navigate to the **Search** page
2. Select your collection
3. Enter a search query
4. View ranked results with snippets

#### Via API (cURL)

```bash
curl -X POST "http://localhost:8000/api/search/query" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "my_collection",
    "query": "What is machine learning?",
    "top_k": 5
  }'
```

#### Via Python

```python
import requests

url = "http://localhost:8000/api/search/query"
payload = {
    "collection_name": "my_collection",
    "query": "What is machine learning?",
    "top_k": 5
}

response = requests.post(url, json=payload)
results = response.json()

for result in results["results"]:
    print(f"Score: {result['score']:.3f}")
    print(f"Content: {result['content']}\n")
```

### 5. Chat with Your Documents

#### Via Web UI

1. Navigate to the **Chat** page
2. Select your collection
3. Ask questions in natural language
4. View AI-generated answers with source citations

#### Via API (cURL)

```bash
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "my_collection",
    "query": "Explain the key concepts in this document",
    "session_id": "my-session"
  }'
```

#### Via Python

```python
import requests

url = "http://localhost:8000/api/chat/query"
payload = {
    "collection_name": "my_collection",
    "query": "Explain the key concepts",
    "session_id": "my-session"
}

response = requests.post(url, json=payload)
chat_response = response.json()

print(f"Answer: {chat_response['answer']}")
print(f"\nCitations:")
for citation in chat_response.get("citations", []):
    print(f"  - {citation['source']} (page {citation['page']})")
```

## Common Tasks

### Create a New Collection

```python
import requests

url = "http://localhost:8000/api/collections/create"
payload = {
    "name": "research_papers",
    "description": "Collection of ML research papers",
    "metadata": {"domain": "machine_learning"}
}

response = requests.post(url, json=payload)
print(response.json())
```

### List All Collections

```bash
curl http://localhost:8000/api/collections/list
```

### Delete a Collection

```bash
curl -X DELETE "http://localhost:8000/api/collections/delete/my_collection"
```

### Monitor Upload Progress (WebSocket)

```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    print(f"Progress: {data['progress']}%")
    if data['status'] == 'completed':
        print("Upload complete!")
        ws.close()

ws = websocket.WebSocketApp(
    "ws://localhost:8000/ws/tasks/my-task-id",
    on_message=on_message
)
ws.run_forever()
```

## Document Processing Features

### Supported File Types

- **PDF Documents**: Text, images, tables, equations
- **PowerPoint**: .pptx, .ppt presentations
- **Images**: .png, .jpg, .jpeg (with OCR)
- **Text Files**: .txt, .md

### Semantic Extraction

Pretty Please extracts rich semantic metadata:

- **Tables**: Full HTML structure with rows/columns
- **Equations**: LaTeX representation
- **Images**: Natural language descriptions
- **Text**: Headings, paragraphs, lists
- **Citations**: Automatic source linking

### Processing Options

```python
# Enable specific features during ingestion
payload = {
    "collection_name": "my_collection",
    "enable_ocr": True,              # OCR for scanned documents
    "enable_tables": True,           # Extract table content
    "enable_equations": True,        # Extract LaTeX equations
    "enable_image_descriptions": True, # Generate image descriptions
    "chunk_size": 512,               # Chunk size for embeddings
    "chunk_overlap": 50              # Overlap between chunks
}
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Storage
CHROMA_PERSIST_DIR=./chroma_storage
UPLOAD_DIR=./uploads

# Nanonets OCR
NANONETS_FIRST_ENABLED=true

# Async Processing
DISTRIBUTED_PROCESSING_ENABLED=false
LARGE_FILE_THRESHOLD_MB=10.0

# Redis (if using distributed processing)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=info
```

### Advanced Configuration

See [Configuration Guide](../architecture/system-overview.md) for advanced options.

## Performance Tips

### For Small Files (<5MB)

- Default ThreadPool processing is optimal
- No additional configuration needed

### For Large Files (>10MB)

1. Enable distributed processing:
   ```bash
   export DISTRIBUTED_PROCESSING_ENABLED=true
   ```

2. Start Redis:
   ```bash
   docker run -d -p 6379:6379 redis:latest
   ```

3. Start RQ workers:
   ```bash
   python -m jina_rag_pipeline.workers.worker
   ```

### For Presentations with Many Slides

Use batch processing for better throughput:

```python
from jina_rag_pipeline.ingestion.nanonets_layout import create_analyzer

analyzer = create_analyzer()
all_regions = analyzer.extract_regions_batch(
    file_paths=slide_paths,
    batch_size=4  # Process 4 slides simultaneously
)
```

## Troubleshooting

### API Not Responding

```bash
# Check if the server is running
curl http://localhost:8000/api/health

# Check logs
tail -f logs/api.log
```

### Slow Document Processing

- Check available memory: `htop` or Activity Monitor
- Reduce batch size if using batch processing
- Enable distributed processing for large files

### WebSocket Connection Issues

- Verify WebSocket URL: `ws://localhost:8000/ws/tasks/{task_id}`
- Check firewall settings
- Ensure no proxy is interfering

### Upload Fails

- Check file size limits (default: 100MB)
- Verify file format is supported
- Check disk space in upload directory

### Out of Memory

- Reduce concurrent workers
- Process files sequentially instead of batching
- Increase system RAM or use distributed workers

## Next Steps

- [Async Processing Guide](async-processing.md) - Scale your document processing
- [Nanonets Migration Guide](nanonets-migration.md) - Advanced OCR features
- [Citations Feature](../features/citations.md) - Link answers to sources
- [System Architecture](../architecture/system-overview.md) - Understand the internals

## Getting Help

- Check the [GitHub Issues](https://github.com/chrisnowlin/pretty-please/issues)
- Review API documentation at `http://localhost:8000/docs`
- Read the [Architecture Overview](../architecture/system-overview.md)

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
