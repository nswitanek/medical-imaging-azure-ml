# 04 — Data Platform Design

## Purpose

A governed lakehouse that holds de-identified imaging metadata, clinical text, features, labels, and evaluation datasets — the substrate for training/fine-tuning, evaluation, and analytics.

## Zones (medallion)

| Zone | Contents | PHI status |
|---|---|---|
| **Bronze (raw/landing)** | Raw ingested metadata, HL7/FHIR payloads, report text | May contain PHI → locked zone |
| **Silver (curated)** | Cleaned, conformed, **de-identified** studies, reports, features | De-identified |
| **Gold (serving)** | Curated datasets, labels, evaluation sets, feature views | De-identified |

Pixel imaging data itself stays in the **DICOM service / object storage**; the lakehouse holds **metadata, references, and derived features** (avoid duplicating large binaries).

## Core capabilities needed

- Lakehouse tables (Delta/Parquet) with ACID + time travel for reproducible datasets.
- **Feature store** for model features.
- **Labeling / ground-truth** management and versioned evaluation datasets.
- **Catalog, lineage, and classification** (Microsoft Purview) across the estate.
- **Data contracts** between ingestion and consumers.

See **[DEC-04](../decisions/DEC-04-data-platform.md)** for the platform options (Microsoft Fabric vs. Azure Databricks vs. Snowflake) with advantages/disadvantages. **Company already operates Snowflake**, which can serve as the governed de-identified data/feature layer via **external stages over ADLS** and **Snowpark**, pairing with Azure ML or Databricks for heavy GPU training.

## Dataset versioning & reproducibility

- Every training/eval run pins an **immutable dataset version** (snapshot/commit).
- Link dataset version → model version → evaluation run (traceability into [`docs/08`](./08-ai-foundry-model-strategy.md) and [`docs/11`](./11-governance-compliance.md)).

## Governance integration

- Sensitivity labels + classification propagate from ingestion.
- Access via Entra groups mapped to zone-level RBAC; row/column controls where needed.
- Lineage from source → feature → model → prediction supports audit and incident response.

## Interfaces

- **To AI platform:** curated datasets + feature views consumed by Azure ML / Foundry training & evaluation.
- **From ingestion:** event-driven writes from the de-ID stage.
- **To analytics/BI:** de-identified gold datasets for dashboards (operational + clinical quality).
