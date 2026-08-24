"""Azure ML managed online endpoint scoring script for the CT-report model.

v2 ``code_configuration`` scoring script: ``init()`` loads the registered model once,
``run(raw_data)`` scores a batch of instances. Each instance is a de-identified CT volume
(and optionally a report) and the endpoint returns the zero-shot finding classification plus
the shared-space image embedding -- the same SigLIP similarity the eval gate uses.

Request body (JSON)::

    {
      "input_data": {
        "instances": [
          {"volume": [ ... flat floats ... ], "shape": [D, H, W],
           "report": "liver cyst hypodensity noted"}      // report text optional
        ]
      }
    }

Response (JSON)::

    {"predictions": [
        {"predicted_finding": "...", "scores": {"<finding>": <sim>, ...},
         "image_embedding_preview": [...], "image_report_cosine": <float?>}
    ]}
"""

from __future__ import annotations

import json
import os

import torch

from ctreport.data.synthetic import finding_class_names, finding_class_prompts
from ctreport.serving import load_model

_model = None
_cfg = None
_class_txt = None
_class_names = None


def init() -> None:
    global _model, _cfg, _class_txt, _class_names
    model_root = os.environ.get("AZUREML_MODEL_DIR", ".")
    _model, _cfg = load_model(model_root)
    _class_names = finding_class_names()
    with torch.no_grad():
        _class_txt = _model.encode_text(finding_class_prompts())  # (K, embed)
    print(f"[score] model loaded; text_tower={_model.text_tower_kind}; "
          f"{len(_class_names)} finding classes; volume_shape={_cfg.volume_shape}")


def _score_instance(inst: dict) -> dict:
    shape = inst.get("shape", list(_cfg.volume_shape))
    vol = torch.tensor(inst["volume"], dtype=torch.float32).reshape(*shape).unsqueeze(0)  # (1,D,H,W)
    with torch.no_grad():
        img = _model.encode_image(vol)                       # (1, embed)
        sims = (img @ _class_txt.t()).squeeze(0)             # (K,)
    pred = int(torch.argmax(sims).item())
    out = {
        "predicted_finding": _class_names[pred],
        "scores": {name: float(sims[i].item()) for i, name in enumerate(_class_names)},
        "image_embedding_preview": [float(x) for x in img.squeeze(0)[:8].tolist()],
    }
    report = inst.get("report")
    if report:
        with torch.no_grad():
            rtxt = _model.encode_text([report])              # tokenized by the paired tower
            out["image_report_cosine"] = float((img @ rtxt.t()).item())
    return out


def run(raw_data):
    try:
        data = json.loads(raw_data) if isinstance(raw_data, (str, bytes)) else raw_data
        payload = data.get("input_data", data)
        instances = payload.get("instances", payload if isinstance(payload, list) else [])
        preds = [_score_instance(inst) for inst in instances]
        return {"predictions": preds}
    except Exception as exc:  # noqa: BLE001 -- surface a clean error to the caller
        return {"error": f"{exc.__class__.__name__}: {exc}"}
