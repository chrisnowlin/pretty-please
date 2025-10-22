# Design: RAG Quality Enhancement Architecture

## Architecture Overview

The enhanced RAG pipeline follows a multi-stage approach:

```
User Query
    ↓
[1] Query Encoding (JinaV4 embeddings)
    ↓
[2] Hybrid Retrieval (Semantic + Keyword)
    ↓
[3] Cross-Encoder Reranking
    ↓
[4] Contextual Compression & Formatting
    ↓
[5] LLM Generation with Enhanced Prompts
    ↓
Formatted Response with Citations
```

## Component Design

### 1. Hybrid Retrieval Module

**Purpose**: Combine semantic and keyword-based search for better recall

**Design Decisions**:
- Use ChromaDB's existing vector search for semantic component
- Add BM25/keyword matching using document metadata or separate index
- Combine results using Reciprocal Rank Fusion (RRF) or weighted scoring

**Trade-offs**:
- **Pro**: Higher recall, catches exact keyword matches missed by semantic search
- **Con**: Adds 20-50ms latency; requires managing two search paths
- **Decision**: Implement BM25 scoring in-memory using retrieved documents' text to minimize infrastructure changes

**Implementation Approach**:
```python
class HybridRetriever:
    def __init__(self, vector_store, embedder):
        self.vector_store = vector_store
        self.embedder = embedder
        self.bm25_scorer = BM25Scorer()  # Lightweight in-memory

    async def retrieve(self, query, top_k=20):
        # Step 1: Vector search (larger batch)
        vector_results = await self.vector_store.similarity_search(query, top_k=top_k)

        # Step 2: BM25 scoring on retrieved docs
        bm25_scores = self.bm25_scorer.score(query, vector_results)

        # Step 3: Fusion (RRF or weighted)
        fused_results = self._fuse_results(vector_results, bm25_scores)

        return fused_results
```

### 2. Cross-Encoder Reranking

**Purpose**: Refine retrieval results using bi-encoder attention between query and documents

**Design Decisions**:
- Use pre-trained cross-encoder model: `BAAI/bge-reranker-base` or `ms-marco-MiniLM-L-12-v2`
- Load model lazily and cache in memory
- Apply reranking only to top-K results (K=15-20) to manage latency
- Support 4-bit quantization for memory efficiency

**Trade-offs**:
- **Pro**: Significantly improves precision (30-50% in benchmarks)
- **Con**: Adds 100-300ms latency per query depending on batch size
- **Decision**: Use lightweight reranker with batch processing; make configurable

**Model Selection Criteria**:
| Model | Size | Inference Time | Accuracy | Notes |
|-------|------|---------------|----------|-------|
| bge-reranker-base | ~278MB | ~150ms/20docs | High | Best balance |
| ms-marco-MiniLM | ~120MB | ~80ms/20docs | Medium | Faster, slightly lower quality |
| bge-reranker-large | ~1.3GB | ~400ms/20docs | Highest | Too slow for real-time |

**Selected**: `bge-reranker-base` (quantized to 4-bit ≈ 70MB)

**Implementation Approach**:
```python
class CrossEncoderReranker:
    def __init__(self, model_name="BAAI/bge-reranker-base"):
        self.model = None  # Lazy load
        self.model_name = model_name

    async def rerank(self, query, documents, top_n=5):
        if self.model is None:
            self._load_model()

        # Create query-document pairs
        pairs = [(query, doc.content) for doc in documents]

        # Score in batch
        scores = await self._score_batch(pairs)

        # Sort and return top_n
        reranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in reranked[:top_n]]
```

### 3. Contextual Compression

**Purpose**: Optimize retrieved content for LLM context window

**Design Decisions**:
- Re-chunk long documents into smaller semantic units (400-600 chars)
- Filter chunks using embedding similarity threshold (>0.7)
- Keep metadata (source, chunk position) for citation tracking

**Trade-offs**:
- **Pro**: Better context utilization, removes noise
- **Con**: Adds 50-100ms processing time; risk of losing context
- **Decision**: Make compression optional via config flag; default ON for documents >1000 chars

**Implementation Approach**:
```python
class ContextualCompressor:
    def __init__(self, embedder, chunk_size=500):
        self.embedder = embedder
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " "]
        )

    async def compress(self, documents, query, top_k=10):
        # Re-chunk documents
        chunks = []
        for doc in documents:
            doc_chunks = self.splitter.split_text(doc.content)
            for i, chunk in enumerate(doc_chunks):
                chunks.append({
                    'content': chunk,
                    'source': doc.source,
                    'chunk_id': i,
                    'original_score': doc.score
                })

        # Filter by relevance
        query_embedding = self.embedder.encode_text([query])[0]
        chunk_embeddings = self.embedder.encode_text([c['content'] for c in chunks])

        similarities = cosine_similarity(query_embedding, chunk_embeddings)

        # Keep top_k most relevant chunks
        ranked_chunks = sorted(zip(chunks, similarities), key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in ranked_chunks[:top_k] if score > 0.7]
```

### 4. Enhanced Context Formatting

**Purpose**: Present retrieved information in a structured, citation-friendly format

**Design Decisions**:
- Use numbered citation format: `[1]`, `[2]`, etc.
- Include metadata in a consistent structure
- Separate text and image results clearly
- Add relevance scores for LLM guidance

**Format Structure**:
```markdown
**Retrieved Context:**

**Text Sources:**

[1] **Source**: document.pdf (page 5) | **Relevance**: 0.92
<content chunk>

[2] **Source**: article.md | **Relevance**: 0.87
<content chunk>

---

**Image Sources:**

[IMG-1] **File**: diagram.png | **Description**: Architecture diagram showing... | **Relevance**: 0.85

[IMG-2] **File**: chart.jpg | **Description**: Bar chart comparing... | **Relevance**: 0.79
```

**Implementation Approach**:
```python
class EnhancedContextFormatter:
    def format_multimodal_context(self, text_results, image_results):
        parts = []

        if text_results:
            parts.append("**Text Sources:**\n")
            for i, result in enumerate(text_results, 1):
                citation_id = f"[{i}]"
                source = result.get('source', 'Unknown')
                score = result.get('score', 0.0)
                content = result.get('content', '')

                parts.append(
                    f"{citation_id} **Source**: {source} | **Relevance**: {score:.2f}\n"
                    f"{content}\n\n"
                )

        if image_results:
            parts.append("---\n\n**Image Sources:**\n")
            for i, result in enumerate(image_results, 1):
                citation_id = f"[IMG-{i}]"
                filename = result['metadata'].get('filename', 'unknown')
                description = result['metadata'].get('description', '')
                score = result.get('score', 0.0)

                parts.append(
                    f"{citation_id} **File**: {filename} | "
                    f"**Description**: {description} | **Relevance**: {score:.2f}\n\n"
                )

        return "".join(parts)
```

### 5. System Prompt Enhancements

**Purpose**: Guide LLM to generate well-formatted, cited responses

**Design Decisions**:
- Add explicit citation format instructions
- Include markdown formatting guidelines
- Provide confidence expression templates
- Add examples of good response format

**Enhanced Prompt Template**:
```python
ENHANCED_SYSTEM_PROMPT = """You are a helpful AI assistant with access to a document collection.

**How to Use Context:**
- Context sources are numbered like [1], [2] for text and [IMG-1], [IMG-2] for images
- Always cite sources when using information: "According to [1], ..." or "As shown in [IMG-1], ..."
- If information comes from multiple sources, cite all: "Multiple sources [1][3] indicate..."

**Response Formatting:**
- Use markdown for structure: headers (##), lists, **bold**, *italic*
- Format code with backticks: `code` or ```language blocks
- Use tables when comparing information
- Break long responses into sections with headers

**Confidence and Uncertainty:**
- If context is insufficient: "Based on the available context [1][2], I can partially answer..."
- If uncertain: "The context suggests... but doesn't provide definitive information."
- If no relevant context: "I don't find relevant information in the provided context."

**Example Good Response:**
"According to [1], the system uses a three-tier architecture:

1. **Frontend Layer**: Built with React [1]
2. **API Layer**: FastAPI endpoints [2]
3. **Storage Layer**: ChromaDB for vectors [1]

The architecture diagram [IMG-1] illustrates these components and their interactions."

Now answer the user's question using the provided context below.
"""
```

## Performance Considerations

### Latency Budget (Target: <3s p95)

| Component | Baseline | Enhanced | Optimization |
|-----------|----------|----------|-------------|
| Query Encoding | 50ms | 50ms | Cached embedder |
| Vector Search | 100ms | 120ms | Larger batch (20 vs 10) |
| BM25 Scoring | 0ms | 30ms | In-memory on retrieved docs |
| Reranking | 0ms | 150ms | Quantized cross-encoder |
| Compression | 0ms | 80ms | Parallel chunk embedding |
| LLM Generation | 1500ms | 1500ms | No change |
| **Total** | **1650ms** | **1930ms** | **Within budget** |

### Memory Usage (Target: <32GB active)

| Component | Model Size | Runtime Memory | Notes |
|-----------|-----------|----------------|-------|
| JinaV4 Embedder | 2GB | 3GB | Existing |
| Qwen3-14B LLM | 7GB | 10GB | Existing |
| Cross-Encoder | 70MB | 500MB | 4-bit quantized |
| Context Processing | - | 200MB | Temporary buffers |
| **Total** | **~9GB** | **~14GB** | **Safe margin** |

## Configuration Strategy

Make all enhancements configurable to allow tuning and A/B testing:

```python
@dataclass
class RAGConfig:
    # Retrieval
    enable_hybrid_search: bool = True
    hybrid_alpha: float = 0.5  # Weight between semantic and keyword
    initial_retrieval_k: int = 20

    # Reranking
    enable_reranking: bool = True
    rerank_model: str = "BAAI/bge-reranker-base"
    rerank_top_n: int = 5

    # Compression
    enable_compression: bool = True
    compression_chunk_size: int = 500
    compression_threshold: float = 0.7
    compression_max_chunks: int = 10

    # Formatting
    citation_style: str = "numbered"  # or "inline", "footnote"
    include_relevance_scores: bool = True
```

## Testing Strategy

1. **Unit Tests**: Each component (reranker, compressor, formatter) independently
2. **Integration Tests**: Full pipeline with sample queries and expected output format
3. **Performance Tests**: Latency and memory benchmarks
4. **Quality Tests**: Retrieval relevance metrics (NDCG, MRR)
5. **A/B Tests**: Compare baseline vs enhanced on representative query set

## Rollout Plan

1. **Phase 1**: Implement and test reranking (most impact, lowest risk)
2. **Phase 2**: Add enhanced context formatting and prompts
3. **Phase 3**: Add hybrid search capability
4. **Phase 4**: Implement contextual compression (optional enhancement)

## Open Questions

1. Should we implement query expansion for complex multi-part questions? (Deferred)
2. How to handle citations for compressed/re-chunked documents? (Track original source + chunk ID)
3. Should images be re-scored separately or together with text? (Separate, different modality)
4. Configuration: User-level, session-level, or system-level? (System-level initially, user-level later)
