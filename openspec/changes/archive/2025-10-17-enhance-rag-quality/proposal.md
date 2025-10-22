# Proposal: Enhance RAG Response Quality and Formatting

## Overview

This change enhances the RAG (Retrieval-Augmented Generation) pipeline to deliver higher-quality, better-formatted chat responses by implementing advanced retrieval techniques, contextual compression, and structured response formatting.

## Problem Statement

The current RAG implementation has several limitations:

1. **Basic Retrieval**: Uses only semantic similarity search without reranking or hybrid search, leading to suboptimal context selection
2. **Poor Context Formatting**: Retrieved documents are presented with minimal structure, making it hard for the LLM to parse and cite sources effectively
3. **No Response Formatting Guidance**: System prompts lack specific instructions for markdown formatting, citations, and confidence indicators
4. **Missing Reranking**: Retrieves a small batch (10 docs) and returns top results without relevance refinement
5. **No Query Enhancement**: Complex queries are not broken down or expanded for better retrieval

These limitations result in responses that:
- Miss relevant context due to poor retrieval
- Lack proper citations and source attribution
- Have inconsistent formatting
- Don't communicate uncertainty effectively

## Proposed Solution

Implement a multi-stage RAG enhancement pipeline based on 2025 best practices:

### 1. Advanced Retrieval Strategy
- **Hybrid Search**: Combine semantic (vector) and keyword (BM25) search for better recall
- **Larger Initial Batch**: Retrieve 15-20 candidates instead of 10 for better coverage
- **Cross-Encoder Reranking**: Re-score and rerank retrieved documents for precision

### 2. Contextual Compression
- **Smart Chunking**: Re-chunk retrieved documents for optimal context window usage
- **Relevance Filtering**: Filter out low-relevance chunks using embedding similarity
- **Metadata Enrichment**: Include document metadata (date, type, source) in context

### 3. Enhanced Context Formatting
- **Numbered Citations**: Provide [1], [2] style reference numbers for easy citation
- **Structured Presentation**: Use consistent markdown formatting for different content types
- **Relevance Indicators**: Show confidence scores and relevance to guide LLM attention
- **Image Metadata**: Enhanced image descriptions with visual characteristics

### 4. Response Formatting Instructions
- **Citation Guidelines**: Explicit instructions for inline citation format
- **Markdown Formatting**: Guidelines for headers, lists, code blocks, emphasis
- **Confidence Communication**: Instructions for expressing uncertainty
- **Multi-turn Awareness**: Better conversation context handling

## Benefits

- **Higher Accuracy**: Reranking and hybrid search improve context relevance by 30-50% (industry benchmarks)
- **Better Citations**: Numbered references make source attribution clearer and more verifiable
- **Improved Readability**: Consistent markdown formatting enhances user experience
- **Reduced Hallucination**: Better context and confidence communication reduce factual errors
- **Scalability**: Techniques work well as document collection grows

## Scope

### In Scope
- Cross-encoder reranking implementation
- Hybrid search (semantic + keyword)
- Context formatting improvements
- System prompt enhancements
- Response citation format
- Contextual compression utilities

### Out of Scope
- Query decomposition (future enhancement)
- Multi-step reasoning chains
- External knowledge base integration
- Custom fine-tuning of embedding models
- Real-time learning from feedback

## Dependencies

- Existing: `JinaEmbeddingsV4`, `ChromaVectorStore`, `QwenGenerator`
- New: Cross-encoder model (e.g., `BAAI/bge-reranker-base` or similar)
- Frontend: UI updates to display citations and formatted responses

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Increased latency from reranking | Medium | Use lightweight cross-encoder; parallel processing |
| Memory overhead from larger retrieval batch | Low | Apple Silicon has 48GB RAM; batch size tunable |
| Cross-encoder model size | Medium | Use quantized 4-bit models; lazy loading |
| Breaking changes to response format | Low | Backward compatible; gradual rollout |

## Success Metrics

- Retrieval relevance: Target >80% of queries retrieve at least 3 highly relevant docs
- Response quality: User feedback indicates improved accuracy and formatting
- Citation accuracy: >90% of citations map to actual retrieved sources
- Latency: End-to-end response time <3s for typical queries (p95)
- Memory usage: Stay within 32GB active memory during inference

## Alternatives Considered

1. **LLM-based Reranking**: Using the main LLM to score relevance
   - Rejected: Too slow and expensive; cross-encoders are specialized for this task

2. **Query Decomposition First**: Break down queries before retrieval
   - Deferred: Adds complexity; better as follow-up enhancement

3. **RAG Fusion**: Multiple query variations with reciprocal rank fusion
   - Deferred: Requires more research on query generation quality

## References

- [Retrieval-Augmented Generation: 2025 Definitive Guide](https://www.chitika.com/retrieval-augmented-generation-rag-the-definitive-guide-2025/)
- [Enhancing RAG: A Study of Best Practices (arXiv 2501.07391)](https://arxiv.org/abs/2501.07391)
- [Common RAG Techniques - Microsoft Cloud Blog](https://www.microsoft.com/en-us/microsoft-cloud/blog/2025/02/04/common-retrieval-augmented-generation-rag-techniques-explained/)
- [LangChain RAG Best Practices](https://python.langchain.com/docs/how_to/qa_citations)
- [Reranking in RAG with Cross-Encoders](https://eyka.com/blog/reranking-in-rag-enhancing-accuracy-with-cross-encoders/)
