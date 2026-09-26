---
name: image-gateway
description: >
  Generate or edit a bitmap image through OpenRouter when the user requests an image or another skill needs an image asset. Use the saved image model, output directory, and env-file key location. Other skills invoke this gateway instead of adding image API code. Do not use for vector/code-native visuals or non-image tasks.
argument-hint: '"<prompt>" [--reference path-or-url] [--aspect-ratio ratio] [--quality level]'
license: MIT
---

# image-gateway

> **Quick usage:**
> ```
> image-gateway "A sunlit reading nook with a green armchair"
> image-gateway "Turn this into a watercolor" --reference ./photo.png
> image-gateway "Wide product hero" --aspect-ratio 16:9 --quality high
> ```

Generate or edit images with the saved defaults in `preferences.json`. Run the
single gateway command; do not create new OpenRouter image clients in this or
another skill.

## When to use it

Use this skill for a direct request to generate, draw, render, create, edit,
retouch, restyle, or make an image. A skill that needs a raster asset—such as a
mockup, illustration, texture, thumbnail, or product image—calls this skill and
passes its final prompt plus any references. This is the shared OpenRouter image
boundary for Codex, Claude Code, and Cursor.

Use an SVG/editor/code workflow for a code-native vector, existing icon system,
or layout that should remain editable as source.

## Saved preferences

Read `preferences.json` before running. These are the user's defaults; accept
explicit per-request flags only when the request calls for a deviation.

| Setting | Saved value |
| --- | --- |
| Model | `openai/gpt-image-2.5-sunburst` |
| Quality | `auto` |
| Output directory | `~/Pictures/image-gateway/` |
| API-key env file | `~/.secrets` |

The key file must remain outside this skill and Git. The gateway reads only
`OPENROUTER_API_KEY` from that file at runtime and never prints it. It accepts
both .env assignments and shell-style `export OPENROUTER_API_KEY=...` lines.

## Run the gateway

From this skill directory:

```bash
python3 scripts/image_gateway.py "A clean editorial illustration of a gateway at sunrise"
```

For an edit, pass one or more local image paths, HTTPS URLs, or data URLs with
`--reference`. Local paths are encoded as data URLs only for the request; they
are not copied into the skill.

The command prints each saved file, the OpenRouter request cost when returned,
and an average per returned image. Report that result to the user and show the
saved image when the host supports it.

If OpenRouter reports that account-level Zero Data Retention excludes every
endpoint, stop rather than retrying. Ask the user to select a ZDR-compatible
model or change the account privacy guardrail; that setting is outside this
skill's authority.

## OpenRouter Images API

The gateway sends `POST https://openrouter.ai/api/v1/images` with
`Authorization: Bearer <key>` and a JSON object containing `model` and
`prompt`. Optional current fields include `n`, `aspect_ratio`, `quality`,
`background`, and `input_references` for edits. `input_references` items use
the form `{"type":"image_url","image_url":{"url":"https://..."}}`; URLs
may also be base64 data URLs. The buffered response contains `data[]` entries
with `b64_json` and (when identifiable) `media_type`, plus `usage.cost` when
available. Read [the API reference](references/openrouter-images-api.md) before
adding an unsupported parameter or changing the request shape.

## Cost

The default model is the precision tier of OpenAI's current GPT Image 2.5
series. OpenRouter bills it by tokens, not a fixed price per image: text input
is currently $5/M tokens, image input $8/M tokens, and image output $30/M
tokens. Therefore, treat the returned `usage.cost` as authoritative; with
multiple outputs, the gateway also prints the request total divided by the
number of saved images as a useful average. Verify prices and endpoint support
through OpenRouter's model-endpoints API before changing this note.

## Curl equivalent

The script is the preferred one-command interface. This equivalent reads the
key from the saved env file without embedding it in the skill:

```bash
set -a
. "$HOME/.secrets"
set +a
curl --fail --silent --show-error https://openrouter.ai/api/v1/images \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H 'Content-Type: application/json' \
  --data '{"model":"openai/gpt-image-2.5-sunburst","prompt":"A green gateway at sunrise","quality":"auto","n":1}'
```

Do not save the response or key in a public repository. Decode `data[].b64_json`
using its returned `media_type` when using curl directly; the gateway does this
and selects the filename extension automatically.
