from src.jina_rag_pipeline.embeddings.config import EmbeddingConfig


def test_for_query_uses_full_jina_dimension():
    """Regression test: query embeddings must stay at 2048 dimensions."""
    config = EmbeddingConfig.for_query()
    assert config.dimensions == 2048
    assert config.late_chunking is False
