#!/usr/bin/env python3
"""Generate or edit images through the saved OpenRouter Images API settings."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SKILL_DIR = Path(__file__).resolve().parents[1]
PREFERENCES_PATH = SKILL_DIR / "preferences.json"
API_URL = "https://openrouter.ai/api/v1/images"
MEDIA_EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/svg+xml": ".svg", "image/webp": ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", help="Image-generation or image-editing instruction.")
    parser.add_argument("--reference", action="append", default=[], metavar="PATH_OR_URL", help="Reference image path, HTTPS URL, or data URL; may be repeated.")
    parser.add_argument("--model", help="Override the saved model for this request.")
    parser.add_argument("--output-dir", help="Override the saved output directory for this request.")
    parser.add_argument("--env-file", help="Override the saved env-file path for this request.")
    parser.add_argument("--aspect-ratio", help="Requested aspect ratio, for example 16:9.")
    parser.add_argument("--quality", help="Requested quality level, for example auto or high.")
    parser.add_argument("--background", choices=("auto", "transparent", "opaque"), help="Requested background treatment.")
    parser.add_argument("--n", type=int, default=1, help="Number of images (1-10; default: 1).")
    parser.add_argument("--name", help="Filename prefix; the timestamp is added automatically.")
    return parser.parse_args()


def load_preferences() -> dict[str, str]:
    try:
        data = json.loads(PREFERENCES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read preferences at {PREFERENCES_PATH}: {exc}") from exc
    required = ("model", "quality", "output_dir", "env_file")
    if not all(isinstance(data.get(key), str) and data[key] for key in required):
        raise SystemExit(f"Preferences must contain non-empty strings: {', '.join(required)}")
    return data


def read_key(env_file: Path) -> str:
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SystemExit(f"Cannot read env file {env_file}: {exc}") from exc
    for line in lines:
        match = re.match(r"^\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*(.*?)\s*$", line)
        if match:
            value = match.group(1).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            if value:
                return value
    raise SystemExit(f"OPENROUTER_API_KEY is missing or empty in {env_file}")


def reference_url(reference: str) -> str:
    if reference.startswith(("https://", "http://", "data:")):
        return reference
    path = Path(reference).expanduser()
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise SystemExit(f"Cannot read reference image {path}: {exc}") from exc
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{media_type};base64,{base64.b64encode(content).decode('ascii')}"


def request_image(api_key: str, body: dict[str, Any]) -> dict[str, Any]:
    request = Request(API_URL, data=json.dumps(body).encode("utf-8"), headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=180) as response:
            return json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(detail)
            reasons = payload.get("error", {}).get("metadata", {}).get("ineligibility_reasons", [])
        except (AttributeError, json.JSONDecodeError):
            reasons = []
        if any(reason.get("reason") == "zdr-violation-by-account" for reason in reasons if isinstance(reason, dict)):
            raise SystemExit(
                "OpenRouter excluded every matching endpoint under this account's "
                "Zero Data Retention guardrail. Choose a ZDR-compatible model or "
                "change that account setting, then retry."
            ) from exc
        raise SystemExit(f"OpenRouter returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise SystemExit(f"OpenRouter request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"OpenRouter returned invalid JSON: {exc}") from exc


def safe_stem(name: str | None) -> str:
    candidate = re.sub(r"[^A-Za-z0-9._-]+", "-", name or "image").strip(".-")
    return candidate or "image"


def save_images(response: dict[str, Any], output_dir: Path, name: str | None) -> list[Path]:
    data = response.get("data")
    if not isinstance(data, list) or not data:
        raise SystemExit("OpenRouter response did not contain image data.")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = safe_stem(name)
    saved: list[Path] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict) or not isinstance(item.get("b64_json"), str):
            raise SystemExit(f"OpenRouter response image {index} has no b64_json field.")
        extension = MEDIA_EXTENSIONS.get(item.get("media_type"), ".bin")
        destination = output_dir / f"{stem}-{timestamp}-{index:02d}{extension}"
        try:
            destination.write_bytes(base64.b64decode(item["b64_json"], validate=True))
        except (ValueError, OSError) as exc:
            raise SystemExit(f"Could not save image {index}: {exc}") from exc
        saved.append(destination)
    return saved


def main() -> None:
    args = parse_args()
    if not 1 <= args.n <= 10:
        raise SystemExit("--n must be between 1 and 10.")
    preferences = load_preferences()
    env_file = Path(args.env_file or preferences["env_file"]).expanduser()
    output_dir = Path(args.output_dir or preferences["output_dir"]).expanduser()
    body: dict[str, Any] = {"model": args.model or preferences["model"], "prompt": args.prompt, "quality": args.quality or preferences["quality"], "n": args.n}
    if args.aspect_ratio:
        body["aspect_ratio"] = args.aspect_ratio
    if args.background:
        body["background"] = args.background
    if args.reference:
        body["input_references"] = [{"type": "image_url", "image_url": {"url": reference_url(item)}} for item in args.reference]
    response = request_image(read_key(env_file), body)
    saved = save_images(response, output_dir, args.name)
    for path in saved:
        print(f"Saved: {path}")
    usage = response.get("usage")
    if isinstance(usage, dict) and isinstance(usage.get("cost"), (int, float)):
        cost = float(usage["cost"])
        print(f"Request cost: ${cost:.6f} USD")
        print(f"Average per saved image: ${cost / len(saved):.6f} USD")
    else:
        print("Request cost: unavailable in the OpenRouter response")


if __name__ == "__main__":
    main()
