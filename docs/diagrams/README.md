# Diagrams (diagram-as-code)

Every architecture diagram in this repo is generated from a single **YAML spec** — no hand-drawn
images, no ASCII art, no mermaid. Each `*.yaml` spec renders **four** artifacts via
[`../../tools/render_diagrams.py`](../../tools/render_diagrams.py):

| Artifact | Purpose |
|---|---|
| `<name>.conceptual.graphviz.png` | Vendor-neutral conceptual view (boxes + zones) |
| `<name>.azure.graphviz.png` | Same topology with official **Azure / Microsoft icons** |
| `<name>.conceptual.drawio` | Editable [draw.io](https://drawio.com) starter (conceptual) |
| `<name>.azure.drawio` | Editable draw.io starter (Azure icons) |

Because the conceptual and Azure views come from the same nodes/edges with the same left-to-right
layout, they can never drift apart.

## Specs

| Spec | Embedded in |
|---|---|
| `reference-architecture.yaml` | [`01-reference-architecture.md`](../01-reference-architecture.md) |
| `ingestion.yaml` | [`02-data-ingestion-pacs-dicom-multimodal.md`](../02-data-ingestion-pacs-dicom-multimodal.md) |
| `model-training.yaml` | [`05-model-training.md`](../05-model-training.md) |
| `inference-flow.yaml` | [`06-model-hosting-orchestration.md`](../06-model-hosting-orchestration.md) |
| `payload-routing.yaml` | [`07-payload-processing-backend-alignment.md`](../07-payload-processing-backend-alignment.md) |
| `model-strategy.yaml` | [`08-ai-foundry-model-strategy.md`](../08-ai-foundry-model-strategy.md) |
| `api-exposure.yaml` | [`09-api-exposure.md`](../09-api-exposure.md) |
| `model-lifecycle.yaml` | [`11-governance-compliance.md`](../11-governance-compliance.md) |
| `ahds-dataflow.yaml` | [`12-health-data-services-fhir-dicom.md`](../12-health-data-services-fhir-dicom.md) |
| `evaluation-gate.yaml` | [`13-evaluation-practices.md`](../13-evaluation-practices.md) |
| `agentic.yaml` | [`14-agentic-orchestration.md`](../14-agentic-orchestration.md) |
| `roadmap.yaml` | [`16-roadmap-prod-commercialization.md`](../16-roadmap-prod-commercialization.md) |

## Rendering

```bash
# From the repo root. Install deps once:
pip install -r tools/requirements.txt

# Render every spec:
python tools/render_diagrams.py --glob "docs/diagrams/*.yaml"

# Or a single spec:
python tools/render_diagrams.py docs/diagrams/reference-architecture.yaml
```

Requires **Graphviz** (`dot`) on the system. On Windows it is typically installed at
`C:\Program Files\Graphviz\bin` — add it to `PATH` before rendering
(`winget install Graphviz.Graphviz`). On macOS `brew install graphviz`; on Linux
`sudo apt-get install graphviz`.

Edit the `.yaml` spec (never the PNGs) and re-render so the conceptual + Azure views stay in sync.
Open the `.drawio` files in [app.diagrams.net](https://app.diagrams.net) for manual polish; re-run
with `--no-drawio` afterwards so your hand edits aren't overwritten.
