# Deepseek OCR Configuration Reference

This guide documents the Deepseek OCR configuration surface exposed by the API, CLI, and frontend settings panel.

## Core Parameters

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `batch_size` | int (1–100) | 30 | Number of pages processed per batch. Larger batches increase throughput at the cost of memory. |
| `render_workers` | int (1–50) | 20 | Parallel PDF/PPTX render threads. Scale with available CPU cores. |
| `analysis_workers` | int (1–10) | 2 | Parallel Deepseek inference threads. Keep lower than render workers unless using vLLM. |
| `pre_render_batches` | int (1–10) | 4 | Batches pre-rendered ahead of analysis to keep the pipeline saturated. |
| `checkpoint_enabled` | bool | true | Enables crash-safe checkpoints in `./checkpoints/`. |
| `resolution_mode` | enum | `"base"` | Determines render resolution and token budget. |
| `enable_grounding` | bool | true | Emits bounding boxes (`bbox`) and grounding tokens for spatial metadata. |
| `enable_compression` | bool | true | Enables Deepseek optical compression (~10× fewer tokens). |
| `use_vllm` | bool | false | Routes inference through vLLM when available (CUDA-only). |

## Resolution Modes

| Mode | Resolution | Token Budget | Recommended Use | Notes |
| --- | --- | --- | --- | --- |
| `tiny` | 512×512 | ~64 tokens | High-volume ingestion of simple text | Grounding disabled automatically to maximise speed. |
| `small` | 640×640 | ~100 tokens | Mixed text with light tables/images | Best trade-off for balanced workloads. |
| `base` | 1024×1024 | ~256 tokens | Default general-purpose | Strong quality with grounding and compression enabled. |
| `large` | 1280×1280 | ~400 tokens | Dense tables, equations, diagrams | Increase `batch_size` cautiously to avoid OOM. |
| `gundam` | Dynamic (640×640 + 1024×1024) | Adaptive | Hybrid layouts with complex sections | Requires more VRAM; pair with vLLM for throughput. |

Switch modes via API:

```bash
curl -X POST http://localhost:8000/api/config/ocr \
  -H "Content-Type: application/json" \
  -d '{"resolution_mode": "large"}'
```

## Grounding & Compression

- **Grounding** (default on) produces bounding boxes and grounding token IDs in semantic regions. Disable only when metadata volume must be minimised.
- **Compression** (default on) activates Deepseek’s visual-text compression. Disable for debugging raw markdown or when investigating model hallucinations.

## vLLM Backend

Set `use_vllm=true` to run inference through vLLM. Requirements:
- Linux with CUDA 12.x
- GPU memory ≥24GB (A100-class recommended)
- Install extras: `pip install -e ".[production]"`

When enabled, throughput improvements of 5–10× are typical for large PDF batches. Adjust `analysis_workers` upward (e.g., 4) and increase `batch_size` as memory allows.

## Presets

Deepseek presets are available via API (`/api/config/ocr/presets`) and the frontend selector.

| Preset | Description | Configuration |
| --- | --- | --- |
| `deepseek_tiny` | Maximum speed for simple documents | `resolution_mode="tiny"`, `enable_grounding=false`, `batch_size=30` |
| `deepseek_small` | Balanced speed/quality | `resolution_mode="small"`, grounding+compression enabled |
| `deepseek_balanced` | Default quality | `resolution_mode="base"`, standard batch sizes |
| `deepseek_high_quality` | Dense technical documents | `resolution_mode="large"`, reduced batch size |
| `deepseek_gundam` | Mixed-layout adaptive mode | `resolution_mode="gundam"`, full grounding |
| `deepseek_production` | vLLM + Gundam for scale | `resolution_mode="gundam"`, `use_vllm=true`, `analysis_workers=4` |

Apply presets programmatically:

```python
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig

config = OCRConfig.deepseek_high_quality()
```

## Frontend Settings Panel

The React settings panel (`Settings → OCR`) mirrors these options:
- **Resolution Mode** dropdown displaying descriptions for each mode.
- Toggles for **Grounding**, **Optical Compression**, and **vLLM Backend**.
- Basic pipeline controls (batch size, worker counts, checkpoint toggle).
- Advanced help with tuning recommendations and preset characteristics.

Updates are persisted immediately via the `/api/config/ocr` endpoint and stored in `config/global_config.json`.

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `DEEPSEEK_OCR_ENABLED` | Explicitly enable/disable Deepseek loader (`true` by default). |
| `RUN_DEEPSEEK_INTEGRATION` | Enable integration tests that exercise full Deepseek inference. |
| `PROCESSING_PROFILE` | Optional profile override used in integration tests (`conservative`). |

## Troubleshooting

- **Model download stalls**: Ensure Hugging Face credentials are configured if the model is gated.  
- **Out of memory**: Lower `batch_size`, reduce `resolution_mode`, or disable `enable_grounding`.  
- **Slow throughput on CPU/MPS**: Install FlashAttention or vLLM extras when running on CUDA hardware.  
- **Missing bounding boxes**: Confirm `enable_grounding` is enabled and that the chosen resolution mode supports it (`tiny` disables grounding).

