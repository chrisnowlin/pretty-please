# Proposal: enhance-frontend-ui-controls

## Summary
Enhance the frontend UI to expose existing backend configuration capabilities for RAG settings, generation parameters, collection configuration, and multimodal search. Currently, the backend provides comprehensive control over retrieval, reranking, and generation through REST APIs, but the frontend UI only exposes minimal configuration options in the chat session setup.

## Problem Statement
The RAG pipeline backend has rich configuration capabilities that are not accessible through the frontend UI:

1. **RAG Configuration**: Global RAG settings (`/api/config/rag`) for retrieval batch sizes, reranking, hybrid search, citation styles are not exposed in UI
2. **Advanced Session Configuration**: Session setup only allows basic settings, missing generation parameters (temperature, top_p, top_k) and max_history_turns
3. **Collection Configuration**: Collection-specific layout analysis settings (`enable_layout_analysis`, `layout_ocr_enabled`, `layout_table_extraction`) have no UI management
4. **Multimodal Search**: Image-to-text/image search endpoint (`/api/search/image`) exists but has no frontend component
5. **Metrics Visibility**: Retrieval metrics (vector search time, reranking time) are returned but not displayed
6. **Region Metadata**: Layout analysis region data (type, bbox, page numbers) is not shown in search results

Users must resort to direct API calls or backend configuration files to access these features, reducing usability and discoverability.

## Goals
- Expose RAG configuration controls in a dedicated settings page/panel
- Enhance session setup with advanced generation and RAG configuration options
- Provide collection configuration management UI for layout analysis settings
- Add image upload search capability to SearchPage
- Display retrieval performance metrics in chat interface
- Show region metadata in search result cards when available

## Non-Goals
- Implementing new backend capabilities (focus on UI for existing features)
- Redesigning the overall UI layout or navigation structure
- Adding real-time configuration hot-reloading (existing endpoints require session restart)

## Success Criteria
- [ ] Users can view and update global RAG configuration from settings UI
- [ ] Session setup allows configuration of all generation and RAG parameters
- [ ] Collection configuration page shows and allows editing layout analysis settings
- [ ] Search page supports image upload for image-based queries
- [ ] Chat interface displays retrieval metrics (timing, counts, reranking status)
- [ ] Search results show region metadata when from layout-analyzed documents

## Open Questions
1. Should RAG config changes apply globally or per-session? (Currently backend is global)
2. Should advanced configuration options be hidden behind "Advanced" toggle to avoid overwhelming users?
3. Should we show region bounding boxes visually on extracted images?
4. What level of detail for retrieval metrics is appropriate? (full breakdown vs summary)

## Dependencies
- Existing backend API endpoints (no backend changes required)
- Frontend query/mutation infrastructure (React Query already in use)
- UI component library consistency with current theme system

## Related Changes
- None (this is a frontend-only enhancement leveraging existing backend capabilities)
