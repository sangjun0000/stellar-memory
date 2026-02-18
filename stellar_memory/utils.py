"""Shared utility functions for Stellar Memory."""

from __future__ import annotations

import math
import struct


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors, clamped to [0, 1]."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def serialize_embedding(embedding: list[float]) -> bytes:
    """Serialize list[float] to bytes (4 bytes per float, little-endian)."""
    return struct.pack(f"<{len(embedding)}f", *embedding)


def deserialize_embedding(blob: bytes, dim: int | None = None) -> list[float]:
    """Deserialize bytes to list[float]. Infers dim from blob size if not given."""
    if dim is None:
        dim = len(blob) // 4
    return list(struct.unpack(f"<{dim}f", blob))
