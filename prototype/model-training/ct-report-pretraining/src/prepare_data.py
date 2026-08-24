"""Azure ML component entry: prepare_data.

Materializes a versioned, immutable training snapshot (emulating the de-identified Gold
zone handoff from docs/04). For the scaffold this generates a synthetic CT+report shard;
in production, replace the body with a lakehouse/feature-view read.
"""

from __future__ import annotations

import argparse
import os
import sys

# make the ``ctreport`` package importable whether run locally or as an AML component
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ctreport.config import get_config          # noqa: E402
from ctreport.data.synthetic import generate_synthetic_shard  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the CT–report training snapshot.")
    ap.add_argument("--output-dir", required=True, help="Where to write the shard + manifest.")
    ap.add_argument("--config-preset", default="smoke", choices=["smoke", "default"])
    ap.add_argument("--num-samples", type=int, default=None, help="Override sample count.")
    ap.add_argument("--seed", type=int, default=None,
                    help="Override RNG seed. Use a distinct value to synthesize a held-out "
                         "evaluation split that doesn't overlap the training shard.")
    args = ap.parse_args()

    cfg = get_config(args.config_preset)
    os.makedirs(args.output_dir, exist_ok=True)
    # persist the exact config used so downstream stages + registry lineage are pinned
    with open(os.path.join(args.output_dir, "config.json"), "w", encoding="utf-8") as f:
        f.write(cfg.to_json())

    manifest = generate_synthetic_shard(args.output_dir, cfg, n_samples=args.num_samples,
                                        seed=args.seed)
    print(f"[prepare_data] wrote snapshot to {args.output_dir}")
    print(f"[prepare_data] manifest: {manifest}")


if __name__ == "__main__":
    main()
