# DEC-02 — DICOM Store & Ingestion

- **Status:** 🟥 Open
- **Capability:** Imaging ingestion & storage
- **Related docs:** [`docs/02`](../docs/02-data-ingestion-pacs-dicom-multimodal.md), [`docs/12`](../docs/12-health-data-services-fhir-dicom.md)

## Context

Company needs to land DICOM imaging from PACS/modalities into Azure, standards-based, PHI-controlled, event-driven, and scalable — feeding de-ID, feature extraction, and inference.

## Options

### Option A — Azure Health Data Services (AHDS) DICOM service
**Advantages**
- Managed, HIPAA-eligible; DICOMweb (STOW/WADO/QIDO) standard.
- Built-in **change feed** for event-driven pipelines.
- **DICOMcast** links imaging to FHIR (ImagingStudy).
- Private Link, Entra RBAC, audit built in; low ops burden.
- Interop lowers SaaS onboarding friction (any DICOM source connects).

**Disadvantages**
- Less low-level control than self-managed.
- Service cost + AHDS learning curve.
- Some advanced/edge DICOM features may need supplementation.

### Option B — Self-managed on Azure Blob Storage (+ open-source DICOM server)
**Advantages**
- Maximum control over storage layout, tiering, cost.
- Can run open-source DICOM servers (e.g., on AKS) tailored to needs.

**Disadvantages**
- You own de-ID, change feed, FHIR linkage, security, patching — significant engineering + compliance burden.
- Slower time-to-value; higher long-term ops cost.
- Reinvents what AHDS provides out of the box.

### Option C — Third-party / partner PACS-in-cloud (ISV on Azure Marketplace)
**Advantages**
- Turnkey enterprise imaging features (viewer, workflow) if Company already uses a vendor.
- Vendor-supported.

**Disadvantages**
- Licensing cost + potential lock-in.
- Integration with Foundry/AI pipeline may be less native.
- Governance/BAA depends on vendor.

## Comparison

| Criterion | A: AHDS DICOM | B: Self-managed | C: Third-party PACS |
|---|---|---|---|
| Cost | Medium | Variable (ops-heavy) | License-driven |
| Operational burden | Low | High | Low–Medium |
| PHI/compliance fit | Strong (managed) | You own it | Vendor-dependent |
| Time-to-value | Fast | Slow | Medium |
| AI pipeline integration | Native | Custom | Varies |
| Scale / SaaS-readiness | Strong | Custom | Vendor-dependent |

## Recommendation

**Option A — AHDS DICOM service**, unless Company has an existing PACS-in-cloud investment that must be reused. It minimizes undifferentiated engineering, carries compliance features, and integrates natively with FHIR and the AI pipeline.

## Decision

- **Chosen option:** _TBD_
- **Rationale:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
