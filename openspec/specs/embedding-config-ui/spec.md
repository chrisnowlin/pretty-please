# embedding-config-ui Specification

## Purpose
TBD - created by archiving change expose-advanced-config-ui. Update Purpose after archive.
## Requirements
### Requirement: Embedding Configuration Panel Component

The frontend MUST provide a React component for configuring embedding generation parameters.

#### Scenario: Display preset dropdown with performance hints
- **Given** the Embedding Config Panel is rendered
- **When** user views the preset dropdown
- **Then** shows all available presets (for_query, for_documents, fast, storage_optimized, memory_constrained)
- **And** each preset shows performance characteristics (speed, dimensions, storage)
- **And** default preset is `for_documents`

#### Scenario: Apply preset configuration
- **Given** user selects a preset from dropdown
- **When** selection changes
- **Then** fetches preset configuration from API
- **And** updates form fields with preset values
- **And** shows performance impact preview

#### Scenario: Toggle advanced settings
- **Given** user wants manual control
- **When** clicks "Advanced Settings" toggle
- **Then** reveals all configuration parameters
- **And** allows editing task, dimensions, late_chunking, etc.
- **And** shows validation errors inline

### Requirement: Form Validation and Submission

The system MUST validate configuration inputs and provide clear feedback on save operations.

#### Scenario: Save valid configuration
- **Given** user has configured embeddings
- **When** clicks "Save Configuration"
- **Then** validates all inputs client-side
- **And** sends POST to `/api/config/embeddings`
- **And** shows success toast on 200 OK
- **And** updates cached configuration

#### Scenario: Reject invalid inputs
- **Given** user enters invalid dimension (e.g., 3000)
- **When** attempts to save
- **Then** highlights invalid field with error message
- **And** disables Save button
- **And** does not send API request

