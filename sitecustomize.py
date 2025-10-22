"""
Site customizations for local PaddleOCR-VL testing.

We reuse the safetensors monkey patch from the analyzer so that any script
running in this workspace—like the `paddleocr` CLI—can open Paddle models
without hitting the unsupported `framework='paddle'` error.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_safetensors_patch_applied = False
_original_safe_open = None


def _paddle_safe_open(filename, framework="pt", device="cpu"):
    """Patched safetensors.safe_open that maps Paddle requests onto PyTorch."""
    global _original_safe_open

    if framework == "paddle":
        logger.debug("Sitecustomize safetensors patch: rerouting to PyTorch reader")
        with _original_safe_open(filename, framework="pt", device=device) as pt_file:
            yield _PaddleSafetensorsFile(pt_file)
    else:
        with _original_safe_open(filename, framework=framework, device=device) as f:
            yield f


class _PaddleTensorSlice:
    """Adapter that converts PyTorch tensor slices to Paddle tensors on demand."""

    def __init__(self, pt_slice):
        self.pt_slice = pt_slice
        self.shape = pt_slice.get_shape()

    def get_shape(self):
        return self.shape

    def __getitem__(self, key):
        import paddle
        import torch

        tensor = self.pt_slice[key]
        if tensor.dtype == torch.bfloat16:
            tensor = tensor.to(torch.float32)
        return paddle.to_tensor(tensor.cpu().numpy())


class _PaddleSafetensorsFile:
    """Wrapper exposing the safetensors API but yielding Paddle tensors."""

    def __init__(self, pt_file):
        self.pt_file = pt_file

    def keys(self):
        return self.pt_file.keys()

    def get_slice(self, key):
        return _PaddleTensorSlice(self.pt_file.get_slice(key))


def _apply_patch():
    global _safetensors_patch_applied, _original_safe_open
    if _safetensors_patch_applied:
        return
    try:
        from contextlib import contextmanager

        import safetensors

        _original_safe_open = safetensors.safe_open
        safetensors.safe_open = contextmanager(_paddle_safe_open)
        _safetensors_patch_applied = True
        logger.info("Applied safetensors monkey patch from sitecustomize")
    except ImportError:
        logger.warning("safetensors not available; Paddle patch not applied")


_apply_patch()

