# 15 — Two-Day Rapid Prototype Scope

## Purpose

Validate the **riskiest, highest-uncertainty** integration points hands-on — not the well-understood ones. Prove the architecture's spine end-to-end on a thin slice with de-identified data.

## Prioritization principle

> Prototype what we're unsure about. Skip what we already know works.

| Candidate area | Uncertainty | Prototype priority |
|---|---|---|
| DICOM ingestion (AHDS DICOM, change feed) | Medium | **P1** — prove the spine |
| PHI de-ID (tags + pixel + text) | High | **P1** — biggest risk/leverage |
| Model composition (domain + custom + VLM) | High | **P1** — core value hypothesis |
| Orchestration (agentic flow) | Medium | **P2** |
| Automated eval pipeline | Medium | **P2** |
| Scalable deployment pattern | Low–Med | **P2** (pattern, not full scale) |
| API exposure via APIM | Low | **P3** (thin stub) |

*(Confirm/adjust priorities live with the team — see [DEC-15](../decisions/DEC-15-prototype-priorities.md).)*

## Proposed thin-slice goal

> Ingest a de-identified hip/knee study → run Company's custom model + a domain vision model → have a VLM draft a structured finding → run an automated eval → return a FHIR-shaped result — all within a private, governed Azure environment.

## Day 1

- [ ] Stand up landing environment (resource group, VNet, Key Vault, identities, Log Analytics).
- [ ] Provision AHDS (DICOM + FHIR); load a **de-identified** sample study set.
- [ ] Wire change feed → processing job.
- [ ] Stand up de-ID stage; validate on sample (tags + pixel + one report).
- [ ] Confirm model access/quota (OpenAI + Anthropic) — [`docs/18`](./18-readiness-model-access-quota.md).

## Day 2

- [ ] Deploy Company custom model to an endpoint; call a domain vision model from the catalog.
- [ ] Thin orchestration: compose domain + custom + VLM into a structured finding.
- [ ] Run an automated evaluation on a small labeled set; capture metrics.
- [ ] Expose one API endpoint (stub) returning a FHIR-shaped result.
- [ ] Capture observability traces end-to-end.
- [ ] Readout: what worked, what's risky, what production needs.

## Success criteria for the prototype

- End-to-end path runs on **de-identified** data in a **private** environment.
- De-ID validated on the sample (no residual PHI in promoted data).
- Model composition produces a plausible structured finding.
- At least one automated eval metric captured.
- Traces/telemetry visible for the full flow.

## Explicitly out of scope for the two days

- Production scale/perf tuning.
- Full multi-tenant SaaS.
- Complete clinical validation.
- Exhaustive de-ID coverage across all modalities (prove the mechanism, not completeness).

## Reference starting points

To accelerate Day 2, borrow deployment + calling code from Microsoft's [healthcareai-examples](https://github.com/microsoft/healthcareai-examples) (research samples, not clinical-ready):

- Deploy a catalog model to an endpoint: [MedImageInsight](https://aka.ms/healthcare-ai-examples-mi2-deploy), [MedImageParse](https://aka.ms/healthcare-ai-examples-mip-deploy), [CXRReportGen](https://aka.ms/healthcare-ai-examples-cxr-deploy).
- Compose modalities end-to-end: [rad-path survival demo](https://github.com/microsoft/healthcareai-examples/blob/main/azureml/advanced_demos/radpath/rad_path_survival_demo.ipynb) (MI2 + Providence-GigaPath).
- Thin agent orchestration: [classification agent](https://github.com/microsoft/healthcareai-examples/blob/main/azureml/medimageinsight/agent-classification-example.ipynb) · [MedImageInsight MCP plugin](https://github.com/microsoft/healthcareai-examples/tree/main/agentic/medimageinsight).
- The repo deploys via **`azd`** and AzureML — the same landing pattern this prototype targets. GPU quota per model: [`docs/18`](./18-readiness-model-access-quota.md).

## Inputs required before day 1

- De-identified sample dataset (or approval + mechanism to de-ID a small set).
- Company custom model artifact + how to run it.
- Confirmed Azure subscription/landing zone + model quota.
- Named owners for each checklist item.
