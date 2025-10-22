## Context
Jina Embeddings v4 is built on Qwen2.5-VL-3B, providing native vision-language understanding. This enables processing of images, PDFs with visuals, charts, and diagrams alongside text.

## Goals / Non-Goals
- Goals:
  - Support image embedding generation
  - Enable cross-modal search capabilities
  - Process visual documents with layout awareness
  - Implement both dense and multi-vector approaches
  - Maintain unified search interface
- Non-Goals:
  - Video processing
  - Real-time image generation
  - Complex image editing/manipulation
  - OCR as primary text extraction (nice-to-have)

## Decisions
- Decision: Use native Jina v4 visual encoder
  - Rationale: Already included in model, no extra dependencies
- Decision: Store images as file references, not in vector DB
  - Rationale: Vector DBs not optimized for binary data
- Decision: Implement both dense and multi-vector modes
  - Rationale: Different use cases benefit from each approach
- Alternatives considered:
  - CLIP: Separate model, additional memory overhead
  - OCR-first approach: Loses visual context
  - Image-only DB: Splits the search experience

## Risks / Trade-offs
- Image processing is memory intensive → Implement batch size limits
- Large images slow down inference → Add resolution limits
- Multi-vector search is complex → Start with dense, add multi-vector later

## Migration Plan
- Extends existing embeddings capability
- Backward compatible with text-only pipelines
- Gradual rollout: dense first, then multi-vector

## Open Questions
- Should we support video frames as images?
- What's the optimal image resolution for embeddings?
- Should OCR be mandatory or optional?