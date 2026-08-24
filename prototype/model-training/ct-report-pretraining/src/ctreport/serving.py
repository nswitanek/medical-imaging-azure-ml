"""Shared helpers for reloading a trained CT–report model for eval and serving.

Both the evaluation component (``evaluate.py``) and the online scoring script
(``score.py``) need to rebuild the exact model that Stage 2 saved. Keeping the logic here
guarantees they reconstruct it identically from the pinned ``config.json`` + weights.
"""

from __future__ import annotations

import os
from typing import Tuple

import torch

from .config import ModelConfig
from .models.multimodal import CTReportModel

_WEIGHTS = "ct_report_model.pt"
_CONFIG = "config.json"


def find_model_dir(root: str) -> str:
    """Locate the directory holding ``ct_report_model.pt``.

    A registered Azure ML model mounts under ``AZUREML_MODEL_DIR`` often nested one level
    deep (``<mount>/<model_name>/...``), so search shallowly for the weights file.
    """
    for dirpath, _dirs, files in os.walk(root):
        if _WEIGHTS in files and _CONFIG in files:
            return dirpath
    # fall back to the root even if not found, so the caller raises a clear error
    return root


def load_model(model_dir: str, map_location: str = "cpu") -> Tuple[CTReportModel, ModelConfig]:
    """Rebuild ``CTReportModel`` + ``ModelConfig`` from a saved/registered model folder."""
    resolved = find_model_dir(model_dir)
    cfg_path = os.path.join(resolved, _CONFIG)
    weights_path = os.path.join(resolved, _WEIGHTS)
    if not os.path.exists(weights_path) or not os.path.exists(cfg_path):
        raise FileNotFoundError(
            f"expected {_WEIGHTS} and {_CONFIG} under {model_dir} (searched to {resolved})"
        )
    with open(cfg_path, encoding="utf-8") as f:
        cfg = ModelConfig.from_json(f.read())

    model = CTReportModel(cfg)
    state = torch.load(weights_path, map_location=map_location)
    model.load_state_dict(state)
    model.eval()
    return model, cfg
