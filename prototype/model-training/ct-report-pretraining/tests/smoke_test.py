"""End-to-end CPU smoke test for the CT–report pretraining scaffold.

Runs the full pipeline on tiny synthetic tensors (``smoke_config``):
  prepare_data -> Stage 1 (L_SSL) -> Stage 2 (L_SigLIP)
and asserts that artifacts are produced and losses are finite.

Run:  uv run python tests/smoke_test.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src")
sys.path.insert(0, os.path.abspath(SRC))

import torch  # noqa: E402

from ctreport.config import smoke_config  # noqa: E402
from ctreport.data.synthetic import generate_synthetic_shard, ShardDataset, collate  # noqa: E402
from ctreport.data.windowing import extract_windows  # noqa: E402
from ctreport.models.vit_local import LocalViT  # noqa: E402
from ctreport.models.multimodal import CTReportModel  # noqa: E402
from ctreport.losses.dino import DINOHead, DINOLoss, MultiCropWrapper, build_teacher, ema_update  # noqa: E402
from ctreport.data.augment import make_views  # noqa: E402
from ctreport.losses.siglip import siglip_loss  # noqa: E402


def _check_shapes(cfg):
    print("  windows/scan:", cfg.num_windows(), "patches/window:", cfg.patches_per_window())
    ds = ShardDataset  # noqa: F841 (import touch)
    vol = torch.randn(*cfg.volume_shape)
    wv = extract_windows(vol, cfg)
    assert wv.windows.shape[0] == cfg.num_windows(), "unexpected window count"
    local = LocalViT(cfg)
    out = local(wv.windows)
    assert out["cls"].shape == (cfg.num_windows(), cfg.local_dim)
    assert out["patches"].shape[1] == cfg.patches_per_window()
    print("  [ok] windowing + ViT_l forward")


def _stage1(cfg, data_dir, out_dir):
    ds = ShardDataset(data_dir)
    batch = collate([ds[i] for i in range(min(cfg.batch_size, len(ds)))])
    per = [extract_windows(batch["volume"][i], cfg).windows for i in range(batch["volume"].shape[0])]
    windows = torch.stack(per, dim=0).reshape(-1, *per[0].shape[1:])

    backbone = LocalViT(cfg)
    student = MultiCropWrapper(backbone, DINOHead(cfg.local_dim, cfg.ssl_out_dim))
    teacher = build_teacher(student)
    loss_fn = DINOLoss(cfg.ssl_out_dim, cfg.ssl_student_temp, cfg.ssl_teacher_temp)
    opt = torch.optim.AdamW(student.parameters(), lr=cfg.lr)
    n_t = cfg.ssl_global_crops
    n_s = cfg.ssl_global_crops + cfg.ssl_local_crops

    losses = []
    for _ in range(cfg.stage1_steps):
        views = make_views(windows, n_s)
        s_out = student(views)
        with torch.no_grad():
            t_out = teacher(views[:n_t])
        loss = loss_fn(s_out, t_out, n_s, n_t)
        opt.zero_grad(); loss.backward(); opt.step()
        ema_update(student, teacher, cfg.ssl_teacher_momentum)
        assert torch.isfinite(loss), "L_SSL not finite"
        losses.append(loss.item())
    os.makedirs(out_dir, exist_ok=True)
    torch.save(backbone.state_dict(), os.path.join(out_dir, "vit_local.pt"))
    print(f"  [ok] Stage 1 L_SSL {losses[0]:.3f} -> {losses[-1]:.3f}")
    return backbone


def _stage2(cfg, data_dir, backbone):
    ds = ShardDataset(data_dir)
    batch = collate([ds[i] for i in range(min(cfg.batch_size, len(ds)))])
    model = CTReportModel(cfg, local_vit=backbone)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=cfg.lr)
    losses = []
    for _ in range(cfg.stage2_steps):
        img, txt, scale, bias = model(batch["volume"], batch["reports"])
        loss = siglip_loss(img, txt, scale, bias)
        opt.zero_grad(); loss.backward(); opt.step()
        assert torch.isfinite(loss), "L_SigLIP not finite"
        losses.append(loss.item())
    assert img.shape == (batch["volume"].shape[0], cfg.embed_dim)
    print(f"  [ok] Stage 2 L_SigLIP {losses[0]:.3f} -> {losses[-1]:.3f}")


def main() -> None:
    cfg = smoke_config
    torch.manual_seed(cfg.seed)
    print("CT–report scaffold smoke test (smoke_config)")
    _check_shapes(cfg)
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = os.path.join(tmp, "data")
        manifest = generate_synthetic_shard(data_dir, cfg)
        assert os.path.exists(manifest)
        print("  [ok] prepare_data (synthetic shard)")
        backbone = _stage1(cfg, data_dir, os.path.join(tmp, "s1"))
        _stage2(cfg, data_dir, backbone)
        with open(manifest, encoding="utf-8") as f:
            assert json.load(f)["samples"] == cfg.synthetic_samples
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
