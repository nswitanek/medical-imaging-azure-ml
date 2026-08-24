"""Azure ML component entry: evaluate + gate (docs/13 evaluation gate).

Loads a trained CT-report model asset, evaluates it on a held-out synthetic eval shard, and
compares the gate metric against a threshold that stands in for "the best current model". If
the candidate clears the bar it is copied to the ``blessed_model`` output (which the pipeline
registers as a versioned Model asset); if not, the job exits non-zero so the pipeline fails
and nothing downstream (registration / deployment) runs.

Metrics (all computed zero-shot from the SigLIP-aligned embeddings):
  * ``zero_shot_accuracy``     -- argmax over the canonical finding-class prompts == label.
  * ``image_text_recall_at_1`` -- each image retrieves its own paired report first.
  * ``mean_pos_cosine``        -- mean cosine of matched image/report pairs.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch  # noqa: E402
from torch.utils.data import DataLoader  # noqa: E402

from ctreport.data.synthetic import (  # noqa: E402
    ShardDataset,
    collate,
    finding_class_names,
    finding_class_prompts,
)
from ctreport.serving import load_model  # noqa: E402


@torch.no_grad()
def evaluate(model, cfg, data_dir: str) -> dict:
    ds = ShardDataset(data_dir)
    loader = DataLoader(ds, batch_size=cfg.batch_size, shuffle=False, collate_fn=collate)

    class_txt = model.encode_text(finding_class_prompts())  # (K, embed)

    img_embs, txt_embs, labels = [], [], []
    for batch in loader:
        img_embs.append(model.encode_image(batch["volume"]))
        txt_embs.append(model.encode_text(batch["reports"]))
        labels.append(batch["label"])
    img = torch.cat(img_embs, dim=0)                       # (N, embed)
    txt = torch.cat(txt_embs, dim=0)                       # (N, embed)
    label = torch.cat(labels, dim=0)                       # (N,)
    n = img.shape[0]

    # zero-shot classification: image vs the K class prompts
    zs_logits = img @ class_txt.t()                        # (N, K)
    zs_pred = zs_logits.argmax(dim=1)
    zero_shot_accuracy = float((zs_pred == label).float().mean().item())

    # image -> report retrieval within the eval set (diagonal is the true pair)
    sim = img @ txt.t()                                    # (N, N)
    retrieved = sim.argmax(dim=1)
    image_text_recall_at_1 = float((retrieved == torch.arange(n)).float().mean().item())

    # mean cosine of the matched pairs (embeddings are already L2-normalized)
    mean_pos_cosine = float((img * txt).sum(dim=1).mean().item())

    return {
        "zero_shot_accuracy": zero_shot_accuracy,
        "image_text_recall_at_1": image_text_recall_at_1,
        "mean_pos_cosine": mean_pos_cosine,
        "num_eval_samples": n,
        "num_classes": len(finding_class_names()),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate + gate the CT-report model.")
    ap.add_argument("--model-dir", required=True, help="Trained/candidate model asset folder.")
    ap.add_argument("--data-dir", required=True, help="Held-out eval shard folder.")
    ap.add_argument("--output-dir", required=True, help="Where to write metrics + gate result.")
    ap.add_argument("--blessed-dir", required=True,
                    help="On pass, the model is copied here for registration by the pipeline.")
    ap.add_argument("--gate-metric", default="zero_shot_accuracy",
                    choices=["zero_shot_accuracy", "image_text_recall_at_1", "mean_pos_cosine"])
    ap.add_argument("--threshold", type=float, default=0.30,
                    help="Stand-in for the incumbent/best-current-model score. Candidate must "
                         "meet or beat it to be registered + deployed.")
    args = ap.parse_args()

    model, cfg = load_model(args.model_dir)
    metrics = evaluate(model, cfg, args.data_dir)

    metric_value = metrics[args.gate_metric]
    passed = metric_value >= args.threshold

    os.makedirs(args.output_dir, exist_ok=True)
    with open(os.path.join(args.output_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    gate = {
        "gate_metric": args.gate_metric,
        "metric_value": metric_value,
        "threshold": args.threshold,
        "passed": passed,
        "comparison": f"{metric_value:.4f} >= {args.threshold:.4f} -> {passed}",
    }
    with open(os.path.join(args.output_dir, "gate.json"), "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2)

    # Emit MLflow metrics for the run UI (best-effort; the job still gates without it).
    try:
        import mlflow  # noqa: WPS433
        for k, v in metrics.items():
            mlflow.log_metric(k, float(v))
        mlflow.log_metric("gate_passed", 1.0 if passed else 0.0)
        mlflow.log_metric("gate_threshold", args.threshold)
    except Exception as exc:  # noqa: BLE001
        print(f"[evaluate] mlflow logging skipped ({exc.__class__.__name__}: {exc})")

    print(f"[evaluate] metrics: {json.dumps(metrics)}")
    print(f"[evaluate] gate: {gate['comparison']}")

    if not passed:
        print(f"[evaluate] GATE FAILED -- {args.gate_metric}={metric_value:.4f} < "
              f"{args.threshold:.4f}. Not registering; failing the pipeline.")
        sys.exit(1)

    # Bless: copy the model artifact (weights + config + cards) for registration.
    os.makedirs(args.blessed_dir, exist_ok=True)
    src = model  # noqa: F841 -- keep a handle for clarity; files come from model-dir
    from ctreport.serving import find_model_dir  # noqa: WPS433
    resolved = find_model_dir(args.model_dir)
    for fname in os.listdir(resolved):
        s = os.path.join(resolved, fname)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(args.blessed_dir, fname))
    with open(os.path.join(args.blessed_dir, "eval_result.json"), "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "gate": gate}, f, indent=2)
    print(f"[evaluate] GATE PASSED -- blessed model written to {args.blessed_dir}")


if __name__ == "__main__":
    main()
