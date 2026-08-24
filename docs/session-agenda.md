# Whiteboard Session Agenda

A suggested flow for the architecture/decisions day. Adjust timings to the room. Primary focus: **whiteboarding, architecture, operationalization, observability, and decisions.**

## Objectives for the day

- Agree the reference architecture ([`docs/01`](../docs/01-reference-architecture.md)).
- Make and **record** each open decision ([`/decisions`](../decisions)).
- Lock the two-day prototype scope ([DEC-15](../decisions/DEC-15-prototype-priorities.md)).
- Draft the roadmap + SOW inputs ([`docs/16`](../docs/16-roadmap-prod-commercialization.md)).

## Suggested flow

| Block | Topic | Output |
|---|---|---|
| 1 | Goals, success statement, guardrails ([`docs/00`](../docs/00-goals-and-success.md)) | Shared framing |
| 2 | Whiteboard reference architecture ([`docs/01`](../docs/01-reference-architecture.md)) | Agreed diagram |
| 3 | Ingestion + AHDS (DICOM/FHIR) — **DEC-02** | Decision recorded |
| 4 | PHI de-ID + residency — **DEC-03** | Decision recorded |
| 5 | Data platform — **DEC-04** | Decision recorded |
| 6 | Model strategy: VLM + domain + custom — **DEC-08a, DEC-08b** | Decisions recorded |
| 7 | Hosting, compute, orchestration — **DEC-06a, DEC-06b, DEC-14** | Decisions recorded |
| 8 | API, observability, governance — **DEC-09, DEC-10**, [`docs/11`](../docs/11-governance-compliance.md) | Decisions recorded |
| 9 | Prototype scope — **DEC-15** | Scope + owners |
| 10 | Roadmap, cost, funding, SaaS ([`docs/16`](../docs/16-roadmap-prod-commercialization.md), [`docs/17`](../docs/17-saas-path.md)) | Roadmap + SOW inputs |
| 11 | Readiness: model access/quota ([`docs/18`](../docs/18-readiness-model-access-quota.md)) | Action owners |

## Decision-capture discipline

For every decision: **choice → rationale → owner → date**, written into the record before moving on. A decision without an owner is not a decision.

## Parking lot

Track anything that needs follow-up outside the room (regulatory, contracts, data access).
