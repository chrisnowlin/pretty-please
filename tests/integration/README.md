# Integration Tests - Lesson Plan Generation

## Overview

This directory contains end-to-end integration tests that verify the complete lesson plan generation workflow from material ingestion through final output.

## Test Files

### `test_lesson_plan_e2e.py`

Comprehensive integration tests covering:
- ✅ System component initialization
- ✅ Educational material ingestion
- ✅ Complete lesson generation workflow
- ✅ Retrieval with metadata filtering
- ✅ Citation validation
- ✅ Abbreviated grade format validation
- ✅ Default duration (50 minutes) validation

### `sample_materials/`

Sample educational materials for testing:
- **Grade3_Math_Fractions_Textbook.txt** - Textbook content about fractions
- **Grade3_Math_Activities_Workbook.txt** - Hands-on activities and assessments
- **Visual_Aids_Fractions.txt** - Visual models and diagrams

These materials simulate real educational content and include:
- Grade level information (Grade 3)
- Subject area (Mathematics)
- Multiple content types (textbook, activities, visual aids)
- Sufficient content for meaningful lesson generation

## Running the Tests

### Run All Integration Tests

```bash
# From project root
pytest -v -m integration tests/integration/
```

### Run Specific Test

```bash
pytest -v tests/integration/test_lesson_plan_e2e.py::TestLessonPlanEndToEnd::test_complete_lesson_generation_workflow
```

### Run Without Integration Tests (Regular Test Suite)

```bash
# Excludes integration tests (they require models and are slower)
pytest -v -m "not integration"
```

## Test Markers

Integration tests are marked with `@pytest.mark.integration` to:
- Allow selective execution
- Exclude from regular CI/CD (optional)
- Separate fast unit tests from slower integration tests

## What Gets Tested

### 1. Complete Workflow (`test_complete_lesson_generation_workflow`)

**Steps**:
1. Initialize embedder, vector store, generator
2. Ingest sample materials into collections
3. Generate lesson plan using materials
4. Verify lesson structure and content

**Verifications**:
- ✅ Lesson metadata (title, grade, subject, duration)
- ✅ YAML frontmatter format
- ✅ Grade format is abbreviated ("3", not "Grade 3")
- ✅ Duration is 50 minutes (default)
- ✅ Sources are included (sources_count >= 2)
- ✅ Citations present in content ([1], [2])
- ✅ "Sources Referenced" section exists
- ✅ Required sections (Learning Objectives, Materials, Lesson Flow)

### 2. Retrieval with Metadata Filtering (`test_retrieval_with_metadata_filtering`)

**Tests**:
- Retrieval with grade filter ("3")
- Retrieval with subject filter ("Mathematics")
- Source attribution in retrieved materials

**Verifications**:
- ✅ Materials are retrieved successfully
- ✅ Materials have source attribution (document_name, chunk_id)
- ✅ Relevance scores are calculated

### 3. Citation Validation (`test_citation_validation`)

**Tests**:
- Inline citations in lesson content
- Sources Referenced section

**Verifications**:
- ✅ Lesson includes inline citations [1], [2], etc.
- ✅ "Sources Referenced" section is present

### 4. Abbreviated Grade Format (`test_abbreviated_grade_format`)

**Tests**:
- Generates lessons with various grade formats: "3", "K", "6-8"

**Verifications**:
- ✅ Metadata uses abbreviated format
- ✅ YAML frontmatter uses abbreviated format
- ✅ No full grade names like "Grade 3" or "Kindergarten"

### 5. Default Duration (`test_default_duration`)

**Tests**:
- Generates lesson without specifying duration

**Verifications**:
- ✅ Duration defaults to 50 minutes (not 45)

## Expected Output

```
tests/integration/test_lesson_plan_e2e.py::TestLessonPlanEndToEnd::test_complete_lesson_generation_workflow PASSED

============================================================
LESSON PLAN GENERATION TEST - PASSED
============================================================
Title: Understanding Fractions: Parts of a Whole
Grade: 3
Duration: 50 minutes
Sources: 5
Images: 3
Content length: 3847 characters
============================================================
```

## Test Data Cleanup

Integration tests create temporary data:
- **ChromaDB**: `tests/integration/test_chroma_db/`

This directory is automatically cleaned up after tests complete.

## Requirements

To run integration tests, you need:

1. **Models downloaded**:
   - Jina Embeddings v4 (~8GB)
   - Qwen3-14B-4bit (~8GB)

2. **System requirements**:
   - Apple Silicon Mac (for MLX)
   - 16GB+ RAM
   - ~20GB disk space

3. **Dependencies installed**:
   ```bash
   pip install -e ".[dev]"
   ```

## Performance

Integration tests are slower than unit tests:
- **Typical runtime**: 1-3 minutes per test
- **Model loading**: ~10-30 seconds (first run)
- **Generation**: ~20-30 seconds per lesson

## Troubleshooting

### Test Fails: Model Not Found

**Solution**: Download models manually:
```bash
python -c "from transformers import AutoModel; AutoModel.from_pretrained('jinaai/jina-embeddings-v4')"
```

### Test Fails: Out of Memory

**Solution**: Close other applications or reduce batch sizes in test code.

### Test Fails: MPS Not Available

**Solution**: Ensure you're on Apple Silicon Mac with macOS 12+:
```python
import torch
print(torch.backends.mps.is_available())  # Should be True
```

### Test Fails: No Materials Retrieved

**Solution**: Check sample materials exist in `sample_materials/` directory.

## Adding New Integration Tests

To add a new integration test:

1. **Mark the test**:
   ```python
   @pytest.mark.integration
   async def test_new_feature(self, system_components):
       # Your test code
   ```

2. **Use fixtures**:
   - `system_components` - Pre-initialized embedder, vector store, generator
   - `ingested_materials` - Sample materials already ingested
   - `sample_materials_dir` - Path to sample materials

3. **Follow naming convention**:
   - `test_<feature>_<aspect>`
   - Example: `test_retrieval_with_image_filtering`

4. **Verify requirements**:
   - Citations present
   - Grade format abbreviated
   - Duration is 50 minutes (default)
   - YAML frontmatter correct

## CI/CD Integration

To skip integration tests in CI:

```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: pytest -v -m "not integration"
```

To run integration tests separately:

```yaml
- name: Run integration tests
  run: pytest -v -m integration
  timeout-minutes: 10
```

## Success Criteria

All integration tests should:
- ✅ Pass without errors
- ✅ Complete in <3 minutes each
- ✅ Produce valid lesson plans
- ✅ Include proper citations
- ✅ Use correct grade format
- ✅ Have default duration of 50 minutes

## Related Documentation

- [Setup Guide](../../docs/LESSON_PLAN_SETUP_GUIDE.md)
- [POC Complete](../../docs/LESSON_PLAN_POC_COMPLETE.md)
- [Markdown Format](../../docs/LESSON_MARKDOWN_FORMAT.md)

---

**Status**: All integration tests passing ✅
**Last Updated**: 2025-10-18
