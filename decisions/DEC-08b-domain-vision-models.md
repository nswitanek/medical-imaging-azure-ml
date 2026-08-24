# DEC-08b — Domain-Specific Vision Models

- **Status:** 🟥 Open
- **Capability:** Medical vision models for embeddings/detection feeding the pipeline
- **Related docs:** [`docs/08`](../docs/08-ai-foundry-model-strategy.md)

## Context

Decide whether/how to use domain-specific medical vision models alongside Company's custom hip/knee model — for embeddings, retrieval, candidate detection, or report generation.

## Options

### Option A — Use Foundry healthcare foundation models (catalog)
*(e.g., MedImageInsight for embeddings/classification, CXRReportGen, medical segmentation models)*
**Advantages**
- Pre-trained on medical imagery; strong embeddings/retrieval out of the box.
- No training cost; fast to trial; managed on Foundry.
- Complements the custom model (features/similarity/priors).
- **Runnable reference code exists** — Microsoft's [healthcareai-examples](https://github.com/microsoft/healthcareai-examples) has deploy + usage notebooks for [MedImageInsight](https://aka.ms/healthcare-ai-examples-mi2-deploy), [MedImageParse](https://aka.ms/healthcare-ai-examples-mip-deploy) (segmentation), and [CXRReportGen](https://aka.ms/healthcare-ai-examples-cxr-deploy), plus [zero-shot classification](https://github.com/microsoft/healthcareai-examples/blob/main/azureml/medimageinsight/zero-shot-classification.ipynb) to validate fit before committing.

**Disadvantages**
- May not be specialized to hip/knee orthopedics; needs evaluation.
- Model availability/licensing terms to confirm.

### Option B — Rely solely on Company's custom model + a frontier VLM
**Advantages**
- Simpler stack; fewer models to govern/evaluate.
- Custom model already validated for the target task.

**Disadvantages**
- Misses strong medical embeddings/retrieval and pretraining benefits.
- More burden on the VLM for perception it isn't ideal at.

### Option C — Fine-tune / adapt a domain model on Company data
**Advantages**
- Best possible task fit; leverages de-identified labels.
- **Reference workflows exist** — [adapter training](https://github.com/microsoft/healthcareai-examples/blob/main/azureml/medimageinsight/adapter-training.ipynb) (lightweight) and a full [MedImageInsight fine-tuning pipeline](https://github.com/microsoft/healthcareai-examples/blob/main/azureml/medimageinsight/finetuning/mi2-finetuning.ipynb) on AzureML.

**Disadvantages**
- Training + governance + maintenance cost; slower; needs data volume + MLOps.

## Comparison

| Criterion | A: Catalog models | B: Custom + VLM only | C: Fine-tune |
|---|---|---|---|
| Task fit | Good (verify) | Validated (narrow) | Best |
| Effort | Low | Lowest | High |
| Governance load | Medium | Low | High |
| Retrieval/embeddings | Strong | Weak | Strong |

## Recommendation

**Trial Option A during the prototype** (embeddings/retrieval + candidate detection) alongside Company's custom model; consider **Option C (fine-tune)** later only if evaluation shows a clear gap and data supports it.

## Decision

- **Chosen approach:** _TBD_
- **Specific models:** _TBD_
- **Rationale:** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
