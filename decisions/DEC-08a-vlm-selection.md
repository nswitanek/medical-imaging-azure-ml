# DEC-08a — Vision-Language Model Selection

- **Status:** 🟥 Open
- **Capability:** Frontier VLM(s) for reasoning, report drafting, structuring
- **Related docs:** [`docs/08`](../docs/08-ai-foundry-model-strategy.md), [`docs/18`](../docs/18-readiness-model-access-quota.md)

## Context

Select the frontier VLM(s) to reason over imaging outputs, draft structured findings, and orchestrate. Company intends to evaluate **advanced OpenAI and Anthropic** models. Access + quota are gating ([`docs/18`](../docs/18-readiness-model-access-quota.md)).

## Options

### Option A — OpenAI (GPT-4o / GPT-5-class) via Foundry
**Advantages**
- Strong multimodal + structured-output + tool-calling; broad tooling/ecosystem.
- Mature on Azure; PTU option for latency.

**Disadvantages**
- Cost at scale; capability varies by exact model/version.

### Option B — Anthropic Claude (via Foundry Models)
**Advantages**
- Strong reasoning, long context, careful/structured outputs; good instruction-following.
- Adds vendor diversity.

**Disadvantages**
- Availability/quota by region; feature parity varies by version.

### Option C — Multi-model (both, routed by task) — evaluate and choose per step
**Advantages**
- Best-of-breed per task; resilience to provider limits/outages; negotiating leverage.
- Matches Company's stated intent to evaluate both.

**Disadvantages**
- More integration + eval + governance overhead; two data-handling reviews.

## Comparison

| Criterion | A: OpenAI | B: Anthropic | C: Multi-model |
|---|---|---|---|
| Multimodal reasoning | Strong | Strong | Best-of-breed |
| Vendor diversity | No | No | Yes |
| Integration overhead | Low | Low | Higher |
| Quota risk mitigation | Single | Single | Diversified |
| Governance reviews | 1 | 1 | 2 |

## Recommendation

**Evaluate both (Option C mindset) during the prototype**, then converge to the best primary with the other as fallback. Foundry's unified catalog makes multi-model comparison straightforward. **Gate:** confirm access + quota for the exact models first.

## Decision

- **Models to evaluate:** _TBD_
- **Primary / fallback:** _TBD_
- **Rationale:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
