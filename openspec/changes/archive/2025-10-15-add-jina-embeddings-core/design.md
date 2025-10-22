## Context
The Jina Embeddings v4 model is a 4B parameter multimodal model based on Qwen2.5-VL-3B. Running this efficiently on Apple Silicon requires careful memory management and proper MPS backend configuration.

## Goals / Non-Goals
- Goals:
  - Efficient model loading and inference on M4 Max
  - Support all three task adapters (retrieval, text-matching, code)
  - Lazy loading to minimize memory footprint
  - Proper caching to avoid repeated downloads
- Non-Goals:
  - Image/visual processing (separate multimodal feature)
  - API endpoints (handled by query interface)
  - Batch optimization (separate feature)

## Decisions
- Decision: Use PyTorch MPS backend instead of CUDA
  - Rationale: Native Apple Silicon acceleration
- Decision: Implement lazy loading pattern
  - Rationale: 4B parameters require ~8-16GB memory; avoid loading until needed
- Decision: Use Hugging Face transformers directly
  - Rationale: Official implementation, best compatibility
- Alternatives considered:
  - MLX framework: Less mature, limited transformer support
  - ONNX conversion: Loses task adapter flexibility
  - Jina API: Requires internet, adds latency

## Risks / Trade-offs
- MPS may have compatibility issues with some operations → Fallback to CPU if needed
- Model size requires significant memory → Implement memory monitoring
- First load will be slow due to download → Clear user feedback needed

## Migration Plan
N/A - Greenfield implementation

## Open Questions
- Should we pre-download the model during setup?
- What's the optimal default embedding dimension for our use case?