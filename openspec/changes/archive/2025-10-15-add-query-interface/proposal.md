## Why
Provide a REST API for querying the RAG pipeline, enabling applications to perform semantic search and retrieve relevant documents based on natural language queries.

## What Changes
- Implement FastAPI-based REST API server
- Add semantic search endpoints with query processing
- Create response formatting with relevance scores
- Add health checks and monitoring endpoints
- Implement query caching for performance

## Impact
- Affected specs: api (new)
- Affected code: New API module, integrates with embeddings and storage
- Blocks: None
- Depends on: Core embeddings and vector database