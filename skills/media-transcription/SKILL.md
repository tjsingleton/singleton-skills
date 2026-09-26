---
name: media-transcription
description: >
  Transcribe a local audio or video file with AssemblyAI when the user asks for a
  transcript, captions, chapters, speaker labels, or to make media searchable.
  Produces a consistent local package for editing and research. Do not use for
  live meeting transcription, summarizing an existing transcript, or media hosted only at a URL.
argument-hint: "<media-path> [--output-dir <directory>]"
license: MIT
---

# Media transcription

> **Quick usage:**
> ```
> media-transcription "/path/to/interview.mp3"
> media-transcription "/path/to/recording.mov"
> media-transcription "/path/to/talk.wav" --output-dir "/path/to/output"
> ```

Use this skill whenever the user provides a local media file and asks for a transcript,
captions, chapters, speaker labels, or asks to make it searchable.

## Inputs and setup

1. Accept one existing local audio or video file path. If no path is supplied, ask for it and stop.
2. Read `ASSEMBLYAI_API_KEY` from `~/.secrets`. The file may use either
   `ASSEMBLYAI_API_KEY=value` or `export ASSEMBLYAI_API_KEY=value`. Never print,
   commit, or copy its value into an artifact.
3. Save the package beside the media by default:

   ```text
   <media-parent>/transcripts/<media-stem>/
   ```

   The caller may override this with `--output-dir`.

## Workflow

1. Validate the media path and configured key without revealing sensitive content or credentials.
2. For video (`.mov`, `.mp4`, `.m4v`, `.mkv`, `.webm`, `.avi`, `.wmv`, or `.flv`),
   extract audio before upload:

   ```bash
   ffmpeg -y -i <video> -vn -c:a libmp3lame -q:a 2 <package>/<stem>.source-audio.mp3
   ```

   Keep the extracted file in the package so the remote input is reproducible. Upload audio directly.
3. Run the bundled script:

   ```bash
   python3 <skill-directory>/scripts/transcribe_media.py <media-path>
   ```

4. The script uploads selected audio to `POST /v2/upload`, submits `POST /v2/transcript`,
   and polls `GET /v2/transcript/<id>`. Its current transcription request shape is:

   ```json
   {
     "audio_url": "<AssemblyAI upload URL>",
     "speech_models": ["universal-3-5-pro"],
     "speaker_labels": true,
     "format_text": true,
     "punctuate": true
   }
   ```

   `speech_models` is the current field; singular `speech_model` is deprecated.
   The script intentionally omits the deprecated `auto_chapters` field. It retrieves
   `GET /v2/transcript/<id>/paragraphs`, groups adjacent paragraphs in pairs, and calls
   AssemblyAI LLM Gateway (`POST /v1/chat/completions`, currently
   `claude-sonnet-4-6`) with a strict JSON schema for
   `headline`, `gist`, and `summary`. It preserves paragraph `start` and `end` values.
5. Inspect all four standard artifacts before reporting success. A failed transcript,
   paragraph retrieval, or LLM Gateway schema result makes the package incomplete.
   If the key explicitly lacks LLM Gateway model access, the script re-transcribes the
   uploaded audio with legacy Universal-2 Auto Chapters and records that fallback in
   `chapter_source` in the chapters JSON. It does not use that fallback for other
   LLM Gateway or schema failures.

## Standard output package

For a media stem `meeting`, the package contains:

```text
meeting.transcript.md       # readable transcript; speaker turns and millisecond ranges
meeting.words.json          # word-level timestamps; millisecond unit declared
meeting.chapters.json       # AssemblyAI LLM Gateway semantic chapter metadata; millisecond ranges
meeting.speakers.json       # diarized utterances and speaker labels
meeting.assemblyai.json     # complete raw completed response for provenance
```

All JSON files retain AssemblyAI's millisecond timestamps. The Markdown file uses the same
speaker turns as `meeting.speakers.json`.

These names and schemas are an interface: editing and research skills consume these artifacts.
Keep the package shape consistent, and make future schema changes across downstream consumers.

## Failure handling

- A missing or unreadable `~/.secrets` entry is a setup error; state the variable name without revealing a value.
- A missing `ffmpeg` is a setup error for video; do not upload video as though it were audio.
- A non-`completed` response, API error, paragraph failure, or invalid LLM chapter result is an incomplete package.
- Local media is uploaded to AssemblyAI. Confirm with the user before processing sensitive media when transfer was not already authorized.
