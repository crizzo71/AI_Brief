# Feature: Adaptive Feedback Loop

## What It Does

After reading a report, the user rates articles. The agent uses those ratings to adjust future searches: promoting keywords from articles you liked, suppressing keywords from articles you didn't.

## Feedback Input

A `feedback.json` file in the project directory, keyed by URL:

```json
{
  "https://example.com/article-you-loved": 5,
  "https://other.com/boring-article": 2
}
```

Ratings are 1–5. If `feedback.json` is absent, `apply_feedback()` skips silently — no error.

This replaces the current `feedback.txt` (line-order-dependent, fragile). URL-keyed JSON is explicit and order-independent.

> **Note**: `ratings.json` (currently written by the code) is a dead end — it's written but never read. It should either become the feedback input format or be removed. Recommendation: use `feedback.json` as the input (user-edited) and drop `ratings.json`.

## How Learning Works

| Rating | Effect |
|--------|--------|
| 4–5 | Extract top keywords from article text → add to `keyword_weights.positive` |
| 3 | No effect |
| 1–2 | Extract top keywords → add to `keyword_weights.negative`; remove from positive if present |

Keywords are extracted by simple word frequency (stop-word filtered). Top 5 words per article. If `text` is empty (paywall, parse failure), fall back to `snippet` for extraction. If both are empty, skip keyword extraction for that article — the topic rating still counts.

Topic ordering in `config.search_topics` is updated to reflect average rating per topic (highest rated first).

Both changes are written back to `config.json` after the run.

## Weight Accumulation

Weights are integers that grow over time. A keyword rated positively across multiple runs gets a higher weight, producing stronger query boosts. There is no decay — old preferences persist indefinitely.

> **Known limitation**: Without decay, very old preferences can permanently bias searches even if your interests have changed. A future improvement would halve all weights periodically. Not in scope now.

## Enabling the Feedback Loop

Currently commented out in `main()`. Uncomment once:
1. LLM summarization is working (so article text is real, not placeholder)
2. `feedback.json` format replaces `feedback.txt`
