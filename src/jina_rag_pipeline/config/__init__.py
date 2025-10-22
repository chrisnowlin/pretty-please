"""Configuration management for jina-rag-pipeline."""

from .profiles import (
    ProcessingProfile,
    PROFILES,
    get_profile,
    auto_detect_profile,
    detect_m4_max,
    get_profile_summary,
)

__all__ = [
    "ProcessingProfile",
    "PROFILES",
    "get_profile",
    "auto_detect_profile",
    "detect_m4_max",
    "get_profile_summary",
]
