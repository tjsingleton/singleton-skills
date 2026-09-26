#!/usr/bin/env python3
"""Convert a text-layer PDF to anchored Markdown without changing the source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ANCHOR_SCHEME = "pdf:pNNNN:bbox(x0,y0,x1,y1)"


@dataclass(frozen=True)
class Paragraph:
    page: int
    anchor: str
    text: str


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def element_children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element.iter() if local_name(child.tag) == name]


def extract_paragraphs(xhtml_path: Path) -> tuple[list[Paragraph], int, int]:
    root = ET.parse(xhtml_path).getroot()
    pages = element_children(root, "page")
    paragraphs: list[Paragraph] = []
    pages_with_text = 0

    for page_number, page in enumerate(pages, start=1):
        page_has_text = False
        for block in element_children(page, "block"):
            words = element_children(block, "word")
            if not words:
                continue

            line_texts: list[str] = []
            for line in element_children(block, "line"):
                line_words = [
                    "".join(word.itertext()).strip()
                    for word in element_children(line, "word")
                ]
                line_text = " ".join(word for word in line_words if word)
                if line_text:
                    line_texts.append(line_text)

            text = " ".join(line_texts).strip()
            if not text:
                continue

            x_min = min(float(word.attrib["xMin"]) for word in words)
            y_min = min(float(word.attrib["yMin"]) for word in words)
            x_max = max(float(word.attrib["xMax"]) for word in words)
            y_max = max(float(word.attrib["yMax"]) for word in words)
            anchor = (
                f"pdf:p{page_number:04d}:"
                f"bbox({x_min:.2f},{y_min:.2f},{x_max:.2f},{y_max:.2f})"
            )
            paragraphs.append(Paragraph(page_number, anchor, text))
            page_has_text = True

        if page_has_text:
            pages_with_text += 1

    return paragraphs, len(pages), pages_with_text


def relative_display(path: Path, base: Path) -> str:
    try:
        return os.path.relpath(path, base)
    except ValueError:
        return str(path)


def markdown_for(
    source: Path,
    source_hash: str,
    paragraphs: list[Paragraph],
    page_count: int,
    pages_with_text: int,
) -> tuple[str, str]:
    confidence = "Medium"
    coverage = f"text extracted from {pages_with_text} of {page_count} PDF pages"
    reason = f"{coverage}; source spot-check pending"
    lines = [
        "---",
        f"source_path: {json.dumps(str(source))}",
        'document_type: "PDF text layer"',
        f"source_sha256: {source_hash}",
        f"anchor_scheme: {json.dumps(ANCHOR_SCHEME)}",
        f"conversion_confidence: {json.dumps(confidence + ' - ' + reason)}",
        "---",
        "",
        f"# {source.stem}",
        "",
    ]

    current_page = 0
    for paragraph in paragraphs:
        if paragraph.page != current_page:
            current_page = paragraph.page
            lines.extend([f"## PDF page {current_page}", ""])
        lines.extend(
            [
                f"<!-- source-anchor: {paragraph.anchor} -->",
                paragraph.text,
                "",
            ]
        )

    return "\n".join(lines), f"{confidence} - {reason}"


def update_index(
    index_path: Path,
    artifact_path: Path,
    source_path: Path,
    confidence: str,
) -> None:
    header = (
        "# Ingestion Index\n\n"
        "| Artifact | Source path | Document type | Conversion confidence |\n"
        "| --- | --- | --- | --- |\n"
    )
    artifact_display = relative_display(artifact_path, index_path.parent)
    source_display = relative_display(source_path, index_path.parent)
    row = (
        f"| `{artifact_display}` | `{source_display}` | PDF text layer | "
        f"{confidence} |"
    )

    existing = index_path.read_text(encoding="utf-8") if index_path.exists() else header
    kept = [
        line
        for line in existing.rstrip().splitlines()
        if not line.startswith(f"| `{artifact_display}` |")
    ]
    index_path.write_text("\n".join(kept + [row, ""]), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a text-layer PDF to source-anchored Markdown."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--index", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve(strict=True)
    if source.suffix.lower() != ".pdf":
        raise SystemExit("source must be a PDF")
    if shutil.which("pdftotext") is None:
        raise SystemExit("pdftotext is required; install Poppler and retry")

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / f"{source.stem}.md"
    if artifact.exists():
        raise SystemExit(f"refusing to overwrite existing artifact: {artifact}")
    index_path = (
        args.index.expanduser().resolve()
        if args.index
        else output_dir / "index.md"
    )
    if index_path == source:
        raise SystemExit("index path must not be the original source")
    if index_path == artifact:
        raise SystemExit("index path must not be the converted artifact")

    before_hash = sha256(source)
    with tempfile.TemporaryDirectory(prefix="pdf-document-ingestion-") as temp_name:
        xhtml_path = Path(temp_name) / "source.xhtml"
        completed = subprocess.run(
            ["pdftotext", "-bbox-layout", str(source), str(xhtml_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(completed.stderr.strip() or "pdftotext failed")
        paragraphs, page_count, pages_with_text = extract_paragraphs(xhtml_path)

    if not paragraphs:
        raise SystemExit(
            "no text-layer content found; use OCR that preserves page geometry"
        )
    after_hash = sha256(source)
    if before_hash != after_hash:
        raise SystemExit("source hash changed during conversion")

    markdown, confidence = markdown_for(
        source, before_hash, paragraphs, page_count, pages_with_text
    )
    artifact.write_text(markdown, encoding="utf-8")
    update_index(index_path, artifact, source, confidence)

    print(f"artifact: {artifact}")
    print(f"index: {index_path}")
    print(f"source_sha256: {before_hash}")
    print(f"paragraphs: {len(paragraphs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
