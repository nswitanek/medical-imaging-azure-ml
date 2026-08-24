"""ViT_l -- the window-level (local) vision transformer.

Fig. 2 "Window-level" box: 3D Tokenization -> [cls] + N patches -> 24x (Transformer
Block + 3D RoPE). Operates on a single CT window and produces a [cls] summary plus the N
patch tokens. Pretrained in Stage 1 with the DINOv3-style SSL objective.
"""

from __future__ import annotations

from typing import Tuple

import torch
import torch.nn as nn

from ..config import ModelConfig
from ..data.windowing import patch_positions
from .rope3d import TransformerBlock


class Patch3DEmbed(nn.Module):
    """3D tokenization: non-overlapping Conv3d patch projection."""

    def __init__(self, in_ch: int, dim: int, patch_size: Tuple[int, int, int]):
        super().__init__()
        self.proj = nn.Conv3d(in_ch, dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, C, D, H, W) -> (B, N, dim)
        x = self.proj(x)
        b, dim = x.shape[0], x.shape[1]
        return x.reshape(b, dim, -1).transpose(1, 2)


class LocalViT(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.cfg = cfg
        in_ch = len(cfg.hu_windows)
        self.patch_embed = Patch3DEmbed(in_ch, cfg.local_dim, cfg.patch_size)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, cfg.local_dim))
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        self.blocks = nn.ModuleList(
            [TransformerBlock(cfg.local_dim, cfg.local_heads, dropout=cfg.dropout)
             for _ in range(cfg.local_depth)]
        )
        self.norm = nn.LayerNorm(cfg.local_dim)
        self.register_buffer("patch_pos", patch_positions(cfg), persistent=False)

    def forward(self, windows: torch.Tensor) -> dict:
        """Encode a batch of windows.

        Args:
            windows: ``(B, C, wd, wh, ww)``.
        Returns:
            dict with ``cls`` ``(B, dim)`` and ``patches`` ``(B, N, dim)``.
        """
        tokens = self.patch_embed(windows)                 # (B, N, dim)
        b = tokens.shape[0]
        cls = self.cls_token.expand(b, -1, -1)
        x = torch.cat([cls, tokens], dim=1)                # (B, 1+N, dim)
        for blk in self.blocks:
            x = blk(x, self.patch_pos)
        x = self.norm(x)
        return {"cls": x[:, 0], "patches": x[:, 1:]}

    def pooled(self, windows: torch.Tensor) -> torch.Tensor:
        """Pooled window descriptor = concat([cls], mean(patches)).

        Fig. 2 shows a "Pooling" + "Concat" step turning each window into a token that
        feeds ViT_g. We concat the [cls] token with mean-pooled patch tokens.
        """
        out = self.forward(windows)
        return torch.cat([out["cls"], out["patches"].mean(dim=1)], dim=-1)  # (B, 2*dim)
