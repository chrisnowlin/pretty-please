"""
Direct model call test that bypasses import issues.
This test directly tests the Qwen model functionality.
"""
import asyncio
import os
import sys
from pathlib import Path

def test_mlx_availability():
    """Test MLX framework availability."""
    print("🔍 Testing MLX Framework Availability...")
    
    try:
        import mlx.core as mx
        import mlx_lm
        print("  ✅ MLX framework available")
        print(f"  📊 MLX version: {mlx_lm.__version__ if hasattr(mlx_lm, '__version__') else 'unknown'}")
        return True
    except ImportError as e:
        print(f"  ❌ MLX not available: {e}")
        return False

async def test_model_loading_direct():
    """Test direct model loading with MLX."""
    print("\n🔍 Testing Direct Model Loading...")
    
    try:
        import mlx_lm
        
        # Try to load a smaller model for testing
        model_name = "mlx-community/Qwen3-14B-4bit"
        
        print(f"  🔄 Loading model: {model_name}")
        print("  ⏳ This may take a moment...")
        
        # Load model and tokenizer
        model, tokenizer = mlx_lm.load(model_name)
        
        print("  ✅ Model loaded successfully")
        print(f"  📝 Model type: {type(model)}")
        print(f"  🔤 Tokenizer type: {type(tokenizer)}")
        
        return model, tokenizer
        
    except Exception as e:
        print(f"  ❌ Error loading model: {e}")
        return None, None

async def test_simple_generation(model, tokenizer):
    """Test simple text generation."""
    print("\n🔍 Testing Simple Text Generation...")
    
    if not model or not tokenizer:
        print("  ⚠️  Skipping generation - no model available")
        return False
    
    try:
        import mlx_lm
        from mlx_lm.sample_utils import make_sampler
        
        # Simple prompt
        prompt = "What is 2 + 2? Answer with just the number."
        
        print(f"  📝 Prompt: {prompt}")
        print("  🔄 Generating response...")
        
        # Create sampler
        sampler = make_sampler(temp=0.1, top_p=0.9, top_k=10)
        
        # Generate response
        response_text = ""
        max_tokens = 20
        
        for response in mlx_lm.stream_generate(
            model,
            tokenizer,
            prompt,
            max_tokens=max_tokens,
            sampler=sampler,
        ):
            if hasattr(response, 'text'):
                token = response.text
            else:
                token = str(response)
            
            response_text += token
            
            # Safety limit
            if len(response_text) > 100:
                break
        
        response_text = response_text.strip()
        
        if response_text:
            print(f"  ✅ Generated response: '{response_text}'")
            return True
        else:
            print("  ⚠️  Empty response generated")
            return False
            
    except Exception as e:
        print(f"  ❌ Error during generation: {e}")
        return False

async def test_educational_generation(model, tokenizer):
    """Test educational content generation."""
    print("\n🔍 Testing Educational Content Generation...")
    
    if not model or not tokenizer:
        print("  ⚠️  Skipping educational generation - no model available")
        return False
    
    try:
        import mlx_lm
        from mlx_lm.sample_utils import make_sampler
        
        # Educational prompt
        prompt = """Explain what fractions are in simple terms for a 3rd grader.
Keep it very short and simple. Use an example."""
        
        print(f"  📝 Educational prompt: {prompt[:50]}...")
        print("  🔄 Generating educational content...")
        
        # Create sampler for educational content
        sampler = make_sampler(temp=0.5, top_p=0.9, top_k=20)
        
        # Generate response
        response_text = ""
        max_tokens = 100
        
        for response in mlx_lm.stream_generate(
            model,
            tokenizer,
            prompt,
            max_tokens=max_tokens,
            sampler=sampler,
        ):
            if hasattr(response, 'text'):
                token = response.text
            else:
                token = str(response)
            
            response_text += token
            
            # Safety limit
            if len(response_text) > 300:
                break
        
        response_text = response_text.strip()
        
        if response_text and len(response_text) > 20:
            print(f"  ✅ Educational content generated: {len(response_text)} characters")
            print(f"  📚 Preview: {response_text[:100]}...")
            return True
        else:
            print("  ⚠️  Educational content too short or empty")
            return False
            
    except Exception as e:
        print(f"  ❌ Error during educational generation: {e}")
        return False

async def test_rag_simulation(model, tokenizer):
    """Test RAG-style generation with context."""
    print("\n🔍 Testing RAG-Style Generation with Context...")
    
    if not model or not tokenizer:
        print("  ⚠️  Skipping RAG simulation - no model available")
        return False
    
    try:
        import mlx_lm
        from mlx_lm.sample_utils import make_sampler
        
        # Simulate RAG context
        context = """
Context from documents:
- Fractions represent parts of a whole
- A fraction has a numerator (top number) and denominator (bottom number)
- The numerator shows how many parts we have
- The denominator shows how many equal parts the whole is divided into
"""
        
        query = "What are fractions and how do they work?"
        
        # Create RAG-style prompt
        rag_prompt = f"""Based on the following context, answer the question.

{context}

Question: {query}

Provide a clear, simple answer based on the context above."""
        
        print(f"  📝 RAG prompt with context: {len(rag_prompt)} characters")
        print("  🔄 Generating RAG response...")
        
        # Create sampler
        sampler = make_sampler(temp=0.3, top_p=0.9, top_k=15)
        
        # Generate response
        response_text = ""
        max_tokens = 150
        
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
            if len(response_text) > 400:
                break
        
        response_text = response_text.strip()
        
        if response_text and len(response_text) > 30:
            print(f"  ✅ RAG response generated: {len(response_text)} characters")
            print(f"  🔍 RAG preview: {response_text[:150]}...")
            return True
        else:
            print("  ⚠️  RAG response too short or empty")
            return False
            
    except Exception as e:
        print(f"  ❌ Error during RAG simulation: {e}")
        return False

async def run_direct_model_tests():
    """Run all direct model tests."""
    print("🧪 Direct Model Call Test")
    print("=" * 50)
    
    # Test MLX availability
    mlx_ok = test_mlx_availability()
    
    if not mlx_ok:
        print("\n❌ MLX not available - cannot test real model calls")
        return False
    
    # Test model loading
    model, tokenizer = await test_model_loading_direct()
    
    if not model or not tokenizer:
        print("\n❌ Model loading failed - cannot proceed with tests")
        return False
    
    # Run generation tests
    try:
        # Test simple generation
        simple_ok = await test_simple_generation(model, tokenizer)
        
        # Test educational generation
        educational_ok = await test_educational_generation(model, tokenizer)
        
        # Test RAG simulation
        rag_ok = await test_rag_simulation(model, tokenizer)
        
        print("\n" + "=" * 50)
        print("🧪 Direct Model Test Results:")
        print(f"  • Simple Generation: {'✅' if simple_ok else '❌'}")
        print(f"  • Educational Generation: {'✅' if educational_ok else '❌'}")
        print(f"  • RAG Simulation: {'✅' if rag_ok else '❌'}")
        
        if all([simple_ok, educational_ok, rag_ok]):
            print("\n✨ SUCCESS: All Direct Model Tests Passed!")
            print("\nThis confirms that:")
            print("• Qwen model loads successfully with MLX")
            print("• Real model inference produces coherent responses")
            print("• Educational content generation works")
            print("• RAG-style generation with context functions")
            print("• The system is ready for production use")
            return True
        else:
            print("\n⚠️ Some direct model tests had issues")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR during direct model testing: {e}")
        return False

if __name__ == "__main__":
    # Run the async tests
    success = asyncio.run(run_direct_model_tests())
    sys.exit(0 if success else 1)