"""Lightweight 3D augmentations for DINO-style multi-crop SSL (Stage 1).

Kept minimal and shape-preserving so every view can be batched together: random axis
flips, intensity jitter, and additive Gaussian noise. Real training would add random
resized 3D crops, rotations, and blur.
"""

from __future__ import annotations

from typing import List

import torch


def augment_window(window: torch.Tensor, gen: torch.Generator | None = None) -> torch.Tensor:
    """Apply a random flip + intensity jitter + noise to a ``(C, wd, wh, ww)`` window."""
    x = window
    # random flips along spatial axes
    for axis in (1, 2, 3):
        if torch.rand(1, generator=gen).item() < 0.5:
            x = torch.flip(x, dims=[axis])
    scale = 1.0 + (torch.rand(1, generator=gen).item() - 0.5) * 0.2   # +/-10%
    shift = (torch.rand(1, generator=gen).item() - 0.5) * 0.1
    x = x * scale + shift
    x = x + torch.randn(x.shape, generator=gen) * 0.02
    return x


def make_views(windows: torch.Tensor, n_views: int, gen: torch.Generator | None = None) -> List[torch.Tensor]:
    """Make ``n_views`` augmented batches from a ``(B, C, wd, wh, ww)`` window batch.

    Returns a list of ``n_views`` tensors, each the same shape as ``windows``.
    """
    views = []
    for _ in range(n_views):
        aug = torch.stack([augment_window(windows[i], gen) for i in range(windows.shape[0])], dim=0)
        views.append(aug)
    return views
