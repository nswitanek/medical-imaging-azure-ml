"""CT volume windowing and 3D patch tokenization.

Mirrors the "Windowing" box in Fig. 2: a volumetric CT scan is split into ``G`` windows,
and each window is later tokenized into ``N`` 3D patches by the local ViT.

Everything here is plain tensor bookkeeping so it runs on CPU with tiny volumes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import torch

from ..config import ModelConfig


@dataclass
class WindowedVolume:
    """A CT volume reshaped into windows.

    Attributes:
        windows: float tensor ``(G, C, wd, wh, ww)`` -- G windows, C HU channels.
        grid: the (nd, nh, nw) window grid the volume was split into.
    """

    windows: torch.Tensor
    grid: Tuple[int, int, int]


def apply_hu_windows(volume: torch.Tensor, cfg: ModelConfig) -> torch.Tensor:
    """Clamp+normalize a raw HU volume into one channel per configured HU window.

    Args:
        volume: ``(D, H, W)`` tensor of Hounsfield-unit-like values.
    Returns:
        ``(C, D, H, W)`` tensor, C == len(cfg.hu_windows), each channel in [0, 1].
    """
    channels = []
    for lo, hi in cfg.hu_windows:
        clamped = volume.clamp(min=lo, max=hi)
        channels.append((clamped - lo) / max(1e-6, (hi - lo)))
    return torch.stack(channels, dim=0)


def extract_windows(volume: torch.Tensor, cfg: ModelConfig) -> WindowedVolume:
    """Split a ``(D, H, W)`` (or ``(C, D, H, W)``) volume into non-overlapping windows.

    Returns windows of shape ``(G, C, wd, wh, ww)``.
    """
    if volume.dim() == 3:
        volume = apply_hu_windows(volume, cfg)
    c, d, h, w = volume.shape
    wd, wh, ww = cfg.window_shape
    nd, nh, nw = d // wd, h // wh, w // ww
    nd, nh, nw = max(1, nd), max(1, nh), max(1, nw)

    windows = []
    for i in range(nd):
        for j in range(nh):
            for k in range(nw):
                win = volume[
                    :,
                    i * wd : (i + 1) * wd,
                    j * wh : (j + 1) * wh,
                    k * ww : (k + 1) * ww,
                ]
                windows.append(win)
    return WindowedVolume(windows=torch.stack(windows, dim=0), grid=(nd, nh, nw))


def window_volume(volume: torch.Tensor, cfg: ModelConfig) -> torch.Tensor:
    """Convenience wrapper returning just the ``(G, C, wd, wh, ww)`` window tensor."""
    return extract_windows(volume, cfg).windows


def patch_positions(cfg: ModelConfig) -> torch.Tensor:
    """3D grid coordinates for the N patches in a window (used by 3D RoPE).

    Returns a ``(N, 3)`` long tensor of (z, y, x) patch indices.
    """
    gz, gy, gx = cfg.patch_grid()
    coords = torch.stack(
        torch.meshgrid(
            torch.arange(gz), torch.arange(gy), torch.arange(gx), indexing="ij"
        ),
        dim=-1,
    ).reshape(-1, 3)
    return coords.long()


def window_positions(grid: Tuple[int, int, int]) -> torch.Tensor:
    """3D grid coordinates for the G windows (used by ViT_g 3D RoPE)."""
    nd, nh, nw = grid
    coords = torch.stack(
        torch.meshgrid(
            torch.arange(nd), torch.arange(nh), torch.arange(nw), indexing="ij"
        ),
        dim=-1,
    ).reshape(-1, 3)
    return coords.long()
