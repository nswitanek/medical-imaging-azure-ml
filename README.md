# Medical Imaging AI — Azure Production Architecture

A working repository to guide **Company**, **Microsoft**, and **Partner/Consultant** through the topics required to take Company's validated hip-and-knee imaging AI prototype into a governed, scalable Azure platform.

> **Placeholders:** This repo uses generic placeholders — **Company** (the healthcare customer), **Partner/Consultant** (the delivery partner), and **Microsoft**. Replace them with real names before external distribution.

---

## The goal

Deliver a concrete, production-ready direction for operationalizing Company's validated medical-imaging AI solution on Azure — not a conceptual discussion, but **captured architectural decisions** ready to feed a partner Statement of Work (SOW).

## The success statement

> Success is aligning Company, Microsoft, and the Consultant on a **documented, secure, and scalable Azure architecture** for operationalizing Company's validated medical-imaging AI solution, making the key **platform and model-strategy decisions**, and defining a **prioritized build plan** for the two-day rapid prototype and the path to production.

## What Company should leave with

1. A **reference production architecture** — PACS/DICOM + multimodal ingestion, PHI detection & de-identification, data platform, model hosting & orchestration, API exposure, monitoring, governance, auditability.
2. A **validated AI platform strategy** for Microsoft Foundry — vision-language models, domain-specific vision models, custom models, evaluation practices, and agentic orchestration.
3. **Healthcare governance & compliance guidance** — PHI handling, secure AI patterns, model lifecycle management, observability, and Azure Health Data Services (FHIR + DICOM).
4. **Key architectural decisions captured** (see [`/decisions`](./decisions)) — the constituent pieces of a partner SOW.
5. A **prioritized two-day rapid-prototype scope** — what to validate hands-on.
6. A **roadmap from prototype to production and commercialization** — ownership, partner execution, capacity/cost, funding alignment, and a potential SaaS path.

## Immediate readiness item

Confirm **access and quota** for the advanced OpenAI and Anthropic models Company intends to evaluate. See [`docs/18-readiness-model-access-quota.md`](./docs/18-readiness-model-access-quota.md).

---

## How this repo is organized

| Area | Path | Purpose |
|---|---|---|
| **Narrative docs** | [`/docs`](./docs) | Topic-by-topic guidance and reference architecture. |
| **Decision records** | [`/decisions`](./decisions) | Where multiple Azure options exist, each captures options with **advantages / disadvantages**, a recommendation, and a place to record the team's decision. |
| **Prototype plan** | [`/prototype`](./prototype) | The prioritized two-day rapid-prototype scope and checklist. |
| **Diagrams** | [`/docs/diagrams`](./docs/diagrams) | Diagram-as-code YAML specs rendered to conceptual + Azure PNGs (and editable draw.io starters). |

## Reference architecture at a glance

![Medical-Imaging AI reference production architecture — Azure / Microsoft](./docs/diagrams/reference-architecture.azure.graphviz.png)

> Full walkthrough in [`docs/01-reference-architecture.md`](./docs/01-reference-architecture.md). Diagrams are generated from [`docs/diagrams`](./docs/diagrams) — edit the YAML and re-render.

## How to use it in the session

1. Walk the **docs** in order to build shared understanding.
2. For each **decision record**, review the options table, discuss, and record the decision + owner + date at the bottom.
3. Lock the **prototype scope** and assign owners.
4. Feed captured decisions into the partner **SOW**.

## Decision index

See [`decisions/README.md`](./decisions/README.md) for the full list of open decisions and their status.
