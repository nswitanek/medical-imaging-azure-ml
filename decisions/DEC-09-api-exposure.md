# DEC-09 — API Exposure / Gateway

- **Status:** 🟥 Open
- **Capability:** Secure, governed API front door for the imaging-AI capability
- **Related docs:** [`docs/09`](../docs/09-api-exposure.md)

## Context

Expose inference to clinician apps and downstream systems with authN/Z, throttling, versioning, audit, and (eventually) multi-tenant metering.

## Options

### Option A — Azure API Management (APIM) in front of app/inference services
**Advantages**
- Full gateway: authN/Z, rate limiting, quotas, versioning, request/response policies, audit.
- Per-tenant throttling + metering (SaaS-ready).
- Central policy enforcement, content-safety hooks, developer portal.

**Disadvantages**
- Added component + cost; policy learning curve.
- Slight latency hop (usually negligible).

### Option B — Direct App Service / Container Apps ingress (no dedicated gateway)
**Advantages**
- Simpler, fewer moving parts; lower cost for a single consumer.
- Fine for the prototype stub.

**Disadvantages**
- Reimplement throttling/versioning/audit/metering per service.
- Weak fit for multi-tenant SaaS governance.

### Option C — Azure Front Door / App Gateway (WAF) + APIM
**Advantages**
- Adds global routing + WAF for public-facing edges on top of APIM.
- Strong for internet-exposed, multi-region SaaS.

**Disadvantages**
- More components/cost; overkill for internal-only v1.

## Comparison

| Criterion | A: APIM | B: Direct ingress | C: FrontDoor+APIM |
|---|---|---|---|
| Governance features | Strong | Weak | Strong |
| SaaS/metering fit | Strong | Poor | Strong |
| Complexity/cost | Medium | Low | High |
| Public-edge/WAF | Add-on | No | Yes |
| Best for | Production/SaaS | Prototype | Global SaaS |

## Recommendation

- **Prototype:** Option B (direct stub) to move fast.
- **Production / SaaS:** **Option A (APIM)**, adding **Front Door + WAF (Option C)** when exposing publicly across regions.

## Decision

- **Chosen option:** _TBD_
- **Rationale:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
