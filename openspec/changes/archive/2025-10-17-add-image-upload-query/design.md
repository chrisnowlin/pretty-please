# Design Document: Image Upload and Query Support

## Overview
This document outlines the architectural design for adding comprehensive image support to the Jina RAG Pipeline, enabling users to upload, index, and search images using both text and visual queries.

## Architecture Decisions

### 1. Image Storage Strategy

**Decision**: Separate file storage from vector embeddings with linked metadata.

**Rationale**:
- ChromaDB is optimized for vector storage, not binary data
- Storing images separately enables flexible caching and CDN integration
- Thumbnail generation can be decoupled from embedding generation
- Easier to implement backup and migration strategies

**Implementation**:
```
project_root/
├── uploads/
│   └── {collection_name}/
│       ├── images/
│       │   ├── {uuid}.png
│       │   ├── {uuid}.jpg
│       │   └── ...
│       └── thumbnails/
│           ├── {uuid}_thumb.jpg  (256x256)
│           └── ...
```

**Metadata Linking**:
- Store image file path in ChromaDB metadata: `{"file_path": "uploads/collection/images/{uuid}.png", "thumbnail_path": "uploads/collection/thumbnails/{uuid}_thumb.jpg"}`
- Use UUID-based filenames to avoid collisions
- Maintain index mapping for fast ID → file lookups

### 2. Thumbnail Generation Pipeline

**Decision**: Asynchronous thumbnail generation after embedding

**Rationale**:
- Thumbnail generation (PIL operations) can be slow for large images
- Embedding generation is the critical path for search functionality
- Users can start searching before thumbnails are ready (graceful degradation)

**Flow**:
1. User uploads image → immediate validation
2. Task queued → load image → generate embedding → store in ChromaDB
3. Background task → generate thumbnail → cache to disk → update metadata
4. WebSocket notifies frontend when thumbnail is ready

**Fallback**: If thumbnail missing on request, generate on-demand and cache

### 3. Cross-Modal Search Strategy

**Decision**: Unified embedding space with modality tags in metadata

**Rationale**:
- Jina v4 provides unified embedding space for text and images
- Single similarity search operation across both modalities
- No need for separate indices or complex merging logic
- Enables true cross-modal retrieval (text → images, images → text)

**Implementation**:
```python
# All embeddings (text and image) go into same collection
metadata = {
    "modality": "image",  # or "text"
    "file_type": "png",
    "dimensions": {"width": 1920, "height": 1080},
    ...
}

# Search with optional modality filter
results = vector_store.similarity_search(
    query_embedding=query_emb,
    metadata_filter={"modality": "image"}  # optional
)
```

### 4. Frontend Image Handling

**Decision**: Client-side preview generation with server-side encoding

**Rationale**:
- Client-side previews provide instant feedback without server round-trip
- Server-side encoding ensures consistent embedding quality
- Keeps image encoding logic in Python where it can leverage MPS acceleration

**Implementation**:
- Frontend: Use FileReader API to generate data URLs for preview
- Backend: Accept multipart/form-data or base64-encoded images
- Frontend: Display thumbnails from `/api/images/thumbnail/{id}` endpoint

### 5. Image Search Modes

**Decision**: Three distinct search modes with shared UI

**Modes**:
1. **Text-to-Image**: Text query → image results (using text encoder → similarity search → filter by modality="image")
2. **Image-to-Image**: Image query → similar images (using vision encoder → similarity search → filter by modality="image")
3. **Image-to-Text**: Image query → related text (using vision encoder → similarity search → filter by modality="text")

**UI Design**:
- Single search bar with mode selector (Text / Image)
- When in Image mode, show file picker or paste area
- Results display adapts based on result modality

### 6. Caching and Performance

**Decision**: Multi-layer caching strategy

**Layers**:
1. **Browser Cache**: Thumbnail URLs with long-lived cache headers (Cache-Control: max-age=31536000)
2. **Server Disk Cache**: Thumbnails persist in `uploads/{collection}/thumbnails/`
3. **Embedding Cache**: Query embeddings cached in memory (existing implementation)

**Cache Invalidation**:
- Content-addressed filenames (UUID-based) eliminate need for invalidation
- If image is re-uploaded, gets new UUID and new cache entry
- Old files cleaned up by scheduled cleanup job (future enhancement)

## Data Models

### Backend Models

```python
# Extended SearchResult model
class SearchResult(BaseModel):
    id: str
    score: float
    document: Optional[str]  # None for images
    metadata: Dict[str, Any]
    result_type: Literal["text", "image"]
    image_metadata: Optional[ImageMetadata]  # Only for images

class ImageMetadata(BaseModel):
    width: int
    height: int
    format: str  # "png", "jpeg", "webp"
    file_size: int  # bytes
    thumbnail_url: str
    full_image_url: str
    mean_rgb: List[float]  # [R, G, B]

# Image search request
class ImageSearchRequest(BaseModel):
    image: UploadFile  # or base64 string
    collection_name: str
    top_k: int = 10
    modality_filter: Optional[Literal["image", "text"]] = None
```

### Frontend Models

```typescript
// TypeScript interfaces
interface ImageMetadata {
  width: number;
  height: number;
  format: string;
  file_size: number;
  thumbnail_url: string;
  full_image_url: string;
  mean_rgb: [number, number, number];
}

interface SearchResult {
  id: string;
  score: number;
  document: string | null;
  metadata: Record<string, any>;
  result_type: "text" | "image";
  image_metadata?: ImageMetadata;
}
```

## API Contracts

### Image Upload
```http
POST /api/ingest/upload
Content-Type: multipart/form-data

files: [File, File, ...]  # Accept .png, .jpg, .jpeg, .webp
collection_name: string

Response:
{
  "task_id": "uuid",
  "files": [
    {
      "name": "image.png",
      "status": "queued",
      "size": 1024000,
      "type": "image"
    }
  ]
}
```

### Image Search
```http
POST /api/search/image
Content-Type: multipart/form-data

image: File
collection_name: string
top_k: int = 10
modality_filter: "image" | "text" | null

Response: SearchResponse (same as text search)
```

### Image Retrieval
```http
GET /api/images/thumbnail/{collection}/{image_id}
Response: image/jpeg (256x256 thumbnail)
Headers: Cache-Control: max-age=31536000

GET /api/images/full/{collection}/{image_id}
Response: image/* (original image)
Headers: Cache-Control: max-age=31536000
```

## Component Interactions

```
┌─────────────────┐
│  Frontend UI    │
│  - UploadZone   │
│  - SearchBar    │
│  - ResultsList  │
└────────┬────────┘
         │
         │ HTTP/WebSocket
         ▼
┌─────────────────────────────────┐
│  FastAPI Server                 │
│  - /api/ingest/upload           │
│  - /api/search (text & image)   │
│  - /api/images/thumbnail/{id}   │
│  - /api/images/full/{id}        │
│  - WebSocket /ws/progress/{id}  │
└────────┬────────────────────────┘
         │
         ├─► TaskManager (async processing)
         │   │
         │   ├─► ImageLoader (load & validate)
         │   │   └─► PIL.Image
         │   │
         │   ├─► JinaEmbeddingsV4.encode_image()
         │   │   └─► Vision Encoder (MPS accelerated)
         │   │
         │   ├─► Thumbnail Generator
         │   │   └─► PIL.Image.thumbnail()
         │   │
         │   └─► ChromaVectorStore.add()
         │       └─► Embeddings + Metadata
         │
         └─► Search Pipeline
             ├─► JinaEmbeddingsV4.encode_{text|image}()
             └─► ChromaVectorStore.similarity_search()
                 └─► Filter by modality (optional)
```

## Performance Considerations

### Target Metrics (Apple M4 Max)
- **Image encoding latency**: <200ms per image (1080p)
- **Thumbnail generation**: <50ms per image
- **Batch ingestion throughput**: >5 images/second
- **Search latency**: <500ms (text-to-image or image-to-image)
- **Memory usage**: <500MB for batch of 100 images

### Optimization Strategies
1. **Batch Processing**: Process multiple images in parallel using ThreadPoolExecutor
2. **MPS Acceleration**: Leverage Apple Silicon GPU for embedding generation
3. **Progressive Loading**: Load thumbnails lazily in frontend using Intersection Observer
4. **Image Preprocessing**: Resize large images before encoding to reduce memory footprint
5. **Caching**: Aggressive caching at all layers (browser, server, embeddings)

## Security Considerations

### Input Validation
- Validate file extensions and MIME types (prevent code execution via malicious filenames)
- Limit image file size (default: 20MB per image, configurable)
- Validate image dimensions (reject extremely large images that could cause DoS)
- Check for image bombs (decompression bombs that expand to huge sizes)

### File Storage
- Use UUID-based filenames to prevent path traversal attacks
- Store uploaded files in dedicated directory outside web root
- Implement access control for image retrieval endpoints (future: per-collection auth)
- Sanitize collection names to prevent directory traversal

### Privacy
- Strip EXIF GPS data by default (opt-in to preserve)
- Do not expose internal file paths in API responses
- Implement optional image encryption at rest (future enhancement)

## Migration and Rollback

### Backward Compatibility
- Existing text-only collections continue to work unchanged
- New image fields are optional in SearchResult model
- API endpoints are additive (no breaking changes)

### Rollback Strategy
- Image files stored separately from embeddings (can be deleted without affecting text search)
- New metadata fields nullable (can be ignored by older code)
- Feature flag to disable image upload while keeping search functional

## Testing Strategy

### Unit Tests
- ImageLoader with various formats (valid, corrupted, edge cases)
- Thumbnail generation with different aspect ratios
- Metadata extraction and validation
- API endpoint request/response validation

### Integration Tests
- End-to-end image upload → embedding → search flow
- Mixed modality search (text + images in same collection)
- WebSocket progress updates for image ingestion
- Thumbnail caching and retrieval

### Performance Tests
- Benchmark encoding latency for various image sizes
- Measure batch ingestion throughput (10, 50, 100 images)
- Profile memory usage during large batch processing
- Load test search endpoints with concurrent requests

### User Acceptance Tests
- Manual testing of drag-and-drop upload
- Visual verification of thumbnails and full images
- Cross-browser testing (Chrome, Safari, Firefox)
- Mobile responsiveness testing

## Future Enhancements (Out of Scope)

1. **OCR Integration**: Extract text from images using tesseract or vision models
2. **Image Editing**: Crop, rotate, adjust brightness/contrast before upload
3. **Advanced Filters**: Search by color, dominant objects, scene type
4. **Video Support**: Extract keyframes and embed as image sequences
5. **Multi-Vector Search**: Use late-interaction retrieval for fine-grained matching
6. **CDN Integration**: Serve thumbnails from CDN for faster global access
7. **Smart Collections**: Auto-organize images by visual similarity clusters
8. **Duplicate Detection**: Identify and merge visually identical images
