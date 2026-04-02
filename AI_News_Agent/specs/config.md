# Config Schema

`config.json` is the user-facing configuration file and the persistence store for learned preferences. It is loaded at startup and validated into a typed structure before use.

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
    "mit-technology-review",
    "the-wall-street-journal",
    "ars-technica"
  ],

  "other_domains": [
    "anthropic.com",
    "deepmind.google",
    "openai.com",
    "blog.google",
    "meta.ai",
    "hbr.org"
  ],

  "keyword_weights": {
    "positive": {},
    "negative": {}
  },

  "delivery": {
    "file": {
      "enabled": true,
      "path": "report.md"
    },
    "gmail": {
      "enabled": false,
      "recipient": "you@example.com"
    },
    "smtp": {
      "enabled": false,
      "host": "smtp.example.com",
      "port": 587,
      "username": "you@example.com",
      "recipient": "you@example.com"
    },
    "slack": {
      "enabled": false
    },
    "webhook": {
      "enabled": false,
      "url": "https://example.com/hook"
    }
  },

  "summarization": {
    "model": "claude-haiku-4-5-20251001",
    "max_chars": 8000
  },

  "days": 7
}
```

## Field Reference

### `search_topics`
Ordered list of topics to search. Order reflects user preference — higher-rated topics appear first (managed by the feedback loop). At least one topic is required.

### `preferred_sources`
List of **NewsAPI source IDs** (not domain names). Find valid IDs at `https://newsapi.org/v2/sources`. These are queried as the `sources` parameter for high-trust results.

### `other_domains`
List of domain names to include in the broader query string. These supplement the official sources with content from sites not indexed as NewsAPI publishers (e.g., `anthropic.com`).

### `keyword_weights`
Managed by the feedback loop — do not edit manually unless you understand the effect. Both `positive` and `negative` are `{keyword: int}` maps. Weights are cumulative across runs.

### `delivery`
At least one delivery adapter must be enabled. `file` is recommended as the always-on baseline. Adapter-specific secrets (passwords, API keys) are read from environment variables, not stored here.

### `summarization`
Controls the LLM used for article summarization. `model` must be a valid Anthropic model ID. `max_chars` limits input text length to avoid token overflow.

### `days`
How many days back to search for articles. Default: 7.

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `NEWS_API_KEY` | Yes | NewsAPI authentication |
| `ANTHROPIC_API_KEY` | Yes (if summarization enabled) | Claude API |
| `GMAIL_SMTP_PASSWORD` | Yes (if smtp delivery enabled) | SMTP auth |
| `SLACK_WEBHOOK_URL` | Yes (if slack delivery enabled) | Slack incoming webhook |

OAuth credentials for Gmail delivery are file-based (`credentials.json`, `token.json`) and not environment variables.

## Validation Rules

- `search_topics` must be non-empty.
- `preferred_sources` entries must match the pattern `[a-z0-9-]+` (NewsAPI source ID format).
- At least one delivery adapter must have `enabled: true`.
- `days` must be between 1 and 30 (NewsAPI free tier limit).
- `summarization.max_chars` must be > 0.
