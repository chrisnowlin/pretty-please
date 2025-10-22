# ocr-config-ui Specification

## Purpose
TBD - created by archiving change expose-advanced-config-ui. Update Purpose after archive.
## Requirements
### Requirement: OCR Configuration Panel Component

The frontend MUST provide a React component for configuring OCR processing parameters.

#### Scenario: Display preset dropdown with performance hints
- **Given** the OCR Config Panel is rendered
- **When** user views the preset dropdown
- **Then** shows all available presets (mlx_optimized, balanced, two_tier, memory_constrained)
- **And** each preset shows performance characteristics (speed, memory, workers)
- **And** default preset is `mlx_optimized` on Apple Silicon, `balanced` otherwise

#### Scenario: Apply preset configuration
- **Given** user selects a preset from dropdown
- **When** selection changes
- **Then** fetches preset configuration from API
- **And** updates form fields with preset values
- **And** shows performance impact preview

#### Scenario: Configure two-tier hybrid settings
- **Given** user selects `two_tier` preset
- **When** advanced settings are expanded
- **Then** shows complexity threshold controls
- **And** allows configuration of table, equation, image, and text thresholds
- **And** explains two-tier routing strategy

### Requirement: Hardware-Aware Suggestions

The system MUST detect user hardware and suggest optimal OCR presets.

#### Scenario: Suggest optimal preset based on detected hardware
- **Given** user opens OCR config panel
- **When** system detects Apple Silicon
- **Then** recommends `mlx_optimized` preset with explanation
- **And** shows memory savings (2.2 GB vs 8 GB)

