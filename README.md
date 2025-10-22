# Jina RAG Pipeline

A production-ready RAG (Retrieval-Augmented Generation) pipeline using Jina Embeddings v4, optimized for Apple Silicon.

## Features

- **Deepseek OCR**: Grounded document understanding with bounding boxes, optical compression, and 5 resolution modes.
- **Configurable Inference**: Toggle grounding/compression, choose resolution presets, and opt into vLLM acceleration.
- **Jina Embeddings v4**: 2048-dimensional embeddings optimised for Apple Silicon and CUDA environments.
- **Vector Storage**: ChromaDB integration for persistent similarity search.
- **Local-First**: Runs entirely on local hardware with optional GPU acceleration; no external services required.

## Installation

```bash
# Create virtual environment with Python 3.10+
uv venv --python 3.10
source .venv/bin/activate

# Install core dependencies (transformers backend)
uv pip install -e .

# Optional: developer tooling and integration test dependencies
uv pip install -e ".[dev]"

# Optional: CUDA acceleration (Linux only)
uv pip install -e ".[deepseek]"       # FlashAttention 2.7.3 for transformers backend
uv pip install -e ".[production]"     # vLLM ≥0.8.5 for high-throughput inference
```

> **Note**  
> FlashAttention and vLLM require a Linux CUDA environment. Skip the optional extras when running on CPU or Apple Silicon (MPS).

## Quick Start

### 1. Generate Embeddings

```python
from src.jina_rag_pipeline.embeddings import JinaEmbeddingsV4

# Initialize embedder (uses MPS on Apple Silicon)
embedder = JinaEmbeddingsV4(device="mps")

# Encode text for retrieval
text = "Machine learning is a subset of artificial intelligence."
embedding = embedder.encode_text(text, task="retrieval")
print(f"Embedding shape: {embedding.shape}")  # (2048,)
```

### 2. Deepseek OCR Ingestion

```python
from pathlib import Path

from jina_rag_pipeline.ingestion.ocr_config import OCRConfig
from jina_rag_pipeline.ingestion.deepseek_loader import DeepseekLoader

# Load Deepseek with balanced preset
config = OCRConfig.deepseek_balanced()
loader = DeepseekLoader(config=config)

document = loader.load(Path("path/to/document.pdf"))

print(document.metadata["ocr_engine"])        # "deepseek"
print(document.metadata["resolution_mode"])   # "base"
print(len(document.metadata["regions"]))      # Semantic regions with optional bounding boxes
```

Toggle grounding or compression by updating `config.enable_grounding` / `config.enable_compression` before instantiating the loader. Set `config.use_vllm = True` when running on CUDA hardware with vLLM installed.

### 3. Vector Storage and Search

```python
from src.jina_rag_pipeline.storage import ChromaVectorStore

# Initialize vector store
store = ChromaVectorStore(persist_directory="./my_db")

# Create collection
store.create_collection(
    name="documents",
    embedding_dimension=2048,
    metadata={"description": "My document collection"}
)

# Add embeddings
documents = ["Text 1", "Text 2", "Text 3"]
embeddings = [
    embedder.encode_text(doc, task="retrieval").tolist()
    for doc in documents
]

ids = store.add_embeddings(
    collection_name="documents",
    embeddings=embeddings,
    documents=documents,
    metadatas=[{"source": f"doc_{i}"} for i in range(len(documents))]
)

# Similarity search
query = "Find similar documents"
query_embedding = embedder.encode_text(query, task="retrieval").tolist()
results = store.similarity_search(
    collection_name="documents",
    query_embedding=query_embedding,
    top_k=5
)

for result in results:
    print(f"Score: {result.score:.4f}, Doc: {result.document}")
```

## Documentation

- `docs/guides/migration-to-deepseek.md` – migration steps and rollout checklist.
- `docs/guides/deepseek-ocr-configuration.md` – full reference for resolution modes, grounding, and vLLM options.

## Running the Application

The project includes a Makefile for easy service management (backend API + frontend).

### Starting Services

```bash
# Start all services (backend + frontend)
make start
# or
make dev

# Start only backend
make backend

# Start only frontend
make frontend
```

After starting, the application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Managing Services

```bash
# Check service status
make status

# View logs
make logs              # All logs
make logs-backend      # Backend only
make logs-frontend     # Frontend only

# Stop all services
make stop

# Restart all services
make restart
```

### Cleaning Data

```bash
# Clean database and uploads (with confirmation)
make clean

# Stop services and clean all data
make clean-all
```

### Other Commands

```bash
# Install all dependencies
make install

# Build frontend for production
make build

# Run tests
make test

# Format code
make format

# Lint code
make lint

# Show all available commands
make help
```

## Testing

```bash
# Fast unit tests
pytest tests -m "not slow" -v

# Deepseek OCR smoke tests (requires model download, optionally GPU)
RUN_DEEPSEEK_INTEGRATION=1 pytest tests/integration/test_deepseek_ocr.py -v

# Legacy compatibility verification
pytest tests/integration/test_migration.py -v

# Optional quality/performance benchmarks
python scripts/deepseek_benchmark.py --help
```

## Project Structure

```
src/jina_rag_pipeline/
├── embeddings/           # Jina Embeddings v4 implementation
│   ├── __init__.py
│   └── jina_v4.py
└── storage/             # Vector database integration
    ├── __init__.py
    ├── base.py          # Abstract interface
    └── chroma_store.py  # ChromaDB implementation

tests/                   # Test suite
├── test_embeddings.py
└── test_storage.py

openspec/               # OpenSpec change proposals
├── changes/
└── specs/             # Technical specifications
```

## Performance

Benchmarks on M4 Max MacBook Pro (48GB RAM):

- **Embedding generation**: 15+ texts/second (retrieval task)
- **Batch insertion**: 100 embeddings in <5 seconds
- **Similarity search**: 10 results from 1000 vectors in <1 second

## Documentation

- [Embeddings Spec](openspec/specs/embeddings/spec.md)
- [Storage Spec](openspec/specs/storage/spec.md)
- [Change Proposals](openspec/changes/)

## Development

This project uses OpenSpec for change management:

```bash
# View active changes
ls openspec/changes/

# View archived changes
ls openspec/changes/archive/
```

## Requirements

- Python 3.10+
- macOS with Apple Silicon (M1/M2/M3/M4)
- 16GB+ RAM recommended (48GB for optimal performance)

## License

MIT
