"""Configuration for the CT–report pretraining scaffold.

Two presets:
  * ``default_config`` -- paper-scale-ish dimensions (ViT_l with 24 blocks, ViT_g with
    4 blocks). Meant for GPU on Azure ML. Not the exact paper hyper-parameters.
  * ``smoke_config``   -- tiny dimensions so the whole 2-stage pipeline runs in seconds
    on CPU for local validation.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Tuple
import json


@dataclass
class ModelConfig:
    # ---- Volume windowing (Fig. 2: "Windowing" -> G windows of N patches) ----
    volume_shape: Tuple[int, int, int] = (128, 128, 128)  # (D, H, W) voxels
    window_shape: Tuple[int, int, int] = (64, 64, 64)     # each of G windows
    patch_size: Tuple[int, int, int] = (16, 16, 16)       # 3D tokenization patch
    hu_windows: Tuple[Tuple[int, int], ...] = ((-1000, 400),)  # (level clamp) HU ranges

    # ---- ViT_l (window-level, local) ----
    local_dim: int = 384
    local_depth: int = 24            # "x24" in the figure
    local_heads: int = 6

    # ---- ViT_g (scan-level, global) ----
    global_dim: int = 384
    global_depth: int = 4            # "x4" in the figure
    global_heads: int = 6

    # ---- Shared projection / embedding space (SigLIP) ----
    embed_dim: int = 256

    # ---- Text tower (Qwen3-0.6B embedding + LoRA) ----
    # ``text_tower`` selects the tokenizer+encoder pair and is PINNED into the saved
    # config.json so eval/serving rebuild the identical tower:
    #   * "auto"     -- use Qwen3 when transformers/peft + weights are reachable, else fallback.
    #   * "qwen"     -- require the real Qwen3-0.6B tower (raises if unavailable).
    #   * "fallback" -- the dependency-free stand-in tower (no downloads).
    # On governed compute that can't reach HuggingFace, mount Qwen as a model asset and point
    # ``CTREPORT_QWEN_DIR`` at the mount (see scripts/qwen-text-tower.md).
    text_tower: str = "auto"
    text_model_name: str = "Qwen/Qwen3-0.6B"
    text_max_tokens: int = 256
    lora_rank: int = 16
    lora_alpha: int = 32

    # ---- DINOv3-style SSL (Stage 1) ----
    ssl_out_dim: int = 4096          # prototype/projection head dimension
    ssl_teacher_momentum: float = 0.996
    ssl_center_momentum: float = 0.9
    ssl_student_temp: float = 0.1
    ssl_teacher_temp: float = 0.04
    ssl_global_crops: int = 2
    ssl_local_crops: int = 4

    # ---- SigLIP (Stage 2) ----
    siglip_init_logit_scale: float = 2.3   # log(10)
    siglip_init_logit_bias: float = -10.0

    # ---- Training ----
    batch_size: int = 8
    lr: float = 1e-4
    weight_decay: float = 0.05
    stage1_steps: int = 2000
    stage2_steps: int = 2000
    seed: int = 13
    dropout: float = 0.0

    # ---- Synthetic dataset (prototype only) ----
    synthetic_samples: int = 64
    vocab_size: int = 4096           # fallback text tower vocab

    def num_windows(self) -> int:
        d = self.volume_shape[0] // self.window_shape[0]
        h = self.volume_shape[1] // self.window_shape[1]
        w = self.volume_shape[2] // self.window_shape[2]
        return max(1, d) * max(1, h) * max(1, w)

    def patches_per_window(self) -> int:
        d = self.window_shape[0] // self.patch_size[0]
        h = self.window_shape[1] // self.patch_size[1]
        w = self.window_shape[2] // self.patch_size[2]
        return max(1, d) * max(1, h) * max(1, w)

    def patch_grid(self) -> Tuple[int, int, int]:
        return (
            max(1, self.window_shape[0] // self.patch_size[0]),
            max(1, self.window_shape[1] // self.patch_size[1]),
            max(1, self.window_shape[2] // self.patch_size[2]),
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, text: str) -> "ModelConfig":
        raw = json.loads(text)
        # tuples come back as lists from JSON -- coerce the known tuple fields
        for k in ("volume_shape", "window_shape", "patch_size"):
            if k in raw and raw[k] is not None:
                raw[k] = tuple(raw[k])
        if "hu_windows" in raw and raw["hu_windows"] is not None:
            raw["hu_windows"] = tuple(tuple(x) for x in raw["hu_windows"])
        return cls(**raw)


default_config = ModelConfig()

smoke_config = ModelConfig(
    volume_shape=(32, 32, 32),
    window_shape=(16, 16, 16),
    patch_size=(8, 8, 8),
    local_dim=32,
    local_depth=2,
    local_heads=4,
    global_dim=32,
    global_depth=2,
    global_heads=4,
    embed_dim=32,
    text_tower="fallback",   # keep the CPU smoke test offline + dependency-free
    text_max_tokens=24,
    lora_rank=4,
    lora_alpha=8,
    ssl_out_dim=128,
    ssl_local_crops=2,
    batch_size=4,
    stage1_steps=3,
    stage2_steps=3,
    synthetic_samples=8,
    vocab_size=256,
)


def get_config(preset: str) -> ModelConfig:
    presets = {"default": default_config, "smoke": smoke_config}
    if preset not in presets:
        raise ValueError(f"unknown config preset '{preset}', expected one of {list(presets)}")
    return presets[preset]
