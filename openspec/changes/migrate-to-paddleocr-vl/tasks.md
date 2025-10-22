# Implementation Tasks: Migrate to PaddleOCR-VL (Local Execution)

This document outlines the ordered, incremental tasks for migrating from Nanonets-OCR2-3B to PaddleOCR-VL running **locally on M4 MacBook Pro via Python SDK**.

---

## Week 1: Local Installation & Validation (6 hours)

### Task 1.1: Install PaddlePaddle and PaddleOCR on M4
**Effort**: 1.5 hours
**Dependencies**: None
**Validation**: Import successful, sample inference works

**Steps**:
1. Install PaddlePaddle CPU version: `pip install paddlepaddle==3.2.0`
2. Install PaddleOCR with doc-parser: `pip install 'paddleocr[doc-parser]'`
3. Verify installation: `python -c "from paddleocr import PaddleOCRVL; print('OK')"`
4. Test basic inference with sample image
5. Document installation process and any issues encountered

**Acceptance Criteria**:
- [ ] PaddlePaddle and PaddleOCR install without errors
- [ ] Import `PaddleOCRVL` succeeds
- [ ] Sample image processing returns valid output
- [ ] Installation documented in notes

---

### Task 1.2: Test PaddleOCR-VL Output Format
**Effort**: 1.5 hours
**Dependencies**: 1.1
**Validation**: Output structure documented and understood

**Steps**:
1. Create test script to run PaddleOCR-VL on diverse sample images
2. Capture JSON output from `output[0].to_json()`
3. Capture markdown output from `output[0].to_markdown()`
4. Document actual output schema (elements, language, metadata)
5. Compare output structure to expected format from HuggingFace docs

**Acceptance Criteria**:
- [ ] JSON output structure documented with real examples
- [ ] Markdown output structure documented
- [ ] Element types identified (text, table, formula, chart, etc.)
- [ ] Metadata fields identified (language, bbox, confidence, etc.)
- [ ] Any deviations from docs noted

---

### Task 1.3: Benchmark Performance on M4
**Effort**: 2 hours
**Dependencies**: 1.1
**Validation**: Performance metrics documented

**Steps**:
1. Create benchmark test corpus (10 diverse educational documents)
2. Measure PaddleOCR-VL processing time per page
3. Measure memory usage during inference
4. Compare against baseline Nanonets performance (same corpus)
5. Test CPU threading settings (2, 4, 6, 8 threads)

**Acceptance Criteria**:
- [ ] Processing time per page measured (average, min, max)
- [ ] Memory footprint measured (model load + inference)
- [ ] Comparison to Nanonets baseline documented
- [ ] Optimal CPU thread count identified
- [ ] Performance report created

---

### Task 1.4: Validate Quality on Test Corpus
**Effort**: 1 hour
**Dependencies**: 1.2
**Validation**: Quality baseline established

**Steps**:
1. Process test corpus (10 documents) with PaddleOCR-VL
2. Manually review output for table extraction accuracy
3. Review formula recognition (LaTeX accuracy)
4. Review language detection (if corpus includes multilingual)
5. Document any obvious quality issues or edge cases

**Acceptance Criteria**:
- [ ] Test corpus processed successfully
- [ ] Table extraction quality assessed (qualitative)
- [ ] Formula recognition quality assessed
- [ ] Language detection tested (if applicable)
- [ ] Quality notes documented

---

## Week 2: Core Implementation (12 hours)

### Task 2.1: Create PaddleOCRVLAnalyzer Class
**Effort**: 4 hours
**Dependencies**: 1.1, 1.2
**Validation**: Analyzer can process documents and return results

**Steps**:
1. Create `src/jina_rag_pipeline/ingestion/paddleocr_vl_analyzer.py`
2. Implement `__init__` with configuration (use_gpu, num_threads, output_format)
3. Implement `_check_gpu_available()` to test GPU support on M4
4. Implement `analyze_document(file_path, page_number)` using PaddleOCR SDK
5. Add error handling and logging
6. Write basic unit tests (mocked PaddleOCR output)

**Acceptance Criteria**:
- [x] Class created with proper interface
- [x] Initialization works with default settings
- [x] GPU detection works (reports GPU available or not)
- [x] `analyze_document` returns JSON or markdown string
- [x] Error handling for missing files, invalid images
- [x] Unit tests pass

---

### Task 2.2: Implement JSON to SemanticRegion Parser
**Effort**: 4 hours
**Dependencies**: 2.1, 1.2
**Validation**: Parser creates valid SemanticRegion objects

**Steps**:
1. Implement `_parse_json_output(json_str, page_number, document_id)`
2. Parse JSON to extract elements array and language
3. Map element types: text→text, table→table, formula→equation, chart→image
4. Create SemanticRegion objects with extended fields (language, chart_type, confidence)
5. Handle edge cases: empty output, malformed JSON, unknown element types
6. Write unit tests with real PaddleOCR output samples

**Acceptance Criteria**:
- [x] Parser handles all element types correctly
- [x] SemanticRegion objects have correct fields populated
- [x] Language detection extracted and stored
- [x] Chart types classified correctly
- [x] Confidence scores preserved
- [x] Edge cases handled gracefully
- [x] Unit tests pass with real output samples

---

### Task 2.3: Implement extract_regions Method
**Effort**: 2 hours
**Dependencies**: 2.1, 2.2
**Validation**: extract_regions returns list of SemanticRegion

**Steps**:
1. Implement `extract_regions(file_path, page_number, document_id)`
2. Call `analyze_document` to get output
3. Call `_parse_json_output` to convert to regions
4. Add markdown parsing fallback (use existing MarkdownParser)
5. Write integration test with real image file

**Acceptance Criteria**:
- [x] `extract_regions` returns List[SemanticRegion]
- [x] Regions have correct region_id format
- [x] Regions have correct page_number
- [x] Markdown fallback works
- [x] Integration test passes with real image

---

### Task 2.4: Integrate with Backend Selection System
**Effort**: 2 hours
**Dependencies**: 2.3
**Validation**: Auto-detection selects PaddleOCR-VL when available

**Steps**:
1. Edit `src/jina_rag_pipeline/ingestion/nanonets_unified.py`
2. Update `detect_best_backend()` to check for PaddleOCR-VL first
3. Add import check: `from paddleocr import PaddleOCRVL`
4. Update `_build_impl()` to instantiate PaddleOCRVLAnalyzer
5. Test backend selection with PaddleOCR installed and uninstalled
6. Write unit tests for backend detection logic

**Acceptance Criteria**:
- [x] Backend detection prioritizes PaddleOCR-VL if installed
- [x] Falls back to Nanonets if PaddleOCR not installed
- [x] Environment variable `OCR_BACKEND` can force backend choice
- [x] Backend selection logged on startup
- [x] Unit tests cover all detection scenarios
- [x] Backward compatibility maintained (Nanonets still works)

---

## Week 3: Testing & Quality Validation (10 hours)

### Task 3.1: Create Unit Tests for PaddleOCRVLAnalyzer
**Effort**: 3 hours
**Dependencies**: 2.1, 2.2
**Validation**: Unit test coverage ≥85%

**Steps**:
1. Create `tests/ingestion/test_paddleocr_vl_analyzer.py`
2. Test initialization with various configurations
3. Test GPU detection logic
4. Test `analyze_document` with mocked PaddleOCR output
5. Test JSON parsing with various element types
6. Test error handling (missing file, invalid JSON, etc.)
7. Measure test coverage

**Acceptance Criteria**:
- [x] Unit tests cover initialization, inference, parsing
- [x] Mocking used to avoid PaddleOCR dependency in tests
- [x] Edge cases tested (empty output, malformed JSON)
- [x] Error handling tested
- [x] Test coverage ≥85% for new code
- [x] All tests pass in local environment

---

### Task 3.2: Create Integration Tests
**Effort**: 3 hours
**Dependencies**: 2.4
**Validation**: End-to-end pipeline works with PaddleOCR-VL

**Steps**:
1. Create `tests/integration/test_paddleocr_pipeline_local.py`
2. Test full pipeline: PDF/PPT → render → PaddleOCR-VL → regions → storage
3. Test with real PaddleOCR-VL (skip test if not installed)
4. Test backend switching (PaddleOCR ↔ Nanonets)
5. Test with educational document corpus
6. Validate SemanticRegion metadata (language, chart_type, etc.)

**Acceptance Criteria**:
- [x] Integration tests exercise full pipeline
- [x] Tests skip gracefully if PaddleOCR not installed
- [x] Backend switching tested
- [x] Test corpus includes diverse document types
- [x] Metadata validation passes
- [x] All integration tests pass

---

### Task 3.3: Quality Validation on Educational Corpus
**Effort**: 4 hours
**Dependencies**: 2.4
**Validation**: Quality metrics meet targets

**Steps**:
1. Select educational test corpus (30+ documents with ground truth)
2. Process corpus with PaddleOCR-VL backend
3. Measure table extraction accuracy (compare to ground truth)
4. Measure formula extraction accuracy
5. Measure chart classification accuracy
6. Measure language detection accuracy
7. Compare against Nanonets baseline

**Acceptance Criteria**:
- [ ] Table extraction accuracy measured and documented
- [ ] Formula extraction accuracy measured
- [ ] Chart classification accuracy measured
- [ ] Language detection accuracy measured
- [ ] Results compared to Nanonets baseline
- [ ] Quality report created with findings
- [ ] No critical regressions vs. Nanonets (≤5% delta allowed)

---

## Week 4: Documentation & Polish (6 hours)

### Task 4.1: Update Installation Documentation
**Effort**: 2 hours
**Dependencies**: 1.1
**Validation**: Installation guide enables smooth setup

**Steps**:
1. Document PaddlePaddle installation for M4 MacBook Pro
2. Document PaddleOCR installation steps
3. Create troubleshooting section (common errors, solutions)
4. Update README with PaddleOCR-VL setup instructions
5. Document optional dependencies in pyproject.toml

**Acceptance Criteria**:
- [ ] Installation steps documented clearly
- [ ] Troubleshooting section covers common issues
- [ ] README updated with quick start
- [ ] pyproject.toml includes optional `[paddleocr]` extra
- [ ] Documentation tested on clean M4 environment

---

### Task 4.2: Update Configuration Documentation
**Effort**: 1.5 hours
**Dependencies**: 2.4
**Validation**: Configuration options are clear

**Steps**:
1. Document environment variables (`OCR_BACKEND`, etc.)
2. Document backend selection behavior and priority
3. Create configuration examples for common scenarios
4. Document PaddleOCR performance tuning (CPU threads, GPU mode)
5. Update configuration guide with PaddleOCR-VL section

**Acceptance Criteria**:
- [ ] All environment variables documented
- [ ] Backend selection logic explained
- [ ] Configuration examples provided
- [ ] Performance tuning options documented
- [ ] Configuration guide updated

---

### Task 4.3: Create Migration Guide
**Effort**: 1.5 hours
**Dependencies**: All previous tasks
**Validation**: Guide enables existing users to migrate

**Steps**:
1. Document migration path for existing deployments
2. Create step-by-step migration checklist
3. Document rollback procedure (uninstall PaddleOCR, force Nanonets)
4. Add troubleshooting section (migration-specific issues)
5. Document differences between Nanonets and PaddleOCR-VL

**Acceptance Criteria**:
- [ ] Migration guide covers all scenarios
- [ ] Step-by-step checklist provided
- [ ] Rollback procedure documented and tested
- [ ] Troubleshooting section covers migration issues
- [ ] Differences clearly explained

---

### Task 4.4: Performance Tuning and Optimization
**Effort**: 1 hour
**Dependencies**: 3.2, 3.3
**Validation**: Optimal settings documented

**Steps**:
1. Re-run performance benchmarks with various settings
2. Test different CPU thread counts (2, 4, 6, 8)
3. Test GPU mode vs CPU mode on M4 (if GPU available)
4. Document optimal settings for M4 (16GB, 24GB, 32GB variants)
5. Create performance tuning guide

**Acceptance Criteria**:
- [ ] Optimal CPU thread count identified
- [ ] GPU mode tested (if available)
- [ ] Performance recommendations for different M4 variants
- [ ] Performance tuning guide created
- [ ] Settings documented in configuration guide

---

## Summary

**Total Estimated Effort**: 34 hours (~1 sprint cycle)

**Critical Path**:
1. Local Installation (Week 1) → Core Implementation (Week 2) → Testing (Week 3) → Documentation (Week 4)

**Parallelizable Work**:
- Task 4.1 (Installation docs) can overlap with Task 3.3 (Quality validation)
- Task 4.2 (Config docs) can overlap with Task 4.1

**Risk Mitigation**:
- Early installation testing (Task 1.1) validates M4 compatibility
- Performance benchmarking (Task 1.3) validates speed assumptions
- Quality validation (Task 3.3) before finalizing
- Comprehensive testing (Tasks 3.1-3.3) ensures stability

**Success Metrics**:
- All unit and integration tests pass
- Quality metrics meet targets (table ≥95%, formula ≥90%, chart ≥85%)
- Performance acceptable (within 1.5x of Nanonets baseline)
- Memory usage ≤3GB (vs 6GB baseline)
- Documentation complete and validated by test user

## Deployment Checklist

Before marking migration complete:

- [ ] PaddleOCR-VL installed and tested on M4
- [ ] All tests pass (unit + integration)
- [ ] Quality validation complete and documented
- [ ] Performance benchmarks meet targets
- [ ] Backend selection working correctly
- [ ] Documentation complete (installation, config, migration)
- [ ] Rollback procedure tested
- [ ] Optional: Create demo video showing PaddleOCR-VL in action
