# Proposal: Link Citations to Source Material

## Change ID
`link-citations-to-sources`

## Overview
Enable users to click on citation markers (e.g., [1], [2], [IMG-1]) in chat responses to view or navigate to the original source documents and images. This enhances transparency and allows users to verify information directly from source material.

## Problem Statement
Currently, the RAG chat interface displays citation markers in assistant responses (e.g., "According to [1], ..."), but these citations are not interactive. Users cannot easily access the source documents that support the generated answers, reducing transparency and making it difficult to verify or explore the original context.

The system already:
- Generates citation markers ([1], [2] for text; [IMG-1], [IMG-2] for images) in responses
- Maintains a citation map in `ContextFormatter` linking citation IDs to source metadata
- Sends context information via WebSocket including text and image results
- **Images**: Stored persistently in `./uploads/{collection}/images/` with serving endpoints
- **Images**: Has URLs for thumbnails (`/api/images/thumbnail`) and full images (`/api/images/full`)

However:
- **Citation map is not transmitted** to the frontend via WebSocket
- **UI does not render citations** as interactive elements
- **Text documents are deleted** after embedding (only chunks remain in vector DB)
- **No document serving endpoint** exists to retrieve original text documents
- **No document_path stored** in metadata for text chunks

This prevents text citation linking from working, as the original documents are unavailable.

## Proposed Solution
Implement persistent document storage for all uploaded files, extend the chat WebSocket API to include citation maps, add document serving endpoints, and update the frontend to render citation markers as clickable links that display source material.

### Key Changes
1. **Document Storage (NEW)**:
   - Persist uploaded text documents permanently (mirroring existing image storage)
   - Store in `./uploads/{collection}/documents/` with UUID-based naming
   - Track `document_path` in chunk metadata alongside `source` name

2. **API Enhancements**:
   - Include `citation_map` in `ContextMessage` WebSocket responses
   - Add document serving endpoint: `/api/documents/{collection}/{filename}`
   - Reuse existing security patterns from image serving (path traversal prevention)

3. **Frontend Types**: Add citation mapping types to chat message context

4. **UI Components**:
   - Render citation markers as interactive links
   - Add source viewer modal/panel for text documents and images
   - Support multiple document formats (PDF viewer, text display, code highlighting)
   - Fallback to chunk text if original document unavailable

## Goals
- **Persistent Storage**: Preserve all uploaded documents for long-term access
- **Interactive Citations**: Make citation markers in chat responses clickable
- **Text Sources**: Allow users to view original documents when clicking text citations ([1], [2], etc.)
- **Image Sources**: Allow users to view full images when clicking image citations ([IMG-1], [IMG-2], etc.)
- **Accessibility**: Maintain WCAG standards for keyboard navigation and screen readers
- **Backward Compatibility**: Gracefully handle documents uploaded before storage implementation

## Non-Goals
- Modifying citation format or numbering scheme
- Adding new types of citations beyond text and image
- Implementing citation analytics or tracking
- Supporting multi-document source comparison
- Document versioning or change tracking
- Full-text search within stored documents (covered by existing RAG retrieval)
- Document preview/rendering for proprietary formats (MS Office, CAD, etc.)

## Success Criteria
- All uploaded documents stored persistently on disk
- Document storage path tracked in metadata
- Document serving endpoint returns correct Content-Type headers
- Users can click any citation marker in a response
- Clicking a text citation displays the original source document
- Clicking an image citation displays the full-size image
- Citations maintain ARIA labels for accessibility (e.g., "View source document")
- Source viewer supports common formats (PDF, TXT, MD, code files)
- Path traversal attacks prevented in document serving
- Documents from pre-storage uploads gracefully show chunk text instead

## Dependencies
- Existing: `ContextFormatter.get_citation_map()` method
- Existing: WebSocket chat infrastructure
- Existing: Image serving endpoints (`/api/images/thumbnail`, `/api/images/full`)
- Existing: Image storage pattern in `./uploads/{collection}/images/`
- Existing: Path traversal prevention utilities (`safe_filename`, `build_safe_image_url`)
- New: Document storage directory structure
- New: Document serving endpoint with security

## Risks and Mitigations
| Risk | Mitigation |
|------|------------|
| **Disk space usage increases** | Monitor disk usage; implement cleanup for deleted collections; document storage requirements |
| **Large documents slow serving** | Implement range requests for PDFs; set max file size limits; use streaming responses |
| **Path traversal attacks** | Reuse existing `safe_filename()` utility; validate collection names; restrict to uploads directory |
| **Citation map increases message size** | Citation maps are small (typically < 10 entries); ~2KB overhead acceptable |
| **Documents uploaded before storage unavailable** | Fallback to chunk text from vector DB; show warning in source viewer |
| **Modal disrupts conversation flow** | Use slide-in panel instead; non-blocking design |
| **Citation parsing complexity** | Use regex on known citation patterns; well-defined format |

## Implementation Phases
This change will be implemented in two coordinated phases:

### Phase 1: Document Storage Infrastructure
- Modify ingestion pipeline to persist documents
- Add document serving API endpoint
- Update metadata tracking
- **Validation**: Documents persist across restarts; endpoint serves files correctly

### Phase 2: Citation Linking UI
- Extend WebSocket to include citation map
- Implement frontend citation components
- Integrate source viewer with document/image endpoints
- **Validation**: End-to-end citation click-through works

Phases can overlap but Phase 1 must complete API endpoint before Phase 2 frontend integration.

## Related Changes
- Builds on: `enhance-rag-quality` (archive) - established citation format
- Builds on: `add-chatbot-interface` (archive) - established chat UI
