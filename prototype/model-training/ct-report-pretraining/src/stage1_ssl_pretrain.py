"""Azure ML component entry: stage1_ssl_pretrain (L_SSL, DINOv3-style).

Pretrains the window-level ViT_l on CT windows via self-distillation. Emits the trained
ViT_l weights, which Stage 2 loads as the frozen/warm-started local backbone.
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
from ctreport.data.windowing import extract_windows  # noqa: E402
from ctreport.data.augment import make_views  # noqa: E402
from ctreport.models.vit_local import LocalViT  # noqa: E402
from ctreport.losses.dino import (  # noqa: E402
    DINOHead, DINOLoss, MultiCropWrapper, build_teacher, ema_update,
)


def _windows_from_batch(volumes: torch.Tensor, cfg: ModelConfig) -> torch.Tensor:
    """(B, D, H, W) -> (B*G, C, wd, wh, ww): every window is an SSL sample."""
    per = [extract_windows(volumes[i], cfg).windows for i in range(volumes.shape[0])]
    stacked = torch.stack(per, dim=0)                      # (B, G, C, wd, wh, ww)
    return stacked.reshape(-1, *stacked.shape[2:])


def load_config(args) -> ModelConfig:
    cfg_path = os.path.join(args.data_dir, "config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            return ModelConfig.from_json(f.read())
    return get_config(args.config_preset)


def main() -> None:
    ap = argparse.ArgumentParser(description="Stage 1 SSL pretraining of ViT_l.")
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--config-preset", default="smoke", choices=["smoke", "default"])
    ap.add_argument("--max-steps", type=int, default=None)
    args = ap.parse_args()

    cfg = load_config(args)
    torch.manual_seed(cfg.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    max_steps = args.max_steps if args.max_steps is not None else cfg.stage1_steps

    ds = ShardDataset(args.data_dir)
    loader = DataLoader(ds, batch_size=cfg.batch_size, shuffle=True, collate_fn=collate)

    backbone = LocalViT(cfg)
    head = DINOHead(cfg.local_dim, cfg.ssl_out_dim)
    student = MultiCropWrapper(backbone, head).to(device)
    teacher = build_teacher(student).to(device)
    loss_fn = DINOLoss(cfg.ssl_out_dim, cfg.ssl_student_temp, cfg.ssl_teacher_temp,
                       cfg.ssl_center_momentum).to(device)
    opt = torch.optim.AdamW(student.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    n_teacher = cfg.ssl_global_crops
    n_student = cfg.ssl_global_crops + cfg.ssl_local_crops

    step, history = 0, []
    student.train()
    while step < max_steps:
        for batch in loader:
            if step >= max_steps:
                break
            windows = _windows_from_batch(batch["volume"].to(device), cfg)
            views = make_views(windows, n_student)
            views = [v.to(device) for v in views]
            student_out = student(views)                       # (n_student*Bw, D)
            with torch.no_grad():
                teacher_out = teacher(views[:n_teacher])       # (n_teacher*Bw, D)
            loss = loss_fn(student_out, teacher_out, n_student, n_teacher)

            opt.zero_grad()
            loss.backward()
            opt.step()
            ema_update(student, teacher, cfg.ssl_teacher_momentum)

            history.append({"step": step, "l_ssl": float(loss.item())})
            if step % max(1, max_steps // 5) == 0:
                print(f"[stage1] step {step}/{max_steps}  L_SSL={loss.item():.4f}")
            step += 1

    os.makedirs(args.output_dir, exist_ok=True)
    torch.save(backbone.state_dict(), os.path.join(args.output_dir, "vit_local.pt"))
    with open(os.path.join(args.output_dir, "config.json"), "w", encoding="utf-8") as f:
        f.write(cfg.to_json())
    with open(os.path.join(args.output_dir, "stage1_metrics.json"), "w", encoding="utf-8") as f:
        json.dump({"final_l_ssl": history[-1]["l_ssl"] if history else None,
                   "steps": step, "history": history}, f, indent=2)
    print(f"[stage1] saved ViT_l weights to {args.output_dir}/vit_local.pt")


if __name__ == "__main__":
    main()
