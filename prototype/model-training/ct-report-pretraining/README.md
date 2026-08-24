# CT–Report Multimodal Pretraining — Azure ML Scaffold

A **runnable scaffold** that emulates the two-stage volumetric CT–report pretraining
pipeline from *"Scaling Self-Supervised and Cross-Modal Pretraining for Volumetric CT
Transformers"* (CVPR 2026, Figure 2) as an **Azure ML v2 pipeline**.

> **Prototype status.** This is architecture-shaped **sample code**, not clinically
> validated and not tuned. It exists to prove the *training substrate* described in
> [`docs/05-model-training.md`](../../../docs/05-model-training.md) end-to-end on
> **de-identified** (here, **synthetic**) data. It runs on CPU with tiny tensors so the
> whole pipeline can be smoke-tested locally, and scales to GPU on Azure ML by swapping
> compute + config.

## What the paper figure describes

The model jointly processes a volumetric CT scan and its radiology report in two
pretraining stages:

| Stage | Objective | What trains |
|---|---|---|
| **Stage 1 — SSL** | `L_SSL` (DINOv3 self-distillation) | Local vision transformer **ViT_ℓ** learns localized features from CT **window** crops. |
| **Stage 2 — SigLIP** | `L_SigLIP` (sigmoid contrastive) | Vision tower (**ViT_ℓ → pool → ViT_g**) is aligned with a **text transformer** (Qwen3-0.6B embedding + LoRA) in a shared embedding space. |

Architecture components (mapped 1:1 in `src/ctreport/`):

- **Windowing** — the CT volume is split into `G` windows; each window into `N` 3D patches (`data/windowing.py`).
- **ViT_ℓ (window-level)** — 3D tokenization + `[cls]` + 24× *Transformer Block + 3D RoPE* (`models/vit_local.py`).
- **Pool + Concat** — per-window local features pooled and concatenated into `G` window tokens (`models/multimodal.py`).
- **ViT_g (scan-level)** — `[cls]` + 4× *Transformer Block + 3D RoPE* aggregating the `G` windows (`models/vit_global.py`).
- **Text transformer** — Qwen tokenization + Qwen3-0.6B embedding + LoRA (`models/text_encoder.py`
  + `text/tokenizer.py`), with a dependency-free fallback. The tokenizer is **paired** with the
  encoder and the choice is pinned in the model's `config.json` (`text_tower: qwen|fallback`) so
  eval/serving rebuild the identical tower. Reports flow as **text**; the tower tokenizes them.
  See [`scripts/qwen-text-tower.md`](scripts/qwen-text-tower.md).
- **Losses** — `L_SSL` (`losses/dino.py`), `L_SigLIP` (`losses/siglip.py`).

## Pipeline mapping to Azure ML

```
prepare_data ─▶ stage1_ssl_pretrain (ViT_ℓ, L_SSL) ─▶ stage2_siglip_align (ViT_ℓ+ViT_g ↔ text, L_SigLIP) ─▶ candidate model
                                                                                                                    │
                                        evaluate + gate (held-out shard, threshold vs. best model) ◀───────────────┘
                                                                                                                    │
                                                                    register blessed model ─▶ managed online endpoint ─▶ notebook invoke
```

| Paper element | This scaffold | Azure production doc |
|---|---|---|
| De-ID CT volumes + reports | `prepare_data` component (synthetic here) | [`docs/04`](../../../docs/04-data-platform-design.md) Gold zone |
| Stage 1 DINOv3 SSL | `stage1_ssl_pretrain` Azure ML job (GPU) | [`docs/05`](../../../docs/05-model-training.md), [DEC-06b](../../../decisions/DEC-06b-compute-gpu.md) |
| Stage 2 SigLIP align | `stage2_siglip_align` Azure ML job (GPU) | [`docs/05`](../../../docs/05-model-training.md) |
| Model registry + lineage | `azureml/pipeline.yml` outputs → registry | [`docs/05`](../../../docs/05-model-training.md) |
| Evaluation gate before hosting | `azureml/evaluate-pipeline.yml` → `evaluate.py` (metric vs. threshold) | [`docs/13`](../../../docs/13-evaluation-practices.md) |
| Register + host blessed model | pipeline registers `ct-report-siglip`; managed online endpoint | [`docs/13`](../../../docs/13-evaluation-practices.md) |
| Serve / invoke | `azureml/endpoint/` + `notebooks/invoke_endpoint.ipynb` | [`docs/13`](../../../docs/13-evaluation-practices.md) |

## Layout

```
ct-report-pretraining/
├── pyproject.toml                   # uv-managed project: ctreport package + deps + extras
├── uv.lock                          # pinned, reproducible environment
├── .python-version                  # pins Python 3.11 for uv
├── azureml/
│   ├── pipeline.yml                 # 2-stage AML v2 training pipeline
│   ├── evaluate-pipeline.yml        # evaluate + gate + register blessed model
│   ├── datastore.yml                # credential-less (identity-based) Gold datastore
│   ├── components/
│   │   ├── prepare_data.yml
│   │   ├── stage1_ssl_pretrain.yml
│   │   ├── stage2_siglip_align.yml
│   │   └── evaluate.yml             # evaluate + gate command component
│   ├── model-assets/
│   │   └── qwen3-0.6b.yml           # offline Qwen text-tower model asset (mounted on governed compute)
│   └── endpoint/
│       ├── endpoint.yml             # managed online endpoint (token auth, no keys)
│       └── deployment.yml           # blue deployment (score.py + inference env)
├── environment/
│   ├── conda.yaml                   # AML training environment
│   └── inference.yaml               # online endpoint environment (+ inference server)
├── infra/                           # governance-compliant IaC (Bicep) — see ADMIN-SETUP.md
│   ├── main.bicep                   # RG-scoped: storage + KV + App Insights + workspace + RBAC
│   ├── deploy.sh
│   └── modules/{storage,observability,mlworkspace,roles}.bicep
├── src/
│   ├── prepare_data.py              # component entry: build/verify dataset
│   ├── stage1_ssl_pretrain.py       # component entry: Stage 1 SSL
│   ├── stage2_siglip_align.py       # component entry: Stage 2 SigLIP
│   ├── evaluate.py                  # component entry: evaluate + gate + bless
│   ├── score.py                     # managed online endpoint scoring script
│   └── ctreport/                    # the model package (paper components)
│       ├── text/tokenizer.py        # paired Qwen / fallback tokenizers (report text → ids)
│       └── serving.py               # shared model-reload used by eval + scoring
├── notebooks/invoke_endpoint.ipynb  # register → gate → deploy → invoke (images, images+text)
├── notebooks/inspect_dicom.ipynb    # data inspection: view DICOM from local disk + Azure Blob
├── tests/smoke_test.py              # tiny end-to-end run on CPU
├── ADMIN-SETUP.md                   # admin: provision the workspace via IaC
└── scripts/
    ├── preflight.md                 # subscription pre-flight checks
    ├── submit.md                    # how to submit training to Azure ML
    ├── qwen-text-tower.md           # enable the real Qwen3-0.6B tower (local + offline Azure)
    ├── download_qwen.py             # fetch Qwen3-0.6B for offline registration
    └── deploy.md                    # evaluate, gate, register, deploy, invoke
```

## Run locally (CPU smoke test)

This project is a [`uv`](https://docs.astral.sh/uv/)-managed package — `pyproject.toml` +
`uv.lock` pin the environment (Python 3.11), and `ctreport` installs as an importable package:

```bash
cd prototype/model-training/ct-report-pretraining
uv sync                                   # core env: ctreport + torch (CPU) + numpy
uv run python tests/smoke_test.py         # builds synthetic data, runs both stages
```

The smoke test uses deliberately tiny dimensions (see `ctreport.config.smoke_config`)
so both stages complete in seconds on CPU, and it pins the dependency-free **fallback** text
tower. To train/serve with the **real Qwen3-0.6B tower** add `transformers`/`peft` via
`uv sync --extra text` (with `text_tower: auto`/`qwen`); on governed Azure ML compute that can't
reach HuggingFace, mount Qwen as a model asset — see
[`scripts/qwen-text-tower.md`](scripts/qwen-text-tower.md).

### Notebook kernel (aligned env)

The [`notebooks/invoke_endpoint.ipynb`](notebooks/invoke_endpoint.ipynb) walkthrough needs the
Azure ML SDK v2 + Jupyter on top of the core env. Sync the `notebook` extra and register the
kernel once, then select **CT-Report (uv)** in Jupyter/VS Code:

```bash
uv sync --extra notebook
uv run python -m ipykernel install --user \
  --name ct-report-pretraining --display-name "CT-Report (uv)"
```

Because the kernel is this project's venv, the notebook's `ctreport`/`torch` imports match the
training/eval/serve code exactly. The AML jobs/endpoint use their own conda envs
(`environment/conda.yaml`, `environment/inference.yaml`) — keep those aligned with `pyproject.toml`.

## Submit to Azure ML

See [`scripts/submit.md`](scripts/submit.md). In short:

```bash
az ml job create -f azureml/pipeline.yml \
  --set settings.default_compute=azureml:gpu-cluster
```

Swap `ctreport.config.smoke_config` for `default_config` (full-size dims) via the
`--config-preset default` job arg, and point `prepare_data` at the real de-identified
Gold dataset instead of the synthetic generator.

## Evaluate, gate, register, and host

After training, the **evaluate pipeline** ([`azureml/evaluate-pipeline.yml`](azureml/evaluate-pipeline.yml))
scores a candidate model on a **held-out** synthetic shard (distinct seed) and gates it against a
threshold that stands in for the **best current model**. On pass it **registers the blessed
model** `ct-report-siglip` (v2 `custom_model` asset) via a named pipeline output; on fail the job
errors and nothing is registered or deployed.

```bash
# register a training run's output as a candidate, then run the gate:
az ml model create --name ct-report-siglip-candidate --type custom_model \
  --path azureml://jobs/<stage2_job>/outputs/model
az ml job create -f azureml/evaluate-pipeline.yml
```

The blessed model is then hosted on a **managed online endpoint** (token auth, no keys):
[`azureml/endpoint/`](azureml/endpoint/) + the inference environment
[`environment/inference.yaml`](environment/inference.yaml). The scoring script
[`src/score.py`](src/score.py) returns the zero-shot finding classification and the shared-space
image embedding; pass a `report` text string to also get the image↔report cosine.

End-to-end CD (register → gate → deploy → invoke with images and images+text) is walked through in
**[`notebooks/invoke_endpoint.ipynb`](notebooks/invoke_endpoint.ipynb)**; CLI steps are in
**[`scripts/deploy.md`](scripts/deploy.md)**.

> [!WARNING]
> **Prototype shortcuts — do not copy verbatim into production.**
>
> - **Permissive gate.** The gate threshold ships at **`0.20`** (barely above the 0.25 random-chance
>   floor for 4 classes) *on purpose*, so a 3-step smoke model still passes and the register→deploy
>   happy-path demonstrates. **This is not a real quality bar.** In production the threshold must be
>   the **incumbent champion model's score** on the *same* held-out eval set, and the eval set must
>   be a real, versioned, de-identified holdout — not the synthetic generator. Shipping this default
>   unchanged would promote essentially any model.
> - **Non-standard CD handoff.** The pipeline only **gates + registers**. The actual endpoint
>   create/deploy/traffic step is done **interactively** from the notebook / `deploy.md` using your
>   personal Owner credentials. That is convenient for a prototype but is **not** how CD should work:
>   there is no approval gate, no environment promotion, no automated rollback, and it depends on a
>   human with broad rights. See the note below on standard MLOps.

### Not modeled here: standard MLOps promotion (out of scope for the prototype)

This scaffold demonstrates the *shapes* of train / eval / register / host, but deliberately stops
short of a production MLOps promotion loop. A real system would embed these steps in governed
automation (see [`docs/13`](../../../docs/13-evaluation-practices.md) and
[`docs/06`](../../../docs/06-model-serving.md)):

- **CI/CD-driven, not laptop-driven.** Train → eval → register → deploy run as **pipeline jobs /
  GitHub Actions or Azure DevOps** triggered by code/data changes, executing under a **workload
  identity / service principal** with least-privilege RBAC — never a human's Owner token.
- **Champion/challenger promotion.** The gate compares the challenger against the **current
  registered champion** on a shared holdout; promotion updates a registry **stage/alias** (e.g.
  `@champion`) rather than a hard-coded model version in the deployment YAML.
- **Progressive delivery + rollback.** New versions roll out **blue/green or canary** (traffic
  split, health/latency probes, auto-rollback on regression) instead of `--all-traffic` in one shot.
- **Approvals + audit.** Human/automated **approval gates**, signed lineage, and monitoring
  (data/serving drift, ground-truth feedback) close the loop back to retraining.

These are intentionally **out of scope** for the prototype and are called out so nobody mistakes the
scaffold's shortcuts for a deployable MLOps pattern.

## Provision on Azure ML (governance-compliant IaC)

To actually run this on Azure ML in a governed subscription, an admin provisions
the workspace + dependencies into **one existing resource group** with
[`infra/main.bicep`](infra/main.bicep) — identity-based, **no key-based auth**:

- Storage with `allowSharedKeyAccess=false`, Key Vault with RBAC authorization, App Insights
  linked to an **existing** Log Analytics workspace.
- AML workspace + a CPU cluster, each with a managed identity, and the data-plane RBAC
  (Storage Blob Data / AML Data Scientist / KV Secrets Officer) that Owner/Contributor does *not*
  grant.

Full walkthrough: **[`ADMIN-SETUP.md`](ADMIN-SETUP.md)**. Run
[`scripts/preflight.md`](scripts/preflight.md) against the subscription first.
