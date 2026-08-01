---
name: organize-screenshots
description: Organize screenshot collections into chronological day and context-based episode folders, then give each image a concise, content-derived filename. Use when a user wants screenshots or screen captures grouped by day, ordered by time, renamed from their visible content, or cleaned up across one or more month folders.
---

# Organize Screenshots

## Overview

Create one canonical, chronological screenshot collection without guessing beyond visible evidence. Infer episodes from nearby captures and contextual clues rather than imposing an external taxonomy.

## Confirm the organization contract

Before moving files, establish or confirm:

- Scope: the source year/month folders and whether to repeat for other months.
- Destination structure: `YYYY/MM/DD/{Episode}/HH-MM-SS - {Contextual Title}.png`.
- Episode policy: derive each episode from a sliding time window plus on-screen context.
- Uncertainty policy: use `Unclassified` only when no episode can be identified confidently.
- Mutation policy: move originals, do not retain duplicate copies, and remove only folders that are empty after verification.

Do not mutate files until the user confirms these choices. If an essential decision is absent, ask one concise question at a time and recommend the safest default.

## Inspect and infer episodes

1. Enumerate images and extract their capture dates/times from their existing filenames or metadata.
2. Review visual content in chronological order using batches or contact sheets. Use locally available OCR when it works, but do not rely only on the original generic filename.
3. Partition each day into contiguous episodes. Use app/site, task subject, visible headings, navigation flow, and close capture times as evidence.
4. Give every episode a short stable name such as `AI CRED` or `Church Website`. Avoid vague labels like `Misc`.
5. Give every image a title that describes the specific screen or meaningful state, not merely the app name. Use title case and omit redundant date/time text.

## Move and name files

For each source image, move it to:

```text
YYYY/MM/DD/{Episode}/HH-MM-SS - {Contextual Title}.{extension}
```

Use 24-hour, zero-padded times so folder order is capture order. Preserve the original extension. If two files have the same second and title, add a minimal disambiguator after the title; do not change the timestamp.

For a macOS screenshot collection, use `scripts/organize.py` to produce a tab-separated manifest first. Inspect its episode and title columns, correct any weak classifications, then re-run it with `--apply`. Do not use `--apply` until the manifest is accepted.

## Verify and clean up

After the move:

1. Recount source and destination files; totals must match.
2. Check every file path against the naming contract and confirm chronological ordering within each episode.
3. Spot-check titles and episode assignments against the images.
4. Remove only source folders proved empty; never delete image files as cleanup.
5. Report the source scope, total moved, episodes created, unclassified count, empty folders removed, and any uncertainty requiring review.
