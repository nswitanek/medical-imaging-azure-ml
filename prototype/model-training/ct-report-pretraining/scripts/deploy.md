# Evaluate → gate → register → deploy → invoke

The CD half of the scaffold: take a trained CT–report model, prove it on held-out data, and (if
it clears the bar) register + host it on a managed online endpoint. Everything below is **Azure ML
SDK/CLI v2** and honors the governed workspace (identity-based, **no key-based auth**).

> [!WARNING]
> **Two deliberate prototype shortcuts you must not carry into production:**
>
> 1. **Permissive gate.** `gate_threshold` defaults to **`0.20`**, just above the 0.25 random-chance
>    floor, so a smoke-trained model passes and the happy-path demonstrates. It is **not** a quality
>    bar. In production, gate against the **current champion's** score on a real, versioned,
>    de-identified holdout.
> 2. **Interactive CD handoff.** The pipeline only **gates + registers**. Creating the endpoint and
>    shifting traffic below is run **by hand with your Owner credentials** — there is no approval
>    gate, no canary, no automated rollback, and no service-principal isolation. A production system
>    embeds these in CI/CD under a least-privilege workload identity (see the "Standard MLOps" note
>    at the bottom and [`../README.md`](../README.md#not-modeled-here-standard-mlops-promotion-out-of-scope-for-the-prototype)).

Prereqs: the workspace is provisioned (see [`../ADMIN-SETUP.md`](../ADMIN-SETUP.md)) and you've run
the training pipeline ([`submit.md`](submit.md)) at least once. Set your CLI defaults:

```bash
az configure --defaults group=EXP-ADO-ADB-RG workspace=ctrp-mlw
```

## 1. Register the candidate model (v2 `custom_model` asset)

The evaluate pipeline takes a **registered** model as input. Register the Stage-2 job's `model`
output as a versioned `custom_model` asset:

```bash
STAGE2_JOB=<stage2_child_run_name>     # from `az ml job list` / the studio
az ml model create \
  --name ct-report-siglip-candidate \
  --type custom_model \
  --path azureml://jobs/$STAGE2_JOB/outputs/model
```

## 2. Run the evaluate + gate pipeline

```bash
az ml job create -f ../azureml/evaluate-pipeline.yml \
  --set inputs.candidate_model.path=azureml:ct-report-siglip-candidate@latest
```

What it does ([`evaluate.py`](../src/evaluate.py)):

- `prepare_eval` builds a **held-out** synthetic shard with a distinct seed (`eval_seed=999`).
- `evaluate` loads the candidate, computes `zero_shot_accuracy`, `image_text_recall_at_1`, and
  `mean_pos_cosine`, and compares the **gate metric** against **`gate_threshold`** (stand-in for
  the best current model — permissive in the scaffold; set to the champion's score in production).
- **Pass** → the blessed model is emitted on the pipeline's named `blessed_model` output, which AML
  **registers as `ct-report-siglip`** using the workspace identity (no extra compute-MSI RBAC).
- **Fail** → the job exits non-zero, the pipeline fails, and nothing is registered or deployed.

Confirm the blessed model:

```bash
az ml model show --name ct-report-siglip --label latest
```

## 3. Deploy to the managed online endpoint

Token-based auth (no static keys) per governance. The first environment image build takes
~15–25 min.

```bash
az ml online-endpoint create -f ../azureml/endpoint/endpoint.yml
az ml online-deployment create -f ../azureml/endpoint/deployment.yml --all-traffic
```

`deployment.yml` ships `src/` via `code_configuration` so the scoring script's `from ctreport…`
imports resolve alongside the weights-only model asset, and uses
[`environment/inference.yaml`](../environment/inference.yaml) (adds `azureml-inference-server-http`).

## 4. Invoke

```bash
az ml online-endpoint invoke --name ct-report-endpoint --request-file sample-request.json
```

A request is `{"input_data": {"instances": [{"volume": [...], "shape": [D,H,W],
"report": "liver cyst hypodensity noted"}]}}` (`report` optional). The response returns
`predicted_finding`, per-class `scores`, an `image_embedding_preview`, and (when `report` is
present) `image_report_cosine`. The endpoint tokenizes the report with the model's pinned text
tower — for a `qwen`-trained model the inference env needs `transformers`/`peft` + the Qwen
tokenizer offline (see [`qwen-text-tower.md`](qwen-text-tower.md)).

The **[`../notebooks/invoke_endpoint.ipynb`](../notebooks/invoke_endpoint.ipynb)** notebook does all
of the above through the Python SDK and builds sample requests (images, and images+reports) using
the `ctreport` helpers so payloads match training.

## Notes / gotchas

- **Text tower (Qwen vs fallback):** the model rebuilds its text encoder with
  `build_text_encoder`. Governed compute usually can't reach HuggingFace, so the dependency-free
  fallback tower is used consistently at train/eval/serve time. Keep the training and inference
  environments aligned — a mismatch changes `state_dict` keys and breaks `load_state_dict`.
- **Instance SKU:** `Standard_DS3_v2` (CPU) is fine for the smoke-dimension model; size up for
  `default_config`.
- **Cleanup:** `az ml online-endpoint delete --name ct-report-endpoint --yes` to stop endpoint cost.
- **Restore CLI defaults** afterward if you share the subscription:
  `az configure --defaults workspace=aivp-mlw`.

## Standard MLOps promotion — out of scope for this prototype

The steps above are **manual and single-shot**. A production system embeds train / eval / register /
deploy in governed automation instead (see [`../../../docs/13-evaluation-practices.md`](../../../docs/13-evaluation-practices.md)
and [`../../../docs/06-model-serving.md`](../../../docs/06-model-serving.md)). What this scaffold
intentionally does **not** implement:

- **Pipeline/CI-driven promotion** under a **service principal / workload identity** (least
  privilege) triggered by code or data changes — not a human running `az` with Owner rights.
- **Champion/challenger** comparison against the current registered champion, with promotion via a
  registry **stage/alias** (`@champion`) rather than a hard-coded `model:` version in the deployment.
- **Progressive delivery**: blue/green or **canary** traffic split with health probes and
  **automated rollback**, instead of `--all-traffic` in one step.
- **Approval gates, signed lineage, and monitoring** (data/serving drift + ground-truth feedback)
  feeding back into retraining.

Treat this file as a *walkthrough of the moving parts*, not a CD blueprint.
