"""Azure ML component entry: stage2_siglip_align (L_SigLIP).

Loads the Stage 1 ViT_l, builds the full dual-tower CT–report model (ViT_l -> ViT_g vision
tower + Qwen/LoRA text tower), and aligns them in a shared embedding space with the
sigmoid contrastive (SigLIP) loss. Emits the aligned model for the registry + eval gate.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch  # noqa: E402
from torch.utils.data import DataLoader  # noqa: E402

from ctreport.config import ModelConfig, get_config  # noqa: E402
from ctreport.data.synthetic import ShardDataset, collate  # noqa: E402
from ctreport.models.vit_local import LocalViT  # noqa: E402
from ctreport.models.multimodal import CTReportModel  # noqa: E402
from ctreport.losses.siglip import siglip_loss  # noqa: E402


def load_config(args) -> ModelConfig:
    for d in (args.stage1_ckpt, args.data_dir):
        cfg_path = os.path.join(d, "config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, encoding="utf-8") as f:
                return ModelConfig.from_json(f.read())
    return get_config(args.config_preset)


def main() -> None:
    ap = argparse.ArgumentParser(description="Stage 2 SigLIP cross-modal alignment.")
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--stage1-ckpt", required=True, help="Dir with vit_local.pt from Stage 1.")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--config-preset", default="smoke", choices=["smoke", "default"])
    ap.add_argument("--max-steps", type=int, default=None)
    ap.add_argument("--freeze-local", type=lambda s: str(s).lower() in ("1", "true", "yes"),
                    default=False,
                    help="Freeze ViT_l (train ViT_g + text + projections only).")
    args = ap.parse_args()

    cfg = load_config(args)
    torch.manual_seed(cfg.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    max_steps = args.max_steps if args.max_steps is not None else cfg.stage2_steps

    ds = ShardDataset(args.data_dir)
    loader = DataLoader(ds, batch_size=cfg.batch_size, shuffle=True, collate_fn=collate)

    # warm-start ViT_l from Stage 1
    local = LocalViT(cfg)
    ckpt = os.path.join(args.stage1_ckpt, "vit_local.pt")
    if os.path.exists(ckpt):
        local.load_state_dict(torch.load(ckpt, map_location="cpu"))
        print(f"[stage2] loaded Stage 1 ViT_l from {ckpt}")
    else:
        print(f"[stage2] WARNING: {ckpt} not found; training ViT_l from scratch.")

    if args.freeze_local:
        for p in local.parameters():
            p.requires_grad_(False)

    model = CTReportModel(cfg, local_vit=local).to(device)
    # Pin the resolved text tower (qwen|fallback) so eval/serving rebuild the identical model.
    cfg.text_tower = model.text_tower_kind
    print(f"[stage2] text tower: {model.text_tower_kind}")
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=cfg.lr, weight_decay=cfg.weight_decay)

    step, history = 0, []
    model.train()
    while step < max_steps:
        for batch in loader:
            if step >= max_steps:
                break
            volumes = batch["volume"].to(device)
            reports = batch["reports"]                          # list[str]; tokenized in-model
            img, txt, scale, bias = model(volumes, reports)
            loss = siglip_loss(img, txt, scale, bias)

            opt.zero_grad()
            loss.backward()
            opt.step()

            history.append({"step": step, "l_siglip": float(loss.item())})
            if step % max(1, max_steps // 5) == 0:
                print(f"[stage2] step {step}/{max_steps}  L_SigLIP={loss.item():.4f}")
            step += 1

    os.makedirs(args.output_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(args.output_dir, "ct_report_model.pt"))
    with open(os.path.join(args.output_dir, "config.json"), "w", encoding="utf-8") as f:
        f.write(cfg.to_json())
    with open(os.path.join(args.output_dir, "stage2_metrics.json"), "w", encoding="utf-8") as f:
        json.dump({"final_l_siglip": history[-1]["l_siglip"] if history else None,
                   "steps": step, "history": history}, f, indent=2)
    # MLmodel-style stub so a downstream AML register step has lineage metadata
    with open(os.path.join(args.output_dir, "model_card.json"), "w", encoding="utf-8") as f:
        json.dump({
            "name": "ct-report-siglip",
            "stage1_ckpt": args.stage1_ckpt,
            "objective": "SigLIP (L_SigLIP) over ViT_l+ViT_g vision tower and text tower",
            "text_tower": model.text_tower_kind,
            "clinical_status": "NOT clinically validated -- prototype",
            "next": "evaluation gate (docs/13) before hosting (docs/06)",
        }, f, indent=2)
    print(f"[stage2] saved aligned model to {args.output_dir}/ct_report_model.pt")


if __name__ == "__main__":
    main()
