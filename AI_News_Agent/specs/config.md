# Config Schema

`config.json` is loaded and validated at startup by `config.py`. Invalid or missing required fields exit immediately with a clear error message.

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
    "provider": "claude",
    "model": "claude-haiku-4-5-20251001"
  },

  "delivery": {
    "gmail": {
      "enabled": false,
      "recipient": "you@example.com"
    },
    "smtp": {
      "enabled": false,
      "recipient": "you@example.com"
    }
  }
}
```

## Field Reference

### `search_topics`
Ordered list of search topics. Topics are re-ordered by the feedback loop (highest-rated first). Required; must be non-empty.

### `preferred_sources`
NewsAPI **source IDs** — not domain names. Look up valid IDs at `newsapi.org/v2/sources`. Passed to the `sources=` parameter. Can be empty `[]`.

> Common ones: `"techcrunch"`, `"wired"`, `"ars-technica"`, `"the-verge"`, `"bloomberg"`, `"reuters"`, `"the-washington-post"`

### `other_domains`
Domain names for broader coverage. Passed to the `domains=` parameter of NewsAPI (not embedded in the query string). Can be empty `[]`.

### `days`
How many days back to search. Default: `7`. Max: `30` (NewsAPI free tier lookback limit).

### `keyword_weights`
Managed by the feedback loop. Do not edit manually. Both fields start as `{}`.

### `summarization`
- `provider`: `"claude"` or `"passthrough"`. If `"claude"`, requires `ANTHROPIC_API_KEY` env var.
- `model`: Any valid Anthropic model ID.

### `delivery`
File delivery is always on (no config needed). Add `gmail` or `smtp` blocks to enable additional channels. At least `FileChannel` will always run.

- `gmail.enabled`: Requires `credentials.json` in the project directory.
- `smtp.enabled`: Requires env vars `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`.

## Environment Variables

| Variable | Required For |
|----------|-------------|
| `NEWS_API_KEY` | Always (news gathering) |
| `ANTHROPIC_API_KEY` | `summarization.provider = "claude"` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` | SMTP delivery |

Gmail credentials are file-based (`credentials.json`), not env vars.

## Validation Rules

Checked at startup by `config.py`:
- `search_topics` is a non-empty list of strings.
- `days` is an integer between 1 and 30.
- `summarization.provider` is one of the known values.
- `NEWS_API_KEY` env var is set.
- If `summarization.provider == "claude"`, `ANTHROPIC_API_KEY` is set.
- If any delivery channel is `enabled: true`, its required credentials exist (warn, not error — fallback to file).
