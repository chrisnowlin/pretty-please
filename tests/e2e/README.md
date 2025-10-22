# End-to-End Tests for RAG Pipeline

This directory contains end-to-end tests for the complete RAG pipeline from document ingestion to query processing.

## Current Tests

The following tests verify the integration of key pipeline components:

1. **Component Import Test** - Verifies that all major pipeline components can be imported
2. **API Endpoint Test** - Verifies that core API endpoints exist and are accessible

## Pipeline Components

The RAG pipeline consists of these main components:

1. **Document Ingestion**
   - PaddleOCR-VL Analyzer
   - Analysis Pipeline
   - Document Loaders

2. **Vector Storage & Retrieval**
   - Educational Retriever
   - ChromaDB Storage

3. **Lesson Generation**
   - Lesson Planner
   - Qwen Generator

4. **API Layer**
   - FastAPI Application
   - Chat Endpoint
   - Ingestion Endpoint
   - Collection Management

## Test Structure

The tests verify:
- All components can be imported without errors
- Core API endpoints return expected responses
- The complete pipeline architecture is properly structured
- Integration points between components are defined

## Running Tests

```bash
# Run the tests
cd /Users/cnowlin/Developer/pretty_please-paddleocr-vl
bun test tests/e2e/test_pipeline_structure.js
```

## Future Enhancements

Future E2E tests should include:
- Actual document ingestion and processing
- Vector storage and retrieval from real documents
- Query processing with context retrieval
- Lesson generation from retrieved information
- Complete end-to-end flow testing with mocked services