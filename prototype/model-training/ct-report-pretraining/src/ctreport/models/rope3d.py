"""Shared transformer building blocks with 3D Rotary Position Embedding (3D RoPE).

The figure labels every vision transformer block "Transformer Block + 3D RoPE". RoPE is
applied to Q/K by splitting the head dimension into three equal groups -- one per spatial
axis (z, y, x) -- and rotating each group by that axis' coordinate. This is the standard
axial extension of 1D RoPE to volumetric data.
"""

from __future__ import annotations

import torch
import torch.nn as nn


def _rotate_half(x: torch.Tensor) -> torch.Tensor:
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat((-x2, x1), dim=-1)


class RoPE3D(nn.Module):
    """Precomputes and applies axial 3D rotary embeddings for tokens at 3D positions."""

    def __init__(self, head_dim: int, base: float = 10000.0):
        super().__init__()
        if head_dim % 6 != 0:
            # each axis needs an even sub-dimension; 3 axes -> divisible by 6.
            # pad up conceptually by using the largest multiple of 6 <= head_dim.
            self.axis_dim = (head_dim // 6) * 2
        else:
            self.axis_dim = head_dim // 3
        self.head_dim = head_dim
        self.base = base
        inv = 1.0 / (base ** (torch.arange(0, self.axis_dim, 2).float() / self.axis_dim))
        self.register_buffer("inv_freq", inv, persistent=False)

    def _axis_cos_sin(self, pos: torch.Tensor):
        # pos: (N,) coordinates along one axis
        freqs = torch.outer(pos.float(), self.inv_freq)          # (N, axis_dim/2)
        emb = torch.cat((freqs, freqs), dim=-1)                  # (N, axis_dim)
        return emb.cos(), emb.sin()

    def forward(self, q: torch.Tensor, k: torch.Tensor, positions: torch.Tensor):
        """Apply 3D RoPE to q, k.

        Args:
            q, k: ``(B, heads, N, head_dim)``.
            positions: ``(N, 3)`` integer (z, y, x) coordinates for the N tokens.
        """
        n, head_dim = q.shape[-2], q.shape[-1]
        used = self.axis_dim * 3
        cos_parts, sin_parts = [], []
        for axis in range(3):
            cos_a, sin_a = self._axis_cos_sin(positions[:, axis])  # (N, axis_dim)
            cos_parts.append(cos_a)
            sin_parts.append(sin_a)
        cos = torch.cat(cos_parts, dim=-1)  # (N, 3*axis_dim)
        sin = torch.cat(sin_parts, dim=-1)
        # pad rotary section up to head_dim with identity (cos=1, sin=0)
        if used < head_dim:
            pad = head_dim - used
            cos = torch.cat([cos, torch.ones(n, pad, device=q.device, dtype=cos.dtype)], dim=-1)
            sin = torch.cat([sin, torch.zeros(n, pad, device=q.device, dtype=sin.dtype)], dim=-1)
        cos = cos.to(q.dtype)[None, None]  # (1,1,N,head_dim)
        sin = sin.to(q.dtype)[None, None]
        q_out = q * cos + _rotate_half(q) * sin
        k_out = k * cos + _rotate_half(k) * sin
        return q_out, k_out


class Attention(nn.Module):
    def __init__(self, dim: int, heads: int, dropout: float = 0.0):
        super().__init__()
        assert dim % heads == 0, "dim must be divisible by heads"
        self.heads = heads
        self.head_dim = dim // heads
        self.scale = self.head_dim ** -0.5
        self.qkv = nn.Linear(dim, dim * 3)
        self.proj = nn.Linear(dim, dim)
        self.rope = RoPE3D(self.head_dim)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, positions: torch.Tensor | None = None) -> torch.Tensor:
        b, n, d = x.shape
        qkv = self.qkv(x).reshape(b, n, 3, self.heads, self.head_dim).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]  # (B, heads, N, head_dim)
        if positions is not None:
            # positions cover the non-[cls] tokens; prepend a zero position for [cls].
            cls_pos = torch.zeros(1, 3, device=positions.device, dtype=positions.dtype)
            full_pos = torch.cat([cls_pos, positions], dim=0)[:n]
            q, k = self.rope(q, k, full_pos)
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        out = attn @ v
        out = out.transpose(1, 2).reshape(b, n, d)
        return self.drop(self.proj(out))


class TransformerBlock(nn.Module):
    """Pre-norm Transformer block + 3D RoPE (the repeated block in Fig. 2)."""

    def __init__(self, dim: int, heads: int, mlp_ratio: float = 4.0, dropout: float = 0.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = Attention(dim, heads, dropout)
        self.norm2 = nn.LayerNorm(dim)
        hidden = int(dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(dim, hidden), nn.GELU(), nn.Dropout(dropout), nn.Linear(hidden, dim)
        )

    def forward(self, x: torch.Tensor, positions: torch.Tensor | None = None) -> torch.Tensor:
        x = x + self.attn(self.norm1(x), positions)
        x = x + self.mlp(self.norm2(x))
        return x
