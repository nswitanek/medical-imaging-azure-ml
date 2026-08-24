"""Synthetic CT + report dataset (prototype stand-in for the de-identified Gold zone).

Real training reads de-identified volumes + reports from the lakehouse
(``docs/04-data-platform-design.md``). For the scaffold we generate a small synthetic
set where each sample has a latent "finding class" that drives *both* the volume's
texture and its report tokens -- so the SigLIP alignment in Stage 2 has real signal to
learn, without any PHI.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

import torch
from torch.utils.data import Dataset

from ..config import ModelConfig

# A tiny controlled vocabulary of report *words* so the fallback text tower has something
# structured to align to. Each finding class has a signature phrase; noise words are drawn
# from a shared pool. The Qwen tower ignores this and tokenizes the raw strings instead.
_FINDING_WORDS: List[List[str]] = [
    ["lungs", "clear", "no", "effusion"],                    # class 0
    ["liver", "cyst", "hypodensity", "noted"],               # class 1
    ["appendix", "dilated", "inflammation", "abscess"],      # class 2
    ["ovary", "cyst", "adjacent", "inflammation"],           # class 3
]
_NOISE_WORDS: List[str] = [
    "study", "contrast", "mild", "seen", "with", "and",
    "unremarkable", "otherwise", "interval", "stable",
]
_NUM_CLASSES = len(_FINDING_WORDS)

# Special-token ids shared with the fallback tokenizer (text/tokenizer.py).
_PAD, _CLS, _EOS = 0, 1, 2

# Human-readable names for the latent finding classes (index-aligned with _FINDING_WORDS).
# Used by the eval gate and the online endpoint to return zero-shot findings.
_FINDING_NAMES: List[str] = [
    "lungs clear / no effusion",
    "liver cyst / hypodensity",
    "appendicitis / abscess",
    "ovarian cyst / inflammation",
]


def finding_class_names() -> List[str]:
    """Human-readable label per finding class (index-aligned with the phrases)."""
    return list(_FINDING_NAMES)


def finding_class_prompts() -> List[str]:
    """Canonical zero-shot text prompt (a plain report string) per finding class.

    Each prompt is just the class's signature phrase -- the same words :func:`_make_report`
    starts every report with (minus the random noise) -- so a SigLIP-aligned text tower embeds
    them into the shared space for zero-shot classification / retrieval. Returned as strings so
    they flow through whichever tokenizer the pinned text tower uses (Qwen or fallback).
    """
    return [" ".join(words) for words in _FINDING_WORDS]


def controlled_vocabulary() -> Dict[str, int]:
    """Deterministic ``word -> id`` map for the :class:`FallbackTokenizer`.

    Assigns a distinct id (>= 10) to every finding word and noise word so the fallback tower
    keeps per-class signal. Special ids: 0=[pad], 1=[cls], 2=[eos].
    """
    vocab: Dict[str, int] = {}
    next_id = 10
    for words in _FINDING_WORDS:
        for w in words:
            if w not in vocab:
                vocab[w] = next_id
                next_id += 1
    for w in _NOISE_WORDS:
        if w not in vocab:
            vocab[w] = next_id
            next_id += 1
    return vocab


def _make_volume(cls_idx: int, cfg: ModelConfig, gen: torch.Generator) -> torch.Tensor:
    """HU-like volume whose mean intensity + a planted blob depend on the class."""
    d, h, w = cfg.volume_shape
    base = torch.randn(d, h, w, generator=gen) * 150.0
    base = base + (cls_idx - _NUM_CLASSES / 2) * 120.0  # class-dependent HU shift
    # plant a class-located high-density blob so local windows carry the signal
    zc = int((cls_idx + 0.5) / _NUM_CLASSES * d)
    base[max(0, zc - 2) : zc + 2] += 400.0
    return base.clamp(-1000.0, 1000.0)


def _make_report(cls_idx: int, cfg: ModelConfig, gen: torch.Generator) -> str:
    """Report *string*: the class signature phrase + a few random noise words."""
    words = list(_FINDING_WORDS[cls_idx])
    n_noise = int(torch.randint(0, 4, (1,), generator=gen).item())
    if n_noise:
        idxs = torch.randint(0, len(_NOISE_WORDS), (n_noise,), generator=gen).tolist()
        words += [_NOISE_WORDS[i] for i in idxs]
    return " ".join(words)


class SyntheticCTReportDataset(Dataset):
    """Yields dicts with ``volume`` (D,H,W), ``report`` (str), ``label`` (int)."""

    def __init__(self, cfg: ModelConfig, n_samples: int | None = None, seed: int | None = None):
        self.cfg = cfg
        self.n = n_samples if n_samples is not None else cfg.synthetic_samples
        self.seed = cfg.seed if seed is None else seed
        # deterministic latent class per index
        g = torch.Generator().manual_seed(self.seed)
        self.labels = torch.randint(0, _NUM_CLASSES, (self.n,), generator=g).tolist()

    def __len__(self) -> int:
        return self.n

    def __getitem__(self, idx: int) -> Dict[str, object]:
        cls_idx = self.labels[idx]
        gen = torch.Generator().manual_seed(self.seed * 1000003 + idx)
        return {
            "volume": _make_volume(cls_idx, self.cfg, gen),
            "report": _make_report(cls_idx, self.cfg, gen),
            "label": torch.tensor(cls_idx, dtype=torch.long),
        }


def collate(batch: List[Dict[str, object]]) -> Dict[str, object]:
    """Collate volumes/labels into tensors and keep reports as a list of strings.

    Tokenization is deferred to the text tower (``CTReportModel.encode_text``) so the shard
    stays tower-agnostic -- the same reports feed either the Qwen or the fallback tokenizer.
    """
    return {
        "volume": torch.stack([b["volume"] for b in batch], dim=0),
        "reports": [b["report"] for b in batch],
        "label": torch.stack([b["label"] for b in batch], dim=0),
    }


def generate_synthetic_shard(out_dir: str, cfg: ModelConfig, n_samples: int | None = None,
                             seed: int | None = None) -> str:
    """Materialize a synthetic shard to disk and return the manifest path.

    Emulates ``prepare_data`` writing a versioned, immutable training snapshot. Volumes
    and token sequences are saved as a single ``.pt`` file plus a JSON manifest with
    provenance (config hash, sample count, "de-identified" classification). Pass a distinct
    ``seed`` to synthesize a held-out evaluation split.
    """
    os.makedirs(out_dir, exist_ok=True)
    ds = SyntheticCTReportDataset(cfg, n_samples=n_samples, seed=seed)
    volumes = torch.stack([ds[i]["volume"] for i in range(len(ds))])
    reports = [ds[i]["report"] for i in range(len(ds))]
    labels = torch.stack([ds[i]["label"] for i in range(len(ds))])
    torch.save({"volume": volumes, "reports": reports, "label": labels},
               os.path.join(out_dir, "shard.pt"))

    manifest = {
        "format": "ctreport-synthetic-v2",
        "samples": len(ds),
        "num_classes": _NUM_CLASSES,
        "classification": "de-identified (synthetic)",
        "volume_shape": list(cfg.volume_shape),
        "text_max_tokens": cfg.text_max_tokens,
        "text_tower": cfg.text_tower,
        "report_example": reports[0] if reports else "",
        "seed": ds.seed,
    }
    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path


class ShardDataset(Dataset):
    """Loads a shard written by :func:`generate_synthetic_shard`."""

    def __init__(self, shard_dir: str):
        blob = torch.load(os.path.join(shard_dir, "shard.pt"))
        self.volume = blob["volume"]
        self.reports = blob["reports"]
        self.label = blob["label"]

    def __len__(self) -> int:
        return self.volume.shape[0]

    def __getitem__(self, idx: int) -> Dict[str, object]:
        return {
            "volume": self.volume[idx],
            "report": self.reports[idx],
            "label": self.label[idx],
        }
