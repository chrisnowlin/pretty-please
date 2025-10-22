## Why
Extend the RAG pipeline to support images and visual documents, leveraging Jina v4's multimodal capabilities for richer document understanding and cross-modal search.

## What Changes
- Implement image embedding generation using Jina's visual encoder
- Add image loaders for common formats (PNG, JPG, PDF with images)
- Support cross-modal search (text-to-image, image-to-text)
- Add visual document processing with layout understanding
- Implement multi-vector support for complex documents

## Impact
- Affected specs: multimodal (new), embeddings (modified)
- Affected code: Extends embeddings module, new image processing utilities
- Blocks: None
- Depends on: Core embeddings implementation