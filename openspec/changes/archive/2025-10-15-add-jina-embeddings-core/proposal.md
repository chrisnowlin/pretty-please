## Why
Establish the foundational embedding generation capability using Jina Embeddings v4 model, optimized for Apple Silicon. This is the core dependency for all RAG pipeline features.

## What Changes
- Add Jina Embeddings v4 model initialization with MPS backend support
- Implement text embedding generation for all three task types (retrieval, text-matching, code)
- Add model caching and lazy loading for memory efficiency
- Configure environment setup with uv and required dependencies

## Impact
- Affected specs: embeddings (new)
- Affected code: New core embeddings module
- Blocker for: All other RAG pipeline features