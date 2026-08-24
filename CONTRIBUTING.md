# Contributing / Working Agreement

This repo captures architecture and decisions for operationalizing Company's medical-imaging AI on Azure.

## Conventions

- **Docs** (`/docs`) = narrative guidance. Keep concise and current.
- **Decisions** (`/decisions`) = one record per decision. Use [`_TEMPLATE.md`](./decisions/_TEMPLATE.md). Always fill the **Decision** block (choice, rationale, owner, date) once agreed, and update status in [`decisions/README.md`](./decisions/README.md).
- **Prototype** (`/prototype`) = the hands-on build plan.

## Placeholders

Replace **Company**, **Partner/Consultant**, and any bracketed placeholders with real names before external distribution.

## PHI & security

- Never commit PHI, real patient data, credentials, connection strings, or secrets.
- Diagrams and examples must use synthetic/de-identified data only.

## Change flow

1. Branch → edit → PR.
2. For decisions, record the outcome in the record + index.
3. Keep the reference architecture and decision index in sync.
