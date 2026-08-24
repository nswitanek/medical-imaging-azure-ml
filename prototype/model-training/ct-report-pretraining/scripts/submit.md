# Submitting the CT–Report pretraining pipeline to Azure ML

Prereqs: Azure CLI + the ML extension (`az extension add -n ml`), and a workspace you're
logged into (`az login`, `az account set`, `az configure --defaults group=<rg> workspace=<ws>`).

> **Workspace + compute already provisioned?** If an admin ran the IaC in
> [`../ADMIN-SETUP.md`](../ADMIN-SETUP.md), the workspace and a **`cpu-cluster`** (with its own
> managed identity) already exist and step 1 is done — skip to step 2. The manual `az ml compute
> create` below is only for a workspace you stood up by hand.

## 1. Create compute (once, non-IaC only)

```bash
# CPU for smoke validation in the cloud
az ml compute create --name cpu-cluster --type amlcompute --size Standard_DS3_v2 --min-instances 0 --max-instances 2

# GPU for real (paper-scale) training -- see docs/18 for quota
az ml compute create --name gpu-cluster --type amlcompute --size Standard_NC24ads_A100_v4 --min-instances 0 --max-instances 4
```

> Bare `amlcompute` created this way has **no managed identity**, so identity-based data mounts
> fail with `ScriptExecution.StreamAccess.Authentication`. Give it one and grant blob access:
> `az ml compute update -n cpu-cluster --identity-type SystemAssigned`, then assign that MSI
> **Storage Blob Data Contributor** on the data storage account. The IaC path does this for you.

## 2. Smoke run in the cloud (tiny dims, CPU)

```bash
az ml job create -f azureml/pipeline.yml
```

## 3. Real run (paper-scale dims, GPU)

```bash
az ml job create -f azureml/pipeline.yml \
  --set inputs.config_preset=default \
  --set settings.default_compute=azureml:gpu-cluster
```

## 4. Point at real data instead of the synthetic generator

Real de-identified Gold data must be reached through a **credential-less datastore**
([`../azureml/datastore.yml`](../azureml/datastore.yml)) — the storage account has
`allowSharedKeyAccess=false`, so a bare blob URL would never present an identity and the job
would fail auth. Register the datastore once, then reference `azureml://datastores/...` paths:

```bash
# Register the identity-based datastore (fill in the account created by the IaC):
az ml datastore create -f azureml/datastore.yml \
  --set account_name=<storage-account> --set container_name=ct-report-gold

# Submit against it:
az ml job create -f azureml/pipeline.yml \
  --set jobs.stage1_ssl.inputs.dataset='azureml://datastores/ct_report_gold/paths/train' \
  --set jobs.stage2_siglip.inputs.dataset='azureml://datastores/ct_report_gold/paths/train'
```

Or replace the `prepare_data` component body with a lakehouse/feature-view read (docs/04).

## 5. Register the aligned model

Uncomment the `name:`/`type:` block under `stage2_siglip.outputs.model` in
`pipeline.yml` to auto-register, or register the output afterward as the **candidate** the
evaluation gate consumes:

```bash
az ml model create --name ct-report-siglip-candidate --type custom_model \
  --path azureml://jobs/<job-name>/outputs/model
```

The candidate then flows to the **evaluate + gate pipeline** (docs/13), which registers the
blessed `ct-report-siglip` and hosts it on a managed online endpoint — see
[`deploy.md`](deploy.md). It is prototype, not clinically validated.

## Local equivalent (no Azure)

```bash
uv run python src/prepare_data.py       --output-dir .run/data --config-preset smoke
uv run python src/stage1_ssl_pretrain.py --data-dir .run/data --output-dir .run/s1
uv run python src/stage2_siglip_align.py --data-dir .run/data --stage1-ckpt .run/s1 --output-dir .run/s2
```
