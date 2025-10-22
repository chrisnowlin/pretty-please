"""Format converter for different embedding storage formats."""

import base64
from typing import Literal, Union
import numpy as np


class FormatConverter:
    """Converts embeddings between different storage formats."""

    def __init__(self):
        """Initialize the format converter."""
        pass

    def to_float(self, embeddings: np.ndarray) -> np.ndarray:
        """Convert to float format.

        Args:
            embeddings: Input embeddings

        Returns:
            Embeddings in float format
        """
        return embeddings.astype(np.float32)

    def to_binary(self, embeddings: np.ndarray) -> np.ndarray:
        """Convert to binary format (1 byte per value).

        Args:
            embeddings: Input embeddings in [-1, 1] range

        Returns:
            Embeddings in binary format (int8)
        """
        # Quantize to int8
        return (embeddings * 127).astype(np.int8)

    def to_ubinary(self, embeddings: np.ndarray) -> np.ndarray:
        """Convert to unsigned binary format (0.5 byte per value).

        Args:
            embeddings: Input embeddings in [0, 1] range

        Returns:
            Embeddings in unsigned binary format (uint8)
        """
        # Normalize and quantize to uint8
        normalized = (embeddings + 1) / 2  # Map [-1, 1] to [0, 1]
        return (normalized * 255).astype(np.uint8)

    def to_base64(self, embeddings: Union[np.ndarray, bytes]) -> str:
        """Convert to base64 format.

        Args:
            embeddings: Input embeddings as numpy array or bytes

        Returns:
            Base64-encoded string
        """
        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tobytes()
        return base64.b64encode(embeddings).decode('utf-8')

    def from_base64(self, encoded: str, shape: tuple) -> np.ndarray:
        """Decode from base64 format.

        Args:
            encoded: Base64-encoded string
            shape: Target shape for numpy array

        Returns:
            Decoded embeddings
        """
        decoded = base64.b64decode(encoded.encode('utf-8'))
        return np.frombuffer(decoded, dtype=np.float32).reshape(shape)
