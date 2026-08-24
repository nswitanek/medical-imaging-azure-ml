# 17 — SaaS Path

## Vision

Scale Company's validated imaging AI from **its own physician network** to a **multi-tenant SaaS** serving other healthcare providers — turning a validated capability into a product.

## Multi-tenancy model (decision)

| Model | Description | Pros | Cons |
|---|---|---|---|
| **Silo (per-tenant stack)** | Dedicated resources per customer | Strongest isolation; simplest compliance story | Highest cost/ops; slower onboarding |
| **Pooled (shared, logical isolation)** | Shared services, tenant scoping in data/API | Best economics; fast onboarding | Requires rigorous isolation controls |
| **Hybrid** | Shared control plane; isolated PHI data plane per tenant | Balances isolation + economics | More design complexity |

For PHI/healthcare, a **hybrid** (shared control plane, isolated PHI data plane) is a common landing point. Capture the choice with Company/Partner.

## What SaaS adds on top of the platform

- **Tenant onboarding** — automated provisioning, connectivity (per-tenant DICOM/FHIR endpoints), config.
- **Isolation** — data, identity, network, and model scoping per tenant; per-tenant CMK optional.
- **Metering & billing** — usage capture (studies processed, tokens, compute) → billing; Azure Marketplace transactable offer is an option.
- **Per-tenant governance** — each customer's BAA, data residency, retention, and audit.
- **Configurability** — per-tenant thresholds, workflows, and model variants.
- **Support & SLA tiers.**

## Compliance at SaaS scale

- Move from HIPAA-only toward **HITRUST / SOC 2** attestations expected by provider customers.
- Per-tenant data residency/region selection.
- Standards-based interop (FHIR/DICOM) lowers onboarding friction for new providers.

## Go-to-market considerations (for Company + Partner)

- **Azure Marketplace** listing / transactable SaaS offer.
- Co-sell with Microsoft; partner-led implementation & support.
- Pricing model grounded in the **per-study / per-tenant cost model** ([`docs/16`](./16-roadmap-prod-commercialization.md)).

## Sequencing

Don't build full SaaS first. Get the **single-tenant production MVP** right for Company's network, design **multi-tenant-ready** patterns from the start (tenant claim, scoping, metering hooks), then flip on multi-tenancy in Phase 4.
