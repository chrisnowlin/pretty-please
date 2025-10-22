# Lesson Plan Generation - Setup and Usage Guide

## Overview

This guide walks you through setting up and using the lesson plan generation system, from initial setup through generating your first AI-powered lesson plan.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Educational Content Setup](#educational-content-setup)
4. [Using the System](#using-the-system)
5. [Running Integration Tests](#running-integration-tests)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)

## System Requirements

### Hardware
- **Apple Silicon Mac** (M1/M2/M3) recommended for optimal performance
- **16GB RAM minimum**, 32GB+ recommended
- **10GB free disk space** for models and data

### Software
- **Python 3.10+**
- **macOS** with MPS support (for MLX acceleration)
- **Node.js 18+** (for frontend)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/chrisnowlin/pretty-please.git
cd pretty-please
```

### 2. Install Backend Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Download Models

The system will automatically download required models on first use:
- **Jina Embeddings v4** (~8GB) - For semantic search
- **Qwen3-14B-4bit** (~8GB) - For lesson generation

Models are cached in `~/.cache/huggingface/`

## Educational Content Setup

### Option 1: Use Sample Materials (Quick Start)

Sample educational materials are included in `tests/integration/sample_materials/`:

```bash
# The sample materials are ready to use:
# - Grade3_Math_Fractions_Textbook.txt
# - Grade3_Math_Activities_Workbook.txt
# - Visual_Aids_Fractions.txt
```

### Option 2: Add Your Own Materials

#### Supported Formats
- **Text**: `.txt`, `.md`, `.pdf`, `.docx`
- **Presentations**: `.pptx`, `.ppt`
- **Images**: `.png`, `.jpg`, `.jpeg`

#### Recommended Organization

```
educational_materials/
├── math/
│   ├── grade3/
│   │   ├── textbook_chapter3.pdf
│   │   ├── activities.docx
│   │   └── diagrams.pptx
│   └── grade4/
│       └── ...
├── science/
│   └── ...
└── visual_aids/
    └── ...
```

#### Naming Convention

Use descriptive filenames that include grade and subject for better metadata extraction:

- ✅ **Good**: `Grade3_Math_Fractions_Textbook.pdf`
- ✅ **Good**: `5th_Grade_Science_Photosynthesis.docx`
- ❌ **Poor**: `doc1.pdf`
- ❌ **Poor**: `untitled.txt`

The system will automatically extract:
- **Grade level**: From filenames like "Grade3", "5th Grade", "K-2"
- **Subject**: From keywords like "Math", "Science", "ELA"

### Ingesting Content

#### Via Web UI

1. Start the server:
   ```bash
   python -m uvicorn src.jina_rag_pipeline.api.app:app --reload
   ```

2. Open browser: `http://localhost:8000`

3. Navigate to **Ingestion** page

4. Upload files or drag-and-drop

5. Wait for processing to complete

#### Via API

```bash
curl -X POST http://localhost:8000/api/ingest \
  -F "files=@path/to/document.pdf" \
  -F "collection_name=educational_content"
```

#### Via Python Script

```python
from src.jina_rag_pipeline.embeddings import JinaEmbeddingsV4
from src.jina_rag_pipeline.storage import ChromaVectorStore

# Initialize
embedder = JinaEmbeddingsV4()
vector_store = ChromaVectorStore()

# Create collection
vector_store.create_collection(
    name="educational_content",
    embedding_dimension=2048,
)

# Read document
with open("textbook.txt", "r") as f:
    content = f.read()

# Split into chunks (example: by paragraphs)
chunks = [p for p in content.split("\n\n") if p.strip()]

# Generate embeddings
embeddings = embedder.encode_text(
    chunks,
    task="retrieval",
    prompt_name="passage",
)

# Add to vector store
vector_store.add_embeddings(
    collection_name="educational_content",
    embeddings=[emb.tolist() for emb in embeddings],
    documents=chunks,
    metadatas=[
        {
            "source_file": "textbook.txt",
            "edu_grade": "3",
            "edu_subject": "Mathematics",
        }
        for _ in chunks
    ],
)
```

## Using the System

### Method 1: Web UI (Recommended)

1. **Start the server**:
   ```bash
   python -m uvicorn src.jina_rag_pipeline.api.app:app --reload
   ```

2. **Start the frontend** (in another terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open browser**: `http://localhost:5173`

4. **Generate a lesson**:
   - Navigate to "Lesson Plans" page
   - Fill out the form:
     - **Topic**: "Understanding Fractions"
     - **Learning Objective**: "Students will understand fractions as parts of a whole"
     - **Grade**: Select "3rd Grade"
     - **Subject**: Select "Mathematics"
     - **Duration**: Use slider (default: 50 minutes)
     - **Teaching Style**: Select "Balanced"
   - Click "Generate Lesson Plan"
   - Wait ~20-30 seconds for generation
   - Review, copy, or download the lesson

5. **Edit a saved lesson**:
   - Click "Show Saved Lessons" to view your lesson library
   - Click on any lesson title to open the detail view
   - Click the "Edit" button in the top-right corner
   - Modify editable fields:
     - **Title**: Update the lesson title (1-500 characters)
     - **Learning Objective**: Refine the objective (1-500 characters)
     - **Duration**: Adjust lesson length (20-90 minutes)
     - **Teaching Style**: Change approach (balanced, direct, inquiry, project)
     - **Markdown Content**: Edit the full lesson content (1-100,000 characters)
   - Click "Save Changes" to persist your edits
   - Or click "Cancel" to discard changes (you'll be prompted if there are unsaved changes)

### Method 2: API

```bash
curl -X POST http://localhost:8000/api/lesson-plan/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Understanding Fractions",
    "learning_objective": "Students will understand fractions as parts of a whole",
    "grade_level": "3",
    "subject": "Mathematics",
    "duration_minutes": 50,
    "teaching_style": "balanced"
  }'
```

**Response**:
```json
{
  "markdown": "---\ntitle: \"Understanding Fractions\"...",
  "metadata": {
    "title": "Understanding Fractions",
    "grade": "3",
    "subject": "Mathematics",
    "duration": 50
  },
  "sources_count": 5,
  "images_count": 2,
  "generation_time_seconds": 18.5
}
```

### Method 3: Python Code

```python
import asyncio
from src.jina_rag_pipeline.embeddings import JinaEmbeddingsV4
from src.jina_rag_pipeline.storage import ChromaVectorStore
from src.jina_rag_pipeline.retrieval.educational import EducationalRetriever
from src.jina_rag_pipeline.generation import LessonPlanner, QwenGenerator
from src.jina_rag_pipeline.generation.config import GenerationConfig

async def generate_lesson():
    # Initialize components
    embedder = JinaEmbeddingsV4()
    vector_store = ChromaVectorStore()

    # Create retriever
    retriever = EducationalRetriever(
        vector_store=vector_store,
        embedder=embedder,
    )

    # Create generator
    gen_config = GenerationConfig(
        max_tokens=4096,
        temperature=0.7,
    )
    generator = QwenGenerator(config=gen_config)

    # Create planner
    planner = LessonPlanner(
        retriever=retriever,
        generator=generator,
    )

    # Generate lesson
    lesson = await planner.generate_lesson(
        topic="Understanding Fractions",
        learning_objective="Students will understand fractions as parts of a whole",
        grade="3",
        subject="Mathematics",
        duration=50,
        teaching_style="balanced",
    )

    # Save to file
    with open("lesson_plan.md", "w") as f:
        f.write(lesson.markdown_content)

    print(f"Lesson generated!")
    print(f"Sources: {lesson.sources_count}")
    print(f"Images: {lesson.images_count}")

# Run
asyncio.run(generate_lesson())
```

## Running Integration Tests

### Run All Tests (Excluding Integration)

```bash
pytest -v
```

### Run Integration Tests Only

```bash
pytest -v -m integration tests/integration/
```

### Run Specific Integration Test

```bash
pytest -v tests/integration/test_lesson_plan_e2e.py::TestLessonPlanEndToEnd::test_complete_lesson_generation_workflow
```

### Expected Output

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

## Troubleshooting

### Issue: Model Download Fails

**Solution**:
```bash
# Check internet connection
# Manually download models
python -c "from transformers import AutoModel; AutoModel.from_pretrained('jinaai/jina-embeddings-v4')"
```

### Issue: Out of Memory

**Solution**:
- Close other applications
- Use smaller batch sizes:
  ```python
  embedder.encode_text(texts, batch_size=4)  # Reduce from 8
  ```

### Issue: Generation Takes Too Long

**Solution**:
- Check if MPS acceleration is working:
  ```python
  import torch
  print(torch.backends.mps.is_available())  # Should be True
  ```
- Reduce `max_tokens`:
  ```python
  gen_config = GenerationConfig(max_tokens=2048)
  ```

### Issue: No Materials Retrieved

**Solution**:
- Verify materials were ingested:
  ```python
  vector_store.get_collection_stats("educational_content")
  ```
- Check metadata filters match your content
- Try removing filters (grade/subject) temporarily

### Issue: Citations Missing

**Solution**:
- This is an LLM output issue
- The system prompt emphasizes citations
- Try regenerating with a different `temperature` (0.5-0.9)

## API Reference

### POST /api/lesson-plan/generate

Generate a lesson plan.

**Request Body**:
```typescript
{
  topic: string;              // 1-200 characters
  learning_objective: string; // 1-500 characters
  grade_level: string;        // K, 1-12, 3-5, 6-8, 9-12, College
  subject: string;            // Any subject
  duration_minutes?: number;  // 20-90, default: 50
  teaching_style?: string;    // balanced, direct, inquiry, project
}
```

**Response**:
```typescript
{
  markdown: string;              // Complete lesson in markdown
  metadata: {
    title: string;
    grade: string;
    subject: string;
    duration: number;
  };
  sources_count: number;         // Number of sources cited
  images_count: number;          // Number of images included
  generation_time_seconds: float; // Time taken
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid request (bad grade, duration, etc.)
- `500`: Server error (no materials, generation failed)

### PATCH /api/lessons/{lesson_id}

Update an existing saved lesson with partial updates.

**Path Parameters**:
- `lesson_id` (integer): The ID of the lesson to update

**Request Body** (all fields optional):
```typescript
{
  markdown_content?: string;   // 1-100,000 characters
  title?: string;              // 1-500 characters
  duration_minutes?: number;   // 20-90 minutes
  teaching_style?: string;     // balanced, direct, inquiry, project
  learning_objective?: string; // 1-500 characters
}
```

**Response**:
```typescript
{
  id: number;
  lesson_id: string;
  title: string;
  markdown_content: string;
  grade: string;              // Read-only
  subject: string;            // Read-only
  topic: string;              // Read-only
  learning_objective: string;
  duration_minutes: number;
  teaching_style: string;
  metadata_json: object | null;
  sources_count: number;      // Read-only
  images_count: number;       // Read-only
  is_favorite: boolean;
  created_at: string;         // ISO 8601 timestamp (read-only)
  updated_at: string;         // ISO 8601 timestamp (auto-updated)
}
```

**Status Codes**:
- `200`: Success - Lesson updated
- `400`: Bad Request - No fields provided to update
- `404`: Not Found - Lesson with given ID does not exist
- `422`: Validation Error - Invalid field values

**Notes**:
- Only provided fields will be updated (partial update)
- `grade`, `subject`, and `topic` cannot be changed (core identifiers)
- `updated_at` timestamp is automatically set
- `created_at` timestamp is immutable

### Validation Rules

#### Lesson Generation
- **Grade Level**: Must be one of: K, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 3-5, 6-8, 9-12, College
- **Duration**: 20-90 minutes (default: 50)
- **Teaching Style**: balanced, direct, inquiry, project
- **Topic**: 1-200 characters
- **Learning Objective**: 1-500 characters

#### Lesson Editing
- **Title**: 1-500 characters
- **Markdown Content**: 1-100,000 characters
- **Duration**: 20-90 minutes
- **Teaching Style**: balanced, direct, inquiry, project
- **Learning Objective**: 1-500 characters
- **Read-Only Fields**: grade, subject, topic, sources_count, images_count, created_at

## Advanced Configuration

### Customize Retrieval

```python
retriever = EducationalRetriever(
    vector_store=vector_store,
    embedder=embedder,
    text_collection="educational_content",
    image_collection="educational_images",
)

# Retrieve more materials for complex topics
planner = LessonPlanner(
    retriever=retriever,
    generator=generator,
    text_top_k=10,  # Retrieve top-10 instead of 5
    image_top_k=5,   # Retrieve top-5 images
)
```

### Customize Generation

```python
gen_config = GenerationConfig(
    max_tokens=6000,     # Longer lessons
    temperature=0.9,     # More creative
    top_p=0.95,
    enable_thinking=False,
)
generator = QwenGenerator(config=gen_config)
```

## Best Practices

### Content Organization

1. **Use descriptive filenames** with grade and subject
2. **Include variety**: textbooks, activities, visual aids
3. **Quality over quantity**: 5-10 high-quality documents per topic
4. **Update regularly**: Add new materials as curriculum evolves

### Lesson Generation

1. **Be specific** in learning objectives
2. **Match grade level** to your materials
3. **Review and edit**: AI-generated lessons should be reviewed
4. **Iterate**: Regenerate if first result isn't perfect
5. **Save good examples**: Build a library of quality lessons

### Performance Optimization

1. **Batch ingestion**: Upload multiple files at once
2. **Use collections**: Separate content by subject or grade
3. **Monitor performance**: Track generation times
4. **Cache common topics**: Generate frequently-used lessons ahead of time

## Support and Resources

- **Documentation**: [LESSON_MARKDOWN_FORMAT.md](./LESSON_MARKDOWN_FORMAT.md)
- **POC Summary**: [LESSON_PLAN_POC_COMPLETE.md](./LESSON_PLAN_POC_COMPLETE.md)
- **Integration Tests**: `tests/integration/test_lesson_plan_e2e.py`
- **Sample Materials**: `tests/integration/sample_materials/`

## Next Steps

After completing this setup:

1. ✅ Ingest your educational materials
2. ✅ Generate your first lesson plan
3. ✅ Review and refine the output
4. ✅ Share with teachers for feedback
5. ✅ Iterate on prompts and materials

**Ready to generate amazing lesson plans!** 🎓✨
