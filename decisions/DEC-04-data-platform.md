# DEC-04 — Data Platform / Lakehouse

- **Status:** 🟥 Open
- **Capability:** Governed lakehouse for de-identified metadata, features, labels, eval datasets
- **Related docs:** [`docs/04`](../docs/04-data-platform-design.md)

## Context

Need a lakehouse for curated, de-identified imaging metadata, clinical text, features, labels, and versioned evaluation datasets — with catalog, lineage, and governance, feeding training/evaluation. **Company already operates Snowflake**, so an option that reuses that estate and skillset is in scope alongside the Azure-native platforms.

## Options

### Option A — Microsoft Fabric
**Advantages**
- Unified SaaS analytics (OneLake, lakehouse, warehouse, BI) — low setup.
- Tight Purview + Power BI integration; good governance story.
- Fast time-to-value; less infra to manage.

**Disadvantages**
- Newer platform; some advanced ML/data-engineering patterns less mature than Databricks.
- Capacity-based cost model needs planning.

### Option B — Azure Databricks
**Advantages**
- Mature lakehouse + Delta; best-in-class data engineering + ML (MLflow, feature store).
- Strong for large-scale training/feature pipelines; flexible.
- Widely adopted; deep ecosystem.

**Disadvantages**
- More to operate/tune; steeper learning curve.
- Cost management requires discipline (clusters).

### Option C — Snowflake (on Azure)
**Advantages**
- **Already in use at Company** — existing skillset, pipelines, and data products reduce ramp and migration risk.
- Mature multi-cloud data platform; strong SQL, separation of elastic compute/storage, and governed data sharing.
- ML/AI via **Snowpark** (Python) and **Snowflake Cortex**; **external stages** over ADLS for imaging metadata/features so large binaries need not be duplicated.
- Runs on Azure and fits the private-network + Entra story via **Azure Private Link** and SSO/SCIM.

**Disadvantages**
- Governance/lineage/BI integrate less natively with **Microsoft Purview** and Power BI than Fabric (connector-based, not first-party).
- Third-party commercial platform: separate contract, credit-based cost model, and another control plane to secure and audit.
- Not the GPU training runtime — heavy, large-scale model training is still offloaded to Azure ML/Databricks; Snowflake serves the data/feature layer.

## Comparison

| Criterion | A: Fabric | B: Databricks | C: Snowflake |
|---|---|---|---|
| Time-to-value | Fast | Medium | Fast (in use) |
| ML/data-eng maturity | Growing | Strong | Strong (SQL/Snowpark) |
| Governance (Purview/BI) | Native | Good | Connector-based |
| Ops burden | Low (SaaS) | Medium | Low (SaaS) |
| Strategic direction | Forward | Forward | Forward |
| Cost model | Capacity | Cluster | Credits |
| Existing Company adoption | — | — | **Yes** |

## Recommendation

- **Snowflake** where Company's existing Snowflake estate, skills, and data products should be reused — it can serve as the governed de-identified data/feature layer, pairing with Azure ML or Databricks for heavy GPU training when needed.
- **Fabric** if Company values a unified, low-ops SaaS analytics stack with strong Microsoft-native governance/BI.
- **Databricks** if heavy, large-scale ML/data-engineering and an existing Databricks skillset dominate.

All three are valid. Because Company already runs Snowflake, it is the pragmatic default for the data/feature layer unless a unified Microsoft-native governance/BI stack (Fabric) or Spark-centric ML engineering (Databricks) is the priority.

## Decision

- **Chosen option:** _TBD_
- **Rationale:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
