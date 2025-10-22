# Implementation Tasks: Enhance RAG Quality

## Phase 1: Core Retrieval Enhancements (Highest Impact) ✅ COMPLETED

### Task 1.1: Implement Cross-Encoder Reranking Module ✅
- [x] Create `src/jina_rag_pipeline/retrieval/reranker.py`
- [x] Implement `CrossEncoderReranker` class with lazy model loading
- [x] Support `BAAI/bge-reranker-base` model with 4-bit quantization
- [x] Add configuration for model name and top_n parameters
- [x] Implement async `rerank()` method with batch processing
- [x] Add error handling with fallback to original scores
- [ ] Write unit tests for reranking logic
- **Status**: Core implementation complete, tests pending

### Task 1.2: Add RAG Configuration Dataclass ✅
- [x] Extend `src/jina_rag_pipeline/generation/config.py`
- [x] Add `RAGConfig` dataclass with all retrieval parameters
- [x] Include flags: `enable_hybrid_search`, `enable_reranking`, `enable_compression`
- [x] Include parameters: `initial_retrieval_k`, `rerank_top_n`, `compression_chunk_size`
- [x] Add validation method for parameter ranges
- [ ] Write tests for config validation
- **Status**: Complete, tests pending

### Task 1.3: Integrate Reranking into Chat Retrieval ✅
- [x] Modify `src/jina_rag_pipeline/api/chat.py::retrieve_context()`
- [x] Increase initial retrieval batch size to 20 (configurable via RAGConfig)
- [x] Add reranker instantiation in `ChatState`
- [x] Apply reranking after vector search if enabled
- [x] Preserve both original and reranked scores in results
- [x] Update retrieval latency logging
- [ ] Write integration tests for reranked retrieval flow
- **Status**: Complete, integration tests pending

### Task 1.4: Add Retrieval Metrics Tracking ✅
- [x] Create `src/jina_rag_pipeline/retrieval/metrics.py`
- [x] Implement `RetrievalMetrics` dataclass for timing and counts
- [x] Track vector_search_time, reranking_time, total_time
- [x] Track documents_retrieved, documents_after_rerank
- [x] Integrate metrics into `retrieve_context()` function
- [x] Include metrics in WebSocket `ContextMessage`
- **Status**: Complete

## Phase 2: Context Formatting and Prompting ✅ COMPLETED

### Task 2.1: Implement Enhanced Context Formatter ✅
- [x] Modify `src/jina_rag_pipeline/generation/context_formatter.py`
- [x] Implement numbered citation format [1], [2] for text sources
- [x] Implement image citation format [IMG-1], [IMG-2]
- [x] Include relevance scores in formatted output
- [x] Include source metadata (filename, page, type)
- [x] Add method to track citation ID to source mapping
- [ ] Write tests for all formatting methods
- **Status**: Complete, tests pending

### Task 2.2: Create Enhanced System Prompts ✅
- [x] Modify `src/jina_rag_pipeline/generation/prompts.py`
- [x] Create enhanced system prompts with citation instructions
- [x] Add markdown formatting guidelines
- [x] Add confidence expression templates
- [x] Include concrete examples of good responses
- [x] Create separate multimodal enhanced prompt variant
- **Status**: Complete

### Task 2.3: Update Prompt Selection Logic ✅
- [x] `get_system_prompt()` function already supports enhanced prompts
- [x] Enhanced prompts selected by default
- [x] Custom instructions appending supported
- [x] Context injection with proper formatting working
- **Status**: Complete (no changes needed, already functional)

### Task 2.4: Integrate Enhanced Formatting into Chat Flow ✅
- [x] `websocket_chat()` already uses enhanced context formatter
- [x] Enhanced context formatter integrated for multimodal context
- [x] Citation tracking available via `get_citation_map()`
- [x] Context message includes citation IDs and retrieval metrics
- **Status**: Complete

## Phase 3: Real-World Testing and Prompt Refinement

### Task 3.1: Create Test Query Dataset
- Create `tests/fixtures/rag_test_queries.json`
- Compile 20-30 representative real-world queries
- Include diverse query types: factual, comparison, multi-hop, visual
- Include queries about existing documents in collection
- Categorize by difficulty: simple, medium, complex
- Document expected behavior/ideal answers for each
- **Validation**: Cover all major use cases

### Task 3.2: Set Up Interactive Testing Environment
- Create `scripts/test_rag_interactive.py`
- Load test documents into dedicated test collection
- Initialize RAG pipeline with enhanced components
- Provide interactive prompt for testing queries
- Display full retrieval pipeline output (sources, scores, citations)
- Display generated response with formatting preserved
- Allow saving good/bad examples for analysis
- **Validation**: Can easily test and iterate on queries

### Task 3.3: Test Baseline vs Enhanced Retrieval
- Run test queries through baseline (no reranking) pipeline
- Run same queries through enhanced (with reranking) pipeline
- Compare retrieved documents and relevance scores
- Document cases where reranking helps significantly
- Document cases where reranking hurts or has no effect
- Analyze failure modes and edge cases
- **Validation**: Quantify retrieval improvement percentage

### Task 3.4: Evaluate Citation Quality
- Test queries with enhanced context formatting
- Verify citations [1], [2] appear correctly in responses
- Check that citations map to actual retrieved sources
- Test citation hover/click behavior (if frontend ready)
- Identify cases where LLM fails to cite properly
- Document citation accuracy rate (target >90%)
- **Validation**: Citations are accurate and helpful

### Task 3.5: Iterate on System Prompts
- Test enhanced system prompt with sample queries
- Review generated responses for quality issues:
  - Missing citations where expected
  - Incorrect markdown formatting
  - Hallucinations or unsupported claims
  - Poor confidence communication
- Refine prompt instructions based on observed failures
- Test multiple prompt variations and compare outputs
- A/B test different prompt phrasings
- Document prompt version history and performance
- **Validation**: Response quality improves with each iteration

### Task 3.6: Tune Context Formatting
- Test different citation format styles:
  - [1], [2] vs (Source 1) vs footnote style
  - Relevance score display formats
  - Metadata inclusion/exclusion
- Evaluate context length vs quality trade-off
- Test with different numbers of retrieved documents (3, 5, 10)
- Identify optimal context structure for LLM comprehension
- Document formatting decisions and rationale
- **Validation**: Context is clear, parseable, and actionable

### Task 3.7: Test Multimodal Responses
- Test queries requiring both text and image context
- Verify image citations [IMG-1] work correctly
- Check that LLM references images appropriately
- Test cases with only images, only text, and mixed
- Refine multimodal system prompt based on outputs
- Document multimodal response quality
- **Validation**: Multimodal responses are coherent and cite images

### Task 3.8: Analyze Failure Cases
- Collect and categorize failed queries:
  - Poor retrieval (wrong documents)
  - Good retrieval but bad generation
  - Missing citations
  - Formatting issues
  - Hallucinations
- For each failure category, identify root cause
- Prioritize fixes based on frequency and severity
- Create regression test suite from failures
- **Validation**: Understand and document failure modes

### Task 3.9: Test Edge Cases
- Test with very short queries (1-2 words)
- Test with very long queries (multiple sentences)
- Test with queries in different languages (if multilingual)
- Test with ambiguous queries
- Test with queries outside document scope
- Test with follow-up conversational queries
- Document handling of edge cases
- **Validation**: Edge cases handled gracefully

### Task 3.10: Parameter Tuning
- Experiment with reranking top_n (3, 5, 7, 10)
- Experiment with initial retrieval batch size (15, 20, 25)
- Experiment with temperature settings
- Experiment with relevance score thresholds
- Test different cross-encoder models if needed
- Document optimal parameter settings
- Create configuration presets (fast, balanced, quality)
- **Validation**: Find optimal balance of quality and performance

### Task 3.11: Measure Response Quality Metrics
- Implement automated quality scoring (optional):
  - Citation presence rate
  - Markdown formatting compliance
  - Response length appropriateness
  - Factual consistency with sources
- Manually rate responses on quality scale (1-5)
- Compare baseline vs enhanced on quality metrics
- Document improvement percentages
- **Validation**: Quantifiable quality improvements

### Task 3.12: Create Prompt and Config Artifacts
- Save final optimized system prompts to `prompts.py`
- Save final RAG configuration to config file
- Document all tuning decisions in `design.md`
- Create before/after example outputs for documentation
- Archive all test results and analysis
- **Validation**: Reproducible optimal configuration

## Phase 4: Hybrid Search (Optional but Recommended)

### Task 4.1: Implement BM25 Keyword Scoring
- Create `src/jina_rag_pipeline/retrieval/keyword_search.py`
- Implement `BM25Scorer` class for in-memory keyword matching
- Tokenize and score retrieved documents against query
- Support configurable BM25 parameters (k1, b)
- Write unit tests for BM25 scoring
- **Validation**: Verify BM25 scores match expected values on test corpus

### Task 4.2: Implement Result Fusion
- Create `src/jina_rag_pipeline/retrieval/fusion.py`
- Implement Reciprocal Rank Fusion (RRF) algorithm
- Support weighted fusion with alpha parameter
- Deduplicate results from semantic and keyword search
- Write tests for fusion logic
- **Validation**: Verify fused rankings make sense for test queries

### Task 4.3: Create Hybrid Retriever
- Create `src/jina_rag_pipeline/retrieval/hybrid_retriever.py`
- Implement `HybridRetriever` class
- Combine vector search and BM25 scoring
- Apply fusion to produce final ranking
- Add configuration flag to enable/disable
- Write integration tests
- **Validation**: Compare hybrid vs semantic-only on benchmark queries

### Task 4.4: Integrate Hybrid Search into Chat
- Modify `retrieve_context()` to use `HybridRetriever` if enabled
- Pass RAG config to control hybrid search flag
- Update metrics to track hybrid search usage
- Test with various query types (keyword-heavy vs semantic)
- **Validation**: Verify hybrid search improves recall on keyword queries

### Task 4.5: Test Hybrid Search with Real Queries
- Re-run Phase 3 test queries with hybrid search enabled
- Compare hybrid vs semantic-only on test dataset
- Measure improvement in recall for keyword-heavy queries
- Document cases where hybrid search helps
- Tune alpha parameter for optimal semantic/keyword balance
- **Validation**: Hybrid search improves performance on keyword queries

## Phase 5: Contextual Compression (Future Enhancement)

### Task 5.1: Implement Document Splitter
- Create `src/jina_rag_pipeline/retrieval/compression.py`
- Implement `RecursiveCharacterTextSplitter` or use existing library
- Support configurable chunk_size and overlap
- Maintain source and position metadata for each chunk
- Write tests for chunking logic
- **Validation**: Verify chunks maintain semantic coherence

### Task 5.2: Implement Relevance Filtering
- Add `ContextualCompressor` class
- Compute query-chunk embedding similarities
- Filter chunks below threshold (default 0.7)
- Limit to max_chunks configuration
- Write tests for filtering
- **Validation**: Verify high-quality chunks are retained

### Task 5.3: Integrate Compression into Retrieval
- Add compression step after reranking if enabled
- Track chunk provenance (original doc + position)
- Update citation format to handle chunks
- Test compression on long documents
- **Validation**: Compare context quality with/without compression

### Task 5.4: Test Compression with Real Queries
- Test compression on queries with long documents
- Verify chunk quality and relevance
- Ensure citations still map correctly
- Measure impact on response quality
- **Validation**: Compression improves or maintains quality

## Phase 6: API and Configuration

### Task 6.1: Add RAG Config API Models
- Modify `src/jina_rag_pipeline/api/models.py`
- Add `RAGConfigModel` Pydantic model
- Add `rag_config` field to `CreateSessionRequest`
- Add `RetrievalMetadata` model for response metadata
- Update `ContextMessage` to include citation metadata
- Write tests for model validation
- **Validation**: Verify API contracts with OpenAPI schema

### Task 6.2: Implement RAG Config Endpoints
- Add GET `/api/config/rag` endpoint in `app.py`
- Add POST `/api/config/rag` endpoint for updates
- Add POST `/api/config/rag/reset` endpoint
- Implement validation and persistence
- Write API tests for config endpoints
- **Validation**: Test config CRUD operations via API

### Task 6.3: Add Retrieval Metadata to Responses
- Modify `websocket_chat()` to include retrieval metrics
- Add `citations` array to response metadata
- Map citation IDs to source details
- Include original and reranked scores if available
- Test metadata in WebSocket messages
- **Validation**: Verify all metadata fields are populated correctly

### Task 6.4: Add Debug Endpoints
- Create POST `/api/debug/retrieval` endpoint
- Create POST `/api/debug/reranker` endpoint
- Return full pipeline details for debugging
- Add authentication/authorization for debug endpoints
- Write tests for debug functionality
- **Validation**: Use debug endpoints to troubleshoot queries

## Phase 7: Frontend Integration

### Task 7.1: Create Citation Component
- Create `frontend/src/components/chat/Citation.tsx`
- Implement inline citation rendering with [N] format
- Add hover tooltip with source details
- Add click handler to navigate to source
- Style citations subtly but clearly
- Write component tests
- **Validation**: Verify citations render and interact correctly

### Task 7.2: Enhance Message Renderer for Markdown
- Update message rendering component
- Add markdown parsing library (e.g., `marked`, `react-markdown`)
- Support headers, lists, bold, italic, code blocks
- Support syntax highlighting for code
- Preserve citation markers during rendering
- Write rendering tests
- **Validation**: Test with various markdown formats

### Task 7.3: Create Source Attribution Panel
- Create `frontend/src/components/chat/SourcePanel.tsx`
- Display text sources with citation numbers
- Display image sources with thumbnails
- Show relevance scores
- Highlight cited vs uncited sources
- Add expand/collapse functionality
- **Validation**: Verify source panel displays all metadata

### Task 7.4: Add RAG Settings UI
- Create `frontend/src/components/chat/RAGSettings.tsx`
- Add toggles for hybrid_search, reranking, compression
- Add sliders for configurable parameters
- Connect to API config endpoints
- Apply settings to current session
- **Validation**: Verify settings changes affect retrieval

### Task 7.5: Add Retrieval Stats Display
- Add optional stats display in chat interface
- Show documents retrieved, reranking time, total time
- Make stats togglable in settings
- Display confidence indicators based on citations
- **Validation**: Verify stats match backend metrics

### Task 7.6: End-to-End Frontend Testing
- Test full user flow: query → retrieval → citations → sources
- Test citation interactions (hover, click)
- Test RAG settings changes and effects
- Test markdown rendering edge cases
- Test responsive design on different screen sizes
- **Validation**: Full UX works smoothly

## Phase 8: Comprehensive Testing and Validation

### Task 8.1: Create RAG Quality Test Suite
- Create `tests/test_rag_quality.py`
- Implement automated tests for test query dataset
- Measure retrieval relevance using established ground truth
- Compare baseline vs enhanced RAG performance
- Document quality improvements with metrics
- **Validation**: Target >30% improvement in relevance scores

### Task 8.2: Performance Benchmarking
- Create `tests/benchmarks/test_rag_performance.py`
- Measure end-to-end latency for 100 queries
- Measure memory usage during retrieval and reranking
- Profile each pipeline component separately
- Verify p95 latency <3s
- Verify memory stays within limits
- **Validation**: Meet all performance targets

### Task 8.3: Integration Testing
- Write end-to-end tests for full RAG pipeline
- Test all configuration combinations (2^3 = 8 configs)
- Test error handling and fallback mechanisms
- Test with various document types and query patterns
- Test concurrent session handling
- **Validation**: 100% test pass rate

### Task 8.4: Regression Testing
- Create regression test suite from Phase 3 failure cases
- Ensure previously failing queries now work
- Verify fixes don't break other functionality
- Add new regression tests for any bugs found
- **Validation**: All regressions resolved

### Task 8.5: User Acceptance Testing
- Recruit 3-5 beta testers
- Create test plan with sample conversation scenarios
- Gather feedback on citation accuracy and usefulness
- Gather feedback on response quality vs baseline
- Gather feedback on UI enhancements
- Document issues and prioritize fixes
- **Validation**: Positive user feedback (4+/5 average rating)

## Phase 9: Documentation and Deployment

### Task 9.1: Update API Documentation
- Update OpenAPI/Swagger docs with new endpoints
- Document RAG config parameters and defaults
- Document response metadata fields
- Add request/response examples for all endpoints
- Include curl examples for API testing
- **Validation**: Documentation is complete and accurate

### Task 9.2: Write User Guide
- Document RAG quality features for end users
- Explain hybrid search, reranking, compression in simple terms
- Provide configuration recommendations for different use cases
- Show before/after examples from Phase 3 testing
- Add FAQ section
- Add troubleshooting section
- **Validation**: Guide is clear and helpful to non-technical users

### Task 9.3: Create Developer Guide
- Document architecture and component interactions
- Explain how to extend/customize RAG pipeline
- Provide examples of adding new reranker models
- Document configuration options and tuning guidance
- Include performance optimization tips
- **Validation**: Developers can extend the system

### Task 9.4: Create Migration Guide
- Document changes from baseline to enhanced RAG
- Provide backward compatibility notes
- Explain default configurations and behavior changes
- Guide for existing deployments and data
- Include rollback procedures
- **Validation**: Smooth migration path exists

### Task 9.5: Document Learnings from Testing
- Summarize insights from Phase 3 prompt refinement
- Document optimal parameter settings discovered
- Share examples of good vs bad responses
- Explain common failure modes and mitigations
- Create runbook for common issues
- **Validation**: Knowledge captured for team and future work

### Task 9.6: Deploy to Staging
- Deploy enhanced RAG to staging environment
- Run full automated test suite in staging
- Conduct manual smoke tests
- Monitor performance and quality metrics
- Test with production-like data volume
- **Validation**: Staging deployment successful

### Task 9.7: Production Rollout
- Create deployment checklist and runbook
- Deploy to production with feature flag (off by default)
- Gradually enable for 10% of users
- Monitor error rates, latency, memory usage
- Compare quality metrics vs baseline
- Expand to 50%, then 100% if metrics good
- **Validation**: Successful production rollout

### Task 9.8: Set Up Monitoring and Alerts
- Create dashboards for RAG quality metrics
- Add alerts for retrieval latency > 2s
- Add alerts for reranker errors
- Add alerts for memory usage > 80%
- Track citation accuracy over time
- Monitor user feedback and satisfaction
- **Validation**: Comprehensive monitoring in place

## Dependencies and Parallelization

**Can be done in parallel:**
- Phase 1 (Reranking) + Phase 2 (Formatting) - independent modules
- Phase 6 (API) + Phase 7 (Frontend) - can overlap once models defined
- Phase 8 (Testing) can start in parallel with late Phase 7 tasks

**Must be sequential:**
- Phase 1 + Phase 2 → Phase 3 (need working components to test outputs)
- Phase 3 → Phase 4 (prompt refinement informs hybrid search)
- Phase 4 + Phase 5 → Phase 6 (API needs retrieval components)
- Phase 6 → Phase 7 (Frontend needs API endpoints)
- Phases 1-7 → Phase 8 (Comprehensive testing needs all features)
- Phase 8 → Phase 9 (Deploy after validation)

**Critical Path:**
Phase 1 → Phase 2 → Phase 3 (prompt refinement) → Phase 6 → Phase 7 → Phase 8 → Phase 9

## Estimated Timeline

- **Phase 1**: 3-4 days (reranking implementation)
- **Phase 2**: 2-3 days (formatting and prompts, parallel with Phase 1)
- **Phase 3**: 4-5 days (CRITICAL - iterative testing and refinement)
- **Phase 4**: 2-3 days (hybrid search, after Phase 3 insights)
- **Phase 5**: 2-3 days (contextual compression - optional/future)
- **Phase 6**: 2-3 days (API enhancements)
- **Phase 7**: 3-4 days (frontend integration)
- **Phase 8**: 2-3 days (comprehensive testing)
- **Phase 9**: 2-3 days (documentation and deployment)

**Total: ~22-28 days for Phases 1-4, 6-9 (excluding optional Phase 5)**

**Note**: Phase 3 is the most important for quality outcomes. Don't rush it - the iterative refinement of prompts and parameters based on real model outputs is crucial for achieving the 30-50% quality improvement targets.
