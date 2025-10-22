# Citation Linking Feature Documentation

## Overview

This feature enables interactive citation linking in RAG (Retrieval-Augmented Generation) chat responses. When the system includes citations like `[1]`, `[2]`, or `[IMG-1]` in responses, users can click on them to view the original source material.

## Architecture

### Phase 1: Document Persistence

**Problem**: Text documents were being deleted after embedding, making them unavailable for citation viewing.

**Solution**: Modified the ingestion pipeline to persist documents permanently:
- Documents stored in `./uploads/{collection}/documents/` with UUID-based names
- Added `document_path` field to chunk metadata
- Secure document serving endpoint with path traversal prevention

**Key Files Modified**:
- `src/jina_rag_pipeline/api/tasks.py`: Lines 196-226 (document persistence logic)
- `src/jina_rag_pipeline/api/app.py`: Lines 524-565 (document serving endpoint)

### Phase 2: Interactive Citation Links

**Backend Changes**:
1. Added `citation_map` field to `ContextMessage` model (lines 159-162 in models.py)
2. Enhanced WebSocket handler to populate and send citation map with `document_url` for text citations (lines 252-290 in chat.py)
3. Citation format: `{"[1]": {"source": "file.md", "type": "text", "score": 0.95, "document_url": "/api/documents/collection/uuid.md", ...}}`

**Frontend Changes**:
1. TypeScript types for `CitationMetadata` and `CitationMap` (frontend/src/types/chat.ts)
2. State management to capture citation maps from WebSocket messages (ChatPage.tsx)
3. **CitationLink component**: Clickable citation markers with accessibility support
4. **SourceViewer component**: Slide-in panel to display source content
5. Citation parsing in ReactMarkdown custom text renderer (ChatMessage.tsx)

## How Citations Work

### Citation Flow:
1. **Retrieval**: System retrieves relevant chunks and images
2. **Context Formatting**: `ContextFormatter.format_multimodal_context()` assigns citation IDs (`[1]`, `[2]`, `[IMG-1]`, etc.)
3. **Citation Map Generation**: `ContextFormatter.get_citation_map()` creates metadata mapping
4. **WebSocket Transmission**: Backend sends `citation_map` in context message before response streaming
5. **Frontend Parsing**: ChatMessage component parses response text and replaces citation markers with `<CitationLink>` components
6. **User Interaction**: Clicking a citation opens SourceViewer with the original content

### Citation Types:
- **Text citations**: `[1]`, `[2]`, `[3]`, ... → Opens document in viewer
- **Image citations**: `[IMG-1]`, `[IMG-2]`, ... → Shows thumbnail and full image

## Testing

### Automated Tests

Run the document storage test:
```bash
python3 test_document_storage.py
```

This verifies:
- ✓ Documents persist after upload
- ✓ Document serving endpoint works
- ✓ Content is retrievable

### Manual Testing

1. **Start servers**:
   ```bash
   # Backend
   source .venv/bin/activate
   python -m uvicorn src.jina_rag_pipeline.api.app:app --reload --port 8000

   # Frontend
   cd frontend && bun run dev
   ```

2. **Upload documents**:
   - Go to http://localhost:5173
   - Create a new collection or use existing one
   - Upload text documents (.txt, .md, .pdf) and/or images

3. **Test citations**:
   - Start a chat session
   - Ask questions about the uploaded content
   - Look for citation markers (`[1]`, `[2]`, etc.) in responses
   - Click citations to view source content
   - Press ESC or click backdrop to close viewer

### Expected Behavior:
- Citations should be blue, underlined, and clickable
- Clicking opens a slide-in panel from the right
- Text documents display in a scrollable viewer with syntax highlighting
- Images show thumbnail and full-size view
- Keyboard navigation works (ESC to close, TAB to navigate)
- ARIA labels provide screen reader support

## Files Created/Modified

### New Files:
- `frontend/src/components/chat/CitationLink.tsx` - Clickable citation component
- `frontend/src/components/chat/SourceViewer.tsx` - Source content viewer
- `test_document_storage.py` - Automated test suite
- `CITATION_LINKING_FEATURE.md` - This documentation

### Modified Files:
- `src/jina_rag_pipeline/api/tasks.py` - Document persistence
- `src/jina_rag_pipeline/api/app.py` - Document serving endpoint + frontend mount fix
- `src/jina_rag_pipeline/api/models.py` - `citation_map` field
- `src/jina_rag_pipeline/api/chat.py` - Citation map population
- `frontend/src/types/chat.ts` - TypeScript types
- `frontend/src/pages/ChatPage.tsx` - Citation state management
- `frontend/src/components/chat/ChatMessage.tsx` - Citation parsing
- `frontend/src/components/chat/MessageList.tsx` - Prop passing
- `frontend/src/components/chat/index.ts` - Component exports
- `frontend/public/index.html` - Slide-in animation CSS

## Security Considerations

### Path Traversal Prevention:
The `safe_filename()` function in `chat.py` validates filenames to prevent path traversal attacks:
```python
def safe_filename(filename: str) -> Optional[str]:
    # Remove directory components
    name = Path(filename).name
    # Check for dangerous patterns
    if ".." in name or name.startswith((".","/")):
        return None
    return name
```

### Access Control:
- Documents are collection-scoped (can only access documents in the same collection)
- UUID-based filenames prevent filename guessing attacks
- Content-Disposition header set to "inline" for browser preview
- Cache headers optimize performance without security compromise

## Known Limitations

1. **Backward Compatibility**: Documents uploaded before this feature was implemented will not have `document_path` in metadata, so citations won't be viewable. Solution: Re-upload old documents.

2. **No Asset Directory**: The frontend build doesn't create an `assets` directory unless there are actual assets to bundle. The backend gracefully handles this by checking both `frontend_dist` and `frontend_assets` directories exist before mounting.

3. **Citation Format**: Currently supports simple numeric citations (`[1]`, `[2]`) and image citations (`[IMG-1]`). Complex citation formats are not supported.

4. **Mobile UX**: SourceViewer takes full width on small screens, which works but could be optimized further.

## Future Enhancements

- [ ] Add citation copy-to-clipboard functionality
- [ ] Support multi-document comparison view
- [ ] Add citation export (copy citation in various formats)
- [ ] Improve mobile viewer experience
- [ ] Add citation highlighting in source document
- [ ] Support PDF page-specific citations
- [ ] Add citation search within viewer

## Development Notes

### Citation Map Structure:
```typescript
{
  "[1]": {
    "source": "document.md",
    "type": "text",
    "score": 0.95,
    "document_url": "/api/documents/collection/uuid.md",
    "metadata": {
      "document_id": "uuid",
      "upload_timestamp": "2025-01-16T...",
      "modality": "text"
    }
  },
  "[IMG-1]": {
    "source": "image.png",
    "type": "image",
    "score": 0.92,
    "document_id": "uuid",
    "image_urls": {
      "thumbnail_url": "/api/images/thumbnail/collection/uuid",
      "full_image_url": "/api/images/full/collection/uuid"
    },
    "metadata": {
      "width": 1920,
      "height": 1080,
      ...
    }
  }
}
```

### Component Interaction:
```
WebSocket Message (context)
  ↓
ChatPage (captures citation_map)
  ↓
Message State (attaches to assistant message)
  ↓
MessageList → ChatMessage (receives message with citationMap)
  ↓
ReactMarkdown text renderer (parses citations)
  ↓
CitationLink components (renders clickable citations)
  ↓
ChatPage handleCitationClick (opens SourceViewer)
  ↓
SourceViewer (fetches and displays content)
```

## Support

For issues or questions:
1. Check the automated test results
2. Inspect browser console for WebSocket messages
3. Verify document_path exists in metadata
4. Check backend logs for ingestion errors

---

**Implementation Date**: 2025-01-16
**Version**: 1.0
**Status**: ✅ Complete and Tested
