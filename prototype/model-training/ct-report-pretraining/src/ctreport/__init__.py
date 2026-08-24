"""CT–report multimodal pretraining scaffold.

Emulates the two-stage volumetric CT–report transformer from CVPR 2026 Fig. 2:
  * Stage 1 (SSL / DINOv3): local window ViT (ViT_l) learns localized CT features.
  * Stage 2 (SigLIP): vision tower (ViT_l -> pool -> ViT_g) aligned with a text tower.

This is prototype sample code -- not clinically validated.
"""

from .config import ModelConfig, default_config, smoke_config

__all__ = ["ModelConfig", "default_config", "smoke_config"]
