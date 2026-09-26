---
name: pdf-document-ingestion
description: >
  Convert heavy PDFs, forms, CSVs, and messy documents into lightweight Markdown
  or structured text with source-native anchors before analysis. Use when a user
  says "capture this PDF," "convert this form," or needs traceable document
  ingestion. Don't use when a trustworthy anchored artifact already exists.
argument-hint: "<source-path> [output-directory]"
license: MIT
---

# PDF Document Ingestion

> **Quick usage:**
> ```text
> pdf-document-ingestion ./source.pdf
> pdf-document-ingestion ./forms/ ./ingested/
> pdf-document-ingestion ./records.csv ./ingested/
> ```
>
> If invoked without a source, ask for the source path. Default the output to an
> `ingested/` directory beside the source when the user does not specify one.

## Purpose

Create a compact, reviewable artifact that preserves provenance well enough for
every downstream citation to resolve directly to the original document. Keep
the original unchanged. Once a verified ingested artifact exists, use it for
analysis and return to the original only to verify an anchor or repair the
conversion.

## Workflow

### 1. Inventory and protect the source

1. Resolve the exact source files without broad scans.
2. Record each source path, document type, byte size, and SHA-256 hash before
   conversion.
3. Write converted files to a separate output directory. Never edit, rename,
   annotate, optimize, or overwrite an original.
4. If an output path already exists, compare its recorded source hash. Reuse it
   only when the hash matches and the artifact passes the checks below;
   otherwise create a distinct artifact or ask before replacing it.

### 2. Choose one source-native anchor scheme

Choose the most direct stable coordinates exposed by that source. Declare the
scheme once in the artifact metadata and use only that scheme for the entire
source case.

| Source case | Canonical anchor example | Use when |
| --- | --- | --- |
| PDF text or OCR | `pdf:p0007:bbox(72.00,144.00,510.00,198.00)` | Page and source-page region are available. Coordinates are PDF points measured from the top-left. |
| Structured form | `form:box:Emergency%20contact%20phone` | Stable field or box labels are the source's native structure. Preserve the exact label, percent-encoding characters that cannot appear literally. |
| CSV or line-oriented export | `csv:line:0042` | Physical source lines are stable; count the header as line 1. |
| Heading-structured document | `heading:Benefits/Eligibility/Dependents` | The source has stable, unique heading paths. Escape literal `/` characters. |
| Plain file | `file:relative/path.txt:line:0018-0024` | File location and physical line spans are the only stable coordinates. |

Do not add generated paragraph IDs, Markdown line numbers, OCR block numbers,
or a second numbering system. Two anchor schemes for one source case are a
defect. If the preferred coordinates are unavailable, choose a different single
scheme before conversion and record why.

### 3. Convert without interpretation

- Preserve source order, wording, table values, labels, checked states, and
  meaningful section boundaries.
- Remove only representational noise such as repeated page furniture when it
  does not carry meaning. Record any omission policy in the artifact.
- Mark unreadable or uncertain content explicitly. Do not silently repair,
  summarize, classify, or infer during ingestion.
- For born-digital PDFs with a text layer, prefer
  `scripts/ingest_pdf.py <source.pdf> --output-dir <directory>`. It emits
  page-region anchors and updates the ingestion index.
- For scanned PDFs, run an available OCR tool while retaining page geometry,
  then emit the same `pdf:pNNNN:bbox(...)` anchors. Lower confidence for weak
  OCR and record the OCR tool and version.
- For forms, tables, CSVs, or non-PDF files, create Markdown or JSONL directly
  with the selected source-native anchors attached to each converted unit.

Place the exact canonical anchor immediately before or beside the converted
unit. A downstream citation must repeat the identical anchor string, for
example:

```markdown
<!-- source-anchor: pdf:p0007:bbox(72.00,144.00,510.00,198.00) -->
Coverage begins on the first day of the month after eligibility is confirmed.

Citation: [pdf:p0007:bbox(72.00,144.00,510.00,198.00)]
```

### 4. Write the ingestion index

Maintain `index.md` in the output directory. Include one row per artifact with
at least:

| Artifact | Source path | Document type | Conversion confidence |
| --- | --- | --- | --- |
| `policy.md` | `../source/policy.pdf` | PDF text layer | High |

Use `High`, `Medium`, or `Low`, followed by a short reason when useful. Base
confidence on extraction quality, reading order, OCR quality, and unresolved
content rather than the subject matter.

### 5. Verify before analysis

1. Recompute the source hash and confirm it matches the pre-conversion hash.
2. Confirm every substantive converted unit has exactly one canonical anchor.
3. Search the artifact for competing anchor syntax or dual numbering.
4. Pick at least one converted paragraph, row, or form box. Resolve its anchor
   in the original and compare the text or value directly.
5. Confirm `index.md` lists the artifact, source path, document type, and
   confidence.
6. Report the artifact and index paths, source preservation result, selected
   anchor convention, traceability proof, and any low-confidence regions.

After these checks pass, analyze the ingested artifact. Cite claims with the
same anchors already embedded in it. Consult the original only when the
artifact lacks the necessary content or an anchor needs verification.

## Output contract

Produce:

- one Markdown or structured-text artifact per source;
- one `index.md` for the output directory;
- unchanged originals with matching before/after hashes;
- a traceability check showing converted text, its exact anchor, and the
  matching original source location;
- explicit conversion confidence and unresolved extraction issues.

Stop before analysis when source preservation, anchor uniqueness, or the sample
traceability check fails.
