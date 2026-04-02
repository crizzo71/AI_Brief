# Feature: Adaptive Feedback Loop

## Purpose

Let the agent learn from user ratings over time, progressively personalizing search results to match the user's actual interests.

## The Core Idea

After reading a report, the user rates each article 1–5. The agent:
1. Extracts keywords from the full text of highly-rated articles → adds them as **positive** search weights
2. Extracts keywords from low-rated articles → adds them as **negative** search weights
3. Re-orders topics by their average rating (most-loved topics surface first)

On subsequent runs, the weighted keywords modify the NewsAPI query, steering results toward what the user found valuable.

## Rating Scale

| Rating | Meaning | Effect |
|--------|---------|--------|
| 5 | Excellent | Strong positive keyword boost |
| 4 | Good | Positive keyword boost |
| 3 | Neutral | No keyword effect |
| 2 | Poor | Negative keyword suppression |
| 1 | Irrelevant | Strong negative keyword suppression |

## Feedback Ingestion

### Current: `feedback.txt`
A plain text file with one integer per line, in the same order as articles appear in the report. Fragile (order-dependent) and requires the user to manually count article positions. Acceptable as a prototype mechanism.

### Required: Structured Feedback
Replace `feedback.txt` with a `feedback.json` keyed by URL:
```json
{
  "https://example.com/article": 4,
  "https://other.com/story": 2
}
```
This is order-independent and explicit. Can be populated manually or by a future UI.

### Future: Interactive Feedback
- CLI prompt after report generation: show each article title and ask for a rating.
- Or a lightweight local web UI serving the report with thumbs-up/down buttons.

## Keyword Extraction

Uses simple frequency analysis (stop-word filtered word counts) — no ML required. The top 5 most frequent non-stop words from the article body are extracted.

This is intentionally simple. It can be upgraded to TF-IDF or LLM-extracted topics later without changing the surrounding architecture.

## Config Mutation

`config.keyword_weights` accumulates weights across runs:
- A keyword rated positively multiple times gets a higher weight
- A keyword rated negatively is moved to the negative dict (and removed from positive if present)
- Weights are integers; no decay/forgetting mechanism currently exists

**Future**: Add weight decay so old preferences don't permanently dominate.

## Current State

`get_feedback()` and `update_config_with_feedback()` are fully implemented but commented out in `main()`. The feedback loop works end-to-end but has never been tested with real LLM summaries. Uncomment and test once summarization is implemented.
