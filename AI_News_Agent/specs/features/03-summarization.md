# Feature: Summarization

## Purpose

Produce a concise, useful summary of each article's full text using an LLM, replacing the current placeholder stub.

## Current State

`process_article()` returns a hardcoded placeholder:
```python
summary = f"Placeholder summary for: {article.title}\n(Full text has been extracted and is ready for summarization)"
```

The full article `text` is already extracted and available. This feature is the primary unimplemented gap in the system.

## Required Behavior

- Given a `title` and `text`, call an LLM and return a 2–4 sentence summary.
- The summary should capture: what happened, why it matters, and any notable names/organizations.
- If `text` is empty (paywall, parse failure), return a graceful fallback: `"Full article text unavailable."` — do not call the LLM with empty content.
- Summaries run per-article, parallelized within the existing `ThreadPoolExecutor` in `process_and_summarize_articles()`.

## LLM Integration

**Recommended**: Anthropic Claude API (`claude-haiku-4-5-20251001` for cost efficiency at scale).

Suggested prompt template:
```
You are a professional news analyst. Summarize the following article in 2-4 sentences.
Focus on what happened, why it matters, and any key organizations or people involved.
Be concise and factual.

Title: {title}

Article:
{text[:8000]}
```

- Truncate `text` to avoid token limit issues (8000 chars is a safe default).
- Use the `ANTHROPIC_API_KEY` environment variable for auth.
- Surface API errors gracefully — fall back to `"Summary unavailable."` rather than crashing.

## Config

No user-facing config needed for the initial implementation. Optionally add:
```json
{
  "summarization": {
    "model": "claude-haiku-4-5-20251001",
    "max_chars": 8000
  }
}
```

## Open Questions

- Should summaries be cached to avoid re-summarizing the same URL on re-runs?
- Should the user be able to configure the tone/length of summaries?
