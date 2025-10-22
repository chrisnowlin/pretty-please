# Implementation Tasks

## Phase 1: Backend API (No Behavior Change)

- [x] 1. **Add Pydantic configuration models**
   - Create `EmbeddingConfigModel` in `src/jina_rag_pipeline/api/models.py`
   - Create `OCRConfigModel` in `src/jina_rag_pipeline/api/models.py`
   - Create `PresetInfo` model
   - Add field validation with appropriate ranges
   - **Validation**: Unit tests pass for model validation

- [x] 2. **Create configuration persistence layer**
   - Create `ConfigManager` class in `src/jina_rag_pipeline/api/config_manager.py`
   - Implement `load_config()` and `save_config()` methods
   - Use atomic writes (temp file + rename pattern)
   - Default to sensible values if config.json doesn't exist
   - **Validation**: Configuration persists across restarts

- [x] 3. **Add embedding configuration endpoints**
   - Implement `GET /api/config/embeddings`
   - Implement `POST /api/config/embeddings`
   - Implement `GET /api/config/embeddings/presets`
   - Wire to ConfigManager for persistence
   - **Validation**: Endpoints return 200 OK with valid JSON

- [x] 4. **Add OCR configuration endpoints**
   - Implement `GET /api/config/ocr`
   - Implement `POST /api/config/ocr`
   - Implement `GET /api/config/ocr/presets`
   - Wire to ConfigManager for persistence
   - **Validation**: Endpoints return 200 OK with valid JSON

- [x] 5. **Write backend tests**
   - Unit tests for Pydantic models
   - Integration tests for API endpoints
   - Test invalid input rejection
   - Test configuration persistence
   - **Validation**: All tests pass, >85% coverage

## Phase 2: Frontend UI

- [x] 6. **Add TypeScript types and API client methods**
   - Define `EmbeddingConfig`, `OCRConfig`, `PresetInfo` types
   - Add `getEmbeddingConfig`, `updateEmbeddingConfig`, `getEmbeddingPresets` to `apiClient`
   - Add `getOCRConfig`, `updateOCRConfig`, `getOCRPresets` to `apiClient`
   - **Validation**: TypeScript compiles without errors

- [x] 7. **Create EmbeddingConfigPanel component**
   - Create `frontend/src/components/settings/EmbeddingConfigPanel.tsx`
   - Implement preset dropdown with descriptions
   - Implement advanced settings toggle
   - Implement form validation
   - Implement save functionality with React Query
   - **Validation**: Component renders, preset selection works

- [x] 8. **Create OCRConfigPanel component**
   - Create `frontend/src/components/settings/OCRConfigPanel.tsx`
   - Implement preset dropdown with descriptions
   - Implement two-tier settings (conditionally shown)
   - Implement form validation
   - Implement save functionality with React Query
   - **Validation**: Component renders, preset selection works

- [x] 9. **Integrate into Settings page**
   - Add tabs to `CollectionsConfigPage`: RAG / Embeddings / OCR
   - Wire up tab navigation
   - Ensure mobile responsiveness (test at 768px width)
   - **Validation**: All three panels accessible via tabs

- [x] 10. **Add performance hints and validation feedback**
    - Display estimated memory/speed impact for each preset
    - Show inline validation errors
    - Add success/error toast notifications
    - Add loading states
    - **Validation**: User feedback is clear and helpful

- [x] 11. **Write frontend tests**
    - Component rendering tests
    - Preset selection tests
    - Form validation tests
    - API integration tests (with MSW mocking)
    - **Validation**: All tests pass

## Phase 3: Dynamic Configuration

- [x] 12. **Wire dynamic embedding config into TaskManager**
    - Modify `TaskManager` to load config from `ConfigManager`
    - Pass `EmbeddingConfig` to `JinaEmbeddingsV4.embed()`
    - Remove hard-coded `.for_query()` and `.for_documents()` calls
    - **Validation**: Document processing uses configured settings

- [x] 13. **Wire dynamic OCR config into ingestion pipeline**
    - Modify document ingestion to load OCR config from `ConfigManager`
    - Pass `OCRConfig` to `NanonetsLoader`
    - Remove hard-coded preset usage
    - **Validation**: OCR processing uses configured settings

- [x] 14. **Add configuration change logging**
    - Log when configurations are updated
    - Include old/new values in logs
    - Track which preset is selected
    - **Validation**: Configuration changes visible in logs

- [x] 15. **Write integration tests**
    - E2E test: Change embedding config → process document → verify config used
    - E2E test: Change OCR config → upload PDF → verify config used
    - E2E test: Restart server → verify config persists
    - **Validation**: Configuration changes take effect in processing

## Phase 4: Polish and Documentation

- [x] 16. **Add hardware detection and auto-suggestions**
    - Detect Apple Silicon vs x86_64
    - Detect available system memory
    - Show recommended preset based on hardware
    - **Validation**: Recommendations shown in UI

- [x] 17. **Add configuration export/import (optional)**
    - Allow downloading current config as JSON
    - Allow uploading config JSON file
    - **Validation**: Config can be exported and re-imported

- [x] 18. **Update documentation**
    - Add configuration guide to `docs/guides/`
    - Explain when to use each preset
    - Add screenshots of UI
    - Document API endpoints in API docs
    - **Validation**: Documentation is clear and complete

- [x] 19. **Performance testing**
    - Verify config endpoints respond in <100ms
    - Verify UI is responsive on mobile (768px+)
    - Verify no memory leaks in React components
    - **Validation**: Performance targets met

- [x] 20. **Final validation and deployment prep**
    - Run full test suite
    - Test on production-like environment
    - Verify backward compatibility (no config set)
    - Create deployment checklist
    - **Validation**: Ready for production deployment
