# 03 — PHI Detection & De-identification

De-identification is the **highest-leverage control** in the whole platform. Get it right early and the rest of the estate carries far less PHI risk.

## Principles

1. **De-identify as early as possible** — ideally before or at the ingestion edge.
2. **Three surfaces of PHI in imaging**, all must be handled:
   - **DICOM metadata tags** (patient name, MRN, dates, accession, UIDs, institution).
   - **Pixel data / burned-in annotations** (PHI rendered into the image, e.g., ultrasound, secondary captures, scanned film).
   - **Associated free text** (reports, notes).
3. **Minimize the PHI blast radius** — a small, tightly-governed PHI zone; everything downstream is de-identified.
4. **Preserve clinical utility** — date-shifting instead of date removal; consistent surrogate keys for linkage.

## De-identification approaches

| Surface | Technique | Azure options |
|---|---|---|
| DICOM tags | Redact/replace per DICOM PS3.15 Confidentiality Profiles | AHDS DICOM de-ID / anonymization tooling; FHIR/DICOM anonymization engine (config-driven); **Presidio** (custom recognizers over tag values) |
| Pixel PHI | Detect & mask burned-in text regions | OCR + region masking (Vision/Document Intelligence + custom); domain models; **Presidio Image Redactor** (`DicomImageRedactorEngine`, can use Azure Document Intelligence OCR) |
| Free text | Detect & redact/surrogate PHI entities | Azure AI Language **PHI/PII detection**; AHDS de-ID service; **Presidio** analyzer/anonymizer |

See **[DEC-03](../decisions/DEC-03-phi-deidentification.md)** for the options comparison and recommendation.

### Presidio — one OSS toolkit across all three surfaces

[**Presidio**](https://github.com/data-privacy-stack/presidio) ([docs](https://presidio.dataprivacystack.org/)) is an open-source de-identification toolkit whose modules line up with the three PHI surfaces above:

- **Text** — [analyzer](https://presidio.dataprivacystack.org/analyzer/) (NER + regex + rule/checksum recognizers, multi-language, custom recognizers) and [anonymizer](https://presidio.dataprivacystack.org/anonymizer/) (redact, replace, hash, surrogate) for reports/notes.
- **Structured / tags** — [presidio-structured](https://presidio.dataprivacystack.org/structured/) for structured & semi-structured data; custom recognizers can screen DICOM tag values as a complement to PS3.15 profile redaction.
- **Pixels** — [Presidio Image Redactor](https://presidio.dataprivacystack.org/image-redactor/) redacts burned-in text, and its **`DicomImageRedactorEngine`** targets DICOM pixel PHI specifically. It can run on **Tesseract** OCR or **Azure Document Intelligence** OCR (`DocumentIntelligenceOCR`, supports `DefaultAzureCredential`).

Trade-offs: highly **extensible and portable** (Python/PySpark/Docker/Kubernetes) and free, but self-hosted (you own deployment, tuning, and validation), and the image/DICOM redactor is **beta** — the DICOM engine redacts **pixels only, not metadata** (run it *before* tag scrubbing). Recall must be measured like any detector (see Validation & QA). See **[DEC-03](../decisions/DEC-03-phi-deidentification.md)**.

## De-identification vs. anonymization vs. pseudonymization

- **Pseudonymization:** replace identifiers with surrogate keys; re-identification possible via a protected mapping. Useful for longitudinal studies.
- **De-identification (HIPAA Safe Harbor / Expert Determination):** remove/transform the 18 identifier types to a defensible standard.
- **Anonymization:** irreversible; no re-ID key retained.

Company should decide, per use case, which standard applies (research vs. clinical vs. commercial SaaS). Capture in **[DEC-03](../decisions/DEC-03-phi-deidentification.md)**.

## Re-identification key management

If linkage is required:
- Store the surrogate ↔ real-identity mapping in a **segregated boundary** (separate subscription/Key Vault, separate RBAC, break-glass access, full audit).
- Access to re-ID is a **privileged, logged operation**, never available to model/inference paths.

## Where de-ID runs (residency decision)

| Option | PHI residency | Trade-off |
|---|---|---|
| On-prem before egress | PHI never leaves hospital | Highest control; more on-prem engineering |
| At ingestion edge in Azure (landing subnet) | PHI briefly in a locked zone | Balanced; needs strong isolation |
| Post-landing in Azure PHI zone | PHI persists in prod PHI zone | Simplest; largest PHI footprint |

Capture this in **[DEC-03](../decisions/DEC-03-phi-deidentification.md)** — it has direct compliance implications.

## Validation & QA

- Measure de-ID **recall** (missed PHI = a breach) and **precision** (over-redaction hurts utility) on a labeled sample.
- Human-in-the-loop review for pixel de-ID on high-risk modalities.
- Periodic re-audit; treat de-ID model updates as a governed change (see [`docs/11`](./11-governance-compliance.md)).

## Anti-patterns to avoid

- Sending raw PHI images to a generative model endpoint "just for the prototype."
- Relying only on DICOM tag redaction while ignoring burned-in pixel PHI.
- Storing the re-ID map next to the de-identified data.
