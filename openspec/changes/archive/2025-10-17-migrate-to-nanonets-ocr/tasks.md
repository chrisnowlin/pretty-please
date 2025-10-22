# Implementation Tasks: Migrate to Nanonets-OCR2-3B

## Phase 1: Foundation & Model Setup (Day 1, Morning)

### Task 1.1: Install and Test Nanonets Model
**Objective**: Verify model downloads and runs on M4 Max

**Steps**:
1. Add nanonets/Nanonets-OCR2-3B to dependencies
2. Create test script to download and load model
3. Test inference on sample slide image
4. Verify MPS (Metal Performance Shaders) acceleration
5. Measure memory usage and inference time

**Validation**:
- [ ] Model downloads successfully (~6GB)
- [ ] Model loads in < 30 seconds
- [ ] Inference completes on test image
- [ ] Memory usage < 10GB
- [ ] MPS acceleration confirmed

**Files**:
- `test_nanonets_model.py` (new, temporary)
- `pyproject.toml` (update dependencies)

---

### Task 1.2: Create SemanticRegion Dataclass
**Objective**: Define data structure for semantic regions

**Steps**:
1. Create `src/jina_rag_pipeline/ingestion/semantic_region.py`
2. Define `SemanticRegion` dataclass with full metadata
3. Add `to_dict()` and `from_dict()` methods
4. Create type hints for region types
5. Add docstrings and examples

**Validation**:
- [ ] All fields properly typed
- [ ] Serialization/deserialization works
- [ ] Type checking passes (mypy)
- [ ] Unit tests pass

**Files**:
- `src/jina_rag_pipeline/ingestion/semantic_region.py` (new)
- `tests/unit/test_semantic_region.py` (new)

---

## Phase 2: Markdown Parser (Day 1, Afternoon)

### Task 2.1: Implement Markdown Parser Core
**Objective**: Parse Nanonets markdown output into regions

**Steps**:
1. Create `src/jina_rag_pipeline/ingestion/markdown_parser.py`
2. Implement regex patterns for:
   - HTML tables (`<table>...</table>`)
   - Images (`<img>...</img>`)
   - Equations (`$$...$$` and `$...$`)
   - Headers (`# ... ######`)
   - Lists (ordered and unordered)
3. Create `parse_markdown_to_regions()` function
4. Handle edge cases (nested structures, malformed markdown)

**Validation**:
- [ ] Extracts all major structural elements
- [ ] Handles nested lists correctly
- [ ] Preserves content formatting
- [ ] Robust error handling
- [ ] Unit tests cover edge cases

**Files**:
- `src/jina_rag_pipeline/ingestion/markdown_parser.py` (new)
- `tests/unit/test_markdown_parser.py` (new)
- `tests/fixtures/sample_markdown.md` (new, test data)

---

### Task 2.2: Add Table Structure Extraction
**Objective**: Parse HTML tables to extract metadata

**Steps**:
1. Implement HTML table parser
2. Extract row and column counts
3. Detect header rows
4. Preserve cell content with formatting
5. Generate both HTML and markdown representations

**Validation**:
- [ ] Correctly counts rows and columns
- [ ] Identifies headers
- [ ] Handles colspan/rowspan
- [ ] Preserves cell formatting
- [ ] Unit tests with complex tables

**Files**:
- `src/jina_rag_pipeline/ingestion/markdown_parser.py` (update)
- `tests/unit/test_markdown_parser.py` (update)

---

### Task 2.3: Add Image Description Extraction
**Objective**: Extract and classify image descriptions

**Steps**:
1. Parse `<img>...</img>` tags
2. Extract description text
3. Classify image types from descriptions (chart, logo, diagram, photo)
4. Handle edge cases (empty descriptions, malformed tags)

**Validation**:
- [ ] Extracts descriptions correctly
- [ ] Classifies common image types
- [ ] Handles missing descriptions
- [ ] Unit tests with varied descriptions

**Files**:
- `src/jina_rag_pipeline/ingestion/markdown_parser.py` (update)
- `tests/unit/test_markdown_parser.py` (update)

---

## Phase 3: Nanonets Analyzer Implementation (Day 2, Morning)

### Task 3.1: Create NanonetsLayoutAnalyzer Class
**Objective**: Implement main analyzer class

**Steps**:
1. Create `src/jina_rag_pipeline/ingestion/nanonets_layout.py`
2. Implement `__init__()` with model loading
3. Implement `analyze_document()` for markdown generation
4. Implement `extract_regions()` using markdown parser
5. Add configuration options (tables, equations, descriptions)
6. Handle errors gracefully with fallback

**Validation**:
- [ ] Model loads successfully
- [ ] Generates markdown from images
- [ ] Parses markdown to regions
- [ ] Configuration options work
- [ ] Error handling tested

**Files**:
- `src/jina_rag_pipeline/ingestion/nanonets_layout.py` (new)
- `tests/integration/test_nanonets_layout.py` (new)

---

### Task 3.2: Optimize Model Configuration
**Objective**: Configure for optimal M4 Max performance

**Steps**:
1. Set device to "mps" (Metal Performance Shaders)
2. Configure BFloat16 precision
3. Enable Flash Attention 2 if available
4. Set optimal max_new_tokens for documents
5. Configure batch processing settings

**Validation**:
- [ ] MPS acceleration working
- [ ] Memory usage optimized
- [ ] Inference speed acceptable
- [ ] Quality not degraded

**Files**:
- `src/jina_rag_pipeline/ingestion/nanonets_layout.py` (update)

---

## Phase 4: Loader Integration (Day 2, Afternoon)

### Task 4.1: Update PowerPointLoader
**Objective**: Integrate Nanonets analyzer into PowerPoint loader

**Steps**:
1. Update `PowerPointLoader.__init__()` to use `NanonetsLayoutAnalyzer`
2. Keep existing deepdoctection as fallback (for now)
3. Add configuration flag to choose analyzer
4. Update `load()` method to use semantic regions
5. Convert `SemanticRegion` to `Document` format

**Validation**:
- [ ] Loads presentations with Nanonets
- [ ] Fallback works if model unavailable
- [ ] Semantic regions populated correctly
- [ ] Existing tests still pass

**Files**:
- `src/jina_rag_pipeline/ingestion/loaders.py` (update)
- `tests/integration/test_powerpoint_loader.py` (update)

---

### Task 4.2: Update Region Processing in tasks.py
**Objective**: Handle semantic regions in task processing

**Steps**:
1. Update `_process_regions()` to handle `SemanticRegion`
2. Route semantic types to appropriate encoders:
   - Tables → text encoder with HTML
   - Equations → text encoder with LaTeX
   - Images → vision encoder + text description
3. Update metadata schema for semantic tags
4. Preserve markdown structure in metadata

**Validation**:
- [ ] All region types processed correctly
- [ ] Encoder routing works
- [ ] Metadata includes semantic tags
- [ ] Embeddings generated successfully

**Files**:
- `src/jina_rag_pipeline/api/tasks.py` (update)

---

## Phase 5: Testing & Validation (Day 3, Morning)

### Task 5.1: Create Comprehensive Test Suite
**Objective**: Ensure all functionality works end-to-end

**Steps**:
1. Create `tests/integration/test_nanonets_powerpoint.py`
2. Test simple PowerPoint (text only)
3. Test complex PowerPoint (tables, images, equations)
4. Test multilingual content
5. Test error handling and fallback
6. Compare retrieval quality vs deepdoctection

**Validation**:
- [ ] All test scenarios pass
- [ ] Extraction accuracy ≥ 90%
- [ ] Retrieval quality ≥ baseline
- [ ] Error handling robust

**Files**:
- `tests/integration/test_nanonets_powerpoint.py` (new)
- `tests/fixtures/` (add test PowerPoints)

---

### Task 5.2: Performance Benchmarking
**Objective**: Validate performance is acceptable

**Steps**:
1. Create benchmark script
2. Measure processing time per slide
3. Measure memory usage during inference
4. Compare to deepdoctection baseline
5. Document performance characteristics

**Validation**:
- [ ] Processing time ≤ 2x baseline
- [ ] Memory usage < 10GB
- [ ] No memory leaks
- [ ] Performance documented

**Files**:
- `benchmarks/benchmark_nanonets.py` (new)
- `PERFORMANCE.md` (new documentation)

---

## Phase 6: Migration & Cleanup (Day 3, Afternoon)

### Task 6.1: Update Configuration System
**Objective**: Make Nanonets the default analyzer

**Steps**:
1. Update `CollectionConfig` to specify analyzer type
2. Set default to "nanonets"
3. Keep "deepdoctection" as option for backwards compatibility
4. Update configuration documentation

**Validation**:
- [ ] New collections use Nanonets by default
- [ ] Existing collections can opt-in
- [ ] Configuration validated correctly

**Files**:
- `src/jina_rag_pipeline/api/models.py` (update)
- `docs/configuration.md` (update)

---

### Task 6.2: Remove Monkey Patches (Conditional)
**Objective**: Clean up technical debt

**Steps**:
1. Mark `deepdoctection_patch.py` as deprecated
2. Add warnings when deepdoctection is used
3. Update documentation to recommend Nanonets
4. Schedule deepdoctection removal for future version

**Validation**:
- [ ] Warnings display correctly
- [ ] Documentation updated
- [ ] Migration path documented

**Files**:
- `src/jina_rag_pipeline/ingestion/deepdoctection_patch.py` (deprecate)
- `src/jina_rag_pipeline/ingestion/layout_analysis.py` (add warnings)
- `MIGRATION.md` (new documentation)

---

### Task 6.3: Update Dependencies
**Objective**: Clean up dependency list

**Steps**:
1. Mark deepdoctection, detectron2, doctr as optional
2. Add Nanonets dependencies as required
3. Update installation documentation
4. Test fresh install

**Validation**:
- [ ] Fresh install works
- [ ] Optional dependencies documented
- [ ] No import errors

**Files**:
- `pyproject.toml` (update)
- `README.md` (update installation)

---

## Phase 7: Documentation & Polish (Day 3.5)

### Task 7.1: Update Documentation
**Objective**: Document new implementation

**Steps**:
1. Update README with Nanonets features
2. Create migration guide for existing users
3. Document semantic region structure
4. Add examples of table/equation extraction
5. Update troubleshooting guide

**Validation**:
- [ ] Documentation complete and accurate
- [ ] Examples work as shown
- [ ] Migration guide clear

**Files**:
- `README.md` (update)
- `docs/MIGRATION_TO_NANONETS.md` (new)
- `docs/SEMANTIC_REGIONS.md` (new)
- `examples/nanonets_examples.py` (new)

---

### Task 7.2: Update TESTING_SUMMARY
**Objective**: Document implementation completion

**Steps**:
1. Update `TESTING_SUMMARY.md` with Nanonets results
2. Document performance improvements
3. Note removal of monkey patches
4. List new capabilities (tables, equations, etc.)

**Validation**:
- [ ] Summary accurate and complete
- [ ] Results documented
- [ ] Comparison to previous version

**Files**:
- `TESTING_SUMMARY.md` (update)

---

## Task Dependencies

```
Phase 1 (1.1, 1.2) → Phase 2 (2.1, 2.2, 2.3)
                   ↓
Phase 2 (all) → Phase 3 (3.1, 3.2)
                   ↓
Phase 3 (all) → Phase 4 (4.1, 4.2)
                   ↓
Phase 4 (all) → Phase 5 (5.1, 5.2)
                   ↓
Phase 5 (all) → Phase 6 (6.1, 6.2, 6.3)
                   ↓
Phase 6 (all) → Phase 7 (7.1, 7.2)
```

## Parallelization Opportunities

- Tasks 2.2 and 2.3 can run in parallel after 2.1
- Tasks 5.1 and 5.2 can run in parallel
- Tasks 6.1, 6.2, 6.3 can run in parallel
- Tasks 7.1 and 7.2 can run in parallel

## Success Criteria

- [ ] All tests passing
- [ ] Zero monkey patches required
- [ ] Table extraction working (≥90% accuracy)
- [ ] Equation recognition working
- [ ] Image descriptions generated
- [ ] Processing time ≤ 2x baseline
- [ ] Memory usage < 10GB
- [ ] Documentation complete
- [ ] Migration guide provided
- [ ] Performance benchmarked

## Rollback Triggers

If any of the following occur, consider pausing migration:
- Processing time > 3x baseline
- Memory usage > 15GB
- Extraction accuracy < 80%
- Critical bugs in production
- Model download failures > 50% of attempts

In case of rollback:
1. Keep Nanonets code but mark as experimental
2. Revert default to deepdoctection
3. Document issues encountered
4. Plan fixes before retry
