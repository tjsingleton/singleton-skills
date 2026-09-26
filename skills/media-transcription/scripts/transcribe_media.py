#!/usr/bin/env python3
"""Create the media-transcription skill's standard AssemblyAI output package."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_BASE = "https://api.assemblyai.com/v2"
LLM_GATEWAY_URL = "https://llm-gateway.assemblyai.com/v1/chat/completions"
ENV_FILE = Path.home() / ".secrets"
VIDEO_SUFFIXES = {".avi", ".flv", ".m4v", ".mkv", ".mov", ".mp4", ".webm", ".wmv"}
CHAPTER_MODEL = "claude-sonnet-4-6"
PARAGRAPHS_PER_CHAPTER = 2


class TranscriptionError(RuntimeError):
    """An expected transcription setup, transport, or provider failure."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe local media with AssemblyAI.")
    parser.add_argument("media_path", type=Path, help="Existing local audio or video file")
    parser.add_argument("--output-dir", type=Path, help="Package directory (defaults beside media)")
    parser.add_argument("--poll-interval", type=float, default=3)
    return parser.parse_args()


def read_api_key(env_file: Path = ENV_FILE) -> str:
    if not env_file.is_file():
        raise TranscriptionError(f"API-key env file is missing: {env_file}")
    for line in env_file.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        if value.startswith("export "):
            value = value[len("export ") :].lstrip()
        if value.startswith("ASSEMBLYAI_API_KEY="):
            key = value.split("=", 1)[1].strip().strip("'\"")
            if key:
                return key
    raise TranscriptionError("ASSEMBLYAI_API_KEY is missing or empty in the configured env file")


def request_json(url: str, *, headers: dict[str, str], body: bytes | None = None) -> dict[str, Any]:
    try:
        with urlopen(Request(url, data=body, headers=headers), timeout=120) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise TranscriptionError(f"AssemblyAI returned HTTP {error.code}: {detail}") from error
    except URLError as error:
        raise TranscriptionError(f"Could not reach AssemblyAI: {error.reason}") from error
    try:
        return json.loads(response_body)
    except json.JSONDecodeError as error:
        raise TranscriptionError("AssemblyAI returned invalid JSON") from error


def json_request(url: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"Authorization": key}
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    return request_json(url, headers=headers, body=body)


def extract_audio(video_path: Path, package_dir: Path) -> Path:
    extracted = package_dir / f"{video_path.stem}.source-audio.mp3"
    command = ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-c:a", "libmp3lame", "-q:a", "2", str(extracted)]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as error:
        raise TranscriptionError("ffmpeg is required to extract audio from video") from error
    except subprocess.CalledProcessError as error:
        raise TranscriptionError(f"ffmpeg could not extract audio: {error.stderr.strip()}") from error
    return extracted


def upload_media(media_path: Path, key: str) -> str:
    try:
        data = media_path.read_bytes()
    except OSError as error:
        raise TranscriptionError(f"Could not read media file: {error}") from error
    result = request_json(
        f"{API_BASE}/upload",
        headers={"Authorization": key, "Content-Type": "application/octet-stream"},
        body=data,
    )
    upload_url = result.get("upload_url")
    if not isinstance(upload_url, str) or not upload_url:
        raise TranscriptionError("AssemblyAI upload response did not contain upload_url")
    return upload_url


def transcribe(
    upload_url: str,
    key: str,
    poll_interval: float,
    *,
    legacy_auto_chapters: bool = False,
) -> dict[str, Any]:
    request_body = {
        "audio_url": upload_url,
        "speech_models": ["universal-2"] if legacy_auto_chapters else ["universal-3-5-pro"],
        "speaker_labels": True,
        "format_text": True,
        "punctuate": True,
    }
    if legacy_auto_chapters:
        request_body["auto_chapters"] = True
    started = json_request(f"{API_BASE}/transcript", key, request_body)
    transcript_id = started.get("id")
    if not isinstance(transcript_id, str) or not transcript_id:
        raise TranscriptionError("AssemblyAI transcription response did not contain an id")
    while True:
        result = json_request(f"{API_BASE}/transcript/{transcript_id}", key)
        if result.get("status") == "completed":
            return result
        if result.get("status") == "error":
            raise TranscriptionError(f"AssemblyAI transcription failed: {result.get('error', 'unknown error')}")
        time.sleep(max(0.1, poll_interval))


def chapter_schema() -> dict[str, Any]:
    return {
        "name": "semantic_chapter",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "headline": {"type": "string"},
                "gist": {"type": "string"},
                "summary": {"type": "string"},
            },
            "required": ["headline", "gist", "summary"],
        },
        "strict": True,
    }


def read_paragraphs(transcript_id: str, key: str) -> list[dict[str, Any]]:
    response = json_request(f"{API_BASE}/transcript/{transcript_id}/paragraphs", key)
    paragraphs = response.get("paragraphs")
    if not isinstance(paragraphs, list) or not paragraphs:
        raise TranscriptionError("AssemblyAI returned no transcript paragraphs for chapter generation")
    if not all(isinstance(paragraph, dict) for paragraph in paragraphs):
        raise TranscriptionError("AssemblyAI returned malformed transcript paragraphs")
    return paragraphs


def chapter_metadata(text: str, key: str) -> dict[str, str]:
    payload = {
        "model": CHAPTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Create concise semantic metadata for this transcript section. "
                    "Return a headline, one-line gist, and a brief summary.\n\n"
                    f"Transcript section:\n{text}"
                ),
            }
        ],
        "max_tokens": 500,
        "response_format": {"type": "json_schema", "json_schema": chapter_schema()},
        "post_processing_steps": [{"type": "json-repair"}],
    }
    response = json_request(LLM_GATEWAY_URL, key, payload)
    try:
        content = response["choices"][0]["message"]["content"]
        metadata = json.loads(content)
    except (IndexError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise TranscriptionError("LLM Gateway returned an invalid structured chapter response") from error
    if not isinstance(metadata, dict) or not all(
        isinstance(metadata.get(field), str) and metadata[field].strip()
        for field in ("headline", "gist", "summary")
    ):
        raise TranscriptionError("LLM Gateway chapter response did not meet the required schema")
    return {field: metadata[field].strip() for field in ("headline", "gist", "summary")}


def semantic_chapters(transcript_id: str, key: str) -> list[dict[str, Any]]:
    paragraphs = read_paragraphs(transcript_id, key)
    chapters = []
    for index in range(0, len(paragraphs), PARAGRAPHS_PER_CHAPTER):
        group = paragraphs[index : index + PARAGRAPHS_PER_CHAPTER]
        start, end = group[0].get("start"), group[-1].get("end")
        text = " ".join(str(paragraph.get("text") or "").strip() for paragraph in group).strip()
        if not isinstance(start, int) or not isinstance(end, int) or end < start or not text:
            raise TranscriptionError("AssemblyAI returned a malformed paragraph boundary")
        chapters.append({"start": start, "end": end, **chapter_metadata(text, key)})
    return chapters


def is_gateway_model_access_error(error: TranscriptionError) -> bool:
    return "does not have access to this LLM Gateway model" in str(error)


def timestamp(milliseconds: Any) -> str:
    if not isinstance(milliseconds, (int, float)):
        return "unknown"
    hours, remainder = divmod(int(milliseconds), 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_markdown(path: Path, source: Path, result: dict[str, Any]) -> None:
    utterances = result.get("utterances") or []
    lines = [
        f"# {source.stem}",
        "",
        f"- Source: `{source.name}`",
        f"- AssemblyAI transcript ID: `{result.get('id', 'unknown')}`",
        "- Timestamp unit: milliseconds in JSON; displayed as `HH:MM:SS.mmm` below.",
        "",
        "## Transcript",
        "",
    ]
    if utterances:
        for utterance in utterances:
            lines.extend(
                [
                    f"### Speaker {utterance.get('speaker') or 'Unknown'} · "
                    f"{timestamp(utterance.get('start'))}–{timestamp(utterance.get('end'))}",
                    "",
                    str(utterance.get("text") or "").strip(),
                    "",
                ]
            )
    else:
        lines.extend([str(result.get("text") or "").strip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_package(
    media_path: Path,
    package_dir: Path,
    result: dict[str, Any],
    chapters: list[dict[str, Any]],
    chapter_source: str,
) -> list[Path]:
    words, utterances = result.get("words"), result.get("utterances")
    if not isinstance(words, list) or not isinstance(utterances, list):
        raise TranscriptionError("AssemblyAI completed without word timestamps or speaker labels")
    stem = media_path.stem
    common = {
        "schema_version": 1,
        "source_file": media_path.name,
        "transcript_id": result.get("id"),
        "timestamp_unit": "milliseconds",
    }
    paths = {
        "transcript": package_dir / f"{stem}.transcript.md",
        "words": package_dir / f"{stem}.words.json",
        "chapters": package_dir / f"{stem}.chapters.json",
        "speakers": package_dir / f"{stem}.speakers.json",
        "raw": package_dir / f"{stem}.assemblyai.json",
    }
    write_markdown(paths["transcript"], media_path, result)
    write_json(paths["words"], {**common, "words": words})
    write_json(paths["chapters"], {**common, "chapter_source": chapter_source, "chapters": chapters})
    write_json(paths["speakers"], {**common, "utterances": utterances})
    write_json(paths["raw"], result)
    return list(paths.values())


def main() -> int:
    args = parse_args()
    media_path = args.media_path.expanduser().resolve()
    if not media_path.is_file():
        raise TranscriptionError(f"Media path is not a file: {media_path}")
    package_dir = args.output_dir.expanduser().resolve() if args.output_dir else media_path.parent / "transcripts" / media_path.stem
    package_dir.mkdir(parents=True, exist_ok=True)
    api_key = read_api_key()
    upload_source = extract_audio(media_path, package_dir) if media_path.suffix.lower() in VIDEO_SUFFIXES else media_path
    upload_url = upload_media(upload_source, api_key)
    result = transcribe(upload_url, api_key, args.poll_interval)
    transcript_id = result.get("id")
    if not isinstance(transcript_id, str):
        raise TranscriptionError("Completed AssemblyAI response did not contain an id")
    try:
        chapters = semantic_chapters(transcript_id, api_key)
        chapter_source = "AssemblyAI LLM Gateway"
    except TranscriptionError as error:
        if not is_gateway_model_access_error(error):
            raise
        result = transcribe(upload_url, api_key, args.poll_interval, legacy_auto_chapters=True)
        chapters = result.get("chapters")
        if not isinstance(chapters, list) or not chapters:
            raise TranscriptionError("Legacy Auto Chapters fallback completed without chapters")
        chapter_source = "AssemblyAI legacy Auto Chapters fallback (Universal-2)"
    print("Created transcription package:")
    for path in write_package(media_path, package_dir, result, chapters, chapter_source):
        print(path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TranscriptionError as error:
        print(f"media-transcription: {error}", file=sys.stderr)
        raise SystemExit(1)
