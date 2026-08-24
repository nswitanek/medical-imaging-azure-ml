"""Tokenizers for the two text-tower variants.

Both return a padded ``(input_ids, attention_mask)`` LongTensor pair of shape
``(B, max_tokens)`` so the encoders can mask padding correctly:

  * :class:`QwenTokenizer`    -- the real Qwen3 BPE tokenizer (vocab ~151k, pads with the
    ``<|endoftext|>`` id, *not* 0). Loaded from HuggingFace locally, or from a mounted model
    asset on governed compute (see :func:`resolve_text_model_ref`).
  * :class:`FallbackTokenizer` -- a deterministic controlled-vocabulary tokenizer over the
    synthetic report words (pads with 0). No downloads; used by the CPU smoke test and
    whenever Qwen isn't available.

The tokenizer must match the encoder it feeds (Qwen ids only make sense to the Qwen
embedding table), so ``config.text_tower`` pins both together.
"""

from __future__ import annotations

import hashlib
import os
from typing import Dict, List, Sequence, Tuple

import torch

from ..config import ModelConfig

# Special ids shared with the fallback dataset vocabulary (data/synthetic.py).
_PAD, _CLS, _EOS = 0, 1, 2


def resolve_text_model_ref(cfg: ModelConfig) -> str:
    """Where to load the Qwen tokenizer/weights from.

    Governed Azure ML compute usually can't reach ``huggingface.co``. Register Qwen3-0.6B as
    a model asset, mount it into the job/deployment, and set ``CTREPORT_QWEN_DIR`` to the mount
    path; this returns that path. Otherwise it falls back to the hub id in ``text_model_name``
    (resolved from the local HuggingFace cache when ``HF_HUB_OFFLINE=1``).
    """
    return os.environ.get("CTREPORT_QWEN_DIR") or cfg.text_model_name


class TextTokenizer:
    """Common interface: ``encode(texts) -> (input_ids, attention_mask)``."""

    kind: str = "base"

    def encode(self, texts: Sequence[str], max_tokens: int) -> Tuple[torch.Tensor, torch.Tensor]:
        raise NotImplementedError


class FallbackTokenizer(TextTokenizer):
    """Deterministic controlled-vocabulary tokenizer (dependency-free)."""

    kind = "fallback"

    def __init__(self, cfg: ModelConfig):
        self.vocab_size = cfg.vocab_size
        # Import here to avoid a package import cycle (data <-> text).
        from ..data.synthetic import controlled_vocabulary

        self.word2id: Dict[str, int] = controlled_vocabulary()

    def _tok(self, word: str) -> int:
        word = word.lower()
        if word in self.word2id:
            return self.word2id[word]
        # hash out-of-vocabulary words into a reserved, stable range < vocab_size
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        return 50 + (h % max(1, self.vocab_size - 50))

    def encode(self, texts: Sequence[str], max_tokens: int) -> Tuple[torch.Tensor, torch.Tensor]:
        rows: List[List[int]] = []
        masks: List[List[int]] = []
        for text in texts:
            ids = [_CLS] + [self._tok(w) for w in str(text).split()] + [_EOS]
            ids = ids[:max_tokens]
            mask = [1] * len(ids)
            pad = max_tokens - len(ids)
            rows.append(ids + [_PAD] * pad)
            masks.append(mask + [0] * pad)
        return (torch.tensor(rows, dtype=torch.long),
                torch.tensor(masks, dtype=torch.long))


class QwenTokenizer(TextTokenizer):
    """The real Qwen3 tokenizer. Instantiated only when ``transformers`` + weights exist."""

    kind = "qwen"

    def __init__(self, cfg: ModelConfig):
        from transformers import AutoTokenizer  # optional dependency

        ref = resolve_text_model_ref(cfg)
        self.tok = AutoTokenizer.from_pretrained(ref)
        if self.tok.pad_token is None:                     # Qwen pads with <|endoftext|>
            self.tok.pad_token = self.tok.eos_token

    def encode(self, texts: Sequence[str], max_tokens: int) -> Tuple[torch.Tensor, torch.Tensor]:
        enc = self.tok(
            list(texts),
            padding="max_length",
            truncation=True,
            max_length=max_tokens,
            return_tensors="pt",
        )
        return enc["input_ids"].long(), enc["attention_mask"].long()


def build_tokenizer(cfg: ModelConfig, kind: str) -> TextTokenizer:
    """Return the tokenizer paired with a resolved text-tower ``kind``."""
    if kind == "qwen":
        return QwenTokenizer(cfg)
    if kind == "fallback":
        return FallbackTokenizer(cfg)
    raise ValueError(f"unknown tokenizer kind '{kind}', expected 'qwen' or 'fallback'")
