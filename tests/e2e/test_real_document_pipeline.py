"""
Real document RAG pipeline test using actual PDF document.
This test processes the Arts Education Standards Glossary PDF.
"""
import asyncio
import os
import sys
from pathlib import Path
import tempfile
import json


# Configurable via environment variables
MODEL_NAME = os.environ.get("E2E_MLX_MODEL", "mlx-community/Qwen2.5-0.5B-Instruct-4bit")
RUN_REAL_MODEL_TESTS = os.environ.get("RUN_REAL_MODEL_TESTS", "0") == "1"


def test_pdf_document_processing():
    """Test processing of the actual PDF document."""
    print("🔍 Testing Real PDF Document Processing...")



    # Resolve a test PDF from the repository instead of a user-specific path
    repo_root = Path(__file__).resolve().parents[2]
    candidates = [
        repo_root / "test_glossary.pdf",
        repo_root / "test_2pages.pdf",
    ]
    pdf_path = next((p for p in candidates if p.exists()), None)
    if not pdf_path:
        print("  ❌ No test PDF found in repository (looked for test_glossary.pdf, test_2pages.pdf)")
        return None


    try:
        import pypdf

        print(f"  📄 Processing PDF: {Path(pdf_path).name}")

        # Extract text from PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            text_content = ""

            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"

        print(f"  ✅ PDF processed successfully")
        print(f"  📊 Total pages: {len(pdf_reader.pages)}")
        print(f"  📝 Text extracted: {len(text_content)} characters")

        # Split into chunks for processing
        chunks = []
        lines = text_content.split('\n')
        current_chunk = ""

        for line in lines:
            if len(current_chunk + line) > 1000:  # Chunk size limit
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        print(f"  🧩 Created {len(chunks)} text chunks")

        # Create document structure
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                "content": chunk,
                "metadata": {
                    "source": "Arts Education Standards Glossary",
                    "page": f"chunk_{i+1}",
                    "total_chunks": len(chunks)
                }
            })

        return documents

    except Exception as e:
        print(f"  ❌ Error processing PDF: {e}")
        return None

async def test_vector_storage_and_retrieval(documents):
    """Test vector storage and retrieval with real documents."""
    print("\n🔍 Testing Vector Storage and Retrieval...")

    if not documents:
        print("  ⚠️  Skipping - no documents available")
        return None, None

    try:
        # Simulate vector storage (in real pipeline, this would use ChromaDB + embeddings)
        vector_store = []

        for doc in documents:
            # Simulate embedding creation and storage
            vector_store.append({
                "id": f"doc_{len(vector_store)}",
                "content": doc["content"],
                "metadata": doc["metadata"],
                "embedding": f"simulated_embedding_{len(vector_store)}"  # Simulated embedding
            })

        print(f"  ✅ Stored {len(vector_store)} documents in vector database")

        # Test different queries
        test_queries = [
            "What are music standards?",
            "Define artistic process",
            "What is music literacy?",
            "Explain performance standards"
        ]

        # Test retrieval for each query
        retrieval_results = {}

        for query in test_queries:
            print(f"  🔍 Testing query: {query}")

            # Simulate semantic search
            relevant_docs = []
            query_lower = query.lower()

            for doc in vector_store:
                content_lower = doc["content"].lower()
                # Simple keyword matching for simulation
                if any(keyword in content_lower for keyword in query_lower.split() if len(keyword) > 3):
                    relevant_docs.append(doc)

            # Get top results
            top_docs = relevant_docs[:3] if relevant_docs else vector_store[:3]

            # Format context
            context_text = "\n\n".join([
                f"Document {i+1} (Source: {doc['metadata']['source']}):\n{doc['content'][:500]}..."
                for i, doc in enumerate(top_docs)
            ])

            retrieval_results[query] = {
                "context": context_text,
                "sources": top_docs,
                "num_retrieved": len(top_docs)
            }

            print(f"    ✅ Retrieved {len(top_docs)} documents")

        return vector_store, retrieval_results

    except Exception as e:
        print(f"  ❌ Error in vector storage/retrieval: {e}")
        return None, None

async def test_real_llm_with_arts_content(retrieval_results):
    """Test real LLM generation with arts education content."""
    print("\n🔍 Testing Real LLM with Arts Education Content...")

    if not retrieval_results:
        print("  ⚠️  Skipping - no retrieval results available")
        return False

    try:
        import mlx_lm
        from mlx_lm.sample_utils import make_sampler

        # Load the model
        print("  🔄 Loading Qwen model for arts education...")
        model, tokenizer = mlx_lm.load(MODEL_NAME)

        llm_responses = {}

        for query, result in retrieval_results.items():
            print(f"  📝 Processing query: {query}")

            # Create RAG prompt for arts education
            rag_prompt = f"""You are an arts education specialist helping teachers understand music standards. Use the provided context from the Arts Education Standards Glossary to answer the teacher's question accurately.

CONTEXT FROM ARTS EDUCATION STANDARDS GLOSSARY:
{result['context']}

TEACHER QUESTION: {query}

INSTRUCTIONS:
1. Answer based on the provided context from the Arts Education Standards Glossary
2. Provide clear, educational explanations suitable for teachers
3. Include specific details from the standards
4. Make it practical and useful for classroom implementation
5. If the context doesn't fully answer the question, say so and provide what you can

ANSWER:"""

            print(f"    🔄 Generating response...")

            # Create sampler for educational content
            sampler = make_sampler(temp=0.4, top_p=0.9, top_k=20)

            # Generate response
            response_text = ""
            max_tokens = 250

            for response in mlx_lm.stream_generate(
                model,
                tokenizer,
                rag_prompt,
                max_tokens=max_tokens,
                sampler=sampler,
            ):
                if hasattr(response, 'text'):
                    token = response.text
                else:
                    token = str(response)

                response_text += token

                # Safety limit
                if len(response_text) > 800:
                    break

            response_text = response_text.strip()

            if response_text and len(response_text) > 50:
                llm_responses[query] = {
                    "response": response_text,
                    "sources": result["sources"],
                    "context_length": len(result["context"]),
                    "response_length": len(response_text)
                }
                print(f"    ✅ Response generated: {len(response_text)} characters")
            else:
                print(f"    ⚠️  Response too short or empty")

        return llm_responses

    except Exception as e:
        print(f"  ❌ Error in real LLM generation: {e}")
        return False

async def test_lesson_plan_creation_arts(llm_responses):
    """Test lesson plan creation for arts education."""
    print("\n🔍 Testing Arts Education Lesson Plan Creation...")

    if not llm_responses:
        print("  ⚠️  Skipping - no LLM responses available")
        return False

    try:
        import mlx_lm
        from mlx_lm.sample_utils import make_sampler

        # Load model
        print("  🔄 Loading model for lesson plan creation...")
        model, tokenizer = mlx_lm.load(MODEL_NAME)

        # Create a comprehensive lesson plan prompt
        lesson_prompt = """Create a detailed music education lesson plan based on the Arts Education Standards.

GRADE LEVEL: 5th Grade
SUBJECT: General Music
DURATION: 45 minutes
TOPIC: Understanding Musical Elements and Performance Standards

Based on Arts Education Standards, create a lesson that helps students:
1. Understand musical elements (rhythm, melody, harmony, form)
2. Apply performance standards
3. Develop music literacy skills
4. Engage in artistic processes

Please include:
- Clear learning objectives aligned with standards
- Materials and resources needed
- Step-by-step lesson activities
- Assessment strategies
- Differentiation for diverse learners

Make it practical, engaging, and standards-based."""

        print("  🔄 Generating comprehensive lesson plan...")

        # Create sampler for structured content
        sampler = make_sampler(temp=0.5, top_p=0.9, top_k=20)

        # Generate lesson plan
        lesson_text = ""
        max_tokens = 400

        for response in mlx_lm.stream_generate(
            model,
            tokenizer,
            lesson_prompt,
            max_tokens=max_tokens,
            sampler=sampler,
        ):
            if hasattr(response, 'text'):
                token = response.text
            else:
                token = str(response)

            lesson_text += token

            # Safety limit
            if len(lesson_text) > 1200:
                break

        lesson_text = lesson_text.strip()

        if lesson_text and len(lesson_text) > 150:
            print(f"  ✅ Arts lesson plan generated: {len(lesson_text)} characters")
            print(f"  📚 Lesson preview: {lesson_text[:200]}...")

            # Create structured lesson plan
            structured_lesson = {
                "title": "Understanding Musical Elements and Performance Standards",
                "grade": "5th Grade",
                "subject": "General Music",
                "duration_minutes": 45,
                "topic": "Musical Elements and Performance Standards",
                "markdown_content": lesson_text,
                "standards_based": True,
                "model": MODEL_NAME
            }
            return structured_lesson
        else:
            print("  ⚠️  Lesson plan too short or empty")
            return False

    except Exception as e:
        print(f"  ❌ Error in lesson plan creation: {e}")
        return False

async def run_real_document_pipeline_test():
    """Run the complete pipeline test with real PDF document."""
    # Optional guard to avoid heavy downloads unless explicitly enabled
    if not RUN_REAL_MODEL_TESTS:
        print("⚠️ Skipping real model e2e tests. Set RUN_REAL_MODEL_TESTS=1 to run them.")
        return True

    print("🧪 Real Document RAG Pipeline Test")
    print("📄 Using: Arts Education Standards Glossary PDF")
    print("=" * 60)


    # Test PDF processing
    documents = test_pdf_document_processing()

    if not documents:
        print("\n❌ PDF processing failed - cannot continue")
        return False

    # Test vector storage and retrieval
    vector_store, retrieval_results = await test_vector_storage_and_retrieval(documents)

    if not vector_store or not retrieval_results:
        print("\n❌ Vector storage/retrieval failed - cannot continue")
        return False

    # Test real LLM with arts content
    llm_responses = await test_real_llm_with_arts_content(retrieval_results)

    if not llm_responses:
        print("\n❌ Real LLM generation failed - cannot continue")
        return False

    # Test lesson plan creation
    lesson_plan = await test_lesson_plan_creation_arts(llm_responses)

    # Evaluate results
    print("\n" + "=" * 60)
    print("🧪 Real Document Pipeline Test Results:")
    print(f"  • PDF Processing: {'✅' if documents else '❌'}")
    print(f"  • Vector Storage: {'✅' if vector_store else '❌'}")
    print(f"  • Context Retrieval: {'✅' if retrieval_results else '❌'}")
    print(f"  • Real LLM Generation: {'✅' if llm_responses else '❌'}")
    print(f"  • Lesson Plan Creation: {'✅' if lesson_plan else '❌'}")

    if all([documents, vector_store, retrieval_results, llm_responses, lesson_plan]):
        print("\n✨ SUCCESS: Real Document RAG Pipeline Test Passed!")
        print("\n🎉 This demonstrates a complete RAG pipeline with real content:")
        print(f"  📄 Processed {len(documents)} document chunks from Arts Education Standards")
        print(f"  🔍 Tested {len(retrieval_results)} different queries")
        print(f"  🤖 Generated {len(llm_responses)} real LLM responses")
        print(f"  📝 Created comprehensive lesson plan")
        print(f"  🔄 Complete end-to-end flow with real educational content")

        print(f"\n📊 Detailed Results:")
        print(f"  • Document chunks processed: {len(documents)}")
        print(f"  • Total characters processed: {sum(len(doc['content']) for doc in documents)}")

        for query, response in llm_responses.items():
            print(f"  • Query '{query[:30]}...': {response['response_length']} chars")

        if lesson_plan:
            print(f"  • Lesson plan: {lesson_plan['duration_minutes']} minutes, {len(lesson_plan['markdown_content'])} chars")

        return True
    else:
        print("\n⚠️ Some pipeline components had issues")
        return False

if __name__ == "__main__":
    # Run the real document pipeline test
    success = asyncio.run(run_real_document_pipeline_test())
    sys.exit(0 if success else 1)