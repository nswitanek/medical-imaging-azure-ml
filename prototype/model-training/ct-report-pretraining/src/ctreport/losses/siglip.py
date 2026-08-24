"""SigLIP loss -- Stage 2 cross-modal alignment (L_SigLIP in Fig. 2).

Sigmoid contrastive loss (Zhai et al. 2023): every image-text pair in the batch is an
independent binary classification -- the diagonal (matched) pairs are positives, all
off-diagonal pairs are negatives -- scored with a learnable temperature and bias. Unlike
softmax CLIP it needs no all-gather over the full batch to normalize.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F


def siglip_loss(
    image_emb: torch.Tensor,
    text_emb: torch.Tensor,
    logit_scale: torch.Tensor,
    logit_bias: torch.Tensor,
) -> torch.Tensor:
    """Compute the SigLIP loss for L2-normalized image/text embeddings.

    Args:
        image_emb, text_emb: ``(B, embed_dim)`` L2-normalized.
        logit_scale: learnable scalar; the exponentiated value multiplies similarities.
        logit_bias: learnable scalar added to logits.
    Returns:
        scalar loss.
    """
    b = image_emb.shape[0]
    logits = image_emb @ text_emb.t() * logit_scale.exp() + logit_bias  # (B, B)
    # labels: +1 on the diagonal (positives), -1 elsewhere (negatives)
    labels = 2 * torch.eye(b, device=logits.device) - 1.0
    # -log sigmoid(labels * logits), averaged; use logsigmoid for stability
    loss = -F.logsigmoid(labels * logits).sum() / b
    return loss
