# Current-info-search provider research

Research date: 2026-09-26 (America/New_York)

## Direct answer

For a new, durable current-information skill, prefer Perplexity's Agent API
with its `low` preset. Perplexity recommends the Agent API for all new projects
and says its legacy Sonar Chat Completions API is supported only through
2026-09-27. The Agent API retains web grounding and citations, but adds a
Responses-style contract, presets, multi-step tools, and more provider choices.

Use the legacy Sonar Chat Completions endpoint only as a short-lived fallback
when an existing harness specifically requires it. Do not make `sonar-pro` the
new skill's default: it has a one-day published support horizon as of this
research date.

OpenRouter is a useful alternative integration lane. Its server-side
`openrouter:web_search` tool can give any listed model current web information;
the `perplexity` search engine is available through that tool. The server tool
replaces OpenRouter's deprecated web-search plugin and `:online` model suffix.

## Official Perplexity evidence

- [Migrate from Sonar to the Agent API](https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/overview)
  says Sonar Chat Completions is now Agent API, remains supported through
  **2026-09-27**, and recommends the Agent API for new projects. It maps
  `sonar-pro` to the Agent API `low` preset for everyday current-information
  research and light multi-step lookups.
- [How to migrate from Sonar](https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/how-to)
  documents the contract change: Sonar uses `POST /v1/sonar`, `messages`, and
  `choices`; Agent API uses `POST /v1/agent`, `input`, and typed `output`
  items. For OpenAI SDK compatibility, Perplexity also accepts `POST
  /v1/responses`.
- [Agent API quickstart](https://docs.perplexity.ai/docs/agent-api/quickstart)
  documents `PERPLEXITY_API_KEY`, the `POST /v1/agent` endpoint, built-in
  `web_search`, and source-bearing search-result output.
- [Pricing](https://docs.perplexity.ai/docs/getting-started/pricing) lists
  `web_search` at $0.0025 per standard invocation or $0.001 for Fast Search,
  plus selected-model token costs. These are separate costs.

### Perplexity choice tradeoffs

| Choice | Best use | Tradeoff |
| --- | --- | --- |
| Agent API `low` preset | Default for everyday, current-information questions | New Responses-style API, so a harness that only supports chat completions needs a small adapter. |
| Agent API `fast` preset | Simple, latency- and cost-sensitive current fact lookups | Less room for multi-step evidence gathering than `low`. |
| Agent API `medium`/`high` | Multi-hop research or exhaustive claims | More time and model/tool spend; inappropriate as a default. |
| Legacy `sonar-pro` | Existing Sonar chat-completions clients during the transition | Legacy; Perplexity publishes support only through 2026-09-27. |

## OpenRouter catalog snapshot

An authenticated request to `GET https://openrouter.ai/api/v1/models` produced
the catalog snapshot below. No credential values, account metadata, or
completions were printed or saved. At 2026-09-26, the endpoint returned **458**
catalog entries and these five Perplexity IDs.

Prices below are catalog values converted from dollars per token to dollars per
1M tokens. Context/output limits and supported parameters are direct catalog
metadata and can change without a repository change.

| Model ID | Context | Max output | Input / output ($/1M) | Relevant capability / tradeoff |
| --- | ---: | ---: | ---: | --- |
| `perplexity/sonar` | 127,072 | 114,364 | $1 / $1 | Cheapest, lightweight current Q&A; best only when answer quality and source synthesis are simple. |
| `perplexity/sonar-pro` | 200,000 | 8,000 | $3 / $15 | Higher-cost in-depth multi-step Sonar option, but inherits Sonar's legacy-migration risk. |
| `perplexity/sonar-pro-search` | 200,000 | 8,000 | $3 / $15 | Catalog describes it as OpenRouter-exclusive, deeper agentic Pro Search; supports `web_search_options`, reasoning, and structured outputs. A strong OpenRouter-specific quality option, not a durable direct-Perplexity default. |
| `perplexity/sonar-reasoning-pro` | 128,000 | 115,200 | $2 / $8 | Reasoning-focused; supports reasoning and `web_search_options`. Use when the task genuinely needs multi-step analysis, not short factual refreshes. |
| `perplexity/sonar-deep-research` | 128,000 | 115,200 | $2 / $8 | Research-focused multi-step retrieval and synthesis. Reserve for deliberate deep research; its output allowance and likely search work make it excessive for a routine skill invocation. |

The catalog's displayed `web_search_options` parameter on all five indicates
the relevant request surface, but catalog visibility is **not** proof that a
model can complete a billable request right now. A model can still be affected
by account credit/limits, provider availability, runtime routing, or a changed
model policy. No completion was sent in this research. A later, explicitly
authorized minimal request is the appropriate callable verification.

The catalog endpoint itself is platform-wide model metadata, while OpenRouter's
documented user-filtered listing operation additionally applies provider
preferences, privacy settings, and guardrails. Treat that filtering, plus a
successful completion, as stronger evidence for a particular account's
effective access.

## Official OpenRouter evidence

- [Models API: list all models](https://openrouter.ai/docs/api/api-reference/models/get-models)
  documents `GET /api/v1/models`, bearer authentication, the model metadata
  schema (including context length, pricing, capabilities, and supported
  parameters), and catalog filters.
- [OpenRouter TypeScript Models API](https://openrouter.ai/docs/client-sdks/typescript/api-reference/models/models)
  distinguishes ordinary model listing from `listForUser`, which filters by a
  user's provider preferences, privacy settings, and guardrails.
- [Web Search server tool](https://openrouter.ai/docs/guides/features/server-tools/web-search)
  documents `openrouter:web_search` for current web information with any
  model, the `perplexity` search engine, citations, and its beta status. It
  says the older web plugin and `:online` variant are deprecated.
- [OpenRouter quickstart](https://openrouter.ai/docs/quickstart) documents the
  OpenAI-compatible `POST /api/v1/chat/completions` surface and the
  `OPENROUTER_API_KEY` credential variable.

### OpenRouter recommendation

If the skill needs an OpenRouter route, default to a stable model with
`openrouter:web_search` explicitly attached, rather than relying on a stale
model's background knowledge or the deprecated `:online` suffix. Pin a concrete
model ID for reproducibility; do not use an auto/latest alias for a skill whose
behavior must be auditable. For current-info quality, use the server tool's
`engine: "perplexity"` where a Perplexity-style ranked-source search is wanted,
and preserve the returned source URLs and dates in the final answer.

## Credential boundary

The public repository must never contain a credential file, any value from one,
or a copied credential. Examples should read credentials at runtime from a
user-designated environment source.

## Reusable takeaway

Choose Perplexity Agent API `low` for the skill's default direct provider, not
legacy `sonar-pro`. Keep an OpenRouter route as an optional alternative that
attaches `openrouter:web_search`; the authenticated catalog confirms the five
listed Perplexity IDs are visible, but not that each is presently callable for
the account.

## Provider tradeoffs and zero-data retention

This comparison is directional rather than a claim that one provider is always
cheaper: their units differ (tokens plus searches, search requests, or
page-processing credits), and output depth materially changes cost.

| Provider | Better fit than direct Perplexity `low` when | Cost and ZDR boundary |
| --- | --- | --- |
| Perplexity Agent API | The task needs a concise, grounded answer with cited current sources, rather than raw pages or a custom retrieval pipeline. | Pricing combines model tokens and web-search use. The published ZDR statement specifically covers legacy Chat Completions content, not the Agent API; do not extend that claim without current confirmation. |
| Firecrawl | The task needs page-level extraction, crawling, rendering, interaction, or structured content from specified sites. | Its free plan includes 1,000 monthly credits; search costs 2 credits per 10 results and scraping costs 1 credit per page. ZDR adds 1 credit per page and is an enterprise feature. |
| Exa | The task needs a search-first retrieval API, result controls, or an MCP/connector lane. | Its free plan advertises $10 monthly credits plus a $10 onboarding bonus. Base search is listed at $7 per 1,000 requests; its pricing page lists ZDR under Enterprise. |
| OpenRouter | The task needs a provider-neutral inference route or enforceable model-endpoint ZDR routing. | The catalog snapshot contained 458 models, but visibility does not prove a completion will route. `provider.zdr: true` constrains inference routing only; enabled web-search tools have their own retention policies. |

### Primary-source evidence for this comparison

- [Perplexity privacy and security](https://docs.perplexity.ai/docs/resources/privacy-security)
  says its Chat Completions API keeps no prompt or response content and retains
  only listed billing metadata.
- [Firecrawl billing](https://docs.firecrawl.dev/billing) lists the free-plan
  allowance, endpoint credit costs, and the ZDR surcharge; [Enterprise
  features](https://docs.firecrawl.dev/enterprise) identifies ZDR as an
  enterprise capability.
- [Exa pricing](https://exa.ai/pricing) lists the free credits, base request
  prices, and Enterprise ZDR; [Exa's ZDR announcement](https://exa.ai/blog/zdr-search-engine)
  says it covers search, answer, and deep research.
- [OpenRouter ZDR](https://openrouter.ai/docs/guides/features/zdr) documents
  per-request enforcement and the boundary between inference routing and
  third-party tools such as web search.
