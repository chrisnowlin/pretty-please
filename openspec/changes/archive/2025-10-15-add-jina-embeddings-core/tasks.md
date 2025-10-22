## 1. Environment Setup
- [x] 1.1 Install uv package manager
- [x] 1.2 Create Python 3.10+ virtual environment with uv
- [x] 1.3 Create pyproject.toml with core dependencies
- [x] 1.4 Install transformers>=4.52.0, torch>=2.6.0, peft>=0.15.2
- [x] 1.5 Verify MPS backend availability for PyTorch

## 2. Model Implementation
- [x] 2.1 Create embeddings module structure
- [x] 2.2 Implement JinaEmbeddingsV4 class with lazy loading
- [x] 2.3 Add model download and caching from Hugging Face
- [x] 2.4 Implement text encoding with task adapter support
- [x] 2.5 Add dimension truncation support (128-2048)

## 3. Testing and Validation
- [x] 3.1 Create unit tests for embedding generation
- [x] 3.2 Test all three task types (retrieval, text-matching, code)
- [x] 3.3 Validate MPS acceleration is working
- [x] 3.4 Benchmark memory usage and inference speed
- [x] 3.5 Test model caching and reload functionality