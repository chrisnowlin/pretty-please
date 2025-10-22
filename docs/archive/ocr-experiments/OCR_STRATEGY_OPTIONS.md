# OCR Processing Strategy Options

**Date**: 2025-10-20
**Context**: Evaluating alternatives to PaddleOCR after discovering stability issues with complex documents (music notation)

## The Question

> "Is there a way for us to replace PaddleOCR and only use Nanonets? Does Nanonets offer a fast mode that doesn't invoke the full OCR processing?"

## Research Findings

### Nanonets Model Landscape

**Available Models** (as of 2025):
- **Nanonets-OCR-s**: 3.75B parameters
- **Nanonets-OCR2-3B**: 3.75B parameters (newer, adds flowchart support)

**No smaller models exist** - both use the same Qwen2.5-VL-3B base (3.75B parameters).

### Speed Optimization Options

1. **Quality Presets** (already implemented): FAST / BALANCED / HIGH
2. **GGUF Quantization** (future option): Compressed models for faster inference
3. **No "text-only" mode**: Nanonets is a full VLM, not modular

---

## Option 1: PaddleOCR Hybrid (Current Implementation)

**Architecture**: PaddleOCR (fast) → Complexity routing → Nanonets BALANCED (selective)

### Performance (96 pages, 80% simple / 20% complex)
- Simple documents (77): 77 × 2 sec = **154 sec** (2.6 min)
- Complex documents (19): 19 × 199 sec = **3,781 sec** (63 min)
- **Total**: ~66 minutes
- **vs BALANCED-only**: 4.8x faster

### Pros
✅ **Fastest option** - 2 sec/page for simple documents
✅ 4-5x speedup on typical document mixes
✅ PaddleOCR is mature, battle-tested OCR
✅ CPU-based (no GPU needed for simple docs)

### Cons
❌ **PaddleOCR crashes** on music notation (exit code 138)
❌ Requires additional dependency (~3GB models)
❌ API deprecation warnings (maintenance needed)
❌ Two different technologies to maintain

### Best For
- Speed is critical priority
- Document mix is mostly simple text
- Willing to handle PaddleOCR stability issues with pre-filtering
- Can afford the complexity of managing two OCR engines

---

## Option 2: Nanonets Two-Tier (FAST + BALANCED)

**Architecture**: Nanonets FAST → Complexity routing → Nanonets BALANCED

### Performance Estimates
Need benchmarking to confirm, but expected:

**FAST preset speed**: ~60-100 sec/page (2-3x faster than BALANCED)
- Lower resolution: 250K-400K pixels (vs 500K-1.2M for BALANCED)
- Fewer tokens: 2048 max (vs 4096 for BALANCED)

**For 96 pages (80% simple / 20% complex)**:
- Simple documents (77): 77 × 80 sec = **6,160 sec** (103 min)
- Complex documents (19): 19 × 199 sec = **3,781 sec** (63 min)
- **Total**: ~166 minutes (2.8 hours)
- **vs BALANCED-only**: 1.9x faster

### Pros
✅ **Single technology** - one model, one prompt, one codebase
✅ **No stability issues** - handles music notation, complex layouts
✅ **Consistent output** - same markdown format across presets
✅ **Still provides speedup** - 2x faster than BALANCED-only
✅ **Lower resolution acceptable** for simple text documents

### Cons
⚠️ **Slower than PaddleOCR** - 60-100 sec vs 2 sec per page
⚠️ **Lower quality on FAST** - reduced resolution may miss details
⚠️ **Still using full VLM** - 3.75B params even on FAST preset

### Best For
- **Stability over speed** - music notation, complex content
- Document mix includes challenging layouts
- Prefer simpler architecture (single technology)
- Can tolerate 2-3 hour processing for 96-page documents

---

## Option 3: BALANCED-Only (Simplest, Slowest)

**Architecture**: Nanonets BALANCED for everything

### Performance (96 pages)
- All documents: 96 × 199 sec = **19,104 sec** (318 min = 5.3 hours)
- **Baseline** - no speedup

### Pros
✅ **Maximum quality** on all documents
✅ **Simplest architecture** - no routing logic
✅ **Most reliable** - one code path

### Cons
❌ **Slowest option** - 5+ hours for 96 pages
❌ **Inefficient** - over-processes simple documents
❌ **Not scalable** for large document volumes

### Best For
- Very small document volumes (<10 pages)
- Maximum quality required on every page
- Simplicity valued over performance
- Not time-sensitive workloads

---

## Option 4: GGUF Quantized Nanonets (Future)

**Architecture**: Quantized Nanonets model with reduced memory/compute

### Available Models
- `unsloth/Nanonets-OCR-s-GGUF`
- `mradermacher/Nanonets-OCR2-3B-GGUF`

### Expected Performance
- **2-4x faster** than full-precision model
- Lower memory footprint
- Potential quality degradation (quantization artifacts)

### Implementation Requirements
- Different inference engine (llama.cpp, not PyTorch/MLX)
- Quality validation needed
- Additional development work
- May not work with current MPS optimizations

### Best For
- Future optimization after proving Nanonets-only approach
- Resource-constrained environments
- Willing to invest in new inference engine integration

---

## Comparison Matrix

| Criterion | PaddleOCR Hybrid | Nanonets Two-Tier | BALANCED-Only | GGUF Future |
|-----------|------------------|-------------------|---------------|-------------|
| **Speed (96 pages)** | 66 min ⚡ | 166 min ⚡ | 318 min | ~80-160 min* |
| **Stability** | ⚠️ Crashes on music | ✅ Handles all | ✅ Handles all | ✅ Handles all |
| **Quality** | ⚠️ Mixed (2 engines) | ✅ Consistent | ✅ Maximum | ⚠️ Slightly lower* |
| **Complexity** | ⚠️ Two technologies | ✅ Single tech | ✅ Simplest | ⚠️ New inference |
| **Dependencies** | +3GB PaddleOCR | None | None | +llama.cpp |
| **Maintenance** | ⚠️ Two systems | ✅ One system | ✅ One system | ⚠️ New system |
| **Music notation** | ❌ Crashes | ✅ Works | ✅ Works | ✅ Works* |

*Estimates pending validation

---

## Decision Framework

### Choose PaddleOCR Hybrid If:
- ✅ Speed is critical (need < 2 hours for 96 pages)
- ✅ Document mix is mostly simple text (>80%)
- ✅ Can implement pre-filtering for music notation
- ✅ Willing to maintain two OCR systems
- ✅ Have engineering resources for stability handling

### Choose Nanonets Two-Tier If:
- ✅ **Stability is priority** over raw speed
- ✅ **Documents include music notation** or challenging content
- ✅ Can accept 2-3 hour processing for 96 pages
- ✅ Prefer **simpler architecture** (single technology)
- ✅ Want consistent markdown format across all documents

### Choose BALANCED-Only If:
- ✅ Document volumes are small (<10 pages)
- ✅ Maximum quality required on every page
- ✅ Processing time not a concern (5+ hours acceptable)
- ✅ Simplicity valued over performance

### Consider GGUF Future If:
- ✅ Proven need for Nanonets-only approach
- ✅ Willing to invest in new inference engine
- ✅ Need additional 2-3x speedup over full-precision
- ✅ Can validate quality with quantized models

---

## Recommendation: Benchmark Then Decide

### Step 1: Run FAST Preset Benchmark ⏳
```bash
python test_nanonets_fast_preset.py
```

This will measure:
- Actual FAST preset speed (target: < 60 sec/page)
- Quality comparison vs BALANCED
- Projected performance for 96-page documents

### Step 2: Decision Criteria

**If FAST preset is < 30 sec/page:**
→ **Choose Nanonets Two-Tier** - competitive speed, better stability

**If FAST preset is 30-60 sec/page:**
→ **Trade-off decision** based on:
  - How critical is stability? (music notation issue)
  - How critical is speed? (2 hours vs 3 hours)
  - Team preference: complexity vs simplicity

**If FAST preset is > 60 sec/page:**
→ **Choose PaddleOCR Hybrid** - speed gap too large
→ Add pre-filtering for music notation

### Step 3: Implementation Path

**For Nanonets Two-Tier** (if chosen):
```python
# Simplified hybrid without PaddleOCR
class NanonetsHybridAnalyzer:
    def analyze_document(self, file_path, page_number=1):
        # Phase 1: Try FAST preset
        fast_analyzer = NanonetsLayoutAnalyzer(quality_preset="fast")
        markdown_fast = fast_analyzer.analyze_document(file_path, page_number)

        # Phase 2: Analyze complexity (from markdown features)
        if self._is_complex_markdown(markdown_fast):
            # Re-process with BALANCED for complex documents
            balanced_analyzer = NanonetsLayoutAnalyzer(quality_preset="balanced")
            markdown_balanced = balanced_analyzer.analyze_document(file_path, page_number)
            return markdown_balanced, True  # used_balanced

        return markdown_fast, False  # used_fast
```

**Advantages of this approach**:
- ✅ No PaddleOCR dependency
- ✅ No crash risk on music notation
- ✅ Markdown-based complexity detection (more reliable than OCR confidence)
- ✅ Can compare FAST output quality against BALANCED to decide if re-processing needed

---

## Open Questions for Benchmarking

1. **What is actual FAST preset speed?** (Current: unknown, expected 60-100 sec/page)
2. **Quality degradation on FAST preset?** (For simple text, may be acceptable)
3. **Can we detect complexity from FAST markdown?** (Tables present? Equations present? Image descriptions?)
4. **FAST preset stability?** (Does it handle music notation without crashing?)
5. **GGUF quantized performance?** (Future investigation if Nanonets-only chosen)

---

## Timeline

### Immediate (Today)
- ⏳ Run `test_nanonets_fast_preset.py` benchmark
- ⏳ Analyze results and actual timings
- ⏳ Make recommendation based on data

### Short-term (1 week)
- Implement chosen approach
- Add complexity detection (OCR-based or markdown-based)
- Test on production document set
- Validate quality and performance

### Long-term (Future)
- If Nanonets-only chosen: Investigate GGUF quantization for additional speedup
- Monitor for new Nanonets model releases (smaller variants)
- Consider contributing to Nanonets/Qwen community for "fast mode" feature

---

## Conclusion

**Best Answer**: It depends on your priorities and the benchmark results.

**My recommendation**: Run the FAST preset benchmark first. Based on early research:
- **If stability matters most** (music notation documents) → Nanonets Two-Tier
- **If speed matters most** (time-sensitive workloads) → PaddleOCR Hybrid with pre-filtering

**The ideal world**: Nanonets releases a smaller model (1B parameters) optimized for simple text. Until then, we work with the trade-offs above.

**Next step**: Check the benchmark results from `test_nanonets_fast_preset.py` to get actual data for the decision.
