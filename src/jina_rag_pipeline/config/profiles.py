"""Processing profiles for different hardware configurations.

Profiles optimize batch sizes, worker counts, and memory usage for different
hardware capabilities. The aggressive profile is designed for M4 Max with 48GB RAM.
"""

import platform
import psutil
import logging
from dataclasses import dataclass
from typing import Optional
import os

logger = logging.getLogger(__name__)


@dataclass
class ProcessingProfile:
    """Configuration profile for document processing."""

    name: str
    description: str

    # Batch sizes
    render_batch_size: int
    embedding_batch_size: int

    # Worker counts
    max_render_workers: int
    max_analysis_workers: int

    # Memory configuration
    max_memory_gb: int
    memory_target_gb: int
    memory_pressure_threshold: float  # 0-1

    # Pipeline configuration
    pre_render_batches: int  # Number of batches to buffer ahead
    checkpoint_interval_pages: int

    # Feature flags
    progressive_rendering: bool = True
    aggressive_mode: bool = False
    enable_model_caching: bool = True


# Profile definitions
PROFILES = {
    "aggressive": ProcessingProfile(
        name="aggressive",
        description="Maximum speed for 48GB+ systems (M4 Max optimized)",
        render_batch_size=50,
        embedding_batch_size=256,
        max_render_workers=12,
        max_analysis_workers=6,
        max_memory_gb=40,
        memory_target_gb=35,
        memory_pressure_threshold=0.85,
        pre_render_batches=2,
        checkpoint_interval_pages=50,
        progressive_rendering=True,
        aggressive_mode=True,
        enable_model_caching=True,
    ),
    "balanced": ProcessingProfile(
        name="balanced",
        description="Good speed with safety margin (32GB systems)",
        render_batch_size=20,
        embedding_batch_size=128,
        max_render_workers=6,
        max_analysis_workers=3,
        max_memory_gb=32,
        memory_target_gb=28,
        memory_pressure_threshold=0.80,
        pre_render_batches=1,
        checkpoint_interval_pages=20,
        progressive_rendering=True,
        aggressive_mode=False,
        enable_model_caching=True,
    ),
    "conservative": ProcessingProfile(
        name="conservative",
        description="Safest for 16-24GB systems",
        render_batch_size=10,
        embedding_batch_size=64,
        max_render_workers=4,
        max_analysis_workers=2,
        max_memory_gb=24,
        memory_target_gb=20,
        memory_pressure_threshold=0.75,
        pre_render_batches=0,
        checkpoint_interval_pages=10,
        progressive_rendering=True,
        aggressive_mode=False,
        enable_model_caching=False,
    ),
}


def detect_m4_max() -> bool:
    """Detect if running on M4 Max or similar Apple Silicon."""
    if platform.system() != "Darwin":
        return False

    try:
        import subprocess
        result = subprocess.run(
            ["sysctl", "-n", "hw.optional.arm64"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode != 0:
            return False

        # Check if it's ARM64
        if result.stdout.strip() != "1":
            return False

        # Check total memory (M4 Max typically has 32GB or 48GB)
        total_memory_gb = psutil.virtual_memory().total / (1024**3)

        # M4 Max detection: ARM64 + 32GB+ RAM
        return total_memory_gb >= 32
    except Exception as e:
        logger.debug(f"M4 Max detection failed: {e}")
        return False


def auto_detect_profile() -> str:
    """Auto-detect the best profile for the current hardware.

    Returns:
        Profile name: "aggressive", "balanced", or "conservative"
    """
    # Check for explicit override
    env_profile = os.getenv("PROCESSING_PROFILE", "").lower()
    if env_profile in PROFILES:
        logger.info(f"Using explicit profile from environment: {env_profile}")
        return env_profile

    # Auto-detect based on hardware
    total_memory_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count()

    # Detect M4 Max
    is_m4_max = detect_m4_max()

    if is_m4_max and total_memory_gb >= 48:
        profile = "aggressive"
        logger.info(
            f"Auto-detected M4 Max with {total_memory_gb:.1f}GB RAM - "
            f"using '{profile}' profile for maximum performance"
        )
        return profile
    elif total_memory_gb >= 32 and cpu_count >= 8:
        profile = "balanced"
        logger.info(
            f"Auto-detected {total_memory_gb:.1f}GB RAM, {cpu_count} cores - "
            f"using '{profile}' profile"
        )
        return profile
    else:
        profile = "conservative"
        logger.info(
            f"Auto-detected {total_memory_gb:.1f}GB RAM, {cpu_count} cores - "
            f"using '{profile}' profile for safety"
        )
        return profile


def get_profile(profile_name: Optional[str] = None) -> ProcessingProfile:
    """Get a processing profile by name, or auto-detect.

    Args:
        profile_name: Name of profile ("aggressive", "balanced", "conservative")
                     If None, auto-detects based on hardware

    Returns:
        ProcessingProfile configuration
    """
    if profile_name is None:
        profile_name = auto_detect_profile()

    if profile_name not in PROFILES:
        logger.warning(f"Unknown profile '{profile_name}', falling back to 'balanced'")
        profile_name = "balanced"

    profile = PROFILES[profile_name]
    logger.info(f"Using profile: {profile.name} - {profile.description}")

    return profile


def get_profile_summary(profile: ProcessingProfile) -> str:
    """Get a human-readable summary of a profile's settings.

    Args:
        profile: ProcessingProfile to summarize

    Returns:
        Formatted string with profile details
    """
    return f"""
Processing Profile: {profile.name}
{profile.description}

Batch Sizes:
  - Rendering: {profile.render_batch_size} pages
  - Embedding: {profile.embedding_batch_size} chunks

Worker Pools:
  - Render workers: {profile.max_render_workers}
  - Analysis workers: {profile.max_analysis_workers}

Memory Configuration:
  - Max usage: {profile.max_memory_gb}GB
  - Target usage: {profile.memory_target_gb}GB
  - Pressure threshold: {profile.memory_pressure_threshold * 100:.0f}%

Pipeline:
  - Pre-render batches: {profile.pre_render_batches}
  - Checkpoint interval: {profile.checkpoint_interval_pages} pages
  - Aggressive mode: {profile.aggressive_mode}
  - Model caching: {profile.enable_model_caching}
""".strip()
