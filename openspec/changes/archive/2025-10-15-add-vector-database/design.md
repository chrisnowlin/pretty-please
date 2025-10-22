## Context
Vector database is critical infrastructure for the RAG pipeline. ChromaDB offers local-first operation with good Apple Silicon support, while LanceDB provides an alternative with columnar storage benefits.

## Goals / Non-Goals
- Goals:
  - Local persistent storage without external services
  - Fast similarity search on M4 Max hardware
  - Support for metadata filtering
  - Easy collection management
  - Abstract interface for database portability
- Non-Goals:
  - Distributed/cloud storage
  - Real-time synchronization
  - Complex query languages (stick to similarity search)

## Decisions
- Decision: ChromaDB as primary implementation
  - Rationale: Mature, good docs, native Apple Silicon support, embedded mode
- Decision: Abstract VectorStore interface
  - Rationale: Allow switching to LanceDB or others if needed
- Decision: Collection-per-document-type pattern
  - Rationale: Better organization, independent index optimization
- Alternatives considered:
  - FAISS: Requires separate metadata storage
  - Pinecone: Cloud-only, not local
  - Weaviate: Heavier, requires Docker

## Risks / Trade-offs
- ChromaDB persistence format may change → Version lock in pyproject.toml
- Large collections may slow down → Implement collection size limits
- Concurrent writes need coordination → Use threading locks

## Migration Plan
N/A - New functionality

## Open Questions
- Should we support multiple vector databases simultaneously?
- What's the optimal chunk size for batch operations?
- Should we implement automatic backup functionality?