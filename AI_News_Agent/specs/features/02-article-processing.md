# Feature: Article Processing

## Purpose

Download the full text of each discovered article URL so the agent has real content to summarize — not just the headline/snippet returned by NewsAPI.

## Behavior

- For each URL returned by news gathering, download and parse the article using `newspaper3k`.
- Run all article downloads in parallel (`ThreadPoolExecutor(max_workers=5)`).
- On failure (network error, paywalled, parse failure), emit a warning and return a sentinel result rather than crashing.

## Output Per Article

```python
{
    "url": str,       # original URL
    "title": str,     # extracted article title
    "text": str,      # full body text (used by summarization and feedback loop)
    "summary": str,   # produced by summarization step (see feature 03)
}
```

Articles that fail to download return `title: ""` and `text: ""` with a placeholder summary. The report generator skips items with empty titles.

## Failure Handling

- Catch `ArticleException` and generic `Exception` — log the URL and error, return the sentinel.
- Do not propagate exceptions to the thread pool — a single bad URL should not block others.

## Notes

- `newspaper3k` handles encoding, HTML cleaning, and boilerplate removal automatically.
- Full `text` is stored in the in-memory result dict and passed to the feedback loop but **not** persisted to disk (intentionally excluded from `ratings.json` due to size).
- Paywalled articles will produce empty or near-empty `text`. The summarizer should handle this gracefully.
