"""Text transformer -- Fig. 2 "Text" box: Qwen tokenization + Qwen3-0.6B embedding + LoRA.

Two implementations behind one interface:
  * ``QwenTextEncoder``    -- loads Qwen3-0.6B via ``transformers`` and wraps it with a
    LoRA adapter via ``peft`` (only the LoRA weights + projection train). Used on Azure
    ML GPU when the model + libs are available.
  * ``FallbackTextEncoder`` -- a tiny dependency-free token-embedding + 1-layer
    transformer so the scaffold's smoke test runs anywhere (CPU, no downloads).

Each takes an explicit ``attention_mask`` (Qwen pads with a non-zero id, so a mask is
required for correct pooling). ``build_text_encoder`` resolves the tower from
``cfg.text_tower`` and returns ``(encoder, kind)`` so the caller can build the *matching*
tokenizer and pin ``kind`` into the saved config.
"""

from __future__ import annotations

from typing import Tuple

import torch
import torch.nn as nn

from ..config import ModelConfig
from ..text.tokenizer import resolve_text_model_ref


class TextEncoder(nn.Module):
    """Common interface: forward(input_ids, attention_mask) -> (B, text_dim) sentence embedding."""

    text_dim: int
    kind: str = "base"

    def forward(self, input_ids: torch.Tensor,
                attention_mask: torch.Tensor) -> torch.Tensor:  # pragma: no cover
        raise NotImplementedError


def _masked_mean(hidden: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """Mean-pool token embeddings over non-pad positions (avoids div-by-zero)."""
    keep = attention_mask.unsqueeze(-1).to(hidden.dtype)   # (B, L, 1)
    summed = (hidden * keep).sum(dim=1)
    counts = keep.sum(dim=1).clamp(min=1.0)
    return summed / counts


class FallbackTextEncoder(TextEncoder):
    """Dependency-free stand-in for Qwen (used when transformers/peft aren't present)."""

    kind = "fallback"

    def __init__(self, cfg: ModelConfig):
        super().__init__()
        dim = cfg.global_dim
        self.text_dim = dim
        self.embed = nn.Embedding(cfg.vocab_size, dim, padding_idx=0)
        self.pos = nn.Parameter(torch.zeros(1, cfg.text_max_tokens, dim))
        nn.init.trunc_normal_(self.pos, std=0.02)
        layer = nn.TransformerEncoderLayer(
            d_model=dim, nhead=max(1, cfg.global_heads), dim_feedforward=dim * 4,
            batch_first=True, dropout=cfg.dropout,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=2)
        self.norm = nn.LayerNorm(dim)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        pad_mask = attention_mask.eq(0)                    # (B, L) True where pad
        x = self.embed(input_ids) + self.pos[:, : input_ids.shape[1]]
        x = self.encoder(x, src_key_padding_mask=pad_mask)
        x = self.norm(x)
        return _masked_mean(x, attention_mask)


class QwenTextEncoder(TextEncoder):
    """Qwen3-0.6B embedding + LoRA. Instantiated only when libs + weights are available."""

    kind = "qwen"

    def __init__(self, cfg: ModelConfig):
        super().__init__()
        from transformers import AutoModel  # local import: optional dependency
        from peft import LoraConfig, get_peft_model

        # Load in float32 so the shared-space projection + SigLIP math match the vision tower
        # (Qwen3 ships bf16 weights; mixing dtypes breaks the projection matmul on CPU/GPU).
        base = AutoModel.from_pretrained(resolve_text_model_ref(cfg), dtype=torch.float32)
        for p in base.parameters():
            p.requires_grad_(False)                        # freeze the backbone
        lora = LoraConfig(
            r=cfg.lora_rank,
            lora_alpha=cfg.lora_alpha,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            bias="none",
            task_type="FEATURE_EXTRACTION",
        )
        self.backbone = get_peft_model(base, lora)
        self.text_dim = base.config.hidden_size

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        out = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        return _masked_mean(out.last_hidden_state, attention_mask)


def build_text_encoder(cfg: ModelConfig) -> Tuple[TextEncoder, str]:
    """Return ``(encoder, kind)`` for the tower selected by ``cfg.text_tower``.

    * ``"fallback"`` -> the dependency-free encoder.
    * ``"qwen"``     -> the real Qwen tower; RAISES if unavailable (a pinned Qwen model must
      reload with Qwen weights, so we never silently substitute a different tower).
    * ``"auto"``     -> Qwen when it loads, otherwise the fallback (with a printed notice).
    """
    mode = getattr(cfg, "text_tower", "auto")
    if mode == "fallback":
        return FallbackTextEncoder(cfg), "fallback"
    if mode == "qwen":
        return QwenTextEncoder(cfg), "qwen"                # propagate failures on purpose
    # auto
    try:
        return QwenTextEncoder(cfg), "qwen"
    except Exception as exc:  # noqa: BLE001 -- fall back on any import/download failure
        print(f"[text_encoder] Qwen unavailable ({exc.__class__.__name__}: {exc}); "
              f"using FallbackTextEncoder.")
        return FallbackTextEncoder(cfg), "fallback"
