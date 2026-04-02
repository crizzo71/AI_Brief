# Feature: News Gathering

## What It Does

Queries NewsAPI for recent article URLs across the user's configured topics, filtered by learned keyword preferences. Returns a deduplicated list of URLs per topic.

## Source Strategy

Two tiers, both passed to a single `get_everything()` call per topic:

- **`preferred_sources`** — NewsAPI source IDs (e.g., `"techcrunch"`, `"wired"`). Passed to the `sources` parameter. Find valid IDs at `newsapi.org/v2/sources`.
- **`other_domains`** — Domain names (e.g., `"anthropic.com"`). Passed to the `domains` parameter — **not** embedded in the query string.

> **Current bugs to fix:**
> - Code puts `preferred_sources` in `sources=` but config stores domain names — must be NewsAPI source IDs.
> - Code embeds `other_domains` in the query string instead of using the `domains=` parameter.
> - `other_domains` key is missing from `config.json` entirely.

## Query Construction

```
"<topic>"
  [AND ("<pos_kw1>" OR "<pos_kw2>" ...)]
  [AND (NOT "<neg_kw1>" NOT "<neg_kw2>" ...)]
```

Keyword clauses are omitted when empty (fresh config, no feedback yet).

## Parameters

| Parameter | Value |
|-----------|-------|
| `from_param` | `today - config.days` |
| `sort_by` | `relevancy` |
| `page_size` | 5 |
| `language` | `en` |

## What Gets Captured

News gathering captures both the URL **and the NewsAPI snippet** (`description` field in the API response) for each article. The snippet is stored on `Article` and used as a fallback by the summarizer when full text cannot be fetched.

## Deduplication

URLs collected in a `set()` — no duplicate URLs within a topic. Cross-topic duplicates are resolved in `build_report()` (first topic wins).

## Failure Handling

If a NewsAPI call fails (network, rate limit, bad key), log the error and return an empty list for that topic. Do not crash.
