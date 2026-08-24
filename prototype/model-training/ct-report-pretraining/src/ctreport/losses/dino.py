"""DINOv3-style self-supervised objective -- Stage 1 (L_SSL in Fig. 2).

A compact DINO/iBOT-style self-distillation setup used to pretrain the local window ViT
(ViT_l) on CT windows:
  * A shared backbone (ViT_l) + projection ``DINOHead`` form a *student*; an EMA copy is
    the *teacher*.
  * Multiple augmented crops of each window are encoded; the student is trained to match
    the sharpened, centered teacher distribution over prototypes (cross-view).
  * The teacher is updated by momentum; a running center prevents collapse.

This captures the mechanics (self-distillation, centering, sharpening, EMA) at prototype
scale -- it is not a full DINOv3 reimplementation (no Gram anchoring, Sinkhorn, etc.).
"""

from __future__ import annotations

import copy
from typing import List

import torch
import torch.nn as nn
import torch.nn.functional as F


class DINOHead(nn.Module):
    """MLP projection head mapping backbone features to prototype logits."""

    def __init__(self, in_dim: int, out_dim: int, hidden_dim: int = 512, bottleneck: int = 128):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(in_dim, hidden_dim), nn.GELU(),
            nn.Linear(hidden_dim, bottleneck),
        )
        # parametrizations.weight_norm (not the legacy nn.utils.weight_norm) so the
        # module can be deepcopied into the EMA teacher (pytorch/pytorch#103001).
        self.last = nn.utils.parametrizations.weight_norm(
            nn.Linear(bottleneck, out_dim, bias=False)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.mlp(x)
        x = F.normalize(x, dim=-1, p=2)
        return self.last(x)


class MultiCropWrapper(nn.Module):
    """Wraps a window backbone that returns a dict with a ``cls`` feature + a DINO head."""

    def __init__(self, backbone: nn.Module, head: DINOHead):
        super().__init__()
        self.backbone = backbone
        self.head = head

    def forward(self, crops: List[torch.Tensor]) -> torch.Tensor:
        """Encode a list of crop batches -> concatenated prototype logits.

        Each crop batch is ``(B, C, wd, wh, ww)``. Returns ``(len(crops)*B, out_dim)``.
        """
        feats = [self.backbone(c)["cls"] for c in crops]
        return self.head(torch.cat(feats, dim=0))


class DINOLoss(nn.Module):
    def __init__(self, out_dim: int, student_temp: float = 0.1, teacher_temp: float = 0.04,
                 center_momentum: float = 0.9):
        super().__init__()
        self.student_temp = student_temp
        self.teacher_temp = teacher_temp
        self.center_momentum = center_momentum
        self.register_buffer("center", torch.zeros(1, out_dim))

    def forward(self, student_out: torch.Tensor, teacher_out: torch.Tensor,
                n_crops_student: int, n_crops_teacher: int) -> torch.Tensor:
        """Cross-entropy between teacher (target) and student (prediction) over crops.

        student_out: ``(n_crops_student*B, D)``; teacher_out: ``(n_crops_teacher*B, D)``.
        """
        s = student_out / self.student_temp
        s_chunks = s.chunk(n_crops_student)

        t = F.softmax((teacher_out - self.center) / self.teacher_temp, dim=-1).detach()
        t_chunks = t.chunk(n_crops_teacher)

        total, n_terms = 0.0, 0
        for ti, tc in enumerate(t_chunks):
            for si, sc in enumerate(s_chunks):
                if ti == si:
                    continue  # skip matching same crop against itself
                total = total + torch.sum(-tc * F.log_softmax(sc, dim=-1), dim=-1).mean()
                n_terms += 1
        n_terms = max(1, n_terms)
        self._update_center(teacher_out)
        return total / n_terms

    @torch.no_grad()
    def _update_center(self, teacher_out: torch.Tensor) -> None:
        batch_center = teacher_out.mean(dim=0, keepdim=True)
        self.center.mul_(self.center_momentum).add_(batch_center * (1 - self.center_momentum))


@torch.no_grad()
def ema_update(student: nn.Module, teacher: nn.Module, momentum: float) -> None:
    """teacher = momentum*teacher + (1-momentum)*student, param-wise."""
    for ps, pt in zip(student.parameters(), teacher.parameters()):
        pt.data.mul_(momentum).add_(ps.data * (1.0 - momentum))


def build_teacher(student: nn.Module) -> nn.Module:
    """Deep-copy a student into a frozen EMA teacher."""
    teacher = copy.deepcopy(student)
    for p in teacher.parameters():
        p.requires_grad_(False)
    return teacher
