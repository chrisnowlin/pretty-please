# 4-Bit Quantization Prototype

## What We're Testing

Converting the Nanonets OCR model from **8-bit → 4-bit quantization** to achieve:
- **Target**: 2x faster inference
- **Memory**: ~1.2 GB per model instance (vs 2.2 GB)
- **Quality**: <5% degradation (acceptable)

## Why 4-Bit?

With 4-bit quantization + 10 parallel processes:
```
Current:  36 sec/page × 96 pages = 57 minutes
4-bit:    18 sec/page × 96 pages / 10 workers = 2.9 minutes per worker
                                                = ~6 minutes total ✅
```

## Testing Pipeline

### Step 1: Convert Model (In Progress)
```bash
./convert_4bit.sh
```

**What it does**:
- Downloads Nanonets model from HuggingFace
- Converts to MLX format with 4-bit quantization
- Saves to `./models/nanonets-ocr2-3b-mlx-4bit/`

**Output**:
- Model size: ~1.6 GB on disk (vs 3.1 GB for 8-bit)
- Loaded memory: ~1.2 GB (vs 2.2 GB for 8-bit)

**Status**: Running (~10-15 minutes)
**Monitor**: `tail -f 4bit_conversion.log`

### Step 2: Benchmark Speed
```bash
./benchmark_4bit_vs_8bit.py
```

**What it does**:
- Tests both 8-bit and 4-bit models on same image
- Runs 5 iterations each for statistical accuracy
- Measures inference time and memory usage

**Output**:
- Average inference time for each model
- Speedup calculation (target: ≥1.8x)
- Memory comparison
- Projection for 96 pages with 10 workers

**Expected results**:
```
8-bit: 35.6 sec/image, 2.2 GB memory
4-bit: ~18 sec/image, 1.2 GB memory
Speedup: 2x faster
```

### Step 3: Compare Quality
```bash
./compare_quality.py
```

**What it does**:
- Analyzes same document with both models
- Character-level similarity comparison
- Semantic region extraction comparison
- Saves sample outputs for visual inspection

**Output**:
- Similarity score (target: ≥95%)
- Difference analysis
- Sample files in `quality_comparison_samples/`

**Acceptable quality loss**: <5% (≥95% similarity)

## Decision Criteria

### ✅ Proceed with 4-bit if:
- Speedup ≥ 1.8x (target: 2x)
- Quality similarity ≥ 95%
- No significant structural differences

### ⚠️ Careful evaluation if:
- Speedup 1.3-1.8x (moderate gain)
- Quality similarity 90-95% (noticeable loss)

### ❌ Reject 4-bit if:
- Speedup < 1.3x (insufficient gain)
- Quality similarity < 90% (unacceptable loss)

## Next Steps After Testing

### If 4-bit passes (likely):

1. **Update profiles**:
   ```python
   # Use 4-bit model instead of 8-bit
   model_path="./models/nanonets-ocr2-3b-mlx-4bit"
   ```

2. **Implement multi-process**:
   - 10 worker processes
   - Each with own 4-bit model instance
   - Memory: 10 × 1.2 GB = 12 GB total

3. **Expected performance**:
   ```
   Single worker (4-bit): 18 sec/page
   10 workers parallel:   18 / 10 = 1.8 sec/page effective
   96 pages total:        96 × 1.8 / 60 = 2.9 minutes ✅ ✅
   ```

## Memory Analysis

### Current (8-bit, single worker):
```
Model: 2.2 GB
Buffers: 0.5 GB
Total: 2.7 GB
Available: 45.3 GB unused
```

### Proposed (4-bit, 10 workers):
```
Models: 10 × 1.2 GB = 12 GB
Render buffers: ~5 GB
Python overhead: ~2 GB
Total: ~19 GB
Available: 29 GB free (safe)
```

### Could scale to 15 workers:
```
Models: 15 × 1.2 GB = 18 GB
Total: ~25 GB
Time for 96 pages: ~2 minutes
```

## Files Created

- `convert_4bit.sh` - Model conversion script
- `benchmark_4bit_vs_8bit.py` - Speed benchmark
- `compare_quality.py` - Quality comparison
- `4bit_conversion.log` - Conversion progress log
- `4bit_8bit_benchmark_results.json` - Speed test results
- `quality_comparison_samples/` - Sample outputs

## Monitoring Progress

### Check conversion status:
```bash
tail -f 4bit_conversion.log
```

### Check if conversion complete:
```bash
ls -lh ./models/nanonets-ocr2-3b-mlx-4bit/
```

Should show:
- `config.json`
- `model.safetensors` (~1.6 GB)
- `tokenizer.json`
- Other config files

## Timeline

```
[Now]        4-bit conversion started (10-15 min)
   ↓
[+15 min]    Run benchmark_4bit_vs_8bit.py (5-10 min)
   ↓
[+25 min]    Run compare_quality.py (3-5 min)
   ↓
[+30 min]    Analyze results
   ↓
[Decision]   If good → implement multi-process
             If bad → try other approaches
```

## Expected Outcome

**Most likely scenario**: 4-bit quantization works well
- 1.8-2.2x speedup ✅
- 95-98% quality similarity ✅
- 1.2 GB memory per worker ✅

**This enables**: 10-worker parallel processing
- **6-8 minutes for 96 pages** (vs 2 hours originally)
- **10-15x total speedup** from baseline
- **No cloud costs** (runs locally)

**Final comparison**:
| Approach | Time (96p) | Cost | Quality |
|----------|------------|------|---------|
| Original (PyTorch) | 2 hours | $0 | 100% |
| MLX 8-bit optimized | 60-75 min | $0 | 100% |
| **MLX 4-bit + 10 workers** | **6-8 min** | **$0** | **95%+** |
| Cloud GPU (A10G) | 5-10 min | $0.50 | 100% |

The 4-bit approach gives us near-cloud-GPU performance **for free**, running entirely on local hardware.
