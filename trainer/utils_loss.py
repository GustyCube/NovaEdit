from __future__ import annotations

from typing import Sequence


def patch_size_regularizer(predicted_lengths: Sequence[int], weight: float = 0.01) -> float:
    """Simple regularizer: encourages shorter patches."""
    return float(sum(predicted_lengths)) * weight
