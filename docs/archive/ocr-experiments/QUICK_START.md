# Quick Start - Lesson Plan Generation

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies

```bash
# Backend
pip install -e ".[dev]"

# Frontend (optional)
cd frontend && npm install && cd ..
```

### 2. Start the Server

```bash
python -m uvicorn src.jina_rag_pipeline.api.app:app --reload
```

### 3. Generate Your First Lesson

#### Option A: Using the API

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

#### Option B: Using Python

```python
import asyncio
from src.jina_rag_pipeline.embeddings import JinaEmbeddingsV4
from src.jina_rag_pipeline.storage import ChromaVectorStore
from src.jina_rag_pipeline.retrieval.educational import EducationalRetriever
from src.jina_rag_pipeline.generation import LessonPlanner, QwenGenerator
from src.jina_rag_pipeline.generation.config import GenerationConfig

async def main():
    # Initialize
    embedder = JinaEmbeddingsV4()
    vector_store = ChromaVectorStore()
    retriever = EducationalRetriever(vector_store, embedder)
    generator = QwenGenerator(GenerationConfig())
    planner = LessonPlanner(retriever, generator)

    # Generate
    lesson = await planner.generate_lesson(
        topic="Understanding Fractions",
        learning_objective="Students will understand fractions",
        grade="3",
        subject="Mathematics",
    )

    # Save
    with open("lesson.md", "w") as f:
        f.write(lesson.markdown_content)

    print(f"✓ Lesson generated with {lesson.sources_count} sources!")

asyncio.run(main())
```

### 4. Run Tests

```bash
# Unit tests (fast)
pytest -v -m "not integration"

# Integration tests (requires models, slower)
pytest -v -m integration tests/integration/
```

---

## 📚 Documentation

- **[Setup Guide](docs/LESSON_PLAN_SETUP_GUIDE.md)** - Complete installation and usage
- **[Markdown Format](docs/LESSON_MARKDOWN_FORMAT.md)** - Lesson format specification
- **[POC Summary](docs/LESSON_PLAN_POC_COMPLETE.md)** - Implementation details
- **[Phase 1 Complete](PHASE_1_COMPLETE.md)** - Executive summary

---

## ✅ Key Features

- ✅ **Material-Agnostic** - Any grade, any subject
- ✅ **Source Citations** - Automatic [1][2] citations
- ✅ **Image Embedding** - Includes diagrams and visuals
- ✅ **50-Minute Default** - Configurable 20-90 minutes
- ✅ **Abbreviated Grades** - "3", "K", "6-8" format
- ✅ **122 Tests** - Comprehensive test coverage

---

## 🎯 Requirements

### Must Have (for generation to work)

1. **Educational materials** uploaded to vector store
2. **Jina Embeddings v4** model (~8GB, auto-downloaded)
3. **Qwen3-14B-4bit** model (~8GB, auto-downloaded)

### Recommended

- Apple Silicon Mac (for MLX acceleration)
- 16GB+ RAM
- 20GB+ free disk space

---

## 🧪 Sample Materials

Pre-loaded sample materials in `tests/integration/sample_materials/`:

- `Grade3_Math_Fractions_Textbook.txt` - Textbook content
- `Grade3_Math_Activities_Workbook.txt` - Activities and assessments
- `Visual_Aids_Fractions.txt` - Visual models and diagrams

Use these to test the system without uploading your own content.

---

## 🐛 Troubleshooting

### Models not downloading?
```bash
# Manual download
python -c "from transformers import AutoModel; AutoModel.from_pretrained('jinaai/jina-embeddings-v4')"
```

### Out of memory?
```bash
# Close other apps, or reduce batch size in code
embedder.encode_text(texts, batch_size=4)
```

### No materials retrieved?
```bash
# Check if materials were ingested
vector_store.get_collection_stats("educational_content")
```

---

## 📞 Support

- **Integration Tests**: `tests/integration/README.md`
- **API Documentation**: See setup guide
- **Issues**: Check troubleshooting section

---

**Ready to generate amazing lesson plans! 🎓✨**
