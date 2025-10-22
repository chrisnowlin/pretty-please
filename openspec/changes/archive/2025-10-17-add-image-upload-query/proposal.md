# Add Image Uploading and Querying Capabilities

## Summary
Extend the RAG pipeline to fully support image uploads and cross-modal querying, enabling users to upload images through the web UI and query them using text, other images, or visual documents. This builds on the existing multimodal foundation to provide a complete image-centric workflow.

## Problem Statement
While the system has multimodal embeddings infrastructure (Jina v4's visual encoder, image processing utilities), users currently cannot:
- Upload images directly through the web UI
- Search for images using text queries
- Search for text documents using image queries
- View images in search results
- Process image-heavy documents efficiently

The current ingestion pipeline only supports text-based formats (.txt, .pdf, .md, .json, .csv), leaving image capabilities unused despite the underlying technology being ready.

## Proposed Solution
Implement comprehensive image support across all system layers:

1. **Backend Extensions**:
   - Add image formats (.png, .jpg, .jpeg, .webp, .gif, .bmp) to supported upload formats
   - Implement image ingestion pipeline using existing ImageProcessor and encode_image
   - Add image-specific metadata extraction (dimensions, format, color statistics)
   - Create image search endpoint supporting text-to-image and image-to-image queries
   - Add thumbnail generation for efficient UI display

2. **Frontend Extensions**:
   - Support image upload in drag-and-drop zone with preview
   - Display image thumbnails in upload queue and progress tracker
   - Add image preview in search results with metadata overlay
   - Implement image query mode (upload image to search)
   - Show visual indicators for image vs text documents

3. **Cross-Modal Query Interface**:
   - Unified search that automatically detects query type (text or image)
   - Mixed results display showing both text and image matches
   - Query-by-example: click on any result image to find similar items

## Success Criteria
- Users can upload images (.png, .jpg, .jpeg, .webp) through the web UI
- Images are automatically processed and embedded using Jina v4's vision encoder
- Text queries return relevant images ranked by semantic similarity
- Image queries return semantically similar images and related text
- Search results display image thumbnails with metadata (dimensions, format, relevance score)
- Performance: 100+ images can be ingested in a single batch without memory issues
- End-to-end latency: <500ms for image search queries on M4 Max

## Scope
### In Scope
- Image upload support in web UI and API
- Image ingestion pipeline (load → process → embed → store)
- Text-to-image semantic search
- Image-to-image similarity search
- Image-to-text cross-modal search
- Thumbnail generation and storage
- Image metadata extraction and display
- Mixed result presentation (images + text)
- Image format validation and conversion

### Out of Scope
- Image annotation or labeling interface (future enhancement)
- Image editing capabilities
- Optical Character Recognition (OCR) for text extraction from images
- Video processing or frame extraction
- 3D model or point cloud support
- Image generation or synthesis
- Advanced image preprocessing (beyond resizing/normalization)

## Technical Approach
### Backend
- Extend `SUPPORTED_FORMATS` to include image extensions
- Add `ImageLoader` to `loaders.py` using existing `ImageProcessor`
- Modify `TaskManager` to handle image files using `encode_image` method
- Add `/api/search/image` endpoint for image-based queries
- Implement thumbnail generation using PIL and store alongside embeddings
- Update ChromaDB metadata schema to include image properties

### Frontend
- Extend `UploadZone` to show image previews for selected files
- Add image thumbnail display in `ProgressTracker` component
- Create `ImageResultCard` component for displaying image search results
- Add image upload button/mode in `SearchBar` for query-by-image
- Implement modal viewer for full-size image preview
- Update API client to handle image uploads and base64 encoding

### Storage
- Store original images in collection-specific subdirectories
- Generate and cache thumbnails (256x256) for UI display
- Include image file path in metadata for retrieval
- Maintain existing text document storage patterns

## Dependencies
- Existing multimodal infrastructure (JinaEmbeddingsV4.encode_image)
- ImageProcessor utilities already implemented
- Frontend upload infrastructure from add-frontend-ui
- ChromaDB metadata storage capabilities

## Risks and Mitigations
- **Risk**: Large image files (>50MB) may cause upload timeouts or memory pressure
  - **Mitigation**: Implement client-side image compression before upload, enforce file size limits, use streaming uploads for large files

- **Risk**: Thumbnail generation may slow down ingestion pipeline
  - **Mitigation**: Generate thumbnails asynchronously after embedding, cache aggressively, use optimized PIL operations

- **Risk**: Mixed text/image results may be confusing to users
  - **Mitigation**: Clear visual indicators (icons, backgrounds) for each result type, separate tabs for text-only vs image-only views

- **Risk**: Image embeddings use more memory than text embeddings
  - **Mitigation**: Leverage existing batch processing infrastructure, implement progressive loading for large image sets

- **Risk**: Cross-modal search quality may vary significantly
  - **Mitigation**: Expose search quality metrics, allow users to filter by modality, provide feedback mechanism

## Implementation Phases
1. **Phase 1**: Backend image ingestion (API endpoints, loaders, processing)
2. **Phase 2**: Frontend image upload UI (previews, progress, validation)
3. **Phase 3**: Image search implementation (text-to-image, image-to-image)
4. **Phase 4**: Mixed results display and thumbnail optimization
5. **Phase 5**: Testing, performance tuning, and documentation
