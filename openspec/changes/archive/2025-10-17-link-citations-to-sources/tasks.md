# Tasks: Link Citations to Source Material

## Implementation Order
Tasks are ordered in two phases:
- **Phase 1 (Tasks 1-5)**: Document Storage Infrastructure - establishes persistent storage and serving
- **Phase 2 (Tasks 6-14)**: Citation Linking UI - implements interactive citations

## Phase 1: Document Storage Infrastructure

### 1. Modify ingestion to persist text documents
**Owner**: Backend
**Dependencies**: None
**Validation**: Document files remain in `./uploads/{collection}/documents/` after ingestion

- Update `src/jina_rag_pipeline/api/tasks.py:process_task()`
- In text document processing block (line 192-216), add document persistence logic:
  - Create `./uploads/{collection}/documents/` directory
  - Copy file to permanent storage as `{document_id}{extension}`
  - Store `document_path` in chunk metadata
  - **Remove** the `file_path.unlink()` call that deletes the file (line 240)
- Mirror existing image storage pattern (lines 134-148)

**Acceptance**:
- Text documents saved to `./uploads/{collection}/documents/` with UUID names
- `document_path` field present in chunk metadata
- Files persist after ingestion completes
- No temp files remain (cleanup still works for failed uploads)

---

### 2. Add document serving API endpoint
**Owner**: Backend
**Dependencies**: Task 1
**Validation**: `curl http://localhost:8000/api/documents/test/doc.pdf` returns file

- Add endpoint to `src/jina_rag_pipeline/api/app.py`: `@app.get("/api/documents/{collection}/{filename}")`
- Mirror structure of existing `/api/images/full/` endpoint (lines 493-520)
- Security: Use `safe_filename()` to prevent path traversal
- Build path: `./uploads/{collection}/documents/{filename}`
- Determine Content-Type from file extension
- Return FileResponse with caching headers (Cache-Control, ETag)
- Handle 404 for missing files with helpful error

**Acceptance**:
- Endpoint serves PDF, TXT, MD, PY files correctly
- Content-Type headers set appropriately
- Path traversal attempts (e.g., `../../../etc/passwd`) blocked
- 404 returned with clear message for missing files
- Files cached with 1-year max-age

---

### 3. Test document storage end-to-end
**Owner**: Backend
**Dependencies**: Tasks 1, 2
**Validation**: Integration test passes

- Write integration test: upload document → verify stored → retrieve via API
- Test multiple file formats (PDF, TXT, MD)
- Test metadata includes `document_path`
- Test document deletion when collection deleted
- Test fallback for documents without stored files

**Acceptance**:
- Upload-store-retrieve cycle works
- Metadata correctly tracks storage location
- API serves documents with correct MIME types
- Collection deletion removes document files

---

## Phase 2: Citation Linking UI

### 4. Update API models to include citation map
**Owner**: Backend
**Dependencies**: Task 3 complete (storage working)
**Validation**: Run tests for `ContextMessage` serialization

- Add `citation_map` field to `ContextMessage` model in `src/jina_rag_pipeline/api/models.py`
- Field type: `Dict[str, Dict[str, Any]]` mapping citation IDs to source metadata
- Make field optional with default empty dict for backward compatibility
- Update API documentation/schema

**Acceptance**:
- `ContextMessage` includes `citation_map` field
- Field properly serializes to JSON in WebSocket messages
- Existing chat functionality unaffected

---

### 5. Send citation map in WebSocket context messages
**Owner**: Backend
**Dependencies**: Task 4
**Validation**: Inspect WebSocket messages in browser devtools

- After formatting context in `chat.py:websocket_chat()`, retrieve citation map from `context_formatter.get_citation_map()`
- Include citation map in `ContextMessage` construction
- For text citations, include `document_url` field pointing to `/api/documents/{collection}/{filename}`
- Add logging to verify citation map is populated

**Acceptance**:
- WebSocket `context` messages include populated `citation_map`
- Citation IDs match those used in formatted context text
- Map contains correct source metadata (source, type, score, etc.)
- Text citations include `document_url` for API retrieval

---

### 6. Update frontend types for citation data
**Owner**: Frontend
**Dependencies**: Task 5
**Validation**: TypeScript compilation succeeds

- Add `CitationMetadata` interface in `frontend/src/types/chat.ts`
  - Fields: `source`, `type`, `score`, `metadata`, `document_url`, optional `document_id`, `image_urls`
- Add `citation_map` to context message type
- Update `Message` interface to optionally include citations

**Acceptance**:
- TypeScript types reflect API response structure
- No type errors in existing code
- Types support both text and image citation metadata
- `document_url` field present for text citations

---

### 7. Parse and store citation map in chat state
**Owner**: Frontend
**Dependencies**: Task 6
**Validation**: Console logging shows citation map stored

- Update `ChatPage.tsx` WebSocket message handler
- When receiving `context` message, extract and store `citation_map`
- Associate citation map with the current conversation turn
- Store in component state or context for access during rendering

**Acceptance**:
- Citation map available when rendering assistant responses
- Map persists for the duration of the response
- Multiple citation maps tracked for multi-turn conversations

---

### 8. Create CitationLink component
**Owner**: Frontend
**Dependencies**: Task 7
**Validation**: Storybook story or test page

- Create `frontend/src/components/chat/CitationLink.tsx`
- Props: `citationId`, `citationData`, `onClick`
- Render citation as styled link/button (e.g., `[1]` with blue color, underline on hover)
- Handle click to trigger source viewer
- Add ARIA labels for accessibility (e.g., "View source 1")

**Acceptance**:
- Component renders citation markers as clickable links
- Hover state provides visual feedback
- Click handler receives citation data
- Accessible via keyboard navigation (Tab, Enter)

---

### 6. Create SourceViewer component
**Owner**: Frontend
**Dependencies**: None (can parallelize with Task 5)
**Validation**: Storybook story with sample data

- Create `frontend/src/components/chat/SourceViewer.tsx`
- Slide-in panel or modal design (non-blocking)
- Displays text source with metadata (source name, relevance score)
- Displays image source with full-size preview
- Close button and ESC key support
- Responsive design for mobile/tablet

**Acceptance**:
- Panel slides in from right side of screen
- Text content displays in readable format with syntax highlighting if code
- Images display at full resolution with zoom capability
- Panel can be closed via button, ESC key, or click outside
- Works on mobile devices

---

### 7. Parse assistant messages to replace citation markers with links
**Owner**: Frontend
**Dependencies**: Task 5
**Validation**: Test with sample messages containing citations

- Update `ChatMessage.tsx` or create citation parser utility
- Use regex to find citation markers: `\[(\d+)\]` for text, `\[IMG-(\d+)\]` for images
- Replace markers with `CitationLink` components
- Pass appropriate citation data from citation map
- Maintain markdown rendering for non-citation content

**Acceptance**:
- Citation markers in responses are replaced with clickable links
- Non-citation content (markdown, code blocks) renders normally
- Citations not in citation map render as plain text (graceful degradation)
- Multiple citations in single sentence all become clickable

---

### 8. Integrate SourceViewer with citation clicks
**Owner**: Frontend
**Dependencies**: Tasks 6, 7
**Validation**: End-to-end test in running application

- Add state management for selected citation in `ChatPage.tsx`
- When citation link clicked, open `SourceViewer` with citation data
- Load source content from citation metadata
- For images, use thumbnail/full image URLs from metadata
- For text, display the document content from context

**Acceptance**:
- Clicking text citation opens viewer with source document
- Clicking image citation opens viewer with full-size image
- Viewer displays all relevant metadata (filename, score, etc.)
- Multiple clicks switch source content in viewer
- Closing viewer returns focus to chat

---

### 9. Add keyboard navigation support
**Owner**: Frontend
**Dependencies**: Task 8
**Validation**: Manual testing with keyboard only

- Citations focusable via Tab key
- Enter/Space activates citation link
- ESC closes source viewer
- Arrow keys navigate between citations (optional enhancement)
- Focus returns to citation link after closing viewer

**Acceptance**:
- All citation features accessible via keyboard
- Tab order logical and predictable
- Focus indicators visible
- Screen reader announces citation links and source viewer

---

### 13. Add keyboard navigation support
**Owner**: Frontend
**Dependencies**: Task 11
**Validation**: Manual testing with keyboard only

- Citations focusable via Tab key
- Enter/Space activates citation link
- ESC closes source viewer
- Arrow keys navigate between citations (optional enhancement)
- Focus returns to citation link after closing viewer

**Acceptance**:
- All citation features accessible via keyboard
- Tab order logical and predictable
- Focus indicators visible
- Screen reader announces citation links and source viewer

---

### 14. Add tests for citation functionality
**Owner**: Frontend + Backend
**Dependencies**: Tasks 1-12 complete
**Validation**: CI passes

- **Backend Unit**: Test document storage during ingestion
- **Backend Unit**: Test `ContextMessage` with citation_map serialization
- **Backend Integration**: Test WebSocket sends citation_map correctly
- **Backend Integration**: Test document serving endpoint security (path traversal)
- **Frontend Unit**: Component tests for `CitationLink` and `SourceViewer`
- **Frontend Integration**: Test citation parsing and link replacement
- **E2E**: Upload document → chat query → click citation → view source

**Acceptance**:
- All tests pass in CI
- Coverage meets project standards (80%+)
- Tests cover edge cases (missing documents, invalid paths, no citations)
- Security tests verify path traversal prevention

---

### 15. Update documentation
**Owner**: Documentation
**Dependencies**: Tasks 1-14 complete
**Validation**: Docs review

- Add user guide section on using citations
- Update API documentation for `ContextMessage.citation_map`
- Add screenshots showing citation interaction
- Document accessibility features

**Acceptance**:
- Users understand how to click citations
- Developers understand citation_map structure
- Documentation includes examples and screenshots

---

## Parallel Work Opportunities

**Phase 1 (Tasks 1-3):**
- Tasks 1-2 can be developed in parallel (ingestion + API endpoint)
- Task 3 validates both together

**Phase 2 (Tasks 4-14):**
- Backend tasks 4-5 (API models, WebSocket) proceed independently
- Frontend tasks 6-9 (types, state, components) can work in parallel
- Task 8 (CitationLink) and Task 9 (SourceViewer) can be built in parallel
- Task 14 (testing) begins as tasks complete

**Phase Dependencies:**
- Phase 2 frontend work can BEGIN during Phase 1 (preparing components)
- Phase 2 integration (Task 11) requires Phase 1 API endpoint complete

## Testing Strategy
- **Unit**: Component rendering, citation parsing, URL building
- **Integration**: WebSocket messages, citation map flow, state management
- **E2E**: Full user workflow from question to citation click
- **Accessibility**: Screen reader testing, keyboard navigation
- **Visual**: Screenshot tests for citation styles and viewer

## Rollout Plan
1. Deploy backend changes first (backward compatible)
2. Deploy frontend changes (will work with new backend, graceful with old)
3. Monitor for broken citations or viewer issues
4. Gather user feedback on citation UX
