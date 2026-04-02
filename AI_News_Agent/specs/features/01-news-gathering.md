# Feature: News Gathering

## Purpose

Discover recent, relevant articles across the user's configured topics, filtered and ranked by learned keyword preferences.

## Behavior

### Topic Iteration
- For each topic in `config.search_topics`, run two NewsAPI queries in parallel (across topics; sequential within a topic).
- Topics are ordered by preference (highest-rated topics first, maintained by the feedback loop).

### Query Construction

Each topic produces a base query:
```
"<topic>"
  AND ("<positive_kw1>" OR "<positive_kw2>" ...)
  AND (NOT "<negative_kw1>" NOT "<negative_kw2>" ...)
```

Positive/negative keyword clauses are omitted when empty.

### Two-Tier Source Strategy

**Tier 1 — Curated NewsAPI Sources** (`config.preferred_sources`)
- A list of NewsAPI publisher source IDs (e.g., `"techcrunch"`, `"wired"`, `"the-wall-street-journal"`)
- Passed to the `sources` parameter of `newsapi.get_everything()`
- High-trust, high-quality publications

**Tier 2 — Domain-Expanded Search** (`config.other_domains`)
- A list of domain names (e.g., `"anthropic.com"`, `"deepmind.google"`)
- Embedded directly in the query string as additional OR terms
- Captures sources not indexed as official NewsAPI publishers

> **Current bug**: `config.preferred_sources` currently stores domain names, not NewsAPI source IDs. These must be corrected to valid NewsAPI publisher IDs. The `other_domains` key is also missing from `config.json`.

### Deduplication
- URLs are collected in a `set()` per topic — no duplicate URLs within a topic.
- Cross-topic deduplication is not performed (same article may appear under multiple topics).

### Parameters
- `from_param`: `now - config.days` (default 7 days)
- `sort_by`: `relevancy`
- `page_size`: 5 per query (10 URLs max per topic across both tiers)
- `language`: `en`

## Config Schema (this feature)

```json
{
  "search_topics": ["Agentic Engineering", "Context Engineering", ...],
  "preferred_sources": ["techcrunch", "wired", "mit-technology-review"],
  "other_domains": ["anthropic.com", "deepmind.google", "openai.com"],
  "keyword_weights": {
    "positive": { "keyword": weight_int },
    "negative": { "keyword": weight_int }
  }
}
```

## Open Questions / Future Work

- Should `page_size` be configurable?
- Should cross-topic deduplication be added? (Low priority — topics are intentionally distinct)
- Rate limiting: with many topics, parallel requests may hit NewsAPI rate limits.
