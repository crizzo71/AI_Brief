# Specs

This directory is the source of truth for what this system is and how it should behave. Code is an implementation of these specs, not the other way around.

## Index

| Document | Contents |
|----------|---------|
| [vision.md](vision.md) | What this system is, who it's for, the core loop, current gaps |
| [architecture.md](architecture.md) | DDD bounded contexts, hexagonal ports & adapters, directory structure, dependency rules |
| [config.md](config.md) | Full config schema, field reference, environment variables, validation rules |

### Features

| Spec | Feature |
|------|---------|
| [01-news-gathering.md](features/01-news-gathering.md) | NewsAPI queries, two-tier source strategy, keyword filtering |
| [02-article-processing.md](features/02-article-processing.md) | Full-text extraction via newspaper3k, failure handling |
| [03-summarization.md](features/03-summarization.md) | LLM summarization (primary unimplemented gap) |
| [04-report-generation.md](features/04-report-generation.md) | Markdown digest format, deduplication |
| [05-delivery.md](features/05-delivery.md) | Pluggable delivery adapters (file, Gmail, SMTP, Slack, webhook) |
| [06-feedback-loop.md](features/06-feedback-loop.md) | User ratings, keyword weight learning, topic reordering |

## Implementation Status

```
✅ Implemented (working)
⚠️  Implemented (with bugs)
🚧 Implemented (incomplete/commented out)
❌ Not yet implemented
```

| Feature | Status | Notes |
|---------|--------|-------|
| News gathering | ⚠️ | Wrong source ID format; missing other_domains in config |
| Article fetching | ✅ | |
| Summarization | ❌ | Placeholder only; LLM call not implemented |
| Report generation | ⚠️ | Works but minimal; no deduplication |
| File delivery | ✅ | |
| Gmail delivery | ⚠️ | Works but crashes if credentials.json absent |
| SMTP/Slack/Webhook delivery | ❌ | Not implemented |
| Feedback ingestion | 🚧 | Implemented but commented out; uses fragile feedback.txt |
| Adaptive learning | 🚧 | Implemented but commented out; depends on feedback |
| Hexagonal architecture | ❌ | All code is in a single flat agent.py |
| Config validation | ❌ | Config loaded as raw dict with no validation |
| Scheduling | ❌ | Designed for cron but no setup provided |
