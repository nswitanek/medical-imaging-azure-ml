# DEC-03 — PHI Detection & De-identification

- **Status:** 🟥 Open
- **Capability:** PHI control across DICOM tags, pixel data, and free text
- **Related docs:** [`docs/03`](../docs/03-phi-detection-deidentification.md)

## Context

De-ID is the highest-leverage control. Must cover **DICOM tags**, **burned-in pixel PHI**, and **free text**, with a defensible standard (Safe Harbor / Expert Determination), optional re-ID linkage, and a residency decision (where de-ID runs).

## Options (may be combined per surface)

### Option A — Azure Health Data Services de-ID / anonymization (config-driven)
**Advantages**
- Native to AHDS; rule-based DICOM (PS3.15 profiles) + FHIR anonymization.
- Date-shift, redact, surrogate; integrated with the imaging/clinical store.
- Managed, compliance-aligned.

**Disadvantages**
- Config/tuning effort; pixel (burned-in) PHI needs a complementary approach.
- Less flexible than fully custom logic for unusual cases.

### Option B — Azure AI Language — PHI/PII detection (for text)
**Advantages**
- Purpose-built entity detection for PHI in free text (reports/notes).
- Fast to integrate; tunable redaction/surrogates.

**Disadvantages**
- Text only — not DICOM tags or pixels.
- Needs validation on Company's report style; recall must be measured.

### Option C — Pixel de-ID: OCR + region masking (Vision / Document Intelligence + custom)
**Advantages**
- Addresses burned-in PHI that tag redaction misses (critical for some modalities).
- Combines OCR detection with masking; can add human-in-loop review.

**Disadvantages**
- Custom build + validation; higher effort.
- Requires QA to avoid masking clinically relevant pixels.

### Option D — Fully custom de-ID pipeline
**Advantages**
- Maximum control and tunability across all surfaces.

**Disadvantages**
- Highest build/maintenance/compliance burden; you own correctness.

### Option E — Presidio (open-source, spans text + structured + pixels)
*[Presidio](https://github.com/data-privacy-stack/presidio) ([docs](https://presidio.dataprivacystack.org/)) — analyzer/anonymizer for text, presidio-structured for tags, and Image Redactor with a `DicomImageRedactorEngine` for pixel PHI.*
**Advantages**
- **One toolkit across all three surfaces** (text, structured/tags, and burned-in pixels).
- Extensible custom recognizers (NER + regex + rules + checksum); portable (Python/PySpark/Docker/K8s); free/OSS.
- Image redactor can use **Azure Document Intelligence** OCR (with `DefaultAzureCredential`) — complements Option C rather than replacing it.

**Disadvantages**
- Self-hosted: you own deployment, tuning, validation, and compliance defensibility.
- Image/DICOM redactor is **beta**; DICOM engine redacts **pixels only, not metadata** (run before tag scrubbing).
- Recall must be measured per surface; not a managed, compliance-attested service like AHDS.

## Recommended composition

- **Tags:** Option A (AHDS anonymization); optionally screen tag values with Option E recognizers.
- **Text:** Option B (Language PHI detection) or AHDS text de-ID; **Option E (Presidio)** where custom recognizers / on-prem portability are needed.
- **Pixels:** Option C (OCR + masking) and/or **Option E (Presidio `DicomImageRedactorEngine`)**, with human review on high-risk modalities.

> Presidio is attractive when Company wants **one extensible OSS pipeline spanning all three surfaces** or de-ID that runs **on-prem before egress** ([`docs/03`](../docs/03-phi-detection-deidentification.md) residency decision). Weigh against the managed, compliance-aligned AHDS/Language services.

## Sub-decisions to record

1. **De-ID standard** per use case (Safe Harbor vs. Expert Determination).
2. **Re-identification** required? If yes, segregated key-vault boundary + break-glass.
3. **Where de-ID runs:** on-prem before egress / ingestion edge / post-landing (PHI residency trade-off — see [`docs/03`](../docs/03-phi-detection-deidentification.md)).

## Comparison

| Criterion | A: AHDS | B: Language PHI | C: Pixel OCR | D: Custom | E: Presidio |
|---|---|---|---|---|---|
| Surface covered | Tags/FHIR | Text | Pixels | All | Text + tags + pixels |
| Ops burden | Low | Low | Medium | High | Medium (self-hosted) |
| Compliance fit | Strong | Strong (text) | Needs QA | You own | You own (OSS; validate) |
| Effort | Low | Low | Medium | High | Medium |
| Notes | Managed | Managed | — | — | OSS, portable/on-prem; image redactor beta |

## Decision

- **Chosen composition:** _TBD_
- **De-ID standard:** _TBD_
- **Re-ID policy:** _TBD_
- **De-ID location (residency):** _TBD_
- **Owner:** _TBD_
- **Date:** _TBD_
- **Follow-ups / SOW impact:** _TBD_
