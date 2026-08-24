# DEC-10 — Observability Stack

- **Status:** 🟥 Open
- **Capability:** Platform + model + clinical observability and audit
- **Related docs:** [`docs/10`](../docs/10-monitoring-observability.md)

## Context

Need telemetry across platform, model/AI, and clinical-quality planes, plus compliance-grade audit. Decide whether Azure-native suffices or third-party tooling augments it.

## Options

### Option A — Azure-native (Azure Monitor + App Insights + Foundry observability/evals + Content Safety)
**Advantages**
- Integrated, single-vendor; least glue; native to the stack and governance.
- Foundry gives model/agent tracing + evaluations; Monitor covers platform + audit.
- Lower cost/complexity; compliance-friendly (data stays in Azure).

**Disadvantages**
- Some specialized LLM-eval/observability features less deep than dedicated vendors.

### Option B — Azure-native + third-party LLM observability/eval tool
**Advantages**
- Best-in-class LLM tracing/eval/prompt-management features.
- May accelerate advanced eval workflows.

**Disadvantages**
- Added cost + integration; **PHI/data-egress review** required (data leaving Azure boundary).
- Another vendor to govern under BAA/compliance.

### Option C — Third-party APM as primary
**Advantages**
- Mature APM if Company already standardizes on one.

**Disadvantages**
- Duplicates Azure Monitor; data-residency/compliance friction; higher cost.

## Comparison

| Criterion | A: Azure-native | B: Native + LLM tool | C: 3rd-party APM |
|---|---|---|---|
| Integration effort | Low | Medium | Medium |
| LLM-eval depth | Good | Best | Varies |
| Compliance/residency | Strong | Needs review | Needs review |
| Cost | Low | Medium | Higher |

## Recommendation

**Option A (Azure-native)** as the baseline — strongest compliance fit and least glue. Add a **third-party LLM eval/observability tool (Option B)** only if a specific capability gap justifies the data-egress/compliance review.

## Decision

- **Chosen option:** _TBD_
- **Rationale:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
