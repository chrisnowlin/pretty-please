# Tasks for add-image-upload-query

## Phase 1: Backend Image Ingestion Pipeline

### 1. Extend supported formats and validation
- [x] Add image extensions (.png, .jpg, .jpeg, .webp, .gif, .bmp) to SUPPORTED_FORMATS in app.py
- [x] Update file validation to check image-specific constraints (max dimensions, max file size)
- [x] Add MIME type validation for uploaded image files
- [x] Update /api/ingest/supported-formats endpoint to list image formats with specific limits
- [ ] Write tests for format validation with various image types

### 2. Implement ImageLoader for ingestion pipeline
- [x] Create ImageLoader class in src/jina_rag_pipeline/ingestion/loaders.py
- [x] Implement load() method using existing ImageProcessor
- [x] Add supports() method to match image file extensions
- [x] Handle image loading errors (corrupted files, unsupported formats)
- [x] Extract and preserve EXIF metadata (dimensions, camera info, timestamp)
- [ ] Write unit tests for ImageLoader with various image formats

### 3. Add image embedding generation to ingestion
- [x] Extend TaskManager in src/jina_rag_pipeline/api/tasks.py to detect image files
- [x] Route image files to embedder.encode_image() instead of encode_text()
- [x] Handle batch processing of mixed text and image files
- [x] Add error handling for vision encoder failures
- [ ] Track image-specific processing metrics (encoding time, memory usage)
- [ ] Write integration tests for image ingestion workflow

### 4. Implement thumbnail generation
- [x] Create thumbnail generation utility in src/jina_rag_pipeline/multimodal/thumbnails.py
- [x] Generate 256x256 thumbnails with aspect ratio preservation
- [x] Implement efficient caching strategy (content-addressed filenames)
- [x] Store thumbnails in collection-specific directories (./thumbnails/{collection}/)
- [x] Add thumbnail generation to async task pipeline
- [x] Handle thumbnail regeneration for missing files
- [ ] Write tests for thumbnail generation with various sizes/formats

### 5. Extend storage metadata for images
- [x] Update ChromaDB metadata schema to include image properties (width, height, format, file_size)
- [x] Store original image file paths and thumbnail paths in metadata
- [x] Add image statistics (mean RGB, color distribution) to metadata
- [x] Ensure metadata is queryable for filtering (e.g., images >1000px wide)
- [ ] Write tests for metadata storage and retrieval

## Phase 2: Image Search API Endpoints

### 6. Add image search endpoint
- [ ] Create POST /api/search/image endpoint in app.py
- [ ] Accept multipart/form-data with image file or base64-encoded image
- [ ] Implement image encoding using embedder.encode_image()
- [ ] Perform similarity search in vector store
- [ ] Return results with image metadata and thumbnail URLs
- [ ] Add modality filter parameter (images only, text only, mixed)
- [ ] Write endpoint tests with various query types

### 7. Implement thumbnail and image retrieval endpoints
- [x] Create GET /api/images/thumbnail/{collection}/{image_id} endpoint
- [x] Create GET /api/images/full/{collection}/{image_id} endpoint
- [x] Set appropriate Content-Type headers (image/png, image/jpeg, etc.)
- [x] Add cache headers (Cache-Control, ETag) for efficient browser caching
- [x] Handle missing image/thumbnail cases with 404 responses
- [ ] Add rate limiting to prevent abuse
- [ ] Write tests for image retrieval and caching behavior

### 8. Extend search endpoint for mixed modality
- [x] Update POST /api/search to support modality filters
- [x] Add result_type field to SearchResult model ("text" or "image")
- [x] Include thumbnail_url in response for image results
- [x] Implement unified ranking for mixed text/image results
- [ ] Add query parameter for image-only or text-only filtering
- [ ] Write tests for mixed modality search scenarios

### 9. Update API models for image support
- [x] Add ImageMetadata model in src/jina_rag_pipeline/api/models.py
- [x] Extend SearchResult to include optional image_metadata field
- [x] Add thumbnail_url and full_image_url fields
- [ ] Update IngestionResponse to distinguish image vs text files
- [ ] Update OpenAPI documentation with new models and endpoints
- [ ] Write schema validation tests

## Phase 3: Frontend Image Upload Interface

### 10. Extend UploadZone for image preview
- [ ] Detect image files in frontend/src/components/ingestion/UploadZone.tsx
- [ ] Generate client-side preview thumbnails using FileReader API
- [ ] Display image thumbnails in upload queue (grid layout)
- [ ] Show image metadata (dimensions, size) below each thumbnail
- [ ] Add visual indicator for image vs document files (icon overlay)
- [ ] Implement remove button for each queued image
- [ ] Add drag-and-drop visual feedback for images
- [ ] Write component tests for image preview functionality

### 11. Add image validation in frontend
- [ ] Validate image file types before upload (check MIME type)
- [ ] Check image file size against backend limits
- [ ] Display user-friendly error messages for invalid images
- [ ] Prevent upload of corrupted or malformed image files
- [ ] Add loading indicator while generating previews
- [ ] Write validation tests for various scenarios

### 12. Update ProgressTracker for images
- [ ] Show thumbnail in ProgressTracker for image files
- [ ] Display image-specific processing stages (validation → embedding → thumbnail → complete)
- [ ] Add visual progress overlay on image thumbnails
- [ ] Show image dimensions and format in progress details
- [ ] Handle errors with image preview (show broken image icon)
- [ ] Write tests for image progress tracking

## Phase 4: Frontend Image Search Interface

### 13. Add image query mode to SearchBar
- [ ] Create "Search by Image" button in frontend/src/components/search/SearchBar.tsx
- [ ] Implement file picker for image selection
- [ ] Display selected image thumbnail in search bar
- [ ] Add "Clear" button to remove image query
- [ ] Implement paste-from-clipboard for images
- [ ] Encode image to base64 or use FormData for upload
- [ ] Write tests for image query interactions

### 14. Create ImageResultCard component
- [ ] Create frontend/src/components/search/ImageResultCard.tsx
- [ ] Display thumbnail with hover zoom effect
- [ ] Show relevance score overlay on thumbnail
- [ ] Display image metadata (dimensions, format) in card footer
- [ ] Add "Find Similar" button for query-by-example
- [ ] Add "Download" button for full-size image
- [ ] Implement modal viewer for full-size preview
- [ ] Write component tests for image result display

### 15. Implement mixed results display
- [ ] Update ResultsList to handle both text and image results
- [ ] Add visual indicators (icons, background colors) for result types
- [ ] Implement filter controls (All / Text Only / Images Only)
- [ ] Create responsive grid layout for image results
- [ ] Maintain list layout for text results
- [ ] Add smooth transitions when switching filters
- [ ] Write tests for mixed results rendering

### 16. Add image grid view mode
- [ ] Create grid view toggle button in search results header
- [ ] Implement masonry grid layout for images (varying aspect ratios)
- [ ] Maintain list view for text results below grid
- [ ] Add lazy loading for image thumbnails (intersection observer)
- [ ] Implement responsive breakpoints (1-4 columns based on screen width)
- [ ] Preserve view mode preference in local storage
- [ ] Write tests for grid view interactions

## Phase 5: Image API Client Extensions

### 17. Extend API client for image operations
- [ ] Add searchByImage() method to frontend/src/services/api.ts
- [ ] Add getThumbnail() method with URL generation
- [ ] Add getFullImage() method with URL generation
- [ ] Update search() method to handle modality filters
- [ ] Implement image upload with progress tracking
- [ ] Add error handling for image-specific failures
- [ ] Write API client tests

### 18. Add TypeScript types for image data
- [ ] Create ImageMetadata interface in api.ts
- [ ] Extend SearchResult to include image_metadata field
- [ ] Add ImageSearchRequest interface
- [ ] Update IngestionStatusResponse for image files
- [ ] Add ResultType enum ("text" | "image")
- [ ] Ensure type safety across all image operations

## Phase 6: Integration and Testing

### 19. End-to-end testing for image workflow
- [ ] Test complete flow: upload image → wait for ingestion → search by text → view results
- [ ] Test image-to-image search workflow
- [ ] Test mixed results display with various filters
- [ ] Verify thumbnail loading and caching behavior
- [ ] Test with large batches of images (100+ files)
- [ ] Validate memory usage during image processing
- [ ] Test error scenarios (corrupted images, network failures)

### 20. Performance optimization
- [ ] Benchmark image encoding latency on M4 Max
- [ ] Optimize thumbnail generation (use threading/multiprocessing)
- [ ] Implement progressive loading for search results
- [ ] Add CDN-style caching for thumbnails
- [ ] Optimize image metadata extraction
- [ ] Profile and fix any memory leaks in image pipeline
- [ ] Achieve <500ms latency target for image search

### 21. Documentation and examples
- [ ] Update README with image upload instructions
- [ ] Create example notebook demonstrating image search
- [ ] Document image format requirements and limitations
- [ ] Add troubleshooting guide for common image issues
- [ ] Create user guide for query-by-image feature
- [ ] Record demo video of image search workflow

## Dependencies and Parallelization

### Critical Path
- Tasks 1-5 (Backend ingestion) must complete before tasks 10-12 (Frontend upload)
- Tasks 6-9 (Search API) must complete before tasks 13-16 (Search UI)
- Tasks 17-18 (API client) depend on tasks 6-9

### Parallelizable Work
- Phase 1 (Backend ingestion) and Phase 3 (Frontend upload) can start simultaneously
- Phase 2 (Search API) and Phase 4 (Search UI) can progress in parallel after Phase 1
- Tasks 10-12 (Upload UI) and tasks 13-16 (Search UI) are independent
- Documentation (task 21) can be written throughout implementation

### Cross-Team Coordination
- Frontend and backend teams should align on API contracts before starting Phase 2/4
- Share example images and expected results for testing
- Coordinate on metadata schema and thumbnail URL format
