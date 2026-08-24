# DEC-15 — Two-Day Prototype Priorities

- **Status:** 🟥 Open
- **Capability:** Prioritized hands-on validation scope
- **Related docs:** [`docs/15`](../docs/15-two-day-prototype-scope.md)

## Context

Two days is limited. Validate the **riskiest** integration points, not the known-good ones. This record captures what the team agrees to build hands-on.

## Candidate scope (rank/confirm as a team)

| Area | Uncertainty | Proposed priority | In prototype? |
|---|---|---|---|
| DICOM ingestion (AHDS + change feed) | Medium | P1 | _TBD_ |
| PHI de-ID (tags + pixel + text) | High | P1 | _TBD_ |
| Model composition (domain + custom + VLM) | High | P1 | _TBD_ |
| Agentic orchestration | Medium | P2 | _TBD_ |
| Automated eval pipeline | Medium | P2 | _TBD_ |
| Scalable deployment pattern | Low–Med | P2 | _TBD_ |
| API exposure (APIM/stub) | Low | P3 | _TBD_ |

## Trade-off framing

- **Depth vs. breadth:** prove one thin end-to-end slice deeply, or touch more areas shallowly? (Recommend: **thin end-to-end slice**.)
- **De-ID coverage:** prove the mechanism on a sample vs. exhaustive coverage. (Recommend: **mechanism**.)
- **Orchestration:** managed (Foundry Agents) vs. code (Microsoft Agent Framework) for speed. (Recommend: **managed/thin**.)

## Recommended prototype goal

> Ingest a de-identified hip/knee study → custom model + domain model → VLM structured finding → automated eval → FHIR-shaped API result, in a private governed environment, with end-to-end traces.

## Decision

- **Agreed P1 scope:** _TBD_
- **Agreed P2/P3 (stretch):** _TBD_
- **Explicitly excluded:** _TBD_
- **Owners per item:** _TBD_
- **Success criteria:** _TBD_
- **Date:** _TBD_
