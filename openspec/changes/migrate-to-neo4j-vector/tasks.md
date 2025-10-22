# Tasks: Migrate to Neo4j Community Edition

## Implementation Tasks

### Phase 1: Neo4j Vector Store Implementation

- [ ] **Task 1.1**: Install Neo4j Python driver dependency
  - Add `neo4j>=5.14.0` to `pyproject.toml`
  - Update lockfile
  - Verify: `pip list | grep neo4j` shows correct version

- [ ] **Task 1.2**: Implement `Neo4jVectorStore` class
  - Create `src/jina_rag_pipeline/storage/neo4j_store.py`
  - Implement all abstract methods from `VectorStore` base class
  - Add connection pooling with configurable pool size
  - Implement retry logic with exponential backoff
  - Verify: Unit tests for each method pass

- [ ] **Task 1.3**: Implement vector index management
  - Create vector indexes on collection creation
  - Support dynamic index creation for different embedding dimensions
  - Map distance metrics (cosine, l2, ip) to Neo4j similarity functions
  - Verify: Indexes are created correctly via Cypher queries

- [ ] **Task 1.4**: Implement similarity search with Cypher
  - Write optimized Cypher query for vector similarity search
  - Support metadata filtering in WHERE clauses
  - Handle score normalization (distance → similarity)
  - Add query result caching where appropriate
  - Verify: Search returns correct results compared to ChromaDB baseline

- [ ] **Task 1.5**: Add error handling and validation
  - Handle connection failures gracefully
  - Validate embedding dimensions match collection
  - Provide clear error messages for common issues
  - Add logging for debugging
  - Verify: Error cases raise appropriate exceptions with helpful messages

### Phase 2: Configuration and Factory Pattern

- [ ] **Task 2.1**: Create vector store factory
  - Create `src/jina_rag_pipeline/storage/factory.py`
  - Implement `get_vector_store()` factory function
  - Support `VECTOR_STORE_BACKEND` environment variable
  - Default to Neo4j if not specified
  - Verify: Factory returns correct store type based on configuration

- [ ] **Task 2.2**: Add configuration management
  - Add Neo4j connection parameters to environment variables
  - Support URI, username, password, database name
  - Add connection pool size and timeout configuration
  - Document all configuration options in README
  - Verify: Configuration is loaded correctly from `.env` file

- [ ] **Task 2.3**: Update application initialization
  - Modify startup code to use vector store factory
  - Add Neo4j health check on startup
  - Create indexes if they don't exist
  - Log which backend is being used
  - Verify: Application starts successfully with Neo4j backend

### Phase 3: Docker Compose Integration

- [ ] **Task 3.1**: Add Neo4j service to docker-compose.yml
  - Add Neo4j Community Edition 5.15 service
  - Configure ports (7474, 7687)
  - Set up persistent volumes for data and logs
  - Add health check configuration
  - Verify: `docker-compose up neo4j` starts successfully

- [ ] **Task 3.2**: Configure service dependencies
  - Make backend service depend on Neo4j health check
  - Add startup wait logic if needed
  - Configure restart policies
  - Verify: Services start in correct order with `docker-compose up`

- [ ] **Task 3.3**: Add memory tuning profiles
  - Create environment file templates for small/medium/large datasets
  - Document recommended settings for each profile
  - Add `.env.example` with Neo4j configuration
  - Verify: Memory settings work as expected under load

### Phase 4: Data Migration

- [ ] **Task 4.1**: Create migration script
  - Create `scripts/migrate_to_neo4j.py`
  - Implement batch export from ChromaDB
  - Implement batch import to Neo4j (1000 embeddings per batch)
  - Add progress reporting (every 100 embeddings)
  - Add `--collection`, `--all`, `--dry-run` flags
  - Verify: Migration script successfully transfers test collection

- [ ] **Task 4.2**: Add migration validation
  - Implement count validation (ChromaDB vs Neo4j)
  - Add sample similarity search comparison
  - Check metadata and document integrity for sample embeddings
  - Generate validation report
  - Verify: Validation detects discrepancies in test scenarios

- [ ] **Task 4.3**: Implement resume functionality
  - Track migration progress in temporary file
  - Skip already-migrated embeddings on resume
  - Clean up progress file on successful completion
  - Verify: Interrupted migration resumes correctly

- [ ] **Task 4.4**: Add rollback capability
  - Implement `--rollback` flag to delete Neo4j collections
  - Preserve ChromaDB data during migration
  - Document rollback procedure
  - Verify: Rollback successfully removes migrated data

### Phase 5: Testing

- [ ] **Task 5.1**: Write unit tests for Neo4jVectorStore
  - Test each method independently with mocked Neo4j driver
  - Test error handling and edge cases
  - Achieve >90% code coverage
  - Verify: `pytest tests/unit/test_neo4j_store.py` passes

- [ ] **Task 5.2**: Write integration tests
  - Use Testcontainers for real Neo4j instance
  - Test full CRUD operations on collections and embeddings
  - Test similarity search with various filters
  - Test concurrent access scenarios
  - Verify: All integration tests pass

- [ ] **Task 5.3**: Add performance benchmarks
  - Benchmark similarity search latency (top-10, top-100)
  - Benchmark batch insert throughput
  - Compare against ChromaDB baseline
  - Document results in performance report
  - Verify: Neo4j meets or exceeds ChromaDB performance

- [ ] **Task 5.4**: Test migration script
  - Create test ChromaDB with known data
  - Run migration and validate results
  - Test dry-run, resume, and rollback scenarios
  - Verify: Migration completes successfully with data integrity

- [ ] **Task 5.5**: End-to-end testing
  - Test full application flow with Neo4j backend
  - Upload documents, generate embeddings, perform searches
  - Verify chat interface works correctly
  - Test lesson plan generation with Neo4j-backed RAG
  - Verify: All existing functionality works with Neo4j

### Phase 6: Documentation

- [ ] **Task 6.1**: Update installation documentation
  - Add Neo4j installation instructions
  - Document Docker Compose setup
  - Add troubleshooting section
  - Verify: New users can set up Neo4j following documentation

- [ ] **Task 6.2**: Create migration guide
  - Document step-by-step migration process
  - Include pre-migration checklist
  - Add validation and rollback procedures
  - Provide example commands
  - Verify: Guide is complete and easy to follow

- [ ] **Task 6.3**: Document configuration options
  - List all Neo4j environment variables
  - Explain connection pooling settings
  - Document memory tuning recommendations
  - Add configuration examples
  - Verify: All options are documented with examples

- [ ] **Task 6.4**: Update architecture documentation
  - Update system diagrams to show Neo4j
  - Document vector store abstraction layer
  - Explain backend selection mechanism
  - Add performance characteristics
  - Verify: Architecture docs accurately reflect new implementation

### Phase 7: Deployment and Validation

- [ ] **Task 7.1**: Deploy to staging environment
  - Set up Neo4j instance
  - Deploy application with Neo4j backend
  - Run smoke tests
  - Verify: Application runs successfully in staging

- [ ] **Task 7.2**: Perform production migration (if applicable)
  - Schedule maintenance window
  - Run migration script on production data
  - Validate data integrity
  - Monitor performance
  - Verify: Production migration successful with no data loss

- [ ] **Task 7.3**: Monitor and optimize
  - Monitor query performance
  - Tune memory settings if needed
  - Optimize slow queries
  - Document any issues and resolutions
  - Verify: System meets performance SLAs

## Acceptance Criteria

- All unit and integration tests pass
- Migration script successfully transfers all test datasets
- Performance meets or exceeds ChromaDB baseline (<100ms p95 latency)
- Docker Compose setup works out of the box
- Documentation is complete and accurate
- Rollback procedure works correctly
- Zero downtime migration path is available (optional)

## Dependencies

- Neo4j Community Edition 5.11+ installed or available via Docker
- Python `neo4j` driver
- Existing vector store abstraction layer (no breaking changes)

## Estimated Effort

- Phase 1: 16 hours (2 days)
- Phase 2: 8 hours (1 day)
- Phase 3: 8 hours (1 day)
- Phase 4: 16 hours (2 days)
- Phase 5: 24 hours (3 days)
- Phase 6: 8 hours (1 day)
- Phase 7: 8 hours (1 day)

**Total: 88 hours (~11 working days)**

## Parallelization Opportunities

- Phases 1 and 3 can be done in parallel (implementation + Docker setup)
- Phase 4 (migration) can start once Phase 1 is complete
- Phase 6 (documentation) can be written in parallel with implementation
