# Tasks: Add Structured Document Analysis

## Prerequisites
- [x] Review existing loader architecture in `src/jina_rag_pipeline/ingestion/loaders.py`
- [x] Review task processing flow in `src/jina_rag_pipeline/api/tasks.py`
- [x] Review vector storage interface in `src/jina_rag_pipeline/storage/chroma_store.py`

## Phase 1: Dependencies and Foundation (Estimated: 4 hours)

### Task 1.1: Add dependencies to pyproject.toml
- [x] Add `python-pptx>=0.6.21` to main dependencies
- [x] Add `deepdoctection>=0.43.0` to main dependencies (REQUIRED)
- [x] Add `python-doctr>=0.10.0` to main dependencies (REQUIRED)
- [x] Add installation note for `detectron2` (git installation required)
- [x] Update README.md with complete installation instructions
- [x] Add post-install verification script
- **Validation**: `uv pip install -e .` succeeds, then manual detectron2 install
- **Parallel**: Can be done independently

### Task 1.2: Create layout analysis wrapper module
- [x] Create `src/jina_rag_pipeline/ingestion/layout_analysis.py`
- [x] Implement `LayoutAnalyzer` class with strict dependency checking
- [x] Define `Region` dataclass with full granular metadata fields
- [x] Implement `analyze_document()` method wrapping deepdoctection
- [x] Implement `extract_regions()` method returning List[Region]
- [x] Add region type classification (chart, diagram, photo, etc.)
- [x] Calculate normalized bounding boxes (0-1 range)
- [x] Detect relationships between regions (parent-child, related)
- [x] FAIL FAST if deepdoctection not installed (no fallback)
- **Validation**: All imports succeed, region extraction includes full metadata
- **Depends on**: Task 1.1 (dependencies)

### Task 1.3: Create configuration schema
- [x] Create `CollectionConfig` dataclass in `src/jina_rag_pipeline/api/models.py`
- [x] Add fields with precision-first defaults:
  - `enable_layout_analysis: bool = True` (DEFAULT ENABLED)
  - `layout_ocr_enabled: bool = True`
  - `layout_table_extraction: bool = True`
  - `save_extracted_images: bool = True` (ALWAYS save)
  - `region_granularity: Literal["fine", "coarse"] = "fine"` (maximum granularity)
  - `save_region_metadata: bool = True` (full metadata preservation)
- [x] Implement config serialization/deserialization to JSON
- [x] Add config validation with clear error messages
- [x] Add config versioning for future migrations
- **Validation**: Config can be created, saved, loaded, and validated
- **Parallel**: Can be done independently

### Task 1.4: Create organized storage directory structure
- [x] Modify collection creation to include ALL persistent directories:
  - `documents/` (original files)
  - `images/` (standalone images)
  - `extracted_images/` (extracted from documents)
  - `tables/` (extracted tables as HTML/JSON)
  - `thumbnails/` (all thumbnails)
  - `metadata/` (per-document region metadata)
- [x] Create `config.json` with precision-first defaults
- [x] Create `stats.json` for collection statistics
- [x] Implement directory creation helper with error handling
- [x] Update `src/jina_rag_pipeline/api/app.py` collection initialization
- [x] Add directory structure validation on startup
- **Validation**: New collections have complete organized directory structure
- **Depends on**: Task 1.3 (config schema)

## Phase 2: PowerPoint Loader (Estimated: 4 hours)

### Task 2.1: Implement simple PowerPoint loader
- [x] Create `PowerPointLoader` class in `src/jina_rag_pipeline/ingestion/loaders.py`
- [x] Implement `supports()` method for .pptx and .ppt extensions
- [x] Implement `_load_simple()` method using python-pptx
- [x] Extract text from slides, shapes, and optionally speaker notes
- [x] Preserve slide numbers and metadata
- [x] Return `Document` with combined text content
- **Validation**: Can load and extract text from sample .pptx file
- **Depends on**: Task 1.1 (python-pptx dependency)

### Task 2.2: Register PowerPoint loader
- [x] Add PowerPointLoader to `LoaderFactory._register_default_loaders()`
- [x] Add graceful handling if python-pptx not installed
- [x] Update `SUPPORTED_FORMATS` in `src/jina_rag_pipeline/api/app.py`
- [x] Add `.pptx` and `.ppt` to supported formats list
- **Validation**: LoaderFactory returns PowerPointLoader for .pptx files
- **Depends on**: Task 2.1 (PowerPoint loader implementation)

### Task 2.3: Add PowerPoint to API
- [x] Update `SUPPORTED_FORMATS` constant in API
- [x] Update `/api/ingest/formats` endpoint response
- [x] Add MIME type validation for PowerPoint files
- **Validation**: API accepts PowerPoint file uploads
- **Depends on**: Task 2.2 (loader registration)

### Task 2.4: Test simple PowerPoint ingestion
- [x] Create test fixture with sample .pptx file
- [x] Write unit test for PowerPointLoader.load()
- [x] Write integration test for full PowerPoint ingestion pipeline
- [x] Verify text extraction and metadata preservation
- **Validation**: Tests pass, PowerPoint files are processed successfully
- **Depends on**: Task 2.3 (API support)

## Phase 3: Layout Analysis Integration (Estimated: 6 hours)

### Task 3.1: Implement layout-aware PowerPoint loader
- [x] Add `use_layout_analysis` parameter to PowerPointLoader.__init__()
- [x] Implement `_load_with_layout()` method
- [x] Convert PPTX slides to temporary images
- [x] Run LayoutAnalyzer on each slide image
- [x] Extract text, image, and table regions
- [x] Save extracted images to `extracted_images/` directory
- [x] Return Document with regions in metadata
- **Validation**: Layout-aware mode extracts regions correctly
- **Depends on**: Task 1.2 (LayoutAnalyzer), Task 2.1 (PowerPointLoader base)

### Task 3.2: Implement fine-grained region-based task processing
- [x] Modify `TaskManager.process_task()` in `src/jina_rag_pipeline/api/tasks.py`
- [x] Check for `regions` in document metadata
- [x] Process EACH region individually (maximum granularity)
- [x] Route to appropriate encoder:
  - Text regions → Jina text encoder
  - Image regions → Jina vision encoder
  - Table regions → Text encoder on structured HTML/JSON
- [x] Store each region as separate vector entry (precision-first)
- [x] Include FULL granular metadata for each region:
  - region_id, region_type, region_sequence
  - bbox, bbox_normalized, width, height
  - confidence, detection_model, extraction_timestamp
  - visual_type (for images), row/col counts (for tables)
  - parent_region_id, related_region_ids
  - All file paths (image_path, thumbnail_path, table_path)
- [x] Link all regions to source document via document_id
- [x] Preserve reading order in region_sequence
- [x] Calculate and store region relationships
- **Validation**: Each region generates separate vector with full metadata
- **Depends on**: Task 3.1 (layout-aware loader)

### Task 3.3: Implement organized persistent storage for regions
- [x] Create helper function for generating organized filenames
  - Pattern: `{doc_id}_page{N}_region{M}_{type}.{ext}`
  - Example: `a1b2c3_page1_region0_chart.png`
- [x] Save ALL extracted images to `extracted_images/` (no exceptions)
- [x] Save extracted tables to `tables/` as both HTML and JSON
- [x] Generate thumbnails for all extracted images
  - Save to `thumbnails/{doc_id}_page{N}_region{M}_thumb.jpg`
- [x] Create per-document metadata JSON files in `metadata/`
  - `{doc_id}_regions.json` - all regions with full metadata
  - `{doc_id}_layout.json` - layout analysis results
- [x] Store all file paths in region metadata
- [x] Implement atomic file operations (temp file + rename)
- [x] Add cleanup handlers for failed processing
- [x] Update collection stats.json with region counts
- **Validation**: All regions persistently stored with organized naming
- **Depends on**: Task 3.2 (region processing)

### Task 3.4: Add configuration loading
- [x] Load collection config from `config.json` in `TaskManager.process_task()`
- [x] Pass `use_layout_analysis` to loaders based on config
- [x] Handle missing config gracefully (use defaults)
- **Validation**: Collections with layout enabled use layout analysis
- **Depends on**: Task 1.3 (config schema), Task 3.2 (region processing)

## Phase 4: Enhanced Loaders for PDF/DOCX (Estimated: 4 hours)

### Task 4.1: Add optional layout analysis to PDFLoader
- [x] Add `use_layout_analysis` parameter to PDFLoader.__init__()
- [x] Implement layout-aware extraction when enabled
- [x] Extract embedded images from PDF pages
- [x] Combine native text extraction with image regions
- [x] Preserve page boundaries and image locations
- **Validation**: PDFs with images extract both text and visual content
- **Depends on**: Task 1.2 (LayoutAnalyzer)

### Task 4.2: Add optional layout analysis to DocxLoader
- [x] Add `use_layout_analysis` parameter to DocxLoader.__init__()
- [x] Extract inline images from Word documents
- [x] Preserve image positions relative to text
- [x] Save extracted images to extracted_images folder
- **Validation**: DOCX files with images extract visual content
- **Depends on**: Task 1.2 (LayoutAnalyzer)

### Task 4.3: Update loader factory with configuration
- [x] Modify LoaderFactory to accept configuration parameter
- [x] Pass use_layout_analysis to loaders during registration
- [x] Ensure backward compatibility (default: simple mode)
- **Validation**: Loaders respect configuration settings
- **Depends on**: Task 4.1 (PDF layout), Task 4.2 (DOCX layout)

## Phase 5: API Enhancements (Estimated: 3 hours)

### Task 5.1: Add collection configuration endpoints
- [x] Implement GET `/api/collections/{name}/config` endpoint
- [x] Implement PUT `/api/collections/{name}/config` endpoint
- [x] Add config validation before saving
- [x] Return clear error messages for invalid config
- **Validation**: Can read and update collection config via API
- **Depends on**: Task 1.3 (config schema)

### Task 5.2: Add capabilities endpoint
- [x] Implement GET `/api/capabilities` endpoint
- [x] Check if deepdoctection is installed
- [x] Return layout analysis availability status
- [x] List available models/features
- **Validation**: Endpoint reports correct capability status
- **Parallel**: Can be done independently

### Task 5.3: Enhance ingestion status response
- [x] Modify `/api/ingest/status/{task_id}` to include region info
- [x] Add `regions_extracted` count field
- [x] Add region type breakdown (text/image/table counts)
- [x] Indicate processing mode (simple vs layout)
- **Validation**: Status includes region statistics when available
- **Depends on**: Task 3.2 (region processing)

### Task 5.4: Enhance search results with region metadata
- [x] Modify search endpoint to include region fields in response
- [x] Add region_type, bbox, page_number to result metadata
- [x] Include image_path for image regions
- [x] Add optional region_type filter parameter
- **Validation**: Search results include complete region metadata
- **Depends on**: Task 3.2 (region storage)

## Phase 6: Testing and Validation (Estimated: 4 hours)

### Task 6.1: Unit tests for layout analysis
- [x] Test LayoutAnalyzer with sample documents
- [x] Test Region dataclass serialization
- [x] Test fallback behavior when deepdoctection unavailable
- [x] Test configuration validation
- **Validation**: All unit tests pass
- **Depends on**: Phase 3 complete

### Task 6.2: Integration tests for PowerPoint
- [x] Test end-to-end PowerPoint ingestion (simple mode)
- [x] Test end-to-end PowerPoint ingestion (layout mode)
- [x] Test region extraction and storage
- [x] Test search retrieval of PowerPoint content
- **Validation**: All integration tests pass
- **Depends on**: Phase 3 complete

### Task 6.3: Integration tests for mixed-content documents
- [x] Test PDF with embedded images (layout mode)
- [x] Test DOCX with inline images (layout mode)
- [x] Test region-based search and retrieval
- [x] Test configuration toggle between simple and layout modes
- **Validation**: All mixed-content tests pass
- **Depends on**: Phase 4 complete

### Task 6.4: Performance and memory testing
- [x] Measure processing time for various document sizes
- [x] Monitor memory usage during layout analysis
- [x] Verify processing completes within acceptable timeframes
- [x] Test with M4 Max memory constraints (48GB)
- **Validation**: Performance meets success criteria (<60s for 10 pages)
- **Depends on**: Phase 3 complete

## Phase 7: Documentation and Polish (Estimated: 3 hours)

### Task 7.1: Update user documentation
- [x] Document PowerPoint file support in README
- [x] Add layout analysis feature documentation
- [x] Provide installation instructions for optional dependencies
- [x] Add configuration examples
- [x] Document region metadata schema
- **Validation**: Documentation is clear and complete
- **Parallel**: Can be done alongside testing

### Task 7.2: Add inline code documentation
- [x] Add docstrings to LayoutAnalyzer class
- [x] Add docstrings to PowerPointLoader
- [x] Document region metadata structure
- [x] Add type hints to all new functions
- **Validation**: Code documentation is complete
- **Parallel**: Can be done alongside testing

### Task 7.3: Create example notebooks/scripts
- [x] Create example: PowerPoint ingestion
- [x] Create example: Layout-aware PDF processing
- [x] Create example: Region-based search
- [x] Create example: Configuration management
- **Validation**: Examples run successfully
- **Depends on**: Phase 5 complete

### Task 7.4: Update changelog and migration guide
- [x] Add entry to CHANGELOG.md
- [x] Document new features and capabilities
- [x] Provide migration guide for existing users
- [x] Note any behavioral changes
- **Validation**: Changelog is accurate and helpful
- **Parallel**: Can be done alongside testing

## Definition of Done
- [x] All tasks completed and validated
- [x] All tests passing (unit + integration)
- [x] PowerPoint files can be uploaded and processed
- [x] Layout analysis works for PDF/DOCX/PPTX
- [x] Configuration can be managed via API
- [x] Performance meets criteria (<60s for typical documents)
- [x] Documentation is complete
- [x] Code review completed
- [x] No regressions in existing functionality

## Rollback Plan
If issues arise:
1. Set `enable_layout_analysis = False` in collection configs
2. Loaders automatically fall back to simple mode
3. If needed, uninstall deepdoctection: `pip uninstall deepdoctection`
4. Existing collections continue to work without layout analysis
