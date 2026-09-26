# Format recipes

Run the smallest applicable recipe. The commands create derivatives only in the
ingestion directory; they do not modify the source.

## Tool check and installation

Check tools first:

```sh
command -v pdftotext pdfinfo ocrmypdf tesseract libreoffice pandoc python3
python3 -c 'import importlib.util; print({name: bool(importlib.util.find_spec(name)) for name in ("openpyxl", "docx", "pptx")})'
```

Install only tools required by the selected recipe, after approval:

```sh
brew install poppler ocrmypdf tesseract libreoffice pandoc python
python3 -m pip install --user openpyxl python-docx python-pptx
```

Record exact versions with `--version` (or package metadata) in `index.md`.
If installation is unavailable, use an already-installed fallback and lower
confidence; do not silently substitute an unverified converter.

## PDF

1. Inspect page count and text-layer viability with `pdfinfo source.pdf` and
   a small `pdftotext -f 1 -l 3 -layout source.pdf -` sample.
2. For a text-layer PDF, extract each bounded page range with
   `pdftotext -layout -f FIRST -l LAST source.pdf pages-FIRST-LAST.txt`, then
   convert the text faithfully to a Markdown chunk with a `pdf:pNNNN` marker at
   each page break.
3. For a scan, create `ocr.pdf` inside the ingestion directory with
   `ocrmypdf --skip-text source.pdf ocr.pdf`, then follow step 2. Use Tesseract
   only when OCRmyPDF is unavailable and state the limitation.
4. When placement matters, retain page renders made with `pdftoppm` for visual
   verification and use `pdf:pNNNN:bbox(...)` anchors only if the coordinates
   can be produced reliably.

## PPTX, PPT, ODP, or Keynote export

1. Use LibreOffice headlessly to render an office deck to PDF in the ingestion
   directory when rendering, diagrams, or visual order needs verification:
   `libreoffice --headless --convert-to pdf --outdir OUTPUT source.pptx`.
2. Extract slide text, tables, titles, and speaker notes with `python-pptx`
   where supported; use `slide:NNNN` markers in source order. Retain one
   Markdown chunk per slide range and a navigation summary of slide titles.
3. Compare a representative slide's title, visible text, and notes (if any)
   against the rendered PDF. State which visual content could not be represented
   as text; do not invent a description of diagrams or images.

## XLSX, XLS, ODS, and Numbers export

1. Inspect workbook sheets, dimensions, merged cells, formulas, and values with
   `openpyxl` for XLSX. Preserve formula text as well as displayed values when
   both are relevant.
2. Emit a `workbook.md` navigation map and one CSV or Markdown-table artifact
   per sheet or sheet-range. Give each table unit an `xlsx:Sheet!A1:D38` anchor.
3. For legacy XLS/ODS, use LibreOffice to export each sheet or convert a copy to
   XLSX in the ingestion directory, and record the conversion in the index.
4. Check a representative formula, a displayed value, and a merged/header range
   against the source. Flag charts, hidden sheets, external links, macros, and
   unsupported formulas explicitly.

## CSV, TSV, NDJSON, and delimited dumps

1. Detect the delimiter, encoding, header, line endings, and malformed rows
   without normalizing the original. Preserve a byte-identical copy only when
   needed inside the ingestion directory; otherwise reference the source path.
2. Split into CSV chunks at record boundaries, adding a small adjacent Markdown
   map that states the physical source-line range. Use `csv:line:NNNNNN` for
   CSV/TSV and `file:source.ndjson:line:NNNNNN` for NDJSON.
3. Write `schema.md` with column names, declared/inferred types, row count,
   delimiter, and conversion errors. It is descriptive, not an analysis.

## DOCX, ODT, RTF, HTML, and long Markdown/text

1. Prefer `pandoc --extract-media=MEDIA_DIR -t gfm source.docx -o raw.md` for
   documents with headings, tables, and embedded media. Use `python-docx` when
   Pandoc is unavailable and record limitations.
2. Normalize only the derivative into readable Markdown. Split it at heading
   boundaries. Use a unique escaped heading path anchor; if headings are absent
   or ambiguous, use physical file-line anchors instead.
3. Place extracted media in an `assets/` subdirectory and list each asset in
   the index. Review a heading, a table, and an image-adjacent passage against
   the source.
