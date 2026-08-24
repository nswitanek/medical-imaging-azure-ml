# DEC-07 — Backend Alignment & Multi-Tenant Compute Pooling

- **Status:** 🟥 Open
- **Capability:** Aligning real-time/batch × multimodal payloads to right-sized, shared backend compute across health-system tenants
- **Related docs:** [`docs/07`](../docs/07-payload-processing-backend-alignment.md), [`docs/06`](../docs/06-model-hosting-orchestration.md), [`docs/17`](../docs/17-saas-path.md), [`docs/18`](../docs/18-readiness-model-access-quota.md)

## Context

Company processes DICOM studies in **real time** and in **batch**, with payloads that are image-only or image + text (± tabular), and composes a **mix** of managed frontier VLM calls (OpenAI/Anthropic via Foundry) and self-hosted trained/fine-tuned OSS vision, tabular, and LLM models on Azure ML. It serves **multiple health-system customers** and wants to share backend compute for utilization and cost while preserving tenant isolation, protecting clinician-in-loop latency, and being able to provision and right-size predictably. The core question: **how is backend compute organized across tenants and across the real-time/batch split?**

## Options

### Option A — Shared pooled backend with workload separation (multi-tenant)
One set of per-model deployments shared across tenants, with capacity **pooled by workload class** (RT GPU, RT CPU, Batch GPU, Batch CPU, Foundry capacity) rather than by customer, per-tenant quotas/rate-limits/concurrency limits at APIM, and tenant identity flowing through orchestration.

**Advantages**
- Highest utilization / lowest unit cost; one estate to operate and patch.
- Real-time vs. batch pool separation protects interactive latency from batch load.
- Elastic to new tenants without new infrastructure; fits the SaaS path ([`docs/17`](../docs/17-saas-path.md)).

**Disadvantages**
- Requires disciplined isolation (identity, data partitioning, quotas) and noisy-neighbor controls.
- Shared-fate: a platform incident affects all tenants.
- Cost attribution needs per-tenant metering/tagging.

### Option B — Dedicated per-tenant backend
Each health system gets its own endpoints/pools (and possibly subscription).

**Advantages**
- Strongest isolation and blast-radius containment; simplest per-tenant cost attribution.
- Per-tenant customization/compliance where mandated.

**Disadvantages**
- Poor utilization (idle GPUs per tenant); highest cost and ops burden.
- Scales badly as tenants grow; slow onboarding; more quota to hold everywhere.

### Option C — Hybrid: shared batch, isolated real-time (or shared by default, dedicated on request)
Share the cost-sensitive **batch** pool across tenants; give **real-time** clinical paths dedicated or reserved capacity per tenant (or per large tenant).

**Advantages**
- Batch economics of pooling + latency/isolation guarantees where they matter most.
- A clear upgrade path: start shared, peel off dedicated real-time for large/regulated tenants.

**Disadvantages**
- Two operating models to manage; more complex capacity planning.
- Real-time isolation reintroduces some idle cost.

## Comparison

| Criterion | A: Shared pooled | B: Per-tenant | C: Hybrid |
|---|---|---|---|
| Utilization / cost | Best | Worst | Good |
| Isolation / blast radius | Requires controls | Strongest | Strong where it matters |
| Latency protection (clinical) | Pool separation | Inherent | Inherent (dedicated RT) |
| Onboarding new tenants | Fast | Slow | Fast (shared default) |
| Ops burden | Low (one estate) | High | Medium |
| Cost attribution | Metering/tagging | Native | Mixed |
| SaaS-readiness | High | Low | High |

## Recommendation

**Option C (hybrid), defaulting to shared pooled (Option A) with strict workload separation.** Pool capacity **by workload class, not by customer** — shared **batch** pools on spot/scale-to-zero for cost, and shared **real-time** pools (RT GPU / RT CPU) with warm minimums, kept **separate from batch** so a large batch job can't starve clinician-in-loop latency. Allocate tenants via **logical quotas, priorities, and concurrency limits** at APIM plus per-tenant metering, and offer **dedicated/reserved real-time capacity** only for large or regulatory-constrained tenants. This maximizes utilization while protecting clinical latency and containing risk where it matters. Right-size per **[DEC-06b](./DEC-06b-compute-gpu.md)** and [`docs/18`](../docs/18-readiness-model-access-quota.md).

## Decision

- **Tenancy model (batch / real-time):** _TBD_
- **Isolation & noisy-neighbor controls:** _TBD_
- **Dedicated-capacity threshold (which tenants):** _TBD_
- **Cost allocation / metering approach:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
