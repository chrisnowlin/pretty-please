# Expose Advanced Configuration UI for Embeddings and OCR

## Change Metadata
- **Change ID**: expose-advanced-config-ui
- **Type**: Enhancement
- **Status**: Proposed
- **Created**: 2025-10-20
- **Author**: AI Assistant
- **Priority**: Medium

## Problem Statement

Following the recent completion of two major backend optimization efforts (`optimize-jina-embeddings-v4` and `streamline-ocr-processing-pipeline`), the backend now supports sophisticated configuration systems with smart presets:

1. **EmbeddingConfig**: Provides presets like `for_query()`, `for_documents()`, `storage_optimized()`, `fast()`, and `memory_constrained()` with granular control over:
   - Task types (retrieval.query, retrieval.passage, code search, etc.)
   - Embedding dimensions (128-2048)
   - Late chunking behavior
   - Multi-vector embeddings
   - Storage formats (float, binary, ubinary)
   - Batch sizing

2. **OCRConfig**: Offers presets like `mlx_optimized()`, `balanced()`, `two_tier()`, and `memory_constrained()` with control over:
   - Batch sizes
   - Worker allocation
   - Pre-rendering strategies
   - Two-tier hybrid processing (FAST + BALANCED)
   - Complexity-based routing

**However**, these powerful configuration capabilities are currently hard-coded in the backend and NOT exposed through the REST API or frontend UI. This means:

- Users cannot choose between speed-optimized vs quality-optimized processing
- Users cannot adjust configurations for their specific hardware constraints
- Users cannot leverage storage-efficient embedding formats
- Users cannot take advantage of the two-tier OCR system
- Power users have no way to fine-tune performance characteristics

The current frontend configuration UI only exposes:
- Collection-level settings (CollectionConfig) - focused on layout analysis
- RAG retrieval settings (RAGConfigModel) - focused on search parameters

This leaves a significant gap between backend capabilities and user-facing controls.

## Goals

### Primary Goal
**Expose EmbeddingConfig and OCRConfig capabilities to the frontend**, enabling users to select appropriate presets and customize advanced settings for their use cases and hardware.

### Specific Objectives

1. **Add Backend API Endpoints**
   - `GET /api/config/embeddings` - Retrieve current embedding configuration
   - `POST /api/config/embeddings` - Update embedding configuration
   - `GET /api/config/ocr` - Retrieve current OCR configuration
   - `POST /api/config/ocr` - Update OCR configuration
   - Include preset enumeration endpoints for UI dropdowns

2. **Extend Pydantic API Models**
   - Create `EmbeddingConfigModel` (Pydantic) to mirror `EmbeddingConfig` (dataclass)
   - Create `OCRConfigModel` (Pydantic) to mirror `OCRConfig` (dataclass)
   - Add validation and serialization for all config parameters

3. **Frontend Configuration Panels**
   - Add `EmbeddingConfigPanel` component to Settings page
   - Add `OCRConfigPanel` component to Settings page
   - Provide preset dropdown with descriptions (e.g., "Fast (4× faster, 512 dimensions)")
   - Show advanced options toggle for power users
   - Display estimated performance impact (memory, speed, quality tradeoffs)

4. **User Experience Enhancements**
   - Preset-first UI: Encourage users to select presets before manual tuning
   - Hardware detection: Auto-suggest optimal preset based on system memory
   - Performance hints: Show what each setting affects (speed/quality/memory)
   - Configuration validation: Prevent invalid combinations before submission

## Success Criteria

### Functionality
- ✅ Users can select from all embedding presets via UI dropdown
- ✅ Users can select from all OCR presets via UI dropdown
- ✅ Users can view and modify advanced parameters when needed
- ✅ Configuration changes persist across sessions
- ✅ Invalid configurations are rejected with clear error messages

### User Experience
- ✅ 80% of users can configure without touching advanced settings (preset defaults work)
- ✅ Performance hints guide users toward optimal choices
- ✅ Configuration changes take effect on next document upload/query (no restart required)
- ✅ Mobile-responsive configuration panels

### Documentation
- ✅ Each preset has a clear description with performance characteristics
- ✅ Advanced parameters have tooltips explaining their impact
- ✅ Configuration guide added to docs explaining when to use each preset

## Non-Goals

- **Runtime Configuration Changes**: Changing config won't affect already-processed documents or ongoing processing
- **Per-Collection Configuration**: Embedding and OCR configs remain global, not per-collection
- **Automatic Tuning**: No ML-based automatic config optimization (manual or preset-based only)
- **Configuration Profiles**: No saved configuration profiles/templates (future enhancement)

## Constraints

- **Backward Compatibility**: Existing API behavior must remain unchanged when configs aren't explicitly set
- **Mobile Support**: Configuration UI must be usable on tablet-sized screens (≥768px width)
- **Performance**: Configuration endpoints should respond in <100ms
- **Security**: No sensitive information (API keys, passwords) should be in these configs

## Impact Analysis

### Affected Components

**Backend:**
- `src/jina_rag_pipeline/api/app.py` - Add new configuration endpoints
- `src/jina_rag_pipeline/api/models.py` - Add `EmbeddingConfigModel`, `OCRConfigModel`
- `src/jina_rag_pipeline/api/tasks.py` - Use dynamic configs instead of hard-coded presets
- `src/jina_rag_pipeline/embeddings/jina_v4.py` - Accept config parameter
- `openspec/specs/api/spec.md` - Add configuration endpoint requirements

**Frontend:**
- `frontend/src/components/settings/EmbeddingConfigPanel.tsx` - New component
- `frontend/src/components/settings/OCRConfigPanel.tsx` - New component
- `frontend/src/components/settings/CollectionsConfigPage.tsx` - Add new panels
- `frontend/src/services/api.ts` - Add config API methods
- `frontend/src/types/` - Add TypeScript types for config models
- `openspec/specs/frontend/spec.md` - Add configuration UI requirements

### Dependencies
- **Upstream**: None - builds on completed OCR and embedding optimization changes
- **Downstream**: Any future per-collection config would extend this global config system
- **Related**: Monitoring/metrics system should track config usage patterns

### Migration Strategy
1. **Phase 1**: Add API endpoints with current hard-coded defaults (no behavior change)
2. **Phase 2**: Add frontend UI, enable configuration changes
3. **Phase 3**: Add preset usage analytics to guide future default changes
4. **Phase 4**: Consider per-collection configuration overrides (separate proposal)

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Users choose suboptimal configs | Medium | Medium | Provide clear preset descriptions and performance hints |
| Config changes cause processing failures | High | Low | Validate all configs server-side, test edge cases thoroughly |
| UI complexity overwhelms average users | Medium | Medium | Hide advanced settings by default, preset-first design |
| Mobile UI is cramped/unusable | Low | Medium | Test on tablets, use progressive disclosure patterns |
| Performance degradation from poor config choices | Medium | Medium | Show estimated performance impact before applying |

## Alternatives Considered

### 1. Environment Variables Only
- **Pros**: Simpler implementation, no UI needed
- **Cons**: Requires server restart, not user-friendly, no per-user customization
- **Decision**: Rejected - not accessible enough for end users

### 2. Configuration File Upload
- **Pros**: Power users can version control configs
- **Cons**: More complex for average users, security concerns
- **Decision**: Deferred - could add as future enhancement alongside UI

### 3. Auto-Detection Only
- **Pros**: Zero user configuration needed
- **Cons**: May not match user's specific needs (speed vs quality tradeoff)
- **Decision**: Use as default suggestion, but allow override

### 4. Per-Collection Configuration
- **Pros**: Different collections could have different optimization strategies
- **Cons**: More complex implementation, more complex UI
- **Decision**: Start with global config, evaluate per-collection in future

## Open Questions

1. **Should OCR config be per-collection or global?**
   - **Recommendation**: Start global, add per-collection overrides in future proposal
   - **Rationale**: Simpler implementation, most users will want consistent processing

2. **How should we handle config changes for in-flight processing tasks?**
   - **Recommendation**: Complete ongoing tasks with old config, apply new config to future tasks
   - **Rationale**: Avoids partial processing inconsistencies

3. **Should we add a "custom" preset for fully manual configuration?**
   - **Recommendation**: Yes - add "Custom" preset that enables all advanced controls
   - **Rationale**: Gives power users full control while keeping UI simple for others

4. **Should embedding format changes trigger re-indexing prompts?**
   - **Recommendation**: No automatic re-indexing, but show info message about format change effects
   - **Rationale**: Re-indexing is expensive, user should explicitly decide

5. **Should we expose batch_size parameters in the UI?**
   - **Recommendation**: Yes, but in advanced section with clear memory impact warnings
   - **Rationale**: Power users may need to tune for their specific hardware

## Related Work

- **Completed Changes**:
  - `optimize-jina-embeddings-v4`: Established EmbeddingConfig architecture
  - `streamline-ocr-processing-pipeline`: Established OCRConfig architecture

- **Related Documentation**:
  - `docs/guides/ocr-configuration.md`: OCR configuration patterns
  - `NANONETS_TWO_TIER_SYSTEM.md`: Two-tier OCR system explanation

- **Future Enhancements**:
  - Per-collection configuration overrides
  - Configuration profiles/templates
  - Automatic configuration optimization based on usage patterns

## Implementation Notes

- Follow existing UI patterns from `RAGConfigPanel` and `CollectionConfigPanel`
- Use React Query for configuration state management
- Implement optimistic UI updates with rollback on error
- Add comprehensive validation on both frontend and backend
- Use Pydantic model validation to ensure type safety

## Code Verification Findings

Based on thorough code review, the following implementation details have been verified:

### Backend Configuration Architecture

**EmbeddingConfig** (`src/jina_rag_pipeline/embeddings/config.py`):
- ✅ Fully implemented dataclass with all mentioned presets
- ✅ `JinaEmbeddingsV4.embed_with_config()` method at line 396 accepts dynamic config
- ⚠️ TaskManager hard-codes `EmbeddingConfig.for_documents()` at lines 652, 747, 766, 837
- ⚠️ TaskManager hard-codes `EmbeddingConfig.for_query()` for query processing
- **Action Required**: Modify TaskManager to accept configuration from API state

**OCRConfig** (`src/jina_rag_pipeline/ingestion/ocr_config.py`):
- ✅ Fully implemented dataclass with all mentioned presets
- ✅ `NanonetsLoader` constructor accepts OCRConfig parameter
- ✅ Auto-selects `mlx_optimized()` on Apple Silicon, `balanced()` otherwise
- ✅ Two-tier hybrid mode properly integrated with complexity thresholds
- **Ready**: Can be directly exposed through API

### Existing API Patterns

**Configuration Endpoints** (`src/jina_rag_pipeline/api/app.py`):
- Lines 689-761: RAG config endpoints follow `GET /api/config/{type}` and `POST /api/config/{type}` pattern
- Configuration stored in `chat.chat_state.rag_config` for runtime updates
- Immediate effect on subsequent operations (no restart required)

**Pydantic Models** (`src/jina_rag_pipeline/api/models.py`):
- Line 302: `RAGConfigModel` demonstrates validation patterns with Field constraints
- Lines 107-216: `CollectionConfig` implements `save_to_file()` and `load_from_file()` for JSON persistence
- **Pattern to Follow**: Create similar models for EmbeddingConfig and OCRConfig

### Configuration Persistence

**CollectionManager Pattern** (`src/jina_rag_pipeline/api/collection_manager.py`):
- Lines 98-99, 173-177, 253-254: Uses `config.json` files for persistence
- Implements atomic writes for safe updates
- Creates default configs when missing
- **Decision**: Use similar JSON file approach for global embedding/OCR configs

### Integration Points

**Document Upload Flow** (`src/jina_rag_pipeline/api/app.py:347-406`):
- Upload endpoint queues tasks via TaskManager
- TaskManager processes documents with hard-coded configs
- **Integration Point**: TaskManager should load configs from ConfigManager

**Query Processing** (`src/jina_rag_pipeline/api/tasks.py`):
- Currently uses hard-coded `EmbeddingConfig.for_query()`
- **Integration Point**: Should use dynamic config from API state
