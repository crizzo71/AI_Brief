# Vision

## What This Is

A **personalized, self-improving AI news digest** delivered to your inbox on a schedule.

The agent fetches articles from curated sources, summarizes them using an LLM, and emails a structured report. Over time it learns your preferences — what topics, sources, and angles you find valuable — and adjusts future searches accordingly.

## The Core Loop

```
Search → Fetch → Summarize → Report → Email → Feedback → Adjust → repeat
```

1. **Search**: Query NewsAPI for recent articles across configured topics, weighted by learned keyword preferences
2. **Fetch**: Download full article text (not just the API snippet) via `newspaper3k`
3. **Summarize**: Use an LLM to produce concise, meaningful summaries
4. **Report**: Compile summaries into a structured Markdown document
5. **Email**: Deliver the report to the user's inbox via Gmail
6. **Feedback**: User rates articles; ratings are recorded
7. **Adjust**: Keyword weights and topic ordering are updated based on ratings; next run is smarter

## Who It's For

A single user (the owner of the configured `user_email`) who wants a curated, evolving AI news briefing without manually monitoring dozens of publications.

## What Makes It Different

The **adaptive feedback loop**. Most news digests are static. This one observes which articles you rate highly, extracts keywords from their content, and promotes those signals in future searches — while suppressing keywords from articles you found uninteresting. The search query itself becomes a living artifact of your taste.

## What Is Currently Half-Baked

| Component | Status | Gap |
|-----------|--------|-----|
| News gathering | Working (with bugs) | `preferred_sources` uses domain names instead of NewsAPI source IDs; `other_domains` key missing from config |
| Article fetching | Working | None |
| Summarization | Placeholder | Returns a stub string; LLM call not implemented |
| Report generation | Working | Minimal formatting; no deduplication |
| Email delivery | Working (with setup) | Requires manual OAuth credential setup |
| Feedback ingestion | Implemented, commented out | `feedback.txt` is a stand-in; no interactive UI |
| Adaptive learning | Implemented, commented out | Works but untested end-to-end; depends on feedback |
| Scheduling | Not started | Intended to run automatically (e.g., daily cron) |
