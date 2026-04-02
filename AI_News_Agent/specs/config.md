# Config

## Config Is Optional

The tool works without a config file. The minimum viable invocation is:

```
$ export NEWS_API_KEY=...
$ uv run brief "Agentic Engineering"
```

Config unlocks: persistent topics, keyword weights, LLM summarization, delivery channels, source preferences. CLI args always override config equivalents for the current run.

## `brief init`

Interactive scaffold using `rich` prompts. Walks the user through topics, sources, summarization, and delivery. Writes `config.json` to the project directory. See `features/05-cli.md` for the full flow.

## Full Schema

```json
{
  "search_topics": [
    "Agentic Engineering",
    "Context Engineering",
    "Generative AI",
    "Machine Learning"
  ],

  "preferred_sources": [
    "techcrunch",
    "wired",
    "ars-technica"
  ],

  "other_domains": [
    "anthropic.com",
    "deepmind.google",
    "openai.com",
    "hbr.org"
  ],

  "days": 7,

  "keyword_weights": {
    "positive": {},
    "negative": {}
  },

  "summarization": {
    "provider": "anthropic",
    "model": "claude-haiku-4-5-20251001"
  },

  "delivery": {
    "file": {
      "path": "report.md"
    },
    "gmail": {
      "enabled": false,
      "recipient": "you@example.com"
    },
  }
}
```

## Field Reference

### `search_topics`
Ordered list of search topics. Re-ordered by the feedback loop (highest-rated first). Required in config; overridden by CLI positional args.

### `preferred_sources`
NewsAPI **source IDs** — not domain names. Look up valid IDs at `newsapi.org/v2/sources`. Passed to the `sources=` parameter. Can be empty `[]` or omitted.

> Common ones: `"techcrunch"`, `"wired"`, `"ars-technica"`, `"the-verge"`, `"bloomberg"`, `"reuters"`, `"the-washington-post"`

### `other_domains`
Domain names for broader coverage. Passed to the `domains=` parameter of NewsAPI. Can be empty `[]` or omitted.

### `days`
How many days back to search. Default: `7`. Max: `30` (NewsAPI free tier lookback limit). Overridden by `--days` CLI flag.

### `keyword_weights`
Managed by the feedback loop. Do not edit manually. Both fields start as `{}`. Omitted from `brief init` output — created automatically on first feedback application.

### `summarization`
Omit this section entirely to use PassthroughSummarizer (the default). Only needed when enabling LLM summarization.

- `provider`: `"anthropic"`, `"openai"`, or `"vertex"`.
- `model`: Provider-specific model ID. Each provider has a sensible default if omitted.

Overridden by `--summarize` CLI flag (uses the configured provider, or errors if none configured and no env var detected).

### `delivery`
Omit entirely for stdout-only output. Add sections to enable additional channels.

- `file.path`: Where to write the Markdown report. Activated by this config key or `--output` CLI flag.
- `gmail.enabled`: Requires `credentials.json` in the project directory. Activated by this config key or `--deliver gmail`.
## Environment Variables

| Variable | Required For |
|----------|-------------|
| `NEWS_API_KEY` | Always (news gathering) |
| `ANTHROPIC_API_KEY` | `summarization.provider = "anthropic"` |
| `OPENAI_API_KEY` | `summarization.provider = "openai"` |

Vertex AI uses Application Default Credentials (`gcloud auth application-default login`), not an env var.

Gmail uses file-based OAuth (`credentials.json` → `token.json`), not env vars.

## Validation Rules

Checked at startup by `config.py` (only when config file is present):
- `search_topics` is a non-empty list of strings (unless overridden by CLI args).
- `days` is an integer between 1 and 30.
- `summarization.provider` is one of the known values.
- If a summarization provider is configured, its required credentials are available (env var or ADC).
- If Gmail delivery is enabled, its required credentials exist. Warn if missing — don't block the run (stdout still works).

When no config file exists, only `NEWS_API_KEY` and at least one CLI topic are validated.

## CLI Override Precedence

```
CLI args > config.json > defaults
```

| Setting | CLI | Config | Default |
|---------|-----|--------|---------|
| Topics | positional args | `search_topics` | (required from one source) |
| Days | `--days` | `days` | 7 |
| Summarizer | `--summarize` | `summarization.provider` | passthrough |
| File output | `--output PATH` | `delivery.file.path` | off |
| Email | `--deliver gmail` | `delivery.gmail.enabled` | off |

| Stdout | (always on) | — | on |
