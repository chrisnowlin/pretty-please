# MLX Backend Known Issues

## Issue: MLX Quantized Models Produce Hallucinated Output

**Date Identified:** 2025-10-20
**Status:** UNRESOLVED - MLX Support Removed
**Severity:** CRITICAL - Unusable for Production

### Summary

The MLX backend with quantized versions of `nanonets/Nanonets-OCR2-3B` produces completely hallucinated OCR output instead of extracting actual document content. This occurs despite using official MLX Community models and recommended configuration.

### Attempted Solutions

1. **Official 8-bit Model** (`./models/nanonets-ocr2-3b-mlx`)
   - Result: Repetitive mermaid diagram hallucinations

2. **Official 4-bit Model with DWQ** (`mlx-community/Nanonets-OCR2-3B-4bit`)
   - Result: Number table hallucinations (1-350)

3. **Official Prompt Format**
   - Used exact prompt from Nanonets/MLX Community documentation
   - Result: Different hallucination pattern, but still incorrect

4. **Temperature Settings**
   - Already using `temp=0.0` for deterministic output
   - Result: No improvement

### Root Cause Analysis

The issue appears to be a fundamental incompatibility between:
- MLX quantization process for this specific VLM architecture
- MLX-VLM library's handling of the Nanonets-OCR2-3B model
- Quantized model weights themselves

### Comparison with PyTorch/MPS Backend

| Backend | Quality | Speed | Model Size | Status |
|---------|---------|-------|------------|--------|
| **MPS/PyTorch** | ✅ Accurate | 5.75 min/page | 14GB | **Production** |
| **MLX 8-bit** | ❌ Hallucinations | 34 sec/page | 2.2GB | **Removed** |
| **MLX 4-bit DWQ** | ❌ Hallucinations | ~30 sec/page | ~1.5GB | **Removed** |

### Example Outputs

**Expected (MPS):**
```markdown
GRADES K-6

# CLASSROOM MUSIC
## Games & Activities

### Building Dynamics
Dynamics markings indicate the "loud" and "soft" in music...
```

**MLX 8-bit Output:**
```markdown
```mermaid
graph TD
    A[Start] --> B[Input]
    B --> C[Process]
    C --> D[Output]
    D --> E[End]
``` [repeated hundreds of times]
```

**MLX 4-bit Output:**
```markdown
Not applicable.
<table border="1">
<tr><td><b>1</b></td><td><b>2</b></td>...<td><b>350</b></td></tr>
</table>
```

### Decision

**MLX support has been completely removed from the codebase** due to:
1. Critical quality issues making it unusable for production
2. No clear path to resolution with available MLX quantization methods
3. Need for stable baseline before further optimization

The MPS/PyTorch backend provides:
- ✅ 100% accurate OCR output
- ✅ Working batch processing
- ✅ Production reliability
- ⚠️ Slower performance (acceptable trade-off for accuracy)

### Future Investigation

If MLX support is to be revisited:
1. Wait for MLX-VLM library updates addressing VLM quantization
2. Test with non-quantized MLX models (full precision)
3. Investigate alternative VLM models with better MLX support
4. Monitor Nanonets/MLX Community for updated model releases

### References

- MLX Community Model: https://huggingface.co/mlx-community/Nanonets-OCR2-3B-4bit
- Official Documentation: https://nanonets.com/research/nanonets-ocr-2/
- MLX-VLM Repository: https://github.com/Blaizzy/mlx-vlm
