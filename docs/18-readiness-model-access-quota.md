# 18 — Readiness: Model Access & Quota

> **Immediate readiness item:** confirm access and quota for the advanced OpenAI and Anthropic models Company intends to evaluate. This is a gating dependency for the prototype.

## Why this is gating

If the frontier VLMs aren't accessible with sufficient quota **before** the two-day prototype, the model-composition validation (the core hypothesis) can't run. Resolve this in Phase 0.

## Checklist

- [ ] Identify the **exact models** to evaluate (OpenAI GPT-4o / GPT-5-class; Anthropic Claude family) and versions.
- [ ] Confirm **regional availability** of each model in the target Azure region(s).
- [ ] Confirm **access** is enabled on the subscription (some models require registration/approval).
- [ ] Check **quota** (TPM/RPM) is sufficient for prototype + MVP; request increases early.
- [ ] Decide **consumption vs. provisioned throughput (PTU)** for latency-sensitive clinical paths.
- [ ] Confirm **data-handling / no-training** commitments for each model provider on Foundry.
- [ ] Confirm GPU quota for self-hosted domain/custom models ([DEC-06b](../decisions/DEC-06b-compute-gpu.md)).

## Consumption vs. Provisioned Throughput

| | Consumption (pay-per-token) | Provisioned (PTU) |
|---|---|---|
| Cost | Pay per use; great for spiky/dev | Reserved capacity; predictable |
| Latency | Variable under load | Consistent, reserved |
| Best for | Prototype, research, bursty | Clinical, latency-sensitive prod |
| Commitment | None | Reserved (term) |

Prototype on **consumption**; plan **PTUs** for production clinical paths where latency matters.

## Quota planning inputs

- Expected studies/day × tokens per study (VLM steps) → TPM needs.
- Peak concurrency (clinician-in-loop) → RPM + latency target.
- GPU: model size × concurrency × latency target → SKU + instance count ([DEC-06b](../decisions/DEC-06b-compute-gpu.md)).
- Aggregate peak across **all tenants** (shared backend) plus headroom — see multi-tenant provisioning & right-sizing in [`docs/07`](./07-payload-processing-backend-alignment.md).

## Reference: healthcare model GPU quota

Microsoft's [healthcareai-examples](https://github.com/microsoft/healthcareai-examples) documents the **minimum GPU quota** to deploy each catalog model — useful concrete numbers for the quota request (request 2–3× the minimum; requesting quota is free):

| Model | VM family | Instance type | Min cores |
|---|---|---|---|
| MedImageInsight | NCasT4_v3 | `Standard_NC4as_T4_v3` | 8 |
| MedImageParse | NCadsH100_v5 | `Standard_NC40ads_H100_v5` | 40 |
| CXRReportGen | NCadsH100_v5 | `Standard_NC40ads_H100_v5` | 40 |
| Prov-GigaPath | NCv3 | `Standard_NC6s_v3` | 6 |
| GPT-4o / GPT-4.1 (optional) | GlobalStandard | — | 50K–100K TPM |

Healthcare imaging models need **GPU compute cores**; GPT models use **TPM** capacity on Azure AI Services. See [DEC-06b](../decisions/DEC-06b-compute-gpu.md) for SKU right-sizing.

## Actions & owners

| Action | Owner |
|---|---|
| List exact models + regions | Company + Microsoft |
| Enable access / approvals | Microsoft |
| Request quota / PTU | Microsoft + Partner |
| Validate in a smoke test before Day 1 | Partner |

## Related decisions

- [DEC-08a — VLM selection](../decisions/DEC-08a-vlm-selection.md)
- [DEC-06b — Compute / GPU](../decisions/DEC-06b-compute-gpu.md)
