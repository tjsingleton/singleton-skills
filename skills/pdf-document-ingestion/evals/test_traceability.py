from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
INGEST = SKILL_ROOT / "scripts" / "ingest_pdf.py"
SAMPLE_TEXT = "Sample paragraph for source anchor verification."
ANCHOR_PATTERN = re.compile(
    r"pdf:p(?P<page>\d{4}):bbox\("
    r"(?P<x0>\d+\.\d{2}),(?P<y0>\d+\.\d{2}),"
    r"(?P<x1>\d+\.\d{2}),(?P<y1>\d+\.\d{2})\)"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


class PdfTraceabilityTest(unittest.TestCase):
    def test_converted_paragraph_resolves_to_original_pdf_region(self) -> None:
        self.assertIsNotNone(shutil.which("ps2pdf"), "ps2pdf is required")
        self.assertIsNotNone(shutil.which("pdftotext"), "pdftotext is required")
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            source_ps = temp / "sample.ps"
            source_pdf = temp / "sample.pdf"
            output = temp / "ingested"
            source_ps.write_text(
                "%!PS-Adobe-3.0\n"
                "/Helvetica findfont 12 scalefont setfont\n"
                f"72 720 moveto ({SAMPLE_TEXT}) show\n"
                "showpage\n",
                encoding="ascii",
            )
            subprocess.run(
                ["ps2pdf", str(source_ps), str(source_pdf)],
                check=True,
                text=True,
                capture_output=True,
            )
            source_hash_before = sha256(source_pdf)

            completed = subprocess.run(
                [
                    "python3",
                    str(INGEST),
                    str(source_pdf),
                    "--output-dir",
                    str(output),
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )

            artifact_text = (output / "sample.md").read_text(encoding="utf-8")
            self.assertIn(SAMPLE_TEXT, artifact_text)
            match = ANCHOR_PATTERN.search(artifact_text)
            self.assertIsNotNone(match)
            assert match is not None
            artifact_anchor = match.group(0)

            xhtml = temp / "source.xhtml"
            subprocess.run(
                ["pdftotext", "-bbox", str(source_pdf), str(xhtml)],
                check=True,
                text=True,
                capture_output=True,
            )
            root = ET.parse(xhtml).getroot()
            pages = [element for element in root.iter() if name(element.tag) == "page"]
            self.assertEqual(len(pages), 1)
            words = [
                element
                for element in pages[0].iter()
                if name(element.tag) == "word"
            ]
            source_text = " ".join("".join(word.itertext()) for word in words)
            self.assertEqual(source_text, SAMPLE_TEXT)
            source_anchor = (
                "pdf:p0001:bbox("
                f"{min(float(word.attrib['xMin']) for word in words):.2f},"
                f"{min(float(word.attrib['yMin']) for word in words):.2f},"
                f"{max(float(word.attrib['xMax']) for word in words):.2f},"
                f"{max(float(word.attrib['yMax']) for word in words):.2f})"
            )
            self.assertEqual(artifact_anchor, source_anchor)
            print(f"TRACE: {SAMPLE_TEXT} -> {artifact_anchor}")
            self.assertEqual(source_hash_before, sha256(source_pdf))

            index = (output / "index.md").read_text(encoding="utf-8")
            self.assertIn("Artifact | Source path | Document type | Conversion confidence", index)
            self.assertIn("`sample.md`", index)
            self.assertIn("PDF text layer", index)
            self.assertIn("Medium", index)
            self.assertIn("source spot-check pending", index)

    def test_index_cannot_overwrite_source_or_artifact(self) -> None:
        self.assertIsNotNone(shutil.which("ps2pdf"), "ps2pdf is required")
        self.assertIsNotNone(shutil.which("pdftotext"), "pdftotext is required")
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            source_ps = temp / "sample.ps"
            source_pdf = temp / "sample.pdf"
            output = temp / "ingested"
            source_ps.write_text(
                "%!PS-Adobe-3.0\n"
                "/Helvetica findfont 12 scalefont setfont\n"
                f"72 720 moveto ({SAMPLE_TEXT}) show\n"
                "showpage\n",
                encoding="ascii",
            )
            subprocess.run(
                ["ps2pdf", str(source_ps), str(source_pdf)],
                check=True,
                text=True,
                capture_output=True,
            )
            source_hash = sha256(source_pdf)

            source_index = subprocess.run(
                [
                    "python3",
                    str(INGEST),
                    str(source_pdf),
                    "--output-dir",
                    str(output),
                    "--index",
                    str(source_pdf),
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(source_index.returncode, 0)
            self.assertIn("must not be the original source", source_index.stderr)
            self.assertEqual(source_hash, sha256(source_pdf))

            artifact_index = subprocess.run(
                [
                    "python3",
                    str(INGEST),
                    str(source_pdf),
                    "--output-dir",
                    str(output),
                    "--index",
                    str(output / "sample.md"),
                ],
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(artifact_index.returncode, 0)
            self.assertIn("must not be the converted artifact", artifact_index.stderr)
            self.assertEqual(source_hash, sha256(source_pdf))


if __name__ == "__main__":
    unittest.main()
