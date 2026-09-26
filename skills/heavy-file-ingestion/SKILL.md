---
name: heavy-file-ingestion
description: >
  Ingest a large or binary local document before analysis: PDF, slide deck,
  spreadsheet, CSV dump, or long document. Convert it to indexed lightweight
  Markdown/CSV artifacts. Use when an analysis request touches one; don't use
  when a current verified ingestion already exists.
argument-hint: "<source-path> [output-directory]"
license: MIT
---

# Heavy File Ingestion

> **Quick usage:**
> ```text
> heavy-file-ingestion ./annual-report.pdf
> heavy-file-ingestion ./board-deck.pptx ./_ingested/board-deck/
> heavy-file-ingestion ./export.xlsx
> ```
>
> If no source is supplied, ask for its path. Default output to
> `_ingested/<source-stem>-<sha256-prefix>/` beside the source. The hash suffix
> lets multiple source revisions coexist safely.

## Gate: ingest before analysis

This skill applies whenever the user shares a heavy or binary document, or asks
to analyze, summarize, compare, search, answer questions from, or extract data
from one. The first deliverable is a lightweight, indexed ingestion—not an
answer about the source.

Preserve the source unchanged. After a verified ingestion exists, read and cite
the converted artifacts for all analysis. Reopen the original only to resolve
an anchor, repair a failed conversion, or make a visual check that the artifact
cannot support. A verified current ingestion may be reused only when its index
records the source's current SHA-256 hash.

Use the narrower `pdf-document-ingestion` skill when the work is exclusively a
PDF, form, or CSV and demands its page-region/form-field traceability contract.

## Workflow

### 1. Inventory the source and output location

1. Resolve the exact files and identify their type. Record relative source
   path, byte size, modification time, and SHA-256 in `_ingested/.../index.md`.
2. Create a new revision directory when the source hash differs. Do not replace
   an older ingestion or modify the source.
3. Check the required converter before use. Prefer already-installed tools; if
   one is missing, ask before installing it and record the tool and version in
   the index. Use the recipes below.

Completion criterion: the source is unchanged, the output directory is
separate, and the index has a source record before conversion starts.

### 2. Convert by source type

Read [format recipes](references/format-recipes.md) only for the source type at
hand. Convert source content faithfully, in source order. Retain meaningful
text, tables, labels, formulas, slide notes, and chart/data labels. Mark
unreadable or unextractable content as `[UNRESOLVED: reason]`; ingestion does
not repair, summarize, interpret, classify, or infer.

Place a stable source-native anchor adjacent to every converted unit:

| Type | Anchor convention |
| --- | --- |
| PDF | `pdf:p0007` or `pdf:p0007:bbox(x1,y1,x2,y2)` when regions are available |
| Slide deck | `slide:0012` and, where needed, `slide:0012:notes` |
| Spreadsheet | `xlsx:Sheet%20Name!A1:D38` |
| CSV/TSV | `csv:line:000042` (the header is line 1) |
| DOCX/ODT/long text | `heading:Introduction/Scope` or `file:source.txt:line:000018-000024` |

Choose one convention per source case, declare it in the index, and repeat that
exact string in later citations. Do not add a second generated paragraph or
Markdown-line numbering scheme.

### 3. Chunk for reading, not storage

Keep each Markdown artifact under roughly 6,000 words and 1,000 logical lines.
Split at source boundaries—PDF page ranges, slides, workbook sheets, headings,
or CSV row ranges—rather than in the middle of a paragraph, table, or record.
Use zero-padded names such as `pages-0001-0025.md`, `slides-0001-0050.md`, and
`rows-000001-020000.csv`. Repeat the source range and anchor convention in each
chunk's header. Keep tables as CSV when that is more inspectable than Markdown;
split tabular exports at 20,000 data rows or earlier when a chunk is unwieldy.

### 4. Write `index.md`

Maintain one `index.md` at the ingestion root. It must include the source
metadata, converter/version, anchor convention, and one row for every artifact:

| Artifact | Source span | Type | One-line summary | Confidence |
| --- | --- | --- | --- | --- |
| `pages-0001-0025.md` | PDF pages 1-25 | Markdown | Extracted report text and tables. | High |
| `summary.md` | Whole source | Markdown | Navigation only; no interpretation. | High |

`summary.md` is a navigation map: headings, sheets, slide titles, row ranges,
and unresolved regions only. It is not analytical prose. Set confidence to
High, Medium, or Low based on extraction fidelity, reading order, OCR quality,
and omitted content—not the source's subject matter.

### 5. Verify, then release the analysis gate

1. Recompute the source hash and confirm it matches the index.
2. Confirm every expected artifact and chunk appears in `index.md` with a
   one-line summary.
3. Confirm chunk coverage is continuous and all substantive units have one
   canonical anchor.
4. Choose one paragraph, slide, cell range, or CSV row and compare it directly
   with the original source at its anchor.
5. Record the sample, exact anchor, result, and any unresolved regions in the
   index's verification section.

Only after these checks pass may analysis begin. Read the artifacts, not the
heavy original, and cite the artifact path plus its embedded anchor. If a check
fails, repair or rerun ingestion and report the limitation before analysis.

## Output contract

Return the ingestion root, `index.md`, artifact list, source hash result,
converter used, anchor convention, and one traceability check. State whether
the analysis gate is open. Do not return substantive conclusions from the
source as part of ingestion.
