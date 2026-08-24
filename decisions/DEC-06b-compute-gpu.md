# DEC-06b — Compute / GPU Strategy

- **Status:** 🟥 Open
- **Capability:** GPU compute for self-hosted models; throughput mode for VLMs
- **Related docs:** [`docs/06`](../docs/06-model-hosting-orchestration.md), [`docs/18`](../docs/18-readiness-model-access-quota.md)

## Context

Self-hosted domain/custom models need GPUs sized for latency and concurrency. Frontier VLMs need a throughput mode (consumption vs. provisioned). Cost and quota are gating.

## Sub-decision 1 — GPU SKU class (self-hosted models)

### Option A — Smaller/older GPUs (e.g., T4-class)
**Advantages**: Lowest cost; fine for lighter inference; broad availability.
**Disadvantages**: May not meet latency for larger models/high concurrency.

### Option B — Mid/high inference GPUs (e.g., A10 / A100-class)
**Advantages**: Strong inference throughput; headroom for larger models.
**Disadvantages**: Higher cost; quota constraints in some regions.

### Option C — Latest-gen GPUs (e.g., H100-class)
**Advantages**: Best performance for large models/high load.
**Disadvantages**: Highest cost; scarce quota; likely overkill for prototype.

> Right-size to the **actual model + latency + concurrency**. Start small for the prototype; benchmark before committing to production SKUs.

> **Reference SKUs (Microsoft [healthcareai-examples](https://github.com/microsoft/healthcareai-examples)):** the catalog healthcare models publish minimum deploy quotas — MedImageInsight on **`Standard_NC4as_T4_v3`** (T4, 8 cores min), MedImageParse & CXRReportGen on **`Standard_NC40ads_H100_v5`** (H100, 40 cores each), Providence-GigaPath on **`Standard_NC6s_v3`** (6 cores). Concrete anchors for the quota request — see [`docs/18`](../docs/18-readiness-model-access-quota.md).

## Sub-decision 2 — Provisioning mode

| Mode | Advantages | Disadvantages | Best for |
|---|---|---|---|
| **On-demand / autoscale** | Pay for what you use; scale with load | Cold starts; variable cost | Variable clinical load |
| **Reserved / committed** | Lower unit cost; guaranteed capacity | Commitment; risk of under-use | Steady baseline load |
| **Spot** | Cheapest | Can be evicted | Batch/research, fault-tolerant |
| **Scale-to-zero (serverless)** | No idle cost | Cold-start latency | Spiky/dev/research |

## Sub-decision 3 — VLM throughput (Foundry)

| Mode | Advantages | Disadvantages |
|---|---|---|
| **Consumption (per-token)** | No commitment; great for prototype | Variable latency under load |
| **Provisioned Throughput (PTU)** | Reserved, consistent latency | Reserved cost/commitment |

## Recommendation

- **Prototype:** smallest GPU that runs the models + **consumption** VLM + scale-to-zero where possible.
- **Production:** benchmark, then right-size GPUs; **reserved** for steady load, **spot** for batch/research; **PTUs** for latency-sensitive clinical VLM paths.
- Request quota early ([`docs/18`](../docs/18-readiness-model-access-quota.md)).

## Decision

- **GPU SKU (prototype / prod):** _TBD_
- **Provisioning mode:** _TBD_
- **VLM throughput mode:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
