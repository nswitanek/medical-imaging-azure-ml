"""Vision tower + full CT–report model assembling the Fig. 2 components.

VisionTower:  volume -> windowing -> ViT_l (per window) -> pool+concat -> ViT_g -> proj.
CTReportModel: VisionTower + TextEncoder, each with a projection head into the shared
SigLIP embedding space, plus a learnable logit scale/bias.
"""

from __future__ import annotations

from typing import Optional, Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..config import ModelConfig
from ..data.windowing import extract_windows, window_positions
from ..text.tokenizer import build_tokenizer
from .vit_local import LocalViT
from .vit_global import GlobalViT
from .text_encoder import TextEncoder, build_text_encoder


def _batch_windows(volumes: torch.Tensor, cfg: ModelConfig):
    """Turn a batch of volumes into ``(B, G, C, wd, wh, ww)`` windows + shared grid."""
    per_sample = []
    grid = None
    for i in range(volumes.shape[0]):
        wv = extract_windows(volumes[i], cfg)
        per_sample.append(wv.windows)
        grid = wv.grid
    return torch.stack(per_sample, dim=0), grid


class VisionTower(nn.Module):
    def __init__(self, cfg: ModelConfig, local_vit: Optional[LocalViT] = None):
        super().__init__()
        self.cfg = cfg
        self.local = local_vit if local_vit is not None else LocalViT(cfg)
        self.global_vit = GlobalViT(cfg, in_dim=2 * cfg.local_dim)  # pool+concat = 2*dim
        self.proj = nn.Linear(cfg.global_dim, cfg.embed_dim)

    def forward(self, volumes: torch.Tensor) -> torch.Tensor:
        """volumes ``(B, D, H, W)`` or ``(B, C, D, H, W)`` -> ``(B, embed_dim)``."""
        windows, grid = _batch_windows(volumes, self.cfg)          # (B, G, C, wd,wh,ww)
        b, g = windows.shape[0], windows.shape[1]
        flat = windows.reshape(b * g, *windows.shape[2:])
        pooled = self.local.pooled(flat)                           # (B*G, 2*local_dim)
        window_tokens = pooled.reshape(b, g, -1)                   # (B, G, 2*local_dim)
        wpos = window_positions(grid).to(volumes.device)
        scan = self.global_vit(window_tokens, wpos)                # (B, global_dim)
        return self.proj(scan)                                     # (B, embed_dim)


class CTReportModel(nn.Module):
    """Full dual-tower model aligned by SigLIP in Stage 2.

    The text tower owns a *paired* tokenizer + encoder (Qwen or fallback), chosen by
    ``cfg.text_tower`` and recorded on ``text_tower_kind`` so training can pin it into the
    saved config for eval/serving. ``encode_text`` takes raw report **strings** and tokenizes
    them with the paired tokenizer, so callers never handle tower-specific token ids.
    """

    def __init__(self, cfg: ModelConfig, text_encoder: Optional[TextEncoder] = None,
                 local_vit: Optional[LocalViT] = None):
        super().__init__()
        self.cfg = cfg
        self.vision = VisionTower(cfg, local_vit=local_vit)
        if text_encoder is not None:
            self.text = text_encoder
            self.text_tower_kind = getattr(text_encoder, "kind", getattr(cfg, "text_tower", "fallback"))
        else:
            self.text, self.text_tower_kind = build_text_encoder(cfg)
        self.tokenizer = build_tokenizer(cfg, self.text_tower_kind)
        self.text_max_tokens = cfg.text_max_tokens
        self.text_proj = nn.Linear(self.text.text_dim, cfg.embed_dim)
        self.logit_scale = nn.Parameter(torch.tensor(cfg.siglip_init_logit_scale))
        self.logit_bias = nn.Parameter(torch.tensor(cfg.siglip_init_logit_bias))

    def encode_image(self, volumes: torch.Tensor) -> torch.Tensor:
        return F.normalize(self.vision(volumes), dim=-1)

    def encode_text(self, reports: Sequence[str]) -> torch.Tensor:
        """Tokenize report strings with the paired tokenizer, then embed into shared space."""
        input_ids, attention_mask = self.tokenizer.encode(reports, self.text_max_tokens)
        device = self.text_proj.weight.device
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)
        feats = self.text(input_ids, attention_mask)
        return F.normalize(self.text_proj(feats), dim=-1)

    def forward(self, volumes: torch.Tensor, reports: Sequence[str]):
        img = self.encode_image(volumes)
        txt = self.encode_text(reports)
        return img, txt, self.logit_scale, self.logit_bias
