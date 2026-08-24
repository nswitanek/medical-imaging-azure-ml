"""ViT_g -- the scan-level (global) vision transformer.

Fig. 2 "Scan-level" box: [cls] + G windows -> 4x (Transformer Block + 3D RoPE). Takes the
per-window descriptors produced by ViT_l (after pool+concat) and aggregates them into a
single scan-level embedding, using the windows' 3D grid positions for RoPE.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from ..config import ModelConfig
from .rope3d import TransformerBlock


class GlobalViT(nn.Module):
    def __init__(self, cfg: ModelConfig, in_dim: int):
        super().__init__()
        self.cfg = cfg
        self.in_proj = nn.Linear(in_dim, cfg.global_dim)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, cfg.global_dim))
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        self.blocks = nn.ModuleList(
            [TransformerBlock(cfg.global_dim, cfg.global_heads, dropout=cfg.dropout)
             for _ in range(cfg.global_depth)]
        )
        self.norm = nn.LayerNorm(cfg.global_dim)

    def forward(self, window_tokens: torch.Tensor, window_pos: torch.Tensor) -> torch.Tensor:
        """Aggregate window descriptors into a scan-level [cls] embedding.

        Args:
            window_tokens: ``(B, G, in_dim)`` -- one descriptor per window.
            window_pos: ``(G, 3)`` grid coordinates of the windows.
        Returns:
            ``(B, global_dim)`` scan-level embedding (the [cls] token).
        """
        x = self.in_proj(window_tokens)                    # (B, G, global_dim)
        b = x.shape[0]
        cls = self.cls_token.expand(b, -1, -1)
        x = torch.cat([cls, x], dim=1)                     # (B, 1+G, global_dim)
        for blk in self.blocks:
            x = blk(x, window_pos)
        x = self.norm(x)
        return x[:, 0]
