## Why
Enable processing of various document formats into embeddings for the RAG pipeline. This bridges the gap between raw documents and searchable vector representations.

## What Changes
- Add document loaders for common formats (PDF, TXT, MD, DOCX)
- Implement text chunking strategies with overlap
- Create document processing pipeline with embedding generation
- Add document metadata extraction and management
- Implement incremental ingestion to avoid reprocessing

## Impact
- Affected specs: ingestion (new)
- Affected code: New ingestion module, integrates with embeddings and storage
- Blocks: None directly, but needed for useful RAG functionality
- Depends on: Core embeddings and vector database