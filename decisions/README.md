# Decision Records

Where multiple Azure options exist for a desired capability, each record lists the options with **advantages and disadvantages**, a **recommendation**, and a **Decision** block for the development team to record their choice, owner, and date.

## How to use

1. Review the options table and the pros/cons for each option.
2. Discuss as a team.
3. Fill in the **Decision** block at the bottom of the record (choice, rationale, owner, date).
4. Roll the decisions into the partner SOW.

## Status legend

- 🟥 **Open** — not yet decided
- 🟨 **Leaning** — recommendation noted, awaiting confirmation
- 🟩 **Decided** — recorded with owner + date

## Index

| ID | Decision | Capability | Status |
|---|---|---|---|
| [DEC-02](./DEC-02-dicom-ingestion.md) | DICOM store & ingestion | Imaging ingestion | 🟥 Open |
| [DEC-03](./DEC-03-phi-deidentification.md) | PHI detection & de-identification | PHI control | 🟥 Open |
| [DEC-04](./DEC-04-data-platform.md) | Data platform / lakehouse | Data platform | 🟥 Open |
| [DEC-05](./DEC-05-model-training.md) | Model training approach & platform | Model training | 🟥 Open |
| [DEC-06a](./DEC-06a-model-hosting.md) | Custom-model hosting | Model hosting | 🟥 Open |
| [DEC-06b](./DEC-06b-compute-gpu.md) | Compute / GPU strategy | Compute | 🟥 Open |
| [DEC-07](./DEC-07-backend-alignment.md) | Backend alignment & multi-tenant compute pooling | Backend / multi-tenancy | 🟥 Open |
| [DEC-08a](./DEC-08a-vlm-selection.md) | Vision-language model selection | Model strategy | 🟥 Open |
| [DEC-08b](./DEC-08b-domain-vision-models.md) | Domain-specific vision models | Model strategy | 🟥 Open |
| [DEC-09](./DEC-09-api-exposure.md) | API exposure / gateway | API | 🟥 Open |
| [DEC-10](./DEC-10-observability-stack.md) | Observability stack | Observability | 🟥 Open |
| [DEC-14](./DEC-14-orchestration-framework.md) | Orchestration framework | Agentic orchestration | 🟥 Open |
| [DEC-15](./DEC-15-prototype-priorities.md) | Two-day prototype priorities | Prototype scope | 🟥 Open |

See [`_TEMPLATE.md`](./_TEMPLATE.md) to add a new decision.
