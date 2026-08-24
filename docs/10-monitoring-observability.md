# 10 — Monitoring & Observability

Observability is a **first-class** design goal for this session, not an afterthought. Three telemetry planes: platform, model/AI, and clinical-quality.

## 1. Platform / infrastructure telemetry
- **Azure Monitor + Log Analytics** — metrics, logs, alerts across all resources.
- **Application Insights** — distributed tracing across API → orchestration → model calls.
- Diagnostic settings enabled on **every** resource; centralized workspace.
- Health/availability, latency, error rate, saturation (the "golden signals") per service.

## 2. Model / AI observability
- **Microsoft Foundry tracing & observability** — token usage, latency, tool calls, agent steps.
- **Evaluation telemetry** — quality scores over time (see [`docs/13`](./13-evaluation-practices.md)).
- **Content safety** signals — flagged generations, jailbreak attempts.
- **Data & model drift** — input distribution shift, performance decay vs. baseline.
- Per-request lineage: study → model version → prompt/version → output → reviewer action.

## 3. Clinical-quality & operational KPIs
- Turnaround time, throughput, human-override rate, agreement with radiologist ground truth.
- Dashboards for clinical leadership (de-identified).

## Alerting & SLOs

| Signal | Example SLO / alert |
|---|---|
| API availability | 99.9% monthly; alert on error-rate burn |
| Inference latency | p95 within agreed target; alert on breach |
| Model quality | Eval score below threshold → block promotion / page |
| Drift | Input drift > threshold → investigate |
| Safety | Any high-severity content-safety hit → notify |
| Quota | Token/PTU utilization > 80% → capacity review |

## Audit trail (compliance-grade)

- **Immutable, retained** logs of: data access, de-ID operations, re-ID access (privileged), model predictions, and human decisions.
- Sufficient to answer "who saw what PHI, which model produced this result, and who signed off" — see [`docs/11`](./11-governance-compliance.md).

## Decision to capture

- **[DEC-10](../decisions/DEC-10-observability-stack.md)** — observability stack composition (Azure-native vs. augmenting with third-party APM/eval tooling).

## Operational readiness

- Runbooks for common failures (ingestion backlog, endpoint down, quota exhaustion).
- On-call + escalation defined with the partner in the SOW.
- Synthetic (de-identified) probes for end-to-end health.
