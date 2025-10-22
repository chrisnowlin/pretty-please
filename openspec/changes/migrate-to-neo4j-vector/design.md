# Design: Neo4j Vector Storage Migration

## Architecture

### Component Structure

```
src/jina_rag_pipeline/storage/
├── base.py                 # VectorStore ABC (unchanged)
├── chroma_store.py         # Existing ChromaDB implementation (deprecated)
├── neo4j_store.py          # NEW: Neo4j implementation
└── factory.py              # NEW: Factory pattern for store selection
```

### Neo4j Schema Design

**Node Labels:**
- `VectorCollection`: Represents a collection (equivalent to ChromaDB collection)
- `Embedding`: Individual vector embeddings with metadata

**Properties:**
- `VectorCollection`:
  - `name: String` (indexed, unique)
  - `embedding_dimension: Integer`
  - `distance_metric: String` (cosine, l2, ip)
  - `created_at: DateTime`
  - `metadata: Map`

- `Embedding`:
  - `id: String` (indexed, unique)
  - `vector: List<Float>` (vector index)
  - `document: String`
  - `metadata: Map`
  - `created_at: DateTime`

**Relationships:**
- `(Embedding)-[:BELONGS_TO]->(VectorCollection)`

**Indexes:**
```cypher
// Unique constraint on collection name
CREATE CONSTRAINT collection_name_unique IF NOT EXISTS
FOR (c:VectorCollection) REQUIRE c.name IS UNIQUE;

// Unique constraint on embedding ID
CREATE CONSTRAINT embedding_id_unique IF NOT EXISTS
FOR (e:Embedding) REQUIRE e.id IS UNIQUE;

// Vector index for similarity search
CREATE VECTOR INDEX embedding_vector IF NOT EXISTS
FOR (e:Embedding) ON (e.vector)
OPTIONS {indexConfig: {
  `vector.dimensions`: 2048,
  `vector.similarity_function`: 'cosine'
}};
```

## Implementation Details

### Neo4j Vector Search

Neo4j 5.11+ provides native vector search via Cypher:

```cypher
// Similarity search query
MATCH (c:VectorCollection {name: $collection_name})<-[:BELONGS_TO]-(e:Embedding)
WHERE e.metadata.key = $filter_value  // Optional metadata filter
CALL db.index.vector.queryNodes('embedding_vector', $top_k, $query_vector)
YIELD node, score
WHERE node = e
RETURN e.id, e.document, e.metadata, score
ORDER BY score DESC
LIMIT $top_k
```

### Distance Metric Mapping

| VectorStore | Neo4j Similarity Function |
|-------------|---------------------------|
| cosine      | cosine                    |
| l2          | euclidean                 |
| ip          | Not natively supported, compute via cosine |

**Note**: Inner product (ip) requires custom implementation as 1 - cosine similarity approximation.

### Connection Management

- Use connection pooling via `neo4j.GraphDatabase.driver()`
- Default pool size: 50 connections
- Timeout: 30 seconds
- Retry logic for transient failures

### Transaction Strategy

- **Reads**: Use auto-commit transactions for performance
- **Writes**: Use explicit transactions for batch operations
- **Migration**: Large batches (1000 embeddings) with progress tracking

## Data Migration

### Migration Process

1. **Export from ChromaDB**: Read all collections and embeddings
2. **Transform**: Convert to Neo4j node/relationship format
3. **Batch Insert**: Insert in batches of 1000 for efficiency
4. **Validate**: Verify count and sample similarity searches
5. **Cleanup**: Optional ChromaDB data deletion

### Migration Script Flow

```python
def migrate_collection(chroma_store, neo4j_store, collection_name):
    # 1. Create collection in Neo4j
    chroma_info = chroma_store.get_collection_stats(collection_name)
    neo4j_store.create_collection(
        name=collection_name,
        embedding_dimension=chroma_info.metadata['embedding_dimension'],
        distance_metric=chroma_info.metadata['distance_metric']
    )
    
    # 2. Batch export and import embeddings
    batch_size = 1000
    offset = 0
    while True:
        batch = get_chroma_batch(collection_name, offset, batch_size)
        if not batch:
            break
        
        neo4j_store.add_embeddings(
            collection_name=collection_name,
            embeddings=batch.embeddings,
            ids=batch.ids,
            metadatas=batch.metadatas,
            documents=batch.documents
        )
        
        offset += batch_size
        print(f"Migrated {offset} embeddings...")
    
    # 3. Validate counts match
    assert chroma_info.count == neo4j_store.get_collection_stats(collection_name).count
```

## Configuration

### Environment Variables

```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j  # Default database

# Vector Store Selection
VECTOR_STORE_BACKEND=neo4j  # Options: chromadb, neo4j

# Connection Pooling
NEO4J_MAX_CONNECTION_POOL_SIZE=50
NEO4J_CONNECTION_TIMEOUT=30
```

### Docker Compose Service

```yaml
services:
  neo4j:
    image: neo4j:5.15-community
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_dbms_memory_heap_max__size=2G
      - NEO4J_dbms_memory_pagecache_size=1G
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "password", "RETURN 1"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  neo4j_data:
  neo4j_logs:
```

## Performance Considerations

### Optimization Strategies

1. **Batch Operations**: Use `UNWIND` for bulk inserts
2. **Index Warming**: Pre-load vector index into memory on startup
3. **Query Optimization**: Use query parameters to enable query plan caching
4. **Memory Tuning**: Configure heap and page cache based on dataset size

### Expected Performance

- **Latency**: <50ms for top-10 similarity search (2048-dim vectors, <1M embeddings)
- **Throughput**: 1000+ queries/second with proper indexing
- **Insert Rate**: 5000+ embeddings/second in batch mode

## Rollback Strategy

1. Keep ChromaDB backend code intact but deprecated
2. Configuration flag allows switching back: `VECTOR_STORE_BACKEND=chromadb`
3. Data remains in both systems during transition period
4. Full rollback possible by reverting config and restarting services

## Testing Strategy

1. **Unit Tests**: Mock Neo4j driver, test individual operations
2. **Integration Tests**: Real Neo4j instance (via Testcontainers)
3. **Performance Tests**: Benchmark against ChromaDB baseline
4. **Migration Tests**: Validate data integrity after migration
5. **Compatibility Tests**: Ensure existing API clients work unchanged
