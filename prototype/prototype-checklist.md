# Prototype Runbook & Checklist

Operational companion to [`docs/15`](../docs/15-two-day-prototype-scope.md). Use during the two-day build.

## Pre-flight (before Day 1)

- [ ] Azure subscription + landing zone confirmed; contributors have access.
- [ ] Model access + quota confirmed (OpenAI + Anthropic) — smoke test a call. See [`docs/18`](../docs/18-readiness-model-access-quota.md).
- [ ] De-identified sample study set available (or approved de-ID mechanism for a small set).
- [ ] Company custom model artifact + run instructions in hand.
- [ ] Named owners assigned per task ([DEC-15](../decisions/DEC-15-prototype-priorities.md)).
- [ ] Target region(s) selected; AHDS availability confirmed.

## Day 1 — Ingestion + de-ID spine

- [ ] Resource group, VNet, Key Vault, managed identities, Log Analytics.
- [ ] Provision AHDS workspace (DICOM + FHIR).
- [ ] Load de-identified sample DICOM (STOW); verify QIDO/WADO retrieval.
- [ ] Enable change feed; wire to a processing job (Function/Container).
- [ ] Stand up de-ID stage; validate tags + one report + pixel-mask on a high-risk sample.
- [ ] Verify: no residual PHI in promoted (silver) data.

## Day 2 — Model composition + eval + API

- [ ] Deploy Company custom model to an endpoint ([DEC-06a](../decisions/DEC-06a-model-hosting.md)).
- [ ] Call a domain vision model from the Foundry catalog ([DEC-08b](../decisions/DEC-08b-domain-vision-models.md)).
- [ ] Thin orchestration: compose domain + custom + VLM → structured finding ([DEC-14](../decisions/DEC-14-orchestration-framework.md)).
- [ ] Run automated eval on a small labeled set; capture ≥1 metric ([`docs/13`](../docs/13-evaluation-practices.md)).
- [ ] Expose one API endpoint (stub) returning FHIR-shaped result.
- [ ] Confirm end-to-end traces/telemetry visible ([`docs/10`](../docs/10-monitoring-observability.md)).

## Readout (end of Day 2)

- [ ] What worked / what's risky / what production needs.
- [ ] Update each decision record with findings.
- [ ] Draft SOW inputs from validated + open items.

## Definition of done (prototype)

- End-to-end thin slice runs on **de-identified** data in a **private** environment.
- De-ID validated on the sample.
- Model composition yields a plausible structured finding.
- ≥1 automated eval metric captured.
- Full-flow traces visible.

## Optional deep-dive — model training use case

A runnable **Azure ML v2 training scaffold** (two-stage CT–report multimodal pretraining,
CVPR 2026 Fig. 2) lives in
[`model-training/ct-report-pretraining`](./model-training/ct-report-pretraining). It
demonstrates the training substrate from [`docs/05`](../docs/05-model-training.md) — a
pipeline of `prepare_data → Stage 1 SSL (L_SSL) → Stage 2 SigLIP (L_SigLIP)` with a CPU
smoke test on synthetic data. Not on the two-day critical path, but useful when the
training story needs to be shown end-to-end.

To run it on Azure ML in a governed subscription, an admin provisions the workspace with the
identity-based (no key auth) Bicep IaC — see
[`model-training/ct-report-pretraining/ADMIN-SETUP.md`](./model-training/ct-report-pretraining/ADMIN-SETUP.md)
and the subscription
[`preflight`](./model-training/ct-report-pretraining/scripts/preflight.md) checks.
