# Architecture

## Guiding Principle

This is a simple pipeline script, not an enterprise system. Keep it that way. The only structural complexity worth adding is at the two natural extension points: **how articles get summarized** and **where the report gets delivered**.

## The Pipeline

```
config.json + env vars
        │
        ▼
   gather_news()        → NewsAPI
        │
        ▼
   fetch_articles()     → newspaper3k (parallel)
        │
        ▼
   summarize()          → Summarizer (pluggable)
        │
        ▼
   build_report()       → string / Report dataclass
        │
        ▼
   deliver()            → DeliveryChannel[] (pluggable, all run)
        │
        ▼
   apply_feedback()     → config.json (if feedback.json present)
```

## Module Structure

```
ai_news_agent/
├── agent.py          # pipeline orchestration — the main script
├── config.py         # load, validate, and expose config as a typed dataclass
├── news.py           # gather_news(), fetch_articles() — NewsAPI + newspaper3k
├── report.py         # build_report() — assembles the Digest from summaries
├── feedback.py       # apply_feedback() — reads feedback.json, updates config
├── summarizers/
│   ├── base.py       # Summarizer protocol
│   ├── claude.py     # ClaudeSummarizer
│   └── passthrough.py  # PassthroughSummarizer (returns snippet, or title if snippet empty)
└── delivery/
    ├── base.py       # DeliveryChannel protocol
    ├── file.py       # FileChannel (always-on)
    ├── gmail.py      # GmailChannel
    └── smtp.py       # SMTPChannel
```

No `domain/`, no `ports/`, no `adapters/`. Just flat modules and two small plugin directories.

## Extension Points

### Summarizer

```python
class Summarizer(Protocol):
    def summarize(self, title: str, text: str, snippet: str = "") -> str: ...
```

Configured via `config.summarization.provider`. The application selects one summarizer at startup and passes it through the pipeline.

### DeliveryChannel

```python
class DeliveryChannel(Protocol):
    def deliver(self, report: Report) -> None: ...
```

Configured via `config.delivery`. Multiple channels can be active. Each is called independently — a failure in one does not affect others. `FileChannel` is always included regardless of config.

## Data Model

Simple dataclasses, no ORM, no database.

```python
@dataclass
class Article:
    url: str
    title: str
    text: str       # full body from newspaper3k; empty if paywall/parse failure
    snippet: str    # short description from NewsAPI response; fallback when text is empty
    summary: str
    topic: str

@dataclass
class Report:
    date: date
    articles: list[Article]   # deduplicated across topics
    topics: list[str]         # ordered topic list (from config) — drives section ordering in the report
```

`Report` is the artifact that flows into delivery. `Article.text` is in-memory only — not persisted to disk.

## Concurrency

`fetch_articles()` downloads and parses articles in parallel using `ThreadPoolExecutor`. All other pipeline stages are sequential. This is the right tradeoff: fetching is I/O-bound and benefits from parallelism; everything else is fast enough not to need it.

## Resilience Rules

1. A failed article fetch returns a sentinel `Article` with empty `text` and `summary` (the `snippet` from news gathering is preserved). It is included in the report only if it has a title; otherwise dropped silently.
2. If the summarizer raises, log and return `"Summary unavailable."` — never propagate.
3. Each delivery channel is wrapped in try/except. Log failures; continue to next channel.
4. `FileChannel` runs last so other channels have had their chance, but always runs.
5. `apply_feedback()` is optional — if `feedback.json` is absent, skip silently.
6. `config.py` validates config at startup and exits with a clear error message if required fields are missing or malformed. Fail loudly at startup, not silently mid-run.

## What This Is Not

- Not a web service
- Not a multi-user system
- Not a database-backed application
- Not async (no `asyncio`) — `ThreadPoolExecutor` is sufficient and simpler
