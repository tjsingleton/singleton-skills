# AssemblyAI Auto Chapters replacement

Research date: 2026-09-26 (America/New_York)

## Direct answer

Do not send `auto_chapters` when using `universal-3-5-pro`. AssemblyAI marks
the parameter deprecated and says it is supported only by Universal-2. Its
documented replacement is **LLM Gateway**: retrieve transcript paragraphs,
group them, then ask an LLM for a headline, gist, and summary for each group.

AssemblyAI's published reason is product-level, not a technical explanation of
Universal-3.5 Pro: LLM Gateway gives "full control" over how chapters are
created and summarized and is "more flexible and powerful." The docs do not
state that Universal-3.5 Pro cannot technically create chapters, nor do they
describe a model-architecture reason for the incompatibility. Treat any more
specific explanation as unsupported.

## What replaced it

The current Auto Chapters guide prescribes this pipeline:

1. Transcribe the media.
2. Fetch `GET /v2/transcript/{id}/paragraphs` after completion.
3. Group consecutive paragraphs; the guide's example uses a configurable
   fixed group size (`step = 2`) and retains the first group's `start` and last
   group's `end` timestamps.
4. Submit each group to `https://llm-gateway.assemblyai.com/v1/chat/completions`
   for a headline, gist, and summary.

AssemblyAI explicitly recommends Structured Outputs (or a JSON-only prompt)
when structured chapter data is needed. Structured Outputs supports a JSON
Schema response format, including strict schemas and a JSON-repair
post-processing option.

## Can it satisfy `media-transcription`'s semantic chapter artifact?

**Yes, for a stable structured chapter artifact.** The replacement can return
validated JSON such as:

```json
{
  "start_ms": 0,
  "end_ms": 60000,
  "headline": "...",
  "gist": "...",
  "summary": "..."
}
```

The script must supply `start_ms` and `end_ms` from paragraph boundaries and
validate the model's structured fields. Store the resulting array in the
skill's consistently named semantic-chapters JSON artifact.

**Important limitation:** AssemblyAI's replacement example groups *adjacent
paragraphs by a caller-selected fixed count*. It generates semantic metadata
for those time-bounded groups, but the first-party docs do not promise that it
will discover optimal semantic boundary changes across the whole recording.
Call the output “semantic chapters” only in the sense that the chapter title,
gist, and summary are semantic. If adaptive topic-boundary detection is a hard
requirement, that needs an additional design and evaluation pass.

## Practical recommendation for `skills/media-transcription`

- Use `speech_model: "universal-3-5-pro"` for the transcript path, with
  speaker labels and word timestamps as required by the package.
- Omit deprecated `auto_chapters`; do not downgrade to Universal-2 merely to
  obtain the legacy feature.
- Treat LLM Gateway chapter generation as a separate, required post-
  transcription stage. Request a strict JSON schema, retain the paragraph
  timing verbatim, validate every chapter (`end_ms >= start_ms`), and write the
  exact same chapter filename on every run.
- The LLM Gateway call is an additional model request. Its current model name,
  availability, billing, and data-handling terms should be verified when the
  implementation is finalized; the Auto Chapters page currently illustrates
  `claude-sonnet-4-6`, but that example is not a permanence guarantee.

## Official AssemblyAI evidence

- [Transcribe audio API reference](https://www.assemblyai.com/docs/pre-recorded-audio/api-reference/transcripts/submit) — marks `auto_chapters` deprecated, directs users to LLM Gateway, and says the parameter is only supported for Universal-2.
- [Auto Chapters](https://www.assemblyai.com/docs/speech-understanding/auto-chapters) — calls LLM Gateway the replacement; documents the paragraph-grouping workflow, timestamp retention, configurable group size, and headline/gist/summary output.
- [Structured Outputs](https://www.assemblyai.com/docs/llm-gateway/structured-outputs) — documents `response_format.type: "json_schema"`, strict schemas, JSON repair, and the need to validate parsed JSON.
