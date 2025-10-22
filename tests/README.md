# Tests Directory

This directory contains the test suite for the Pretty Please RAG pipeline.

## Directory Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for end-to-end workflows
├── fixtures/          # Test data and expected outputs
├── test_*.py          # Top-level integration tests
└── e2e_*.py          # End-to-end tests
```

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/test_embeddings.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src/jina_rag_pipeline --cov-report=html
```

## Test Categories

### Unit Tests (`unit/`)

| Test File | Description |
|-----------|-------------|
| `test_markdown_parser.py` | Markdown parser for Nanonets output |
| `test_semantic_region.py` | SemanticRegion model and operations |

### Integration Tests (`integration/`)

| Test File | Description |
|-----------|-------------|
| `test_nanonets_layout.py` | Nanonets layout analyzer |
| `test_nanonets_e2e.py` | End-to-end Nanonets processing |
| `test_powerpoint_nanonets.py` | PowerPoint with Nanonets |
| `test_semantic_region_processing.py` | Semantic region processing pipeline |

### Top-Level Integration Tests

| Test File | Description |
|-----------|-------------|
| `test_embeddings.py` | Jina Embeddings v4 functionality |
| `test_storage.py` | ChromaDB vector store operations |
| `test_ingestion.py` | Document ingestion pipeline |
| `test_multimodal.py` | Multimodal (text + image) processing |
| `test_colbert.py` | ColBERT reranking |
| `test_batch.py` | Batch processing for multiple documents |
| `test_api.py` | FastAPI endpoint tests |
| `test_api_ingestion.py` | API ingestion workflow |
| `test_e2e_pipeline.py` | Complete end-to-end pipeline |
| `test_stress.py` | Stress testing and performance |
| `test_nanonets_first_loader.py` | Nanonets-first document loader |
| `e2e_nanonets_pdf_test.py` | E2E Nanonets PDF processing |

## Test Fixtures

The `fixtures/` directory contains:
- `rag_test_queries.json` - Test queries for RAG evaluation
- Sample PDFs and presentations
- Expected outputs for validation

## Writing Tests

### Best Practices

1. **Use Fixtures**: Reuse test data from `fixtures/` directory
2. **Isolation**: Tests should not depend on each other
3. **Cleanup**: Clean up test data in teardown
4. **Descriptive Names**: Use clear test function names
5. **Assertions**: Use specific assertions with clear messages

### Example Test Structure

```python
import pytest
from jina_rag_pipeline.embeddings import JinaEmbeddingsV4

class TestJinaEmbeddings:
    @pytest.fixture
    def embedder(self):
        """Create embedder instance for tests."""
        return JinaEmbeddingsV4(device="cpu")
    
    def test_encode_text(self, embedder):
        """Test basic text encoding."""
        text = "Test document"
        embedding = embedder.encode_text(text, task="retrieval")
        
        assert embedding.shape == (2048,)
        assert embedding.dtype == np.float32
```

## CI/CD Integration

Tests are automatically run on:
- Pull requests
- Commits to main branch
- Nightly builds (stress tests)

## Related Documentation

- [Getting Started Guide](../docs/guides/getting-started.md)
- [System Architecture](../docs/architecture/system-overview.md)
- [Test Scripts](../scripts/README.md) - Additional test scripts in `scripts/tests/`
