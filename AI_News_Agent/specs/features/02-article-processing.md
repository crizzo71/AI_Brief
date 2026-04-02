# Feature: Article Processing & Summarization

## What It Does

For each URL: download the full article text, pass it to the configured summarizer, return an `Article`. Runs in parallel.

## Fetch

Uses `newspaper3k` to download and parse each URL. On failure (network error, paywall, parse error), return a sentinel `Article` with empty `title` and `text`. Articles with empty titles are excluded from the report.

`Article.text` is held in memory only — used for summarization and feedback keyword extraction, never written to disk.

## Summarize

The `Summarizer` protocol:

```python
class Summarizer(Protocol):
    def summarize(self, title: str, text: str, snippet: str = "") -> str: ...
```

`snippet` is the short description returned by NewsAPI alongside the URL. It is captured during news gathering and stored on `Article`. It gives the summarizer a fallback when full text is unavailable (paywall, parse failure).

### ClaudeSummarizer

Calls the Anthropic API. Requires `ANTHROPIC_API_KEY` env var.

Prompt:
```
Summarize the following article in 2-4 sentences.
Focus on what happened, why it matters, and any key organizations or people involved.
Be concise and factual.

Title: {title}

Article:
{text[:8000]}
```

- Truncate input to 8000 characters to stay within token limits.
- If `text` is empty but `snippet` is present, summarize the snippet instead (still a valid LLM call).
- If both `text` and `snippet` are empty, return `"Full article text unavailable."` without calling the API.
- If the API call fails, log the error and return `"Summary unavailable."`.
- Model: configurable via `config.summarization.model` (default: `claude-haiku-4-5-20251001`).

### PassthroughSummarizer

Returns the NewsAPI snippet if present, otherwise the title. Zero-dependency fallback — useful for testing the rest of the pipeline without an API key.

## Concurrency

Both fetch and summarize happen inside the same `ThreadPoolExecutor` per article. Summarizer implementations must be safe to call from multiple threads (stateless, no shared mutable state).
