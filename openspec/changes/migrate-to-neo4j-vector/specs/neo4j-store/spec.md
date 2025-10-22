# Spec: Neo4j Vector Store Implementation

## ADDED Requirements

### Requirement: Neo4j Vector Store Class

The system SHALL provide a `Neo4jVectorStore` class that implements the `VectorStore` abstract base class interface.

#### Scenario: Create a new vector collection

**Given** a Neo4j database connection is available  
**When** the user calls `create_collection(name="documents", embedding_dimension=2048, distance_metric="cosine")`  
**Then** a `VectorCollection` node is created in Neo4j with the specified properties  
**And** a vector index is created for embeddings in this collection  
**And** the collection appears in `list_collections()` results

#### Scenario: Add embeddings to a collection

**Given** a collection named "documents" exists  
**When** the user calls `add_embeddings(collection_name="documents", embeddings=[[0.1, 0.2, ...]], documents=["text"], metadatas=[{"key": "value"}])`  
**Then** `Embedding` nodes are created with the provided vectors, documents, and metadata  
**And** relationships `[:BELONGS_TO]` are created linking embeddings to the collection  
**And** the embeddings are indexed for vector search  
**And** the method returns the list of generated IDs

#### Scenario: Perform similarity search

**Given** a collection "documents" contains 100 embeddings  
**When** the user calls `similarity_search(collection_name="documents", query_embedding=[0.5, 0.3, ...], top_k=10)`  
**Then** the system returns the 10 most similar embeddings based on cosine similarity  
**And** each result includes id, score, embedding, metadata, and document  
**And** results are ordered by score descending  
**And** the query completes in under 100ms

#### Scenario: Similarity search with metadata filtering

**Given** a collection "documents" contains embeddings with various metadata  
**When** the user calls `similarity_search(collection_name="documents", query_embedding=[...], top_k=10, metadata_filter={"type": "pdf"})`  
**Then** the system returns only embeddings where metadata.type equals "pdf"  
**And** results are still ordered by similarity score  
**And** the count does not exceed top_k

#### Scenario: Update an embedding's metadata

**Given** an embedding with id="123" exists in collection "documents"  
**When** the user calls `update_embedding(collection_name="documents", id="123", metadata={"updated": True})`  
**Then** the embedding's metadata is updated in Neo4j  
**And** the embedding vector remains unchanged  
**And** subsequent searches reflect the updated metadata

#### Scenario: Delete an embedding

**Given** an embedding with id="456" exists in collection "documents"  
**When** the user calls `delete_embedding(collection_name="documents", id="456")`  
**Then** the embedding node is deleted from Neo4j  
**And** the embedding no longer appears in search results  
**And** the collection count is decremented by 1

#### Scenario: Delete a collection

**Given** a collection "documents" exists with 50 embeddings  
**When** the user calls `delete_collection(name="documents")`  
**Then** the collection node is deleted  
**And** all associated embedding nodes are deleted  
**And** the collection no longer appears in `list_collections()`  
**And** the vector index is dropped

### Requirement: Connection Management

The system SHALL manage Neo4j database connections efficiently and reliably.

#### Scenario: Connection pooling

**Given** the application starts with default configuration  
**When** multiple concurrent requests access the Neo4j store  
**Then** connections are reused from a connection pool  
**And** the pool size does not exceed the configured maximum (default 50)  
**And** idle connections are automatically closed after timeout

#### Scenario: Connection failure retry

**Given** Neo4j is temporarily unavailable  
**When** the user performs a vector store operation  
**Then** the system retries the operation up to 3 times with exponential backoff  
**And** if all retries fail, a `ConnectionError` is raised with a descriptive message

#### Scenario: Graceful shutdown

**Given** the application is running with active Neo4j connections  
**When** the `close()` method is called  
**Then** all active connections are properly closed  
**And** the connection pool is cleaned up  
**And** no connection leaks occur

### Requirement: Vector Index Management

The system SHALL create and manage vector indexes for efficient similarity search.

#### Scenario: Dynamic vector index creation

**Given** a new collection is created with embedding_dimension=2048 and distance_metric="cosine"  
**When** the first embeddings are added to the collection  
**Then** a vector index is automatically created with the correct dimensions and similarity function  
**And** the index name follows the pattern `{collection_name}_vector_index`

#### Scenario: Support multiple distance metrics

**Given** collections with different distance metrics exist  
**When** similarity searches are performed  
**Then** "cosine" uses Neo4j's cosine similarity function  
**And** "l2" uses Neo4j's euclidean similarity function  
**And** "ip" is computed using cosine similarity approximation  
**And** results are consistent with the specified metric

### Requirement: Error Handling

The system SHALL provide clear error messages and handle failures gracefully.

#### Scenario: Collection already exists

**Given** a collection named "documents" already exists  
**When** the user calls `create_collection(name="documents", ...)`  
**Then** a `ValueError` is raised with message "Collection 'documents' already exists"

#### Scenario: Collection not found

**Given** no collection named "missing" exists  
**When** the user calls `add_embeddings(collection_name="missing", ...)`  
**Then** a `ValueError` is raised with message "Collection 'missing' not found"

#### Scenario: Embedding not found

**Given** an embedding with id="999" does not exist  
**When** the user calls `get_embedding(collection_name="documents", id="999")`  
**Then** the method returns `None` without raising an error

#### Scenario: Invalid embedding dimension

**Given** a collection "documents" with embedding_dimension=2048  
**When** the user tries to add embeddings with dimension 1024  
**Then** a `ValueError` is raised with message "Embedding dimension mismatch: expected 2048, got 1024"

## MODIFIED Requirements

### Requirement: VectorStore Factory Pattern

The system SHALL use a factory pattern to instantiate the appropriate vector store backend.

#### Scenario: Select backend via configuration

**Given** the environment variable `VECTOR_STORE_BACKEND=neo4j`  
**When** the application initializes the vector store  
**Then** a `Neo4jVectorStore` instance is created  
**And** the instance conforms to the `VectorStore` interface

**Given** the environment variable `VECTOR_STORE_BACKEND=chromadb`  
**When** the application initializes the vector store  
**Then** a `ChromaVectorStore` instance is created (legacy support)  
**And** the instance conforms to the `VectorStore` interface
