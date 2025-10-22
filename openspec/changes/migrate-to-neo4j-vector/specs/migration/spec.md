# Spec: ChromaDB to Neo4j Migration

## ADDED Requirements

### Requirement: Migration Script

The system SHALL provide a migration script to transfer data from ChromaDB to Neo4j.

#### Scenario: Migrate a single collection

**Given** a ChromaDB collection "documents" contains 1000 embeddings  
**And** Neo4j is running and accessible  
**When** the user runs `python scripts/migrate_to_neo4j.py --collection documents`  
**Then** a new collection "documents" is created in Neo4j with matching configuration  
**And** all 1000 embeddings are transferred with their metadata and documents  
**And** the migration completes in under 60 seconds  
**And** the script outputs progress every 100 embeddings

#### Scenario: Migrate all collections

**Given** ChromaDB contains collections ["documents", "images", "lessons"]  
**When** the user runs `python scripts/migrate_to_neo4j.py --all`  
**Then** all three collections are migrated to Neo4j  
**And** the script reports total embeddings migrated for each collection  
**And** any errors are logged but do not stop the migration of other collections

#### Scenario: Dry-run migration

**Given** ChromaDB contains data  
**When** the user runs `python scripts/migrate_to_neo4j.py --all --dry-run`  
**Then** the script analyzes and reports what would be migrated  
**And** no data is written to Neo4j  
**And** the output shows collection names, embedding counts, and estimated time

#### Scenario: Resume interrupted migration

**Given** a migration was interrupted at embedding 500 of 1000  
**When** the user runs `python scripts/migrate_to_neo4j.py --collection documents --resume`  
**Then** the migration continues from embedding 501  
**And** previously migrated embeddings are not duplicated  
**And** the final count matches the source collection

### Requirement: Data Validation

The system SHALL validate data integrity after migration.

#### Scenario: Validate embedding counts

**Given** migration has completed for collection "documents"  
**When** the validation runs  
**Then** the count of embeddings in ChromaDB equals the count in Neo4j  
**And** the validation result is logged

#### Scenario: Validate sample similarity searches

**Given** migration has completed  
**When** the validation performs 10 random similarity searches  
**Then** the top-5 results from ChromaDB and Neo4j are compared  
**And** at least 80% of results match (same IDs in top-5)  
**And** score differences are within 1% tolerance  
**And** discrepancies are logged for review

#### Scenario: Validate metadata integrity

**Given** migration has completed  
**When** the validation samples 100 random embeddings  
**Then** the metadata from ChromaDB matches metadata in Neo4j  
**And** the document text matches  
**And** any mismatches are reported with embedding IDs

### Requirement: Rollback Support

The system SHALL support rollback if migration issues occur.

#### Scenario: Rollback a collection

**Given** collection "documents" was migrated to Neo4j  
**And** issues were discovered post-migration  
**When** the user runs `python scripts/migrate_to_neo4j.py --rollback documents`  
**Then** the "documents" collection is deleted from Neo4j  
**And** the ChromaDB data remains intact  
**And** the application can continue using ChromaDB backend

#### Scenario: Preserve ChromaDB during migration

**Given** migration is in progress  
**When** data is copied to Neo4j  
**Then** the original ChromaDB files are not modified or deleted  
**And** ChromaDB remains available as a fallback  
**And** the user can configure `VECTOR_STORE_BACKEND=chromadb` to revert

## MODIFIED Requirements

None - this is a new capability.
