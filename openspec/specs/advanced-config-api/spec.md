# advanced-config-api Specification

## Purpose
TBD - created by archiving change expose-advanced-config-ui. Update Purpose after archive.
## Requirements
### Requirement: Embedding Configuration Endpoints

The API MUST provide endpoints to retrieve, update, and enumerate embedding presets.

####  Scenario: Retrieve current embedding configuration
- **Given** a running API server
- **When** GET `/api/config/embeddings` is called
- **Then** returns `200 OK` with `EmbeddingConfigModel` JSON
- **And** includes all embedding parameters (task, dimensions, late_chunking, etc.)
- **And** responds in <100ms

#### Scenario: Update embedding configuration
- **Given** a valid `EmbeddingConfigModel` payload
- **When** POST `/api/config/embeddings` is called with the payload
- **Then** validates the configuration
- **And** persists to `data/config.json`
- **And** updates global configuration state
- **And** returns `200 OK` with updated configuration
- **And** responds in <200ms

#### Scenario: Reject invalid embedding configuration
- **Given** an invalid `EmbeddingConfigModel` payload (e.g., dimensions=3000)
- **When** POST `/api/config/embeddings` is called
- **Then** returns `422 Unprocessable Entity`
- **And** includes descriptive validation errors

#### Scenario: List embedding presets
- **Given** a running API server
- **When** GET `/api/config/embeddings/presets` is called
- **Then** returns `200 OK` with array of `PresetInfo`
- **And** includes presets: `for_query`, `for_documents`, `fast`, `storage_optimized`, `memory_constrained`
- **And** each preset includes name, display_name, description, and performance_characteristics

### Requirement: OCR Configuration Endpoints

The API MUST provide endpoints to retrieve, update, and enumerate OCR presets.

#### Scenario: Retrieve current OCR configuration
- **Given** a running API server
- **When** GET `/api/config/ocr` is called
- **Then** returns `200 OK` with `OCRConfigModel` JSON
- **And** includes all OCR parameters (batch_size, workers, two_tier settings, etc.)
- **And** responds in <100ms

#### Scenario: Update OCR configuration
- **Given** a valid `OCRConfigModel` payload
- **When** POST `/api/config/ocr` is called with the payload
- **Then** validates the configuration
- **And** persists to `data/config.json`
- **And** updates global configuration state
- **And** returns `200 OK` with updated configuration
- **And** responds in <200ms

#### Scenario: Reject invalid OCR configuration
- **Given** an invalid `OCRConfigModel` payload (e.g., batch_size=1000)
- **When** POST `/api/config/ocr` is called
- **Then** returns `422 Unprocessable Entity`
- **And** includes descriptive validation errors

#### Scenario: List OCR presets
- **Given** a running API server
- **When** GET `/api/config/ocr/presets` is called
- **Then** returns `200 OK` with array of `PresetInfo`
- **And** includes presets: `mlx_optimized`, `balanced`, `two_tier`, `memory_constrained`
- **And** each preset includes name, display_name, description, and performance_characteristics

### Requirement: Configuration Persistence

The system MUST persist configuration changes across server restarts.

#### Scenario: Configuration survives restart
- **Given** an embedding configuration has been updated
- **When** the server restarts
- **Then** GET `/api/config/embeddings` returns the saved configuration
- **And** NOT the default configuration

#### Scenario: Configuration file is human-readable
- **Given** a configuration has been saved
- **When** `data/config.json` is inspected
- **Then** it contains valid, formatted JSON
- **And** includes both `embeddings` and `ocr` sections

### Requirement: Backward Compatibility

The API MUST maintain backward compatibility when no explicit configuration is provided.

#### Scenario: Default behavior unchanged
- **Given** no configuration has been explicitly set
- **When** documents are processed or queries are made
- **Then** system uses sensible defaults matching current hard-coded behavior
- **And** existing API endpoints function identically

