#!/usr/bin/env python3
"""Render a transparent SVG overlay over an image and write a verified PNG."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def dimensions(image: Path, magick: str) -> tuple[int, int]:
    result = run([magick, "identify", "-format", "%w %h", str(image)])
    try:
        width, height = (int(value) for value in result.stdout.split())
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"Could not read image dimensions: {result.stdout!r}") from error
    return width, height


def validate_overlay(overlay: Path, width: int, height: int) -> None:
    root = ET.parse(overlay).getroot()
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError("Overlay root must be an SVG element")

    view_box = root.attrib.get("viewBox", "").replace(",", " ").split()
    expected = [0.0, 0.0, float(width), float(height)]
    try:
        actual = [float(value) for value in view_box]
    except ValueError as error:
        raise ValueError("Overlay viewBox must contain four numeric values") from error
    if actual != expected:
        raise ValueError(
            f"Overlay viewBox must be '0 0 {width} {height}', got "
            f"{root.attrib.get('viewBox')!r}"
        )


def render_overlay(
    overlay: Path, destination: Path, width: int, height: int, magick: str
) -> str:
    rsvg = shutil.which("rsvg-convert")
    if rsvg:
        run(
            [
                rsvg,
                "--width",
                str(width),
                "--height",
                str(height),
                "--output",
                str(destination),
                str(overlay),
            ]
        )
        return "rsvg-convert"

    run(
        [
            magick,
            "-background",
            "none",
            str(overlay),
            "-resize",
            f"{width}x{height}!",
            f"PNG32:{destination}",
        ]
    )
    return "ImageMagick SVG renderer"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Composite a transparent SVG overlay over an image."
    )
    parser.add_argument("source", type=Path, help="Original source image")
    parser.add_argument("overlay", type=Path, help="Transparent SVG overlay")
    parser.add_argument("output", type=Path, help="Destination .png path")
    parser.add_argument(
        "--force", action="store_true", help="Replace an existing output PNG"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    overlay = args.overlay.expanduser().resolve()
    output = args.output.expanduser().resolve()

    for path, label in ((source, "source"), (overlay, "overlay")):
        if not path.is_file():
            raise FileNotFoundError(f"{label.capitalize()} file does not exist: {path}")
    if output.suffix.lower() != ".png":
        raise ValueError(f"Output must have a .png extension: {output}")
    if output in (source, overlay):
        raise ValueError("Output must not overwrite the source or overlay")
    if output.exists() and not args.force:
        raise FileExistsError(f"Output already exists (use --force to replace it): {output}")

    magick = shutil.which("magick")
    if not magick:
        raise RuntimeError("ImageMagick is required; install it and retry")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="image-markup-") as temporary:
        temp = Path(temporary)
        base_png = temp / "base.png"
        overlay_png = temp / "overlay.png"

        run([magick, str(source), "-auto-orient", f"PNG32:{base_png}"])
        width, height = dimensions(base_png, magick)
        validate_overlay(overlay, width, height)
        renderer = render_overlay(overlay, overlay_png, width, height, magick)
        run(
            [
                magick,
                str(base_png),
                str(overlay_png),
                "-compose",
                "over",
                "-composite",
                "-strip",
                f"PNG32:{output}",
            ]
        )

    output_width, output_height = dimensions(output, magick)
    image_format = run([magick, "identify", "-format", "%m", str(output)]).stdout
    if image_format != "PNG" or (output_width, output_height) != (width, height):
        raise RuntimeError(
            "Output verification failed: "
            f"format={image_format}, size={output_width}x{output_height}"
        )

    print(
        f"Rendered {output} ({width}x{height} PNG) using {renderer}; "
        "source and SVG were not modified."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ET.ParseError, OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
