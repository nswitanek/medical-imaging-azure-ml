# DEC-06a — Custom-Model Hosting

- **Status:** 🟥 Open
- **Capability:** Hosting Company's custom models + self-hosted domain models
- **Related docs:** [`docs/06`](../docs/06-model-hosting-orchestration.md)

## Context

Company's validated hip/knee model (and possibly self-hosted domain vision models) needs a serving platform with versioning, autoscaling, safe rollout, and GPU support. (Frontier VLMs are consumed via Foundry — see [DEC-08a](./DEC-08a-vlm-selection.md).)

> **Reference:** Microsoft's [healthcareai-examples](https://github.com/microsoft/healthcareai-examples) deploys catalog models as **AzureML managed online endpoints** (via `azd`), a concrete template for the managed-endpoint option below — see the [MedImageInsight](https://aka.ms/healthcare-ai-examples-mi2-deploy), [MedImageParse](https://aka.ms/healthcare-ai-examples-mip-deploy), and [CXRReportGen](https://aka.ms/healthcare-ai-examples-cxr-deploy) deployment notebooks.

## Options

### Option A — Azure Machine Learning managed online endpoints
**Advantages**
- Purpose-built for model serving: versioning, blue/green, traffic split, autoscale.
- Native model registry, lineage, and MLOps integration.
- GPU support; managed infra — fast path for custom models.

**Disadvantages**
- Less control than raw Kubernetes for complex multi-container topologies.
- Within the Azure ML paradigm.

### Option B — Azure Kubernetes Service (AKS)
**Advantages**
- Maximum control; complex multi-model / multi-container orchestration.
- Mature GPU scheduling, spot nodes, fine-grained networking.
- Portable (K8s standard).

**Disadvantages**
- Highest operational burden (cluster ops, upgrades, security).
- Slower time-to-value; needs platform expertise.

### Option C — Azure Container Apps (ACA)
**Advantages**
- Serverless containers, **scale-to-zero**, simpler than AKS.
- Good for spiky/research inference; low ops.
- GPU support available for container workloads.

**Disadvantages**
- Less control/ecosystem than AKS for very complex topologies.
- Fewer built-in ML-serving features than AML endpoints.

## Comparison

| Criterion | A: AML endpoints | B: AKS | C: Container Apps |
|---|---|---|---|
| ML-serving features | Strong | DIY | Basic |
| Control | Medium | High | Medium |
| Ops burden | Low | High | Low |
| Scale-to-zero | Limited | Custom | Yes |
| Time-to-value | Fast | Slow | Fast |
| Best for | Custom models, MLOps | Complex/large-scale | Spiky/serverless |

## Recommendation

**Option A (AML managed online endpoints)** as the default for Company's custom models — fastest safe path with built-in MLOps. Use **AKS** only if orchestration complexity/scale demands it; **Container Apps** for spiky research/serverless inference.

Regardless of the serving choice, **register models to a shared Azure ML registry** (not just workspace-local) so both Azure ML and Foundry can reference the same versioned artifact. Hub-based Foundry projects share the workspace registry natively; standalone Foundry projects reference it through the registry. This keeps hosting, evaluation, and lineage consistent across both surfaces — see [`docs/06`](../docs/06-model-hosting-orchestration.md) and [`docs/13`](../docs/13-evaluation-practices.md).

## Decision

- **Chosen option:** _TBD_
- **Rationale:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
