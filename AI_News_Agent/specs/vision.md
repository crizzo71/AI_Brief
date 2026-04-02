# Vision

## What This Is

A personal AI news digest delivered to your inbox (or wherever you want it) on a schedule.

The agent searches for recent articles on topics you care about, downloads and summarizes them with an LLM, and delivers a clean report. Over time it learns which articles you found valuable and adjusts future searches accordingly.

## The Pipeline

```
search → fetch → summarize → report → deliver → (feedback → adjust)
```

Each stage is simple and independent. The only extension points are:
- **Summarizer** — which LLM (or none) to use
- **Delivery** — where the report goes (file, email, Slack, etc.)

## Core Properties

- **Runs on a schedule** — invoked externally (cron, systemd timer). No daemon, no internal scheduler.
- **Single user** — configured for one recipient. Not a multi-tenant service.
- **Resilient** — a failed article, a missing credential, or a bad API call should never crash the whole run. Partial results are fine.
- **Always produces output** — the file delivery adapter is always on. Even if email fails, the report exists on disk.
- **Self-improving** — keyword weights in `config.json` accumulate across runs based on user ratings, making future searches progressively more relevant.

## What Is Currently Missing or Broken

| Item | Status |
|------|--------|
| LLM summarization | Not implemented — placeholder text only |
| `preferred_sources` | Wrong format — domain names instead of NewsAPI source IDs |
| `other_domains` | Missing from config; also uses wrong NewsAPI parameter in code |
| Feedback loop | Implemented but commented out; blocked on `feedback.txt` fragility |
| Delivery resilience | Gmail adapter crashes if `credentials.json` is absent |
| Config validation | None — bad config fails silently or with confusing errors |
