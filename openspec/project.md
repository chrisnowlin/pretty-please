# Pretty Please - Lesson Plan Generation System

## Project Overview

Pretty Please is a production-ready **Jina RAG pipeline** for educational content retrieval and augmented lesson plan generation. The system combines state-of-the-art embeddings, vector search, and LLM-based content generation to help teachers create structured, standards-aligned lesson plans.

## Core Capabilities

### Phase 1: RAG Foundation (COMPLETED)
- **Jina Embeddings v4**: 2048-dimensional semantic embeddings with MPS acceleration
- **ChromaDB**: Persistent vector storage with similarity search
- **Multi-format ingestion**: PDFs, PowerPoint, images, markdown, JSON
- **Multimodal support**: Text + image embeddings and retrieval

### Phase 2: Async & Progress (COMPLETED)
- **Non-blocking document processing**: ThreadPool + async offloading
- **Real-time progress tracking**: WebSocket updates per page
- **Progressive rendering**: Memory-efficient batch processing
- **Visual feedback**: Frontend integration with status updates

### Phase 3: Distributed Processing (COMPLETED)
- **RQ worker queues**: Horizontal scaling for large files
- **Smart routing**: <10MB ThreadPool, >10MB distributed workers
- **Priority queues**: High/default/low task scheduling
- **Redis backend**: Shared state management across workers

### Phase 4: Metrics & Monitoring (COMPLETED)
- **Real-time dashboard**: Processing statistics and performance breakdown
- **Performance analytics**: By method (RQ/ThreadPool/Vision) and file type
- **System monitoring**: CPU, memory, queue depth tracking
- **Event history**: Configurable recent event tracking (default 1000)

### Phase 5: Production Deployment (COMPLETED)
- **Multi-worker deployment**: Gunicorn + Uvicorn, Docker Compose, Kubernetes
- **Sticky sessions**: WebSocket handling across workers
- **Shared storage**: S3 integration, persistent volumes
- **Security**: HTTPS, authentication, rate limiting ready

## Current Application State

- **Backend**: FastAPI with async/await, WebSocket support
- **Frontend**: React with TypeScript, Vite build
- **AI Model**: Qwen3-14B-4bit with MLX framework (Apple Silicon optimized)
- **Database**: ChromaDB (vector) + optional metadata store
- **Deployment**: Docker Compose ready, Kubernetes manifests available

## Lesson Planning Context

The system currently supports general-purpose RAG chatting. The next evolution is to **specialize** the RAG system for educational lesson planning:

- **Input**: Educational standards, curriculum guides, teaching resources
- **Processing**: Retrieve contextually relevant materials for specific topics, grade levels, learning objectives
- **Output**: Structured lesson plans with learning objectives, materials, activities, assessments

## OpenSpec Usage

All future changes are proposed through OpenSpec with clear capability specifications, design rationale, and implementation tasks. This ensures comprehensive documentation and traceability.

## Repository Structure

```
.
├── openspec/
│   ├── project.md (this file)
│   ├── changes/
│   │   └── lesson-plan-rag-integration/
│   │       ├── proposal.md
│   │       ├── design.md
│   │       ├── tasks.md
│   │       └── specs/
│   │           ├── educational-content-ingestion/
│   │           ├── lesson-plan-generation/
│   │           ├── standards-alignment/
│   │           └── teacher-customization/
│   └── specs/
│       ├── embeddings/spec.md
│       ├── storage/spec.md
│       └── ...
├── src/jina_rag_pipeline/
│   ├── embeddings/
│   ├── storage/
│   ├── ingestion/
│   ├── retrieval/
│   ├── generation/
│   ├── multimodal/
│   ├── batch/
│   ├── workers/
│   ├── monitoring/
│   └── api/
├── frontend/
└── tests/
```
