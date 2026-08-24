# 00 — Goals, Scope, and Success Criteria

## Session goal

Produce a **concrete, production-ready direction** for taking Company's validated hip-and-knee imaging AI prototype into a **governed, scalable Azure platform**. The day is focused primarily on **whiteboarding, architecture, operationalization, observability, and decisions** — the output is a go-forward architecture with the constituent pieces needed for a partner Statement of Work (SOW).

## In scope

- Reference production architecture (ingestion → data platform → model hosting/orchestration → API → monitoring/governance).
- Microsoft Foundry model strategy (vision-language, domain-specific vision, custom models, evaluation, agentic orchestration).
- Healthcare governance & compliance (PHI, secure AI patterns, model lifecycle, observability, Azure Health Data Services).
- A prioritized two-day rapid-prototype scope.
- A roadmap to production and commercialization, including a potential SaaS path.

## Out of scope (for this session)

- Final clinical validation / regulatory submission (FDA/CE) — noted as a dependency, not solved here.
- Detailed contract terms and pricing negotiation (captured as inputs to the SOW).
- Building the full production system (this session defines the plan and decisions).

## Participants and roles

| Role | Party | Responsibility |
|---|---|---|
| Customer / clinical owner | **Company** | Requirements, clinical validation, data, funding, physician network. |
| Cloud platform | **Microsoft** | Azure architecture guidance, Foundry model access, funding programs, quota. |
| Delivery partner | **Partner / Consultant** | Implementation ownership, SOW execution, rapid prototype build. |

## Success criteria (checklist)

- [ ] Reference architecture agreed and diagrammed.
- [ ] Each open decision in [`/decisions`](../decisions) has a recorded decision, owner, and date.
- [ ] AI platform + model strategy validated for Microsoft Foundry.
- [ ] Governance & compliance approach documented (PHI, auditability, lifecycle).
- [ ] Two-day prototype scope prioritized with owners.
- [ ] Roadmap to production + commercialization drafted.
- [ ] Model access & quota readiness confirmed (OpenAI + Anthropic).

## Guiding principles

1. **PHI-safe by default** — de-identify early, minimize PHI blast radius, private networking.
2. **Decisions over discussion** — every option gets an owner and a recorded choice.
3. **Prototype what's risky** — validate the uncertain integration points hands-on, not the well-trodden ones.
4. **Design for scale and SaaS** — multi-tenant-ready patterns even if v1 is single-tenant.
5. **Observability and evaluation are first-class** — not bolted on later.
