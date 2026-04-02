# Specs

Source of truth for what this system is and how it should behave.

## Index

| Document | Contents |
|----------|---------|
| [vision.md](vision.md) | What this is, the pipeline, current gaps |
| [architecture.md](architecture.md) | Module structure, extension points, resilience rules |
| [config.md](config.md) | Full config schema, env vars, validation rules |
| [features/01-news-gathering.md](features/01-news-gathering.md) | NewsAPI queries, source strategy, keyword filtering |
| [features/02-article-processing.md](features/02-article-processing.md) | Article fetch + LLM summarization |
| [features/03-delivery.md](features/03-delivery.md) | Report format, pluggable delivery channels |
| [features/04-feedback-loop.md](features/04-feedback-loop.md) | Ratings → keyword weights → adaptive search |

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| News gathering | ⚠️ Bug | Wrong source format; wrong NewsAPI parameter for domains |
| Article fetching | ✅ | |
| Summarization | ❌ | Placeholder only |
| Report generation | ⚠️ | Works; missing deduplication and title display |
| File delivery | ✅ | |
| Gmail delivery | ⚠️ | Crashes if `credentials.json` absent |
| SMTP delivery | ❌ | Not implemented |
| Feedback loop | 🚧 | Implemented, commented out; needs `feedback.json` format |
| Config validation | ❌ | None |
