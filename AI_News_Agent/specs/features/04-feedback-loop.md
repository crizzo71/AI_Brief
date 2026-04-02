# Feature: Adaptive Feedback Loop

## What It Does

After reading a report, the user rates articles. On the next run, the agent uses those ratings — combined with pre-extracted keywords from the previous run — to adjust future searches.

## How It Works Across Runs

```
Run N:
  ... pipeline runs ...
  save_manifest()  →  run_manifest.json  (url → topic, keywords, snippet)

Between runs:
  User runs `agent feedback` or manually edits feedback.json

Run N+1:
  apply_feedback()  ←  feedback.json + run_manifest.json
  ... pipeline runs with updated config ...
```

Keywords are extracted during the run while article text is in memory. They are persisted in `run_manifest.json` so the feedback step on the *next* run can use them without needing the original article text.

## Run Manifest

Written at the end of each run by `save_manifest()`:

```json
{
  "date": "2026-04-02",
  "articles": {
    "https://example.com/article": {
      "topic": "Agentic Engineering",
      "keywords": ["agent", "orchestration", "claude", "tool", "reasoning"],
      "snippet": "A new approach to building AI agents..."
    }
  }
}
```

Overwritten each run. Only the most recent manifest is needed.

## Keyword Sources

Keywords come from two places, merged at run time:

1. **Word-frequency extraction** (always runs) — simple stop-word-filtered word counts, top 5 per article. Uses `text`, falling back to `snippet`.
2. **LLM-extracted keywords** (when using an LLM summarizer) — the summarization prompt asks for 5 keywords alongside the summary. Higher quality, no extra API call.

If LLM keywords are available, they take priority. Otherwise word-frequency keywords are used. The merged result is persisted in the manifest.

## Feedback Input

### `agent feedback` command

Opens `feedback.json` in `$EDITOR` pre-populated with URLs from the latest `run_manifest.json` (values set to `null`). User replaces `null` with ratings (1–5), saves, exits.

### Manual editing

`feedback.json` in the project directory, keyed by URL:

```json
{
  "https://example.com/article-you-loved": 5,
  "https://other.com/boring-article": 2
}
```

Ratings are 1–5. If `feedback.json` is absent, `apply_feedback()` skips silently.

> **Note**: `ratings.json` (currently written by the code) is a dead end — it's written but never read. Drop it.

## How Learning Works

`apply_feedback()` reads `feedback.json` and looks up each URL in `run_manifest.json` to get its pre-extracted keywords and topic.

| Rating | Effect |
|--------|--------|
| 4–5 | Keywords from manifest → add to `keyword_weights.positive` |
| 3 | No keyword effect |
| 1–2 | Keywords from manifest → add to `keyword_weights.negative`; remove from positive if present |

If a URL in `feedback.json` is not found in `run_manifest.json`, skip it silently.

Topic ordering in `config.search_topics` is updated to reflect average rating per topic (highest rated first).

Both changes are written back to `config.json`. `feedback.json` is deleted after processing.

## Requires Config

The feedback loop writes to `config.json`. If no config file exists, `apply_feedback()` skips silently — there's nowhere to persist the learned weights. The user should run `agent init` to set up a config before using feedback.

## Weight Accumulation

Weights are integers that grow over time. A keyword rated positively across multiple runs gets a higher weight. There is no decay — old preferences persist indefinitely.

> **Known limitation**: Without decay, very old preferences can permanently bias searches. A future improvement would halve all weights periodically. Not in scope now.
