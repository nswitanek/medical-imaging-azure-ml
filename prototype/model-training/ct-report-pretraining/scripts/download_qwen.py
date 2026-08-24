"""Download Qwen3-0.6B locally for registration as an Azure ML model asset.

Governed Azure ML compute usually can't reach ``huggingface.co``. Run this on a machine that
*can* (e.g. your dev box), then register the resulting folder as a model asset and mount it
into the training/eval/serving jobs (see ``scripts/qwen-text-tower.md``).

Usage::

    uv run --extra text python scripts/download_qwen.py --out ./qwen3-0.6b
"""

from __future__ import annotations

import argparse
import os


def main() -> None:
    ap = argparse.ArgumentParser(description="Snapshot Qwen3-0.6B to a local folder.")
    ap.add_argument("--model-id", default="Qwen/Qwen3-0.6B")
    ap.add_argument("--out", default="./qwen3-0.6b", help="Target folder for the snapshot.")
    args = ap.parse_args()

    from huggingface_hub import snapshot_download

    os.makedirs(args.out, exist_ok=True)
    path = snapshot_download(
        repo_id=args.model_id,
        local_dir=args.out,
        # weights + tokenizer + config only; skip the original consolidated files
        allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "tokenizer*"],
    )
    print(f"[download_qwen] {args.model_id} -> {path}")
    print("[download_qwen] next: register as a model asset, e.g.")
    print(f"  az ml model create -f azureml/model-assets/qwen3-0.6b.yml --set path={args.out}")


if __name__ == "__main__":
    main()
