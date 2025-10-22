# 10-Minute Processing Target Analysis

## Goal: 96 pages in 10 minutes

**Target**: 6.25 seconds per page
**Current**: 80 seconds per page
**Required Speedup**: 12.8x faster

## Current Bottleneck Breakdown

```
Current per-page time (80 sec):
├─ PDF Rendering: ~44 sec (55%)
└─ MLX Inference: ~36 sec (45%)

To reach 10 minutes total:
├─ PDF Rendering: Must be <3 sec/page
└─ MLX Inference: Must be <3 sec/page
```

## Strategies to Reach 10 Minutes

### Strategy 1: Multi-Process MLX Instances ⭐ Most Promising

**Concept**: Run 10+ separate Python processes, each with own MLX model

**Architecture**:
```python
# Master process
processes = []
for i in range(10):  # 10 workers
    p = Process(target=analyze_pages, args=(pages_chunk, model_path))
    processes.append(p)
    p.start()

# Each process:
# - Loads own MLX model instance (2.2 GB)
# - Processes 10 pages independently
# - No shared memory conflicts
```

**Performance Math**:
```
Single worker: 36 sec/page
10 workers:    36 sec / 10 = 3.6 sec/page effective
96 pages:      96 × 3.6 / 10 = 34 minutes (still too slow)

Need 15+ workers for 10 minute target
```

**Memory Requirements**:
```
15 processes × 2.2 GB = 33 GB (fits in 48 GB)
+ Rendering buffers: ~10 GB
Total: ~43 GB (feasible!)
```

**Implementation Complexity**: Medium
- Process pool management
- Inter-process communication
- Result aggregation
- Checkpoint coordination

**Estimated speedup**: 10-15x (with 15 workers)
**Time for 96 pages**: 10-15 minutes ✅

---

### Strategy 2: Smaller/Faster Model ⭐ Quick Win

**Current**: Nanonets OCR2-3B (3B parameters)
**Alternative**: Qwen2-VL-2B or specialized OCR model

**Options**:

#### A) Qwen2-VL-2B-Instruct
- Size: 2B parameters (vs 3B)
- Speed: ~1.5-2x faster inference
- Quality: Slightly lower but still good
- Memory: ~1.5 GB loaded

**Expected**: 36 sec → 18-24 sec/page
**Not enough for 10 min target**

#### B) PaddleOCR / EasyOCR
- Pure OCR (no VLM overhead)
- Speed: 1-2 sec/page
- Quality: Text only, no layout understanding
- **Tradeoff**: Lose semantic region extraction

#### C) TrOCR / Donut
- Document-specific transformers
- Speed: 5-10 sec/page
- Quality: Good for structured docs
- **Better balance**

**Estimated speedup**: 2-10x (depending on model)
**Time for 96 pages**: 15-40 minutes ❌ (still not 10 min)

---

### Strategy 3: GPU Acceleration 🚀 Game Changer

**MLX is CPU-only**. Switch to GPU for massive speedup.

**Option A: Local GPU (if available)**
```
NVIDIA RTX 4090:
- Qwen2.5-VL inference: 2-5 sec/page
- Batch processing: 10 pages in 15 seconds
- 96 pages: ~2.5 minutes ✅
```

**Option B: Cloud GPU**
```
AWS g5.xlarge (A10G GPU):
- Cost: ~$1/hour
- Inference: 3-8 sec/page
- 96 pages: 5-10 minutes ✅
- Total cost: <$0.50 per document
```

**Implementation**:
- Use `transformers` with CUDA
- Same Nanonets model, different backend
- No MLX (switch to PyTorch GPU)

**Estimated speedup**: 10-20x
**Time for 96 pages**: 5-10 minutes ✅

---

### Strategy 4: Extreme Pipeline Optimization

**Current pipeline**:
```
Render → Analyze → Render → Analyze
```

**Optimized pipeline**:
```
1. Pre-render ALL 96 pages (5 minutes with 30 workers)
2. Process all with 15 MLX instances (35 minutes)
Total: 40 minutes (not enough)
```

**Estimated speedup**: 1.5-2x
**Time for 96 pages**: 40-50 minutes ❌

---

### Strategy 5: Hybrid Approach 🎯 RECOMMENDED

**Combine multiple strategies for maximum impact**

#### Configuration:
```python
1. Use 4-bit quantized model (vs 8-bit)
   → 2x faster inference (36s → 18s)

2. Run 8 parallel processes
   → 8x parallelism

3. Pre-render everything with 30 workers
   → Eliminate rendering wait

4. Use lower resolution (150 DPI vs 300 DPI)
   → 2x faster rendering + inference
```

#### Math:
```
Base: 80 sec/page

Optimizations:
- 4-bit quantization: ÷2 = 40 sec
- 8 parallel processes: ÷8 = 5 sec
- Lower resolution: ÷2 = 2.5 sec
- Pre-rendering: No wait

Effective: 2.5 sec/page × 96 pages = 4 minutes ✅
```

#### Quality Tradeoff:
- 4-bit quantization: Minimal quality loss
- Lower resolution: Acceptable for most documents
- Parallel processing: No quality loss

**Estimated speedup**: 15-20x
**Time for 96 pages**: 4-6 minutes ✅

---

## Practical Recommendations

### Option 1: Multi-Process MLX (Conservative) ✅

**Changes needed**:
1. Implement process-based parallelism
2. 15 worker processes
3. Memory: 33 GB used

**Code outline**:
```python
from multiprocessing import Process, Queue

def worker_process(pages, model_path, result_queue):
    analyzer = NanonetsMLXAnalyzer(model_path)
    for page in pages:
        result = analyzer.analyze_document(page)
        result_queue.put(result)

# Split pages into 15 chunks
page_chunks = split_pages(96, num_chunks=15)

processes = []
result_queue = Queue()

for chunk in page_chunks:
    p = Process(target=worker_process, args=(chunk, model_path, result_queue))
    p.start()
    processes.append(p)

# Collect results
for p in processes:
    p.join()
```

**Timeline**: 2-3 days implementation
**Result**: 10-15 minutes for 96 pages

---

### Option 2: Cloud GPU (Fast & Easy) ✅✅

**Changes needed**:
1. Switch from MLX to PyTorch + CUDA
2. Use AWS g5.xlarge or similar
3. Batch inference (10 pages at once)

**Code outline**:
```python
# Instead of MLX
from transformers import Qwen2VLForConditionalGeneration
import torch

model = Qwen2VLForConditionalGeneration.from_pretrained(
    "nanonets/nanonets-ocr2-3b",
    torch_dtype=torch.float16,  # Half precision
    device_map="cuda"  # GPU
)

# Batch processing
images = [load_image(p) for p in pages[:10]]
results = model.generate(images, batch_size=10)
```

**Timeline**: 1 day implementation
**Cost**: $0.50 per 96-page document
**Result**: 5-10 minutes for 96 pages

---

### Option 3: 4-bit Quantization + Multi-Process (Best Balance) ✅✅✅

**Changes needed**:
1. Convert model to 4-bit (vs 8-bit)
2. 10 worker processes
3. Pre-render all pages

**Steps**:
```bash
# Convert to 4-bit
mlx_vlm.convert \
  --hf-path nanonets/nanonets-ocr2-3b \
  --mlx-path ./models/nanonets-4bit-mlx \
  --quantize \
  -q 4  # 4-bit quantization

# Implement multi-process
python process_multiprocess_mlx.py --workers 10
```

**Memory**: 10 × 1.2 GB = 12 GB (plenty of headroom)
**Quality**: Minimal degradation
**Timeline**: 2-3 days implementation
**Result**: 6-8 minutes for 96 pages

---

## Comparison Table

| Strategy | Speedup | Time (96p) | Memory | Cost | Complexity | Quality Loss |
|----------|---------|------------|--------|------|------------|--------------|
| **Current MLX** | 1x | 120 min | 2.5 GB | $0 | Low | None |
| **Optimized Pipeline** | 1.6-2x | 60-75 min | 2.5 GB | $0 | Low | None |
| **15 MLX Processes** | 10-12x | 10-12 min | 33 GB | $0 | Medium | None |
| **Cloud GPU (A10G)** | 15-20x | 5-10 min | N/A | $0.50 | Low | None |
| **4-bit + 10 Processes** | 15-18x | 6-8 min | 12 GB | $0 | Medium | <5% |
| **Smaller Model** | 2-3x | 30-40 min | 1.5 GB | $0 | Low | 10-15% |

---

## My Recommendation: 4-bit + Multi-Process 🎯

**Why**:
1. ✅ Achieves 6-8 minute target (close to 10 min)
2. ✅ Runs on your hardware (no cloud costs)
3. ✅ Minimal quality loss (<5%)
4. ✅ Reasonable implementation (2-3 days)
5. ✅ Memory efficient (12 GB vs 33 GB)

**Implementation Plan**:

### Phase 1: 4-bit Quantization (Day 1)
```bash
# Test 4-bit conversion
mlx_vlm.convert --hf-path nanonets/nanonets-ocr2-3b \
                --mlx-path ./models/nanonets-4bit-mlx \
                --quantize -q 4

# Benchmark quality
python benchmark_quality.py --model 4bit --model 8bit --compare
```

### Phase 2: Multi-Process Framework (Day 2)
```python
# Create multiprocess_mlx_loader.py
class MultiProcessMLXLoader:
    def __init__(self, num_workers=10):
        self.num_workers = num_workers

    def load(self, file_path):
        # Split pages
        pages = split_pdf(file_path, num_workers)

        # Process in parallel
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            futures = [executor.submit(analyze_chunk, chunk)
                      for chunk in pages]
            results = [f.result() for f in futures]

        return merge_results(results)
```

### Phase 3: Integration & Testing (Day 3)
```bash
# Test on sample document
python test_multiprocess.py --workers 10 --pages 20

# Full document
python process_multiprocess.py --workers 10
```

**Expected Outcome**: **6-8 minutes for 96 pages** with <5% quality degradation

---

## Quick Win: Cloud GPU (If Speed Is Critical)

If you need 10 minutes **NOW**:

```bash
# 1. Launch AWS EC2 g5.xlarge (~$1/hour)
# 2. Install PyTorch + CUDA
# 3. Use GPU inference

python process_gpu.py --batch-size 10
# → 5-10 minutes for 96 pages
# → Cost: $0.50 per document
```

**Trade-off**: $0.50 per document vs free local processing

---

## Bottom Line

To reach **10 minutes for 96 pages**, you need one of:

1. **15+ parallel MLX processes** (10-12 min, free, 33 GB RAM)
2. **Cloud GPU** (5-10 min, $0.50/doc, easiest)
3. **4-bit quantization + 10 processes** (6-8 min, free, 12 GB RAM) ⭐ BEST

Current optimized pipeline (60-75 min) is a **huge improvement** from 2 hours, but reaching 10 minutes requires either:
- Throwing more compute at it (multiple processes/GPUs)
- Sacrificing some quality (4-bit quantization, lower resolution)

**My vote**: Implement 4-bit + multi-process for **6-8 minute processing** with minimal quality loss.
