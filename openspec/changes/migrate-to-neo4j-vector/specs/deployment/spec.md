# Spec: Neo4j Deployment Configuration

## ADDED Requirements

### Requirement: Docker Compose Integration

The system SHALL provide Docker Compose configuration for Neo4j Community Edition.

#### Scenario: Start Neo4j service

**Given** the user has Docker installed  
**When** the user runs `docker-compose up neo4j`  
**Then** Neo4j Community Edition 5.15 starts on port 7687 (Bolt) and 7474 (HTTP)  
**And** the database is accessible with default credentials (neo4j/password)  
**And** health checks confirm the service is ready within 30 seconds  
**And** data persists in a Docker volume

#### Scenario: Start full application stack

**Given** Docker Compose is configured  
**When** the user runs `docker-compose up`  
**Then** Neo4j starts first (dependency order)  
**And** the backend application waits for Neo4j health check before starting  
**And** the application successfully connects to Neo4j  
**And** the frontend can access the backend API

#### Scenario: Neo4j data persistence

**Given** Neo4j is running with data  
**When** the user runs `docker-compose down` then `docker-compose up neo4j`  
**Then** existing collections and embeddings are preserved  
**And** no data loss occurs  
**And** the application can query previously stored embeddings

### Requirement: Environment Configuration

The system SHALL support configuration via environment variables.

#### Scenario: Configure Neo4j connection

**Given** a `.env` file contains Neo4j connection parameters  
**When** the application starts  
**Then** it connects to Neo4j using the configured URI, username, and password  
**And** connection errors provide clear messages if configuration is invalid

#### Scenario: Select vector store backend

**Given** `VECTOR_STORE_BACKEND=neo4j` is set in environment  
**When** the application initializes  
**Then** Neo4j is used as the vector store backend  
**And** ChromaDB is not initialized

**Given** `VECTOR_STORE_BACKEND=chromadb` is set  
**When** the application initializes  
**Then** ChromaDB is used (legacy mode)  
**And** Neo4j is not initialized

#### Scenario: Default configuration

**Given** no vector store backend is specified in environment  
**When** the application starts  
**Then** Neo4j is used as the default backend  
**And** a warning is logged recommending explicit configuration

### Requirement: Memory and Performance Tuning

The system SHALL provide recommended Neo4j memory settings for different dataset sizes.

#### Scenario: Small dataset configuration (< 100K embeddings)

**Given** the deployment is for small datasets  
**When** Neo4j is configured with `NEO4J_dbms_memory_heap_max_size=2G` and `NEO4J_dbms_memory_pagecache_size=1G`  
**Then** Neo4j operates efficiently for vector search operations  
**And** memory usage remains under 4GB total

#### Scenario: Medium dataset configuration (100K - 1M embeddings)

**Given** the deployment is for medium datasets  
**When** Neo4j is configured with `NEO4J_dbms_memory_heap_max_size=4G` and `NEO4J_dbms_memory_pagecache_size=2G`  
**Then** query performance meets <100ms latency requirements  
**And** memory usage remains under 8GB total

#### Scenario: Large dataset configuration (> 1M embeddings)

**Given** the deployment is for large datasets  
**When** Neo4j is configured with `NEO4J_dbms_memory_heap_max_size=8G` and `NEO4J_dbms_memory_pagecache_size=4G`  
**Then** vector index fits in memory for optimal performance  
**And** the system can handle 1000+ queries/second

### Requirement: Health Checks and Monitoring

The system SHALL provide health check endpoints for Neo4j connectivity.

#### Scenario: Neo4j health check

**Given** the backend application is running  
**When** the health check endpoint `/health/neo4j` is queried  
**Then** the response indicates Neo4j connection status  
**And** includes version information and database name  
**And** returns 200 OK if connected, 503 Service Unavailable if not

#### Scenario: Startup dependency

**Given** Docker Compose is configured with service dependencies  
**When** services start  
**Then** the backend application waits for Neo4j health check to pass  
**And** does not start accepting requests until Neo4j is ready  
**And** logs indicate waiting for Neo4j if it's not immediately available

## MODIFIED Requirements

### Requirement: Application Startup

The existing application startup process SHALL be modified to support Neo4j initialization.

#### Scenario: Initialize vector store on startup

**Given** the application is configured to use Neo4j  
**When** the application starts  
**Then** it attempts to connect to Neo4j  
**And** creates necessary indexes if they don't exist  
**And** logs the vector store backend being used (neo4j or chromadb)  
**And** fails fast with a clear error if Neo4j is unreachable

## REMOVED Requirements

None - ChromaDB configuration remains for backward compatibility.
