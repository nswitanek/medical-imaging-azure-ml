# Enabling the real Qwen3-0.6B text tower

The text tower (Fig. 2 "Text" box) has two interchangeable, *pinned* implementations,
selected by `text_tower` in `ModelConfig` and recorded into the saved `config.json`:

| `text_tower` | Tokenizer | Encoder | When |
| --- | --- | --- | --- |
| `fallback` | controlled-vocabulary (dependency-free) | tiny 2-layer transformer | CPU smoke test, no network |
| `qwen` | `Qwen/Qwen3-0.6B` BPE (`transformers`) | Qwen3-0.6B (frozen) + LoRA (`peft`) | real runs |
| `auto` (default) | Qwen if it loads, else fallback | — | convenient default |

> The tokenizer is **paired** with the encoder — Qwen token ids only make sense to Qwen's
> embedding table — so the two are always built together and `text_tower` is written into the
> model's `config.json`. Eval and serving rebuild the **identical** tower from that field.

## Local (already works)

`transformers`/`peft` live in the `text` extra, and this box can reach HuggingFace:

```bash
uv sync --extra text            # or: uv sync --extra notebook --extra text
uv run --extra text python tests/smoke_test.py    # still uses the fallback tower (offline)
```

With the `text` extra installed and `text_tower="auto"` (the default preset), Stage 2 will
resolve to the **Qwen** tower automatically and pin `text_tower: qwen` into the saved model.

## Azure ML on governed compute (offline)

Governed training/inference compute usually **can't reach `huggingface.co`**. Two knobs make
the Qwen tower load with zero network egress:

- `CTREPORT_QWEN_DIR` — absolute path to a local copy of Qwen3-0.6B (tokenizer + config +
  weights). `resolve_text_model_ref()` returns it in preference to the hub id.
- `HF_HUB_OFFLINE=1` — hard-fail instead of silently trying the network.

### 1. Download Qwen where you *can* reach HF (e.g. your dev box)

```bash
uv run --extra text python scripts/download_qwen.py --out ./qwen3-0.6b
```

### 2. Register it as a v2 model asset (mountable, no key-based auth)

```bash
az ml model create -f azureml/model-assets/qwen3-0.6b.yml
# override the local path if you downloaded elsewhere:
#   az ml model create -f azureml/model-assets/qwen3-0.6b.yml --set path=/data/qwen3-0.6b
```

### 3. Mount it into the Stage-2 (and evaluate) jobs

Add a `custom_model` input and export the two env vars *in the command* (Linux compute runs
the command in a shell, so `VAR=... python ...` works and the mount path is known at runtime):

```yaml
# azureml/components/stage2_siglip_align.yml  (delta)
inputs:
  # ...existing inputs...
  text_model:
    type: custom_model
    optional: true
command: >-
  CTREPORT_QWEN_DIR=${{inputs.text_model}} HF_HUB_OFFLINE=1
  python stage2_siglip_align.py
  --data-dir ${{inputs.dataset}}
  --stage1-ckpt ${{inputs.vit_local}}
  --output-dir ${{outputs.model}}
  --config-preset ${{inputs.config_preset}}
  $[[--max-steps ${{inputs.max_steps}}]]
  --freeze-local ${{inputs.freeze_local}}
```

Then wire the asset into the pipeline job and force the Qwen tower via the `default` preset
(which ships `text_tower: auto`; with the mount present it resolves to `qwen`). To make it a
hard requirement, set `text_tower: qwen` in the config used by `prepare_data` so a missing
mount fails the job instead of silently falling back.

```yaml
# azureml/pipeline.yml  (delta) — pass the registered asset to the stage-2 step
jobs:
  stage2:
    inputs:
      text_model:
        type: custom_model
        path: azureml:qwen3-0_6b-text-tower:1
```

### 4. Serving (managed online endpoint)

At serving time `score.py` → `load_model` reconstructs the Qwen tower, so the deployment also
needs the tokenizer/config offline. Point it at the same mounted asset:

```yaml
# azureml/endpoint/deployment.yml  (delta)
environment_variables:
  CTREPORT_QWEN_DIR: /var/qwen3-0.6b   # path where you stage the Qwen files in the image/mount
  HF_HUB_OFFLINE: "1"
```

Requests send report **text** (not token ids); the endpoint tokenizes with the Qwen tokenizer:

```json
{"input_data": {"instances": [
  {"volume": [/* floats */], "shape": [128,128,128], "report": "liver cyst hypodensity noted"}
]}}
```

## Trade-offs & production notes (prototype shortcuts)

- **Checkpoint size.** For reload simplicity the scaffold saves the *full* `state_dict`,
  including the frozen Qwen base (~0.6B params ≈ 2.4 GB fp32 per model version). A production
  system saves only the **LoRA adapter + trainable heads** and reconstructs the frozen base
  from the mounted Qwen asset (`AutoModel.from_config`, no weight download), keeping registered
  versions small. Out of scope here.
- **dtype.** Qwen3 ships bf16 weights; the scaffold loads them as **fp32** so the shared-space
  projection + SigLIP math match the vision tower on CPU/GPU. On GPU you may prefer bf16/fp16
  with an autocast context and a matching projection dtype.
- **Tower parity.** Train, eval, and serve **must** use the same `text_tower`. It's pinned in
  `config.json`; loading a `qwen`-trained model with only the fallback deps (or vice-versa)
  fails `load_state_dict(strict=True)` by design — do not "fix" it by switching towers.
- **Governed egress.** Never rely on `text_tower: auto` reaching HF from governed compute — it
  will quietly fall back to the stand-in tower. Use the mounted asset + `HF_HUB_OFFLINE=1`.
