# DEC-05 — Model Training Approach & Platform

- **Status:** 🟥 Open
- **Capability:** Training/fine-tuning models on de-identified DICOM images + metadata + text
- **Related docs:** [`docs/05`](../docs/05-model-training.md), [`docs/04`](../docs/04-data-platform-design.md), [`docs/08`](../docs/08-ai-foundry-model-strategy.md)

## Context

We need repeatable model training that learns from de-identified imaging **pixels**, **metadata**, and **report text** ([`docs/05`](../docs/05-model-training.md)), sourced from the governed lakehouse Gold zone ([`docs/04`](../docs/04-data-platform-design.md)). Two coupled choices: **(1)** the modeling approach — adapt existing medical foundation models vs. build from scratch — and **(2)** the platform that runs training and owns tracking/registry/lineage. Constraints: PHI governance, reproducibility and audit, limited labeled data, GPU cost, and reuse of Company's existing Azure ML / Databricks / Snowflake estate. Microsoft's **healthcareai-examples** provides reference fine-tuning and adapter notebooks (research samples, not clinically validated).

## Options

### Option A — Fine-tune / adapt foundation models on Azure ML
**Advantages**
- Start from imaging foundation models (**MedImageInsight**, **MedImageParse**, **CXRReportGen**) — strong cold-start with limited data.
- Adapter/LoRA/linear-probe training is cheap and fast; modest GPU footprint.
- Azure ML gives native experiment tracking (MLflow), model registry, lineage, and clean handoff to hosting ([`docs/06`](../docs/06-model-hosting-orchestration.md)) and evaluation ([`docs/13`](../docs/13-evaluation-practices.md)).
- Reference notebooks (`mi2-finetuning.ipynb`, `adapter-training.ipynb`) shorten ramp.

**Disadvantages**
- Ties the approach to available foundation models; novel modalities may lack a good backbone.
- Still requires GPU capacity/quota planning (DEC-06b).

### Option B — Train custom models from scratch (Azure ML / Databricks)
**Advantages**
- Full control of architecture; fits tasks with no suitable foundation model and ample data.
- Databricks option reuses existing Spark/feature pipelines for large-scale data prep.

**Disadvantages**
- Highest data, compute, and time cost; largest governance/validation burden.
- Multi-GPU/distributed training is complex to operate and tune.
- Slowest time-to-value; rarely justified for a two-day prototype.

### Option C — Managed Foundry fine-tuning
**Advantages**
- Lowest-ops managed fine-tuning for supported catalog models; minimal infra.
- Integrated with the Foundry model catalog and evaluation tooling.

**Disadvantages**
- Limited to models/methods the managed service supports; less control over custom multimodal fusion of image + metadata + text.
- Feature engineering and complex data joins still happen upstream in the lakehouse.

## Comparison

| Criterion | A: Fine-tune/adapt (Azure ML) | B: From scratch | C: Managed Foundry fine-tune |
|---|---|---|---|
| Cost | Low–Medium | High | Low |
| Data needed | Low–Medium | High | Low–Medium |
| Operational burden | Medium | High | Low |
| Control / flexibility | High | Highest | Limited |
| Multimodal fusion fit | Strong | Strong | Limited |
| Time-to-value | Fast | Slow | Fastest |
| Reproducibility / lineage | Native (MLflow/registry) | Native | Managed |

## Recommendation

- **Default to Option A** — fine-tune/adapt medical foundation models on **Azure ML**, using adapter/LoRA training first and full fine-tuning where warranted. It gives the best accuracy-per-effort on limited labeled data, native tracking/registry/lineage, and clean handoffs to evaluation and hosting.
- Use **Option C (managed Foundry fine-tuning)** when a supported catalog model meets the need and lowest ops is preferred.
- Reserve **Option B (from scratch)** for tasks with no suitable foundation model and sufficient data/compute justification.
- Databricks/Snowflake ([`DEC-04`](./DEC-04-data-platform.md)) may prepare features; centralize heavy GPU training on Azure ML for consistent lineage.

## Decision

- **Chosen option:** _TBD_
- **Rationale:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
