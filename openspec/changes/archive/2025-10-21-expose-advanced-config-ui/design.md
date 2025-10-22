# Design: Expose Advanced Configuration UI

## Architectural Overview

This change extends the existing configuration system to expose backend `EmbeddingConfig` and `OCRConfig` capabilities through REST API endpoints and React frontend components. The design follows the established pattern used for `CollectionConfig` and `RAGConfigModel`.

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + TypeScript)           │
│                                                              │
│  ┌────────────────────┐  ┌─────────────────────┐           │
│  │ EmbeddingConfigPanel│ │  OCRConfigPanel    │           │
│  │                    │  │                     │           │
│  │ - Preset dropdown  │  │ - Preset dropdown   │           │
│  │ - Advanced toggle  │  │ - Advanced toggle   │           │
│  │ - Performance hints│  │ - Performance hints │           │
│  └─────────┬──────────┘  └──────────┬──────────┘           │
│            │                        │                       │
│            └────────┬───────────────┘                       │
│                     │                                       │
│              ┌──────▼─────────┐                             │
│              │ apiClient      │                             │
│              │ - getEmb...    │                             │
│              │ - updateEmb... │                             │
│              │ - getOCR...    │                             │
│              │ - updateOCR... │                             │
│              └──────┬─────────┘                             │
└─────────────────────┼─────────────────────────────────────────┘
                      │ HTTP/JSON
┌─────────────────────┼─────────────────────────────────────────┐
│                     ▼                                         │
│              ┌──────────────┐                                │
│              │ FastAPI App  │                                │
│              │              │                                │
│  ┌───────────┴──────────────┴───────────┐                  │
│  │                                        │                  │
│  │  GET  /api/config/embeddings          │                  │
│  │  POST /api/config/embeddings          │                  │
│  │  GET  /api/config/embeddings/presets  │                  │
│  │                                        │                  │
│  │  GET  /api/config/ocr                 │                  │
│  │  POST /api/config/ocr                 │                  │
│  │  GET  /api/config/ocr/presets         │                  │
│  │                                        │                  │
│  └───────────┬──────────────┬────────────┘                  │
│              │              │                                │
│    ┌─────────▼────┐   ┌─────▼─────────┐                    │
│    │EmbeddingConfig│  │   OCRConfig   │                    │
│    │  Model        │  │   Model       │                    │
│    │(Pydantic)     │  │  (Pydantic)   │                    │
│    └─────────┬────┘   └─────┬─────────┘                    │
│              │              │                                │
│    ┌─────────▼────┐   ┌─────▼─────────┐                    │
│    │EmbeddingConfig│  │   OCRConfig   │                    │
│    │  (dataclass)  │  │  (dataclass)  │                    │
│    └─────────┬────┘   └─────┬─────────┘                    │
│              │              │                                │
│    ┌─────────▼─────────────▼──────────┐                    │
│    │    Document Processing            │                    │
│    │                                    │                    │
│    │  - TaskManager                    │                    │
│    │  - JinaEmbeddingsV4               │                    │
│    │  - NanonetsLoader                 │                    │
│    └────────────────────────────────────┘                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Backend API Layer

#### New Pydantic Models

```python
# src/jina_rag_pipeline/api/models.py

class EmbeddingConfigModel(BaseModel):
    """Pydantic model for embedding configuration."""
    task: Literal[
        "retrieval.query",
        "retrieval.passage",
        "text-matching",
        "classification",
        "separation",
        "code.query",
        "code.passage"
    ] = "retrieval.passage"

    dimensions: Literal[128, 256, 512, 1024, 2048] = 1024
    late_chunking: bool = True
    return_multivector: bool = False
    embedding_format: Literal["float", "base64", "binary", "ubinary"] = "float"
    batch_size: int = Field(default=32, ge=1, le=256)
    max_tokens_per_batch: int = Field(default=8192, ge=1024, le=32768)


class OCRConfigModel(BaseModel):
    """Pydantic model for OCR configuration."""
    batch_size: int = Field(default=30, ge=1, le=100)
    render_workers: int = Field(default=20, ge=1, le=50)
    analysis_workers: int = Field(default=2, ge=1, le=10)
    pre_render_batches: int = Field(default=4, ge=1, le=10)
    checkpoint_enabled: bool = True

    # Two-tier hybrid settings
    use_two_tier: bool = False
    complexity_table_threshold: int = Field(default=1, ge=0, le=10)
    complexity_equation_threshold: int = Field(default=1, ge=0, le=10)
    complexity_image_threshold: int = Field(default=2, ge=0, le=10)
    complexity_min_text_length: int = Field(default=100, ge=0, le=1000)


class PresetInfo(BaseModel):
    """Information about a configuration preset."""
    name: str
    display_name: str
    description: str
    performance_characteristics: Dict[str, str]  # {"speed": "4× faster", "quality": "Good"}
```

#### New API Endpoints

```python
# src/jina_rag_pipeline/api/app.py

@app.get("/api/config/embeddings", response_model=EmbeddingConfigModel)
async def get_embedding_config():
    """Retrieve current embedding configuration."""
    # Return current global config
    pass

@app.post("/api/config/embeddings", response_model=EmbeddingConfigModel)
async def update_embedding_config(config: EmbeddingConfigModel):
    """Update global embedding configuration."""
    # Validate and apply new config
    # Persist to file or environment
    pass

@app.get("/api/config/embeddings/presets", response_model=List[PresetInfo])
async def get_embedding_presets():
    """List available embedding presets with descriptions."""
    return [
        PresetInfo(
            name="for_query",
            display_name="Query Optimized",
            description="Fast single-shot queries, no late chunking",
            performance_characteristics={"speed": "Fast", "dimensions": "1024", "storage": "8 KB/embedding"}
        ),
        PresetInfo(
            name="for_documents",
            display_name="Document Optimized",
            description="Late chunking for better context preservation",
            performance_characteristics={"speed": "Standard", "dimensions": "1024", "storage": "8 KB/embedding"}
        ),
        PresetInfo(
            name="fast",
            display_name="Fast",
            description="4× faster with 512 dimensions",
            performance_characteristics={"speed": "4× faster", "dimensions": "512", "storage": "2 KB/embedding"}
        ),
        PresetInfo(
            name="storage_optimized",
            display_name="Storage Optimized",
            description="8× smaller storage with ubinary format",
            performance_characteristics={"speed": "Standard", "dimensions": "512", "storage": "64 bytes/embedding"}
        ),
        PresetInfo(
            name="memory_constrained",
            display_name="Memory Constrained",
            description="Auto-scaled for low memory systems",
            performance_characteristics={"speed": "Variable", "dimensions": "Auto", "storage": "Auto"}
        ),
    ]

@app.get("/api/config/ocr", response_model=OCRConfigModel)
async def get_ocr_config():
    """Retrieve current OCR configuration."""
    pass

@app.post("/api/config/ocr", response_model=OCRConfigModel)
async def update_ocr_config(config: OCRConfigModel):
    """Update global OCR configuration."""
    pass

@app.get("/api/config/ocr/presets", response_model=List[PresetInfo])
async def get_ocr_presets():
    """List available OCR presets with descriptions."""
    return [
        PresetInfo(
            name="mlx_optimized",
            display_name="MLX Optimized",
            description="Best performance on Apple Silicon (M1/M2/M3)",
            performance_characteristics={"speed": "Fast", "memory": "2.2 GB", "workers": "1 (MLX limitation)"}
        ),
        PresetInfo(
            name="balanced",
            display_name="Balanced",
            description="Good balance of speed and quality",
            performance_characteristics={"speed": "Standard", "memory": "~8 GB", "workers": "2"}
        ),
        PresetInfo(
            name="two_tier",
            display_name="Two-Tier Hybrid",
            description="2× faster using FAST + BALANCED routing",
            performance_characteristics={"speed": "2× faster", "memory": "~8 GB", "workers": "2"}
        ),
        PresetInfo(
            name="memory_constrained",
            display_name="Memory Constrained",
            description="Auto-scaled for systems with limited RAM",
            performance_characteristics={"speed": "Variable", "memory": "Auto-scaled", "workers": "Auto"}
        ),
    ]
```

#### Configuration Persistence

Based on code review, follow the existing `CollectionConfig` pattern:

```python
# Store in data/global_config.json
{
    "embeddings": {
        "task": "retrieval.passage",
        "dimensions": 1024,
        "late_chunking": true,
        "return_multivector": false,
        "embedding_format": "float",
        "batch_size": 32,
        "max_tokens_per_batch": 8192
    },
    "ocr": {
        "batch_size": 30,
        "render_workers": 20,
        "analysis_workers": 2,
        "pre_render_batches": 4,
        "checkpoint_enabled": true,
        "use_two_tier": false,
        "complexity_table_threshold": 1,
        "complexity_equation_threshold": 1,
        "complexity_image_threshold": 2,
        "complexity_min_text_length": 100
    }
}
```

**ConfigManager Implementation** (following CollectionConfig pattern):
```python
class ConfigManager:
    def __init__(self, config_dir: Path = Path("data")):
        self.config_file = config_dir / "global_config.json"
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)

    def load_config(self) -> Dict:
        if not self.config_file.exists():
            return self.get_defaults()
        return json.loads(self.config_file.read_text())

    def save_config(self, config: Dict) -> None:
        # Atomic write pattern from CollectionConfig
        temp_file = self.config_file.with_suffix('.tmp')
        temp_file.write_text(json.dumps(config, indent=2))
        temp_file.replace(self.config_file)
```

### 2. Frontend Components

#### EmbeddingConfigPanel Component

```typescript
// frontend/src/components/settings/EmbeddingConfigPanel.tsx

interface EmbeddingConfig {
  task: string;
  dimensions: number;
  late_chunking: boolean;
  return_multivector: boolean;
  embedding_format: string;
  batch_size: number;
  max_tokens_per_batch: number;
}

interface PresetInfo {
  name: string;
  display_name: string;
  description: string;
  performance_characteristics: Record<string, string>;
}

export default function EmbeddingConfigPanel() {
  const [selectedPreset, setSelectedPreset] = useState<string>('for_documents');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [config, setConfig] = useState<EmbeddingConfig>(...);
  const [presets, setPresets] = useState<PresetInfo[]>([]);

  // Fetch current config and presets on mount
  useEffect(() => {
    fetchConfig();
    fetchPresets();
  }, []);

  // Load preset when selected
  const handlePresetChange = async (presetName: string) => {
    const presetConfig = await apiClient.getEmbeddingPreset(presetName);
    setConfig(presetConfig);
    setSelectedPreset(presetName);
  };

  // UI: Preset dropdown at top
  // UI: Performance characteristics display
  // UI: "Advanced Settings" toggle
  // UI: Advanced fields (conditionally shown)
  // UI: Save button
}
```

#### OCRConfigPanel Component

```typescript
// frontend/src/components/settings/OCRConfigPanel.tsx

interface OCRConfig {
  batch_size: number;
  render_workers: number;
  analysis_workers: number;
  pre_render_batches: number;
  checkpoint_enabled: boolean;
  use_two_tier: boolean;
  complexity_table_threshold: number;
  complexity_equation_threshold: number;
  complexity_image_threshold: number;
  complexity_min_text_length: number;
}

export default function OCRConfigPanel() {
  // Similar structure to EmbeddingConfigPanel
  // Preset dropdown (mlx_optimized, balanced, two_tier, memory_constrained)
  // Performance characteristics
  // Advanced settings toggle
  // Two-tier specific controls (conditionally shown)
}
```

#### Integration into Settings Page

```typescript
// frontend/src/components/settings/CollectionsConfigPage.tsx

export default function CollectionsConfigPage() {
  const [activeTab, setActiveTab] = useState<'rag' | 'embeddings' | 'ocr'>('rag');

  return (
    <div>
      <TabNavigation>
        <Tab active={activeTab === 'rag'} onClick={() => setActiveTab('rag')}>
          RAG Settings
        </Tab>
        <Tab active={activeTab === 'embeddings'} onClick={() => setActiveTab('embeddings')}>
          Embeddings
        </Tab>
        <Tab active={activeTab === 'ocr'} onClick={() => setActiveTab('ocr')}>
          OCR Processing
        </Tab>
      </TabNavigation>

      {activeTab === 'rag' && <RAGConfigPanel />}
      {activeTab === 'embeddings' && <EmbeddingConfigPanel />}
      {activeTab === 'ocr' && <OCRConfigPanel />}
    </div>
  );
}
```

### 3. UI/UX Design Principles

#### Preset-First Design

1. **Preset Dropdown at Top**: Most prominent control, encouraged as primary interaction
2. **Descriptions with Performance Hints**: Each preset shows speed/memory/quality tradeoffs
3. **Advanced Toggle**: Hidden by default, reveal on click
4. **Custom Preset**: Special preset that unlocks all controls

#### Performance Visualization

```tsx
<PerformanceIndicator>
  <Metric label="Speed" value="4× faster" color="green" />
  <Metric label="Quality" value="Good" color="yellow" />
  <Metric label="Storage" value="2 KB/embedding" color="green" />
</PerformanceIndicator>
```

#### Validation and Feedback

- Real-time validation with inline error messages
- Warning badges for potentially problematic configurations (e.g., very high batch_size)
- Success toast on save
- Estimated memory impact display

## Data Flow

### Configuration Update Flow

```
User selects preset
    ↓
Frontend calls GET /api/config/embeddings/presets/{preset_name}
    ↓
Backend returns preset configuration
    ↓
Frontend displays configuration
    ↓
User optionally modifies advanced settings
    ↓
User clicks "Save"
    ↓
Frontend calls POST /api/config/embeddings
    ↓
Backend validates configuration
    ↓
Backend writes to data/global_config.json
    ↓
Backend updates state.config_manager
    ↓
Backend returns updated configuration
    ↓
Frontend shows success message
    ↓
Future uploads/queries use new configuration
```

### Integration with TaskManager

**Current Hard-Coded Usage** (to be replaced):
```python
# src/jina_rag_pipeline/api/tasks.py - Lines 652, 747, 766, 837
config = EmbeddingConfig.for_documents()  # Hard-coded
embeddings = await embedder.embed_with_config(chunks, config)
```

**New Dynamic Usage**:
```python
# Load configuration from ConfigManager
if state.config_manager:
    global_config = state.config_manager.load_config()
    embedding_config_dict = global_config.get("embeddings", {})
    config = EmbeddingConfig(**embedding_config_dict)
else:
    # Fallback to defaults
    config = EmbeddingConfig.for_documents()

# Use dynamic config
embeddings = await embedder.embed_with_config(chunks, config)
```

**OCR Integration** (already supports dynamic config):
```python
# src/jina_rag_pipeline/ingestion/nanonets_loader.py
def __init__(self, config: Optional[OCRConfig] = None):
    if config is None:
        # Auto-select based on hardware
        config = OCRConfig.mlx_optimized() if _is_apple_silicon() else OCRConfig.balanced()
```

**Modified OCR Usage in TaskManager**:
```python
# Load OCR configuration
if state.config_manager:
    global_config = state.config_manager.load_config()
    ocr_config_dict = global_config.get("ocr", {})
    ocr_config = OCRConfig(**ocr_config_dict)
else:
    ocr_config = None  # NanonetsLoader will auto-select

# Use dynamic config
loader = NanonetsLoader(config=ocr_config)
```

## Implementation Phases

### Phase 1: Backend API (No Behavior Change)
- Add Pydantic models
- Add GET/POST endpoints
- Add preset enumeration endpoints
- Add config persistence layer
- **Result**: APIs exist but return hard-coded defaults

### Phase 2: Frontend UI
- Add EmbeddingConfigPanel component
- Add OCRConfigPanel component
- Integrate into Settings page
- Add TypeScript types
- **Result**: Users can view and change configs via UI

### Phase 3: Dynamic Configuration
- Modify TaskManager to accept config parameters
- Modify JinaEmbeddingsV4 to use dynamic configs
- Modify NanonetsLoader to use dynamic configs
- **Result**: Configuration changes take effect

### Phase 4: Enhancements
- Add config usage analytics
- Add hardware detection and auto-suggestion
- Add configuration export/import
- **Result**: Better UX and power-user features

## Testing Strategy

### Backend Tests
- Unit tests for Pydantic model validation
- Integration tests for API endpoints
- Configuration persistence tests
- Invalid configuration rejection tests

### Frontend Tests
- Component rendering tests (React Testing Library)
- Preset selection tests
- Advanced settings toggle tests
- API integration tests (MSW for mocking)

### E2E Tests
- Full configuration change workflow
- Verify config persists across sessions
- Verify config changes affect processing

## Performance Considerations

- Configuration endpoints should be lightweight (<100ms response)
- Use React Query caching to avoid repeated fetches
- Optimistic UI updates for better UX
- Lazy load advanced options to reduce initial bundle size

## Security Considerations

- Validate all inputs server-side (Pydantic validation)
- No sensitive information in configurations
- Rate limit configuration update endpoints
- Log configuration changes for audit trail

## Backward Compatibility

- Existing API behavior unchanged when no config is set
- Default configurations match current hard-coded values
- No database schema changes required
