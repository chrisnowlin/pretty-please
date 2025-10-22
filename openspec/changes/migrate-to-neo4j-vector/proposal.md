# Proposal: Migrate to Neo4j Community Edition for Vector Storage

## Overview

Replace ChromaDB with Neo4j Community Edition as the vector storage backend for the RAG pipeline. This migration will leverage Neo4j's native vector search capabilities (available in Neo4j 5.11+) while maintaining the existing `VectorStore` abstraction interface.

## Motivation

1. **Graph-Native Knowledge Representation**: Neo4j enables rich relationship modeling between documents, chunks, and educational concepts, which aligns better with lesson planning use cases where curricula, standards, and resources have complex interconnections.

2. **Enhanced Querying**: Combine vector similarity search with graph traversal for hybrid retrieval (e.g., "find similar content that's also aligned to specific standards").

3. **Production Maturity**: Neo4j Community Edition offers robust production features including ACID transactions, backup/restore, and monitoring without requiring enterprise licensing.

4. **Unified Data Store**: Consolidate vector embeddings and metadata/relationships in a single database, eliminating the need for separate metadata stores.

5. **Scalability**: Better horizontal scaling options and proven performance at scale compared to ChromaDB.

## Scope

### In Scope
- Implement `Neo4jVectorStore` class conforming to existing `VectorStore` interface
- Migration script to transfer existing ChromaDB collections to Neo4j
- Configuration updates for Neo4j connection parameters
- Docker Compose updates for Neo4j Community Edition service
- Documentation for setup and migration
- Performance benchmarking comparison with ChromaDB

### Out of Scope
- Graph-specific features (will be added in future proposals)
- Neo4j Enterprise features (AuraDB, clustering, etc.)
- Frontend UI changes (API remains compatible)
- Changes to embedding generation logic

## Implementation Strategy

1. **Preserve Interface Compatibility**: Implement Neo4j backend as drop-in replacement using existing `VectorStore` abstract base class
2. **Parallel Operation**: Support both backends during transition with configuration flag
3. **Data Migration**: Provide tooling to migrate existing ChromaDB data to Neo4j
4. **Testing**: Comprehensive integration tests ensuring feature parity

## Success Criteria

- [ ] All existing vector store operations work identically with Neo4j backend
- [ ] Migration completes successfully for test datasets
- [ ] Performance benchmarks show comparable or better latency/throughput
- [ ] All existing tests pass with Neo4j backend
- [ ] Documentation covers installation, configuration, and migration

## Dependencies

- Neo4j Community Edition 5.11+ (vector search support)
- Python `neo4j` driver
- Existing `VectorStore` abstraction (no changes needed)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance regression | High | Benchmark early; implement caching if needed |
| Breaking changes | High | Maintain interface compatibility; provide migration path |
| Deployment complexity | Medium | Docker Compose integration; clear documentation |
| Learning curve | Low | Neo4j has excellent documentation; team familiarity |
