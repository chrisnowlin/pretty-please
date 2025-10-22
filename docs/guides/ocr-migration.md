# OCR Configuration Migration Guide

## Overview

This guide helps you migrate from the old profile-based configuration system to the new streamlined `OCRConfig` presets. The new system simplifies configuration, provides better defaults, and makes the codebase easier to understand and maintain.

## What Changed?

### Old System (Deprecated)

The old system used a complex profile-based approach:

```python
from jina_rag_pipeline.ingestion.loaders import NanonetsFirstLoader

# Old way: Profile-based configuration with environment variables
# PROCESSING_PROFILE=aggressive  (set via environment)
loader = NanonetsFirstLoader(
    batch_size=None,              # Auto-detected from profile
    max_render_workers=None,      # Auto-detected from profile
    max_analysis_workers=None     # Auto-detected from profile
)
```

**Problems with the old system:**
- Multiple overlapping configuration mechanisms (profiles, params, env vars)
- Unclear precedence rules
- Hard to understand which settings were active
- Profile logic scattered across codebase
- No type safety or validation

### New System (Recommended)

The new system uses explicit `OCRConfig` presets:

```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig

# New way: Explicit configuration with type safety
loader = NanonetsLoader(config=OCRConfig.mlx_optimized())

# Or use auto-detection (recommended)
loader = NanonetsLoader()  # Auto-selects best config for your hardware
```

**Benefits:**
- ✅ Explicit and predictable
- ✅ Type-safe with dataclasses
- ✅ Clear parameter names
- ✅ Smart defaults that work for 80% of cases
- ✅ Easy to customize when needed

## Migration Steps

### Step 1: Remove Environment Variables

The new system doesn't use environment variables for OCR configuration.

**Before:**
```bash
# Old environment variables (no longer used)
export PROCESSING_PROFILE=aggressive
export RENDER_BATCH_SIZE=30
export MAX_RENDER_WORKERS=20
```

**After:**
```bash
# No environment variables needed!
# Configuration is now explicit in code
```

### Step 2: Update Imports

**Before:**
```python
from jina_rag_pipeline.ingestion.loaders import NanonetsFirstLoader
```

**After:**
```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig  # If customizing
```

### Step 3: Update Loader Initialization

Choose one of these migration patterns:

#### Pattern 1: Auto-Detection (Recommended)

**Before:**
```python
loader = NanonetsFirstLoader()  # Used profile from environment
```

**After:**
```python
loader = NanonetsLoader()  # Auto-selects best config for your hardware
```

This is the simplest migration - just change the class name and let the system auto-detect the best configuration.

#### Pattern 2: Explicit Preset

**Before:**
```python
# Using "aggressive" profile
loader = NanonetsFirstLoader()
```

**After:**
```python
# Equivalent to "aggressive" profile
loader = NanonetsLoader(config=OCRConfig.mlx_optimized())
```

#### Pattern 3: Custom Configuration

**Before:**
```python
loader = NanonetsFirstLoader(
    batch_size=25,
    max_render_workers=15,
    max_analysis_workers=1
)
```

**After:**
```python
config = OCRConfig(
    batch_size=25,
    render_workers=15,
    analysis_workers=1,
    pre_render_batches=4,
    checkpoint_enabled=True
)
loader = NanonetsLoader(config=config)
```

## Profile → Preset Mapping

If you were using the old profile system, use this table to find the equivalent preset:

| Old Profile | New Preset | Settings | Use Case |
|------------|-----------|----------|----------|
| `aggressive` | `OCRConfig.mlx_optimized()` | batch_size=30, render_workers=auto, analysis_workers=1, pre_render_batches=4 | Apple Silicon with 16GB+ RAM |
| `balanced` | `OCRConfig.balanced()` | batch_size=20, render_workers=auto, analysis_workers=2, pre_render_batches=3 | General-purpose, any platform |
| `conservative` | `OCRConfig.memory_constrained()` | batch_size=8-20 (auto), render_workers=2-auto (auto), analysis_workers=1, pre_render_batches=2-3 | Limited RAM or very large documents |

### Example: Migrating from "aggressive" Profile

**Before:**
```bash
# .env or environment
export PROCESSING_PROFILE=aggressive
```

```python
from jina_rag_pipeline.ingestion.loaders import NanonetsFirstLoader

loader = NanonetsFirstLoader()
documents = loader.load("document.pdf")
```

**After:**
```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig

# Explicit configuration (equivalent to aggressive)
loader = NanonetsLoader(config=OCRConfig.mlx_optimized())

# Or even simpler - auto-detection works great on Apple Silicon
loader = NanonetsLoader()

documents = loader.load("document.pdf")
```

### Example: Migrating from "balanced" Profile

**Before:**
```bash
# .env or environment
export PROCESSING_PROFILE=balanced
```

```python
loader = NanonetsFirstLoader()
documents = loader.load("document.pdf")
```

**After:**
```python
loader = NanonetsLoader(config=OCRConfig.balanced())

# Or auto-detection (will select balanced on non-Apple Silicon)
loader = NanonetsLoader()

documents = loader.load("document.pdf")
```

### Example: Migrating from "conservative" Profile

**Before:**
```bash
export PROCESSING_PROFILE=conservative
```

```python
loader = NanonetsFirstLoader()
documents = loader.load("document.pdf")
```

**After:**
```python
loader = NanonetsLoader(config=OCRConfig.memory_constrained())
documents = loader.load("document.pdf")
```

## Parameter Mapping

Use this table to map old parameters to new parameters:

| Old Parameter | New Parameter | Notes |
|--------------|---------------|-------|
| `batch_size` | `batch_size` | Same name, same meaning |
| `max_render_workers` | `render_workers` | Renamed (removed "max_" prefix) |
| `max_analysis_workers` | `analysis_workers` | Renamed (removed "max_" prefix) |
| *(none)* | `pre_render_batches` | **NEW** - controls pipeline depth |
| `enable_checkpoints` | `checkpoint_enabled` | Renamed for clarity |
| `checkpoint_dir` | *(passed to loader)* | No longer in config, pass to loader |

### Example: Parameter Mapping

**Before:**
```python
loader = NanonetsFirstLoader(
    batch_size=20,
    max_render_workers=12,
    max_analysis_workers=1,
    enable_checkpoints=True,
    checkpoint_dir=Path("./my_checkpoints")
)
```

**After:**
```python
from pathlib import Path

config = OCRConfig(
    batch_size=20,
    render_workers=12,
    analysis_workers=1,
    pre_render_batches=4,        # NEW parameter (recommended: 3-5)
    checkpoint_enabled=True
)

# Note: checkpoint_dir is now passed to loader, not config
loader = NanonetsLoader(config=config)
# If you need custom checkpoint dir, modify the loader initialization
```

## Common Migration Scenarios

### Scenario 1: Default Configuration

**Goal:** Just want OCR to work with good defaults

**Before:**
```python
loader = NanonetsFirstLoader()
```

**After:**
```python
loader = NanonetsLoader()  # That's it!
```

### Scenario 2: High-Performance Apple Silicon

**Goal:** Maximum speed on M1/M2/M3/M4 Mac with 16GB+ RAM

**Before:**
```bash
export PROCESSING_PROFILE=aggressive
```
```python
loader = NanonetsFirstLoader()
```

**After:**
```python
# Auto-detection selects mlx_optimized on Apple Silicon
loader = NanonetsLoader()

# Or be explicit
loader = NanonetsLoader(config=OCRConfig.mlx_optimized())
```

### Scenario 3: Memory-Constrained System

**Goal:** Process on a system with limited RAM (8-16GB)

**Before:**
```bash
export PROCESSING_PROFILE=conservative
```
```python
loader = NanonetsFirstLoader()
```

**After:**
```python
# memory_constrained auto-scales based on available RAM
loader = NanonetsLoader(config=OCRConfig.memory_constrained())
```

### Scenario 4: Custom Settings for Specific Document

**Goal:** Fine-tune settings for a specific document type

**Before:**
```python
loader = NanonetsFirstLoader(
    batch_size=15,
    max_render_workers=10,
    max_analysis_workers=1
)
```

**After:**
```python
config = OCRConfig(
    batch_size=15,
    render_workers=10,
    analysis_workers=1,
    pre_render_batches=3  # Add pipeline depth
)
loader = NanonetsLoader(config=config)
```

### Scenario 5: Processing Multiple Documents with Different Configs

**Before:**
```python
# Had to create multiple loader instances or change environment
loader_aggressive = NanonetsFirstLoader(batch_size=30, max_render_workers=20)
loader_conservative = NanonetsFirstLoader(batch_size=10, max_render_workers=8)

loader_aggressive.load("large_doc.pdf")
loader_conservative.load("small_doc.pdf")
```

**After:**
```python
# More explicit and clearer
loader_fast = NanonetsLoader(config=OCRConfig.mlx_optimized())
loader_memory = NanonetsLoader(config=OCRConfig.memory_constrained())

loader_fast.load("large_doc.pdf")
loader_memory.load("small_doc.pdf")
```

## Backward Compatibility

The old `NanonetsFirstLoader` still works but is deprecated:

```python
from jina_rag_pipeline.ingestion.loaders import NanonetsFirstLoader

# This still works, but you'll see a deprecation warning
loader = NanonetsFirstLoader()
```

**Deprecation warning:**
```
DeprecationWarning: NanonetsFirstLoader is deprecated; use NanonetsLoader with OCRConfig presets
```

**Timeline:**
- **Current version**: Both systems work, NanonetsFirstLoader shows warnings
- **Next minor version**: NanonetsFirstLoader will be marked for removal
- **Next major version**: NanonetsFirstLoader will be removed entirely

**Recommendation:** Migrate to `NanonetsLoader` as soon as possible to avoid breaking changes in future releases.

## Testing Your Migration

After migrating, verify everything works:

```python
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig

# Test 1: Default configuration
loader = NanonetsLoader()
print(f"✓ Default loader created: {loader.config}")

# Test 2: Load a test document
documents = loader.load("test_document.pdf")
print(f"✓ Loaded {len(documents)} pages")

# Test 3: Custom configuration
config = OCRConfig(batch_size=20, render_workers=12)
loader_custom = NanonetsLoader(config=config)
print(f"✓ Custom config: {loader_custom.config}")

# Test 4: Preset configuration
loader_mlx = NanonetsLoader(config=OCRConfig.mlx_optimized())
print(f"✓ MLX-optimized: {loader_mlx.config}")
```

**Expected output:**
```
✓ Default loader created: OCRConfig(batch_size=30, render_workers=16, ...)
✓ Loaded 10 pages
✓ Custom config: OCRConfig(batch_size=20, render_workers=12, ...)
✓ MLX-optimized: OCRConfig(batch_size=30, render_workers=16, ...)
```

## Troubleshooting

### Issue: "NanonetsFirstLoader is deprecated" Warning

**Solution:** This is expected. Migrate to `NanonetsLoader`:

```python
# Before
from jina_rag_pipeline.ingestion.loaders import NanonetsFirstLoader
loader = NanonetsFirstLoader()

# After
from jina_rag_pipeline.ingestion.nanonets_loader import NanonetsLoader
loader = NanonetsLoader()
```

### Issue: "get_profile() not found"

**Solution:** The profile system has been removed. Use `OCRConfig` instead:

```python
# Before
from jina_rag_pipeline.config import get_profile
profile = get_profile()

# After
from jina_rag_pipeline.ingestion.ocr_config import OCRConfig
config = OCRConfig.mlx_optimized()  # Or another preset
```

### Issue: Environment Variables Not Working

**Solution:** Environment variables are no longer used for OCR configuration. Use explicit configuration:

```python
# Before
# export PROCESSING_PROFILE=aggressive

# After
config = OCRConfig.mlx_optimized()
loader = NanonetsLoader(config=config)
```

### Issue: Can't Find Equivalent Preset for Custom Profile

**Solution:** Create a custom `OCRConfig`:

```python
# If you had custom profile settings, create custom config
config = OCRConfig(
    batch_size=<your_value>,
    render_workers=<your_value>,
    analysis_workers=<your_value>,
    pre_render_batches=4,  # Recommended default
    checkpoint_enabled=True
)

loader = NanonetsLoader(config=config)
```

### Issue: Performance Changed After Migration

**Solution:** The new defaults may differ from your old profile. Compare settings:

```python
# Check what configuration is active
loader = NanonetsLoader()
print(f"Active config: {loader.config}")

# Adjust if needed
config = OCRConfig(batch_size=30, pre_render_batches=5)  # More aggressive
loader = NanonetsLoader(config=config)
```

## Frequently Asked Questions

### Q: Do I need to update my code immediately?

**A:** No, but it's recommended. The old `NanonetsFirstLoader` still works but will be removed in a future major version.

### Q: Will my existing checkpoints work?

**A:** Yes! Checkpoint format hasn't changed. Existing checkpoints will resume correctly.

### Q: Can I mix old and new loaders?

**A:** Yes, but it's not recommended. Stick to one approach for consistency.

### Q: How do I know which preset to use?

**A:** Use auto-detection (just `NanonetsLoader()`) - it selects the best preset for your hardware. For manual selection:
- Apple Silicon with 16GB+ RAM → `mlx_optimized()`
- Other platforms → `balanced()`
- Limited memory → `memory_constrained()`

### Q: What happened to the profile files?

**A:** They've been replaced with `OCRConfig` presets. The new system is simpler and more explicit.

### Q: Can I still override individual parameters?

**A:** Yes! Create a custom `OCRConfig`:
```python
config = OCRConfig(
    batch_size=25,  # Custom
    render_workers=15,  # Custom
    analysis_workers=1,
    pre_render_batches=4,
    checkpoint_enabled=True
)
```

### Q: Will this affect my existing pipelines?

**A:** No immediate impact if you're using `NanonetsFirstLoader`. But you'll see deprecation warnings. Migrate at your convenience before the next major version.

## Next Steps

1. ✅ **Update imports** - Change to `NanonetsLoader` and `OCRConfig`
2. ✅ **Remove environment variables** - No longer needed for OCR config
3. ✅ **Choose preset or custom config** - Use auto-detection or explicit preset
4. ✅ **Test with sample documents** - Verify everything works
5. ✅ **Monitor performance** - Check that processing speed meets expectations
6. ✅ **Update documentation** - Update any internal docs or scripts

## Related Documentation

- [OCR Configuration Guide](ocr-configuration.md) - Complete guide to the new system
- [Getting Started](getting-started.md) - Basic setup and usage
- [Nanonets Migration Guide](nanonets-migration.md) - Nanonets analyzer features
- [System Architecture](../architecture/system-overview.md) - System internals

## Getting Help

If you encounter issues during migration:

1. Check this migration guide and the [OCR Configuration Guide](ocr-configuration.md)
2. Review the examples in this document
3. Check the [GitHub Issues](https://github.com/chrisnowlin/pretty-please/issues)
4. Ask in the project discussions or support channels

## Summary

**Migration Checklist:**

- [ ] Remove `PROCESSING_PROFILE` and other OCR-related environment variables
- [ ] Update imports from `NanonetsFirstLoader` to `NanonetsLoader`
- [ ] Add `OCRConfig` import if using custom configuration
- [ ] Choose a preset (`mlx_optimized`, `balanced`, `memory_constrained`) or auto-detection
- [ ] Update loader initialization with new config
- [ ] Test with sample documents
- [ ] Update any deployment scripts or documentation
- [ ] Monitor performance and adjust config if needed

**Key Benefits After Migration:**

✅ Simpler, more predictable configuration
✅ Better defaults that work out-of-the-box
✅ Type-safe with dataclasses
✅ Easier to understand and debug
✅ Future-proof for upcoming enhancements
