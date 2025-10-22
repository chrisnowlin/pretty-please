"""
OCRConfig: simplified configuration with smart defaults and presets.

Using standard dataclasses to avoid adding dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
import os

try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # graceful fallback


def _total_memory_gb() -> int:
    try:
        if psutil is None:
            return 16
        return int(psutil.virtual_memory().total / (1024 ** 3))
    except Exception:
        return 16


@dataclass
class OCRConfig:
    batch_size: int = 30
    render_workers: int = 20
    analysis_workers: int = 2
    pre_render_batches: int = 4
    checkpoint_enabled: bool = True

    # Deepseek-OCR specific settings
    resolution_mode: str = "base"  # tiny/small/base/large/gundam
    enable_grounding: bool = True
    enable_compression: bool = True
    use_vllm: bool = False

    @classmethod
    def mlx_optimized(cls) -> "OCRConfig":
        return cls(batch_size=30, render_workers=_auto_cores(), analysis_workers=1, pre_render_batches=4, checkpoint_enabled=True)

    @classmethod
    def memory_constrained(cls) -> "OCRConfig":
        # scale down based on memory
        mem = _total_memory_gb()
        if mem <= 8:
            return cls(batch_size=8, render_workers=max(2, _auto_cores() // 4), analysis_workers=1, pre_render_batches=2)
        elif mem <= 16:
            return cls(batch_size=10, render_workers=max(4, _auto_cores() // 2), analysis_workers=1, pre_render_batches=3)
        else:
            return cls(batch_size=20, render_workers=_auto_cores(), analysis_workers=2, pre_render_batches=3)

    @classmethod
    def balanced(cls) -> "OCRConfig":
        return cls(batch_size=20, render_workers=_auto_cores(), analysis_workers=2, pre_render_batches=3)

    # Deepseek-OCR Presets

    @classmethod
    def deepseek_tiny(cls) -> "OCRConfig":
        """Deepseek TINY mode for maximum speed (512x512, 64 tokens).

        Best for:
        - Simple documents (text-heavy, minimal tables)
        - High-volume processing where speed is critical
        - Documents that don't require high-quality table extraction

        Performance: 2-3x faster than BASE mode
        Quality: Good for simple documents, may struggle with complex layouts

        Returns:
            OCRConfig with TINY resolution mode
        """
        return cls(
            batch_size=30,
            render_workers=_auto_cores(),
            analysis_workers=2,
            pre_render_batches=4,
            checkpoint_enabled=True,
            resolution_mode="tiny",
            enable_grounding=False,  # Disable for speed
            enable_compression=True,
            use_vllm=False,
        )

    @classmethod
    def deepseek_small(cls) -> "OCRConfig":
        """Deepseek SMALL mode for speed/quality balance (640x640, 100 tokens).

        Best for:
        - Mixed simple/moderate documents
        - When speed matters but quality still important
        - Moderate table complexity

        Performance: ~1.5x faster than BASE mode
        Quality: Good balance for most use cases

        Returns:
            OCRConfig with SMALL resolution mode
        """
        return cls(
            batch_size=25,
            render_workers=_auto_cores(),
            analysis_workers=2,
            pre_render_batches=3,
            checkpoint_enabled=True,
            resolution_mode="small",
            enable_grounding=True,
            enable_compression=True,
            use_vllm=False,
        )

    @classmethod
    def deepseek_balanced(cls) -> "OCRConfig":
        """Deepseek BASE mode for default quality (1024x1024, 256 tokens).

        This is the recommended default for most use cases.

        Best for:
        - General document processing
        - Mixed content (text, tables, equations, images)
        - When you need reliable quality without optimizing for speed

        Performance: Baseline (default speed)
        Quality: High quality for most document types

        Returns:
            OCRConfig with BASE resolution mode
        """
        return cls(
            batch_size=20,
            render_workers=_auto_cores(),
            analysis_workers=2,
            pre_render_batches=3,
            checkpoint_enabled=True,
            resolution_mode="base",
            enable_grounding=True,
            enable_compression=True,
            use_vllm=False,
        )

    @classmethod
    def deepseek_high_quality(cls) -> "OCRConfig":
        """Deepseek LARGE mode for maximum quality (1280x1280, 400 tokens).

        Best for:
        - Complex documents (dense tables, equations, diagrams)
        - When quality is more important than speed
        - Documents requiring precise spatial grounding

        Performance: ~30% slower than BASE mode
        Quality: Maximum quality for complex layouts

        Returns:
            OCRConfig with LARGE resolution mode
        """
        return cls(
            batch_size=15,
            render_workers=_auto_cores(),
            analysis_workers=2,
            pre_render_batches=3,
            checkpoint_enabled=True,
            resolution_mode="large",
            enable_grounding=True,
            enable_compression=True,
            use_vllm=False,
        )

    @classmethod
    def deepseek_gundam(cls) -> "OCRConfig":
        """Deepseek GUNDAM mode for dynamic multi-resolution (complex layouts).

        This mode uses dynamic resolution selection for complex layouts.

        Best for:
        - Documents with highly variable complexity
        - Mixed simple and complex pages
        - When you want automatic resolution adaptation

        Performance: Variable (adapts per page)
        Quality: Optimized for complex layouts

        Returns:
            OCRConfig with GUNDAM resolution mode
        """
        return cls(
            batch_size=20,
            render_workers=_auto_cores(),
            analysis_workers=2,
            pre_render_batches=3,
            checkpoint_enabled=True,
            resolution_mode="gundam",
            enable_grounding=True,
            enable_compression=True,
            use_vllm=False,
        )

    @classmethod
    def deepseek_production(cls) -> "OCRConfig":
        """Deepseek production mode with vLLM for maximum throughput.

        Requires vLLM to be installed (pip install vllm>=0.8.5).

        Best for:
        - Production deployments
        - High-volume document processing
        - When you need 5-10x throughput improvement

        Performance: 5-10x faster than BASE mode (with vLLM on A100)
        Quality: Same as GUNDAM mode

        Returns:
            OCRConfig with GUNDAM resolution and vLLM enabled
        """
        return cls(
            batch_size=30,
            render_workers=_auto_cores(),
            analysis_workers=4,  # Higher parallelism with vLLM
            pre_render_batches=5,
            checkpoint_enabled=True,
            resolution_mode="gundam",
            enable_grounding=True,
            enable_compression=True,
            use_vllm=True,
        )


def _auto_cores() -> int:
    try:
        import psutil as _ps
        return max(2, int(_ps.cpu_count(logical=True) * 0.8))
    except Exception:
        return 4

