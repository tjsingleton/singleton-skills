# OpenRouter Images API

Verified 2026-09-15 against [OpenRouter's image-generation guide](https://openrouter.ai/docs/guides/overview/multimodal/image-generation) and the public model-endpoints API.

## Request

`POST https://openrouter.ai/api/v1/images`

Headers:

```text
Authorization: Bearer $OPENROUTER_API_KEY
Content-Type: application/json
```

Minimum JSON body:

```json
{
  "model": "openai/gpt-image-2.5-sunburst",
  "prompt": "A green gateway at sunrise"
}
```

The selected model currently accepts `aspect_ratio`, `background`,
`input_references`, `n`, `output_compression`, and `quality`. Check
`GET /api/v1/images/models/<model>/endpoints` before sending another field:
model capabilities and prices can differ by provider endpoint.

For image editing, send references as URLs or data URLs:

```json
{
  "model": "openai/gpt-image-2.5-sunburst",
  "prompt": "Make this watercolor.",
  "input_references": [
    {
      "type": "image_url",
      "image_url": { "url": "https://example.com/source.png" }
    }
  ]
}
```

## Response

The non-streaming response contains base64 image bytes. `media_type` tells the
client which extension to use. The `usage.cost` value is the final billed USD
cost for the completed request when present.

```json
{
  "created": 1748372400,
  "data": [
    {
      "b64_json": "<base64-image-bytes>",
      "media_type": "image/png"
    }
  ],
  "usage": {
    "cost": 0.04
  }
}
```

Image generations are billed as completed outputs; the response cost is more
reliable than a preflight estimate because output tokens depend on the request.
