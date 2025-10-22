# Design: enhance-frontend-ui-controls

## Architecture Overview
This change adds frontend UI components to expose existing backend configuration APIs without modifying backend behavior. The enhancement spans multiple frontend capabilities (settings, session setup, collections, search) that currently lack UI controls for backend features.

## Key Design Decisions

### 1. Configuration Scope Strategy
**Decision**: Implement both global RAG settings and per-session overrides
- Global RAG config applies to all new sessions via `/api/config/rag`
- Session creation can override specific parameters via request body
- UI shows global defaults with ability to customize during session setup

**Rationale**: Backend supports both patterns. Global settings provide sane defaults while per-session overrides allow experimentation without affecting all users.

**Trade-offs**:
- ✅ Flexibility for power users and casual users
- ✅ No backend changes required
- ⚠️ Potential confusion about precedence (session vs global)
- Mitigation: Clear UI labeling ("Use global settings" vs "Custom settings")

### 2. Progressive Disclosure Pattern
**Decision**: Hide advanced options behind collapsible "Advanced" sections
- Session setup: Show basic options (collection, thinking mode), hide generation params
- RAG settings: Show common settings (retrieval_k, enable_reranking), hide compression/hybrid
- Collection config: Show layout analysis toggle, hide granular OCR/table extraction

**Rationale**: Reduces cognitive load for new users while preserving access for advanced use cases. Matches patterns in similar tools (VS Code settings, database admin panels).

**Trade-offs**:
- ✅ Cleaner, less overwhelming initial UI
- ✅ Preserves power user features
- ⚠️ Advanced features less discoverable
- Mitigation: Tooltips explaining when advanced settings are useful

### 3. Component Structure
**Decision**: Create dedicated components for each configuration concern
- `RAGConfigPanel` - Global RAG settings with validation
- `SessionSetupAdvanced` - Extends existing `SessionSetup` with collapsible advanced options
- `CollectionConfigPanel` - Layout analysis and collection settings
- `ImageSearchUpload` - Image upload component for search page
- `MetricsDisplay` - Retrieval metrics visualization
- `RegionMetadataBadge` - Display region type/page info on result cards

**Rationale**: Separation of concerns, reusability, testability. Each component owns its API interaction and validation logic.

**Trade-offs**:
- ✅ Clear ownership and maintainability
- ✅ Easy to test in isolation
- ⚠️ More files to manage
- ⚠️ Potential for prop drilling (mitigated with React Context if needed)

### 4. Settings Page Structure
**Decision**: Add new `/settings` route with tabbed interface
- Tabs: "RAG Configuration", "Collections", "System"
- RAG tab shows retrieval, reranking, hybrid search, citation settings
- Collections tab shows list of collections with edit buttons opening config panels
- System tab reserved for future health/stats

**Rationale**: Centralizes configuration in standard settings page pattern. Tabs organize distinct configuration domains.

**Trade-offs**:
- ✅ Familiar UX pattern
- ✅ Room for future expansion
- ⚠️ Adds navigation complexity
- Mitigation: Link to settings from chat setup for discoverability

### 5. Image Search Integration
**Decision**: Add image upload to existing SearchPage rather than separate page
- Add toggle between "Text Search" and "Image Search" modes
- Image mode replaces text input with drag-and-drop upload zone
- Results display same ResultCard/ImageResultCard components
- Support modality filter dropdown (search images, search text, search all)

**Rationale**: Image and text search are variants of the same user goal (find documents). Separate pages would duplicate result display logic.

**Trade-offs**:
- ✅ Unified search experience
- ✅ Code reuse for results display
- ⚠️ SearchPage complexity increases
- Mitigation: Extract search mode logic into `useSearchMode` hook

### 6. Metrics Display Strategy
**Decision**: Show metrics in chat as collapsible status card after context retrieval
- Displays: "Retrieved X docs, Y images in Zms (Reranking: Wms)"
- Collapsible detail view shows: vector search time, reranking time, compression status
- Auto-collapses after 3 seconds, expandable on click

**Rationale**: Provides transparency without cluttering conversation flow. Useful for debugging slow queries and understanding retrieval behavior.

**Trade-offs**:
- ✅ Helpful for troubleshooting
- ✅ Non-intrusive when collapsed
- ⚠️ Adds visual noise during generation
- Mitigation: Auto-collapse and subtle styling

### 7. Region Metadata Presentation
**Decision**: Add subtle badges to ResultCard showing region type and page number
- Badge position: Bottom-left corner of card
- Format: "Page 2 • Title" or "Page 5 • Image"
- Only shown when metadata exists (graceful degradation)
- No bounding box visualization in this change (future enhancement)

**Rationale**: Minimal viable display of region context. Bounding box visualization requires image rendering infrastructure not yet built.

**Trade-offs**:
- ✅ Simple to implement
- ✅ Doesn't break existing result cards
- ⚠️ Limited utility without source document view
- Future: Link to document viewer highlighting region

## Data Flow

### RAG Configuration Update Flow
```
User edits RAGConfigPanel
  → Validates inputs (client-side)
  → PUT /api/config/rag
  → Backend validates and updates chat_state.rag_config
  → Response with updated config
  → UI updates optimistically (React Query mutation)
  → Shows success toast
```

### Session Creation with Custom Config Flow
```
User selects collection in SessionSetup
  → Expands "Advanced" section (optional)
  → Adjusts generation/RAG parameters
  → Clicks "Start Chat"
  → POST /api/chat/session with merged config
  → Backend creates session with custom GenerationConfig
  → WebSocket connects with session_id
  → Chat begins
```

### Image Search Flow
```
User toggles to "Image Search" mode
  → Drags image into upload zone
  → Selects modality filter (optional)
  → Clicks "Search"
  → POST /api/search/image with FormData (image, collection, top_k, modality_filter)
  → Backend encodes image with Jina V4 vision encoder
  → Vector search with optional modality filter
  → Returns SearchResponse with image_metadata
  → ResultsList renders ImageResultCard and ResultCard components
```

## Error Handling
- **Validation Errors**: Show inline form errors before submission (min/max ranges, invalid values)
- **API Errors**: Display toast notifications with error message and retry action
- **Network Errors**: Show connection status indicator, offer retry button
- **Missing Capabilities**: If backend endpoint returns 404/501, hide corresponding UI controls

## Testing Strategy
- **Unit Tests**: Validate configuration forms, validation logic, API request builders
- **Integration Tests**: Mock API endpoints, test full configuration update flows
- **E2E Tests**: Test session creation with advanced config, image search upload, settings page navigation
- **Accessibility**: Keyboard navigation, screen reader labels for all new controls

## Migration Path
No data migration required. This is purely additive UI enhancement.

Frontend deployment:
1. Deploy new components with feature flags (optional)
2. Monitor for errors in configuration endpoints
3. Gather user feedback on advanced settings usability
4. Iterate on progressive disclosure thresholds based on usage

## Future Enhancements
- Real-time config updates via WebSocket (currently requires session restart)
- Visual bounding box overlays for region metadata
- A/B testing framework for RAG parameter presets
- Export/import configuration profiles
- Configuration change history/audit log
