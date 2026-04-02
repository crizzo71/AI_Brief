# Architecture

## Guiding Principle

This is a simple pipeline script, not an enterprise system. Keep it that way. The only structural complexity worth adding is at the two natural extension points: **how articles get summarized** and **where the report gets delivered**.

## The Pipeline

```
config.json + env vars
        │
        ▼
   apply_feedback()     → config.json (if feedback.json + manifest exist)
        │
        ▼
   gather_news()        → NewsAPI (returns dict[topic, dict[url, snippet]])
        │
        ▼
   fetch_articles()     → newspaper3k (parallel, per topic, deduplicated)
        │
        ▼
   summarize()          → Summarizer (pluggable, sequential)
        │
        ▼
   extract_keywords()   → always runs (word frequency); LLM keywords merged if available
        │
        ▼
   build_report()       → Report dataclass
        │
        ▼
   deliver()            → DeliveryChannel[] (pluggable, all run)
        │
        ▼
   save_manifest()      → run_manifest.json (url → topic, keywords, snippet)
```

## Module Structure

```
ai_news_agent/
├── agent.py          # pipeline orchestration — owns topic iteration and deduplication
├── config.py         # load, validate, and expose config as a typed dataclass
├── news.py           # gather_news(), fetch_articles() — NewsAPI + newspaper3k
├── report.py         # build_report() — assembles the Report from summaries
├── feedback.py       # apply_feedback() — reads feedback.json + manifest, updates config
├── keywords.py       # extract_keywords() — word frequency extraction
├── summarizers/
│   ├── base.py       # Summarizer protocol
│   ├── claude.py     # ClaudeSummarizer (returns summary + keywords)
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
    def summarize(self, title: str, text: str, snippet: str = "") -> SummaryResult: ...

@dataclass
class SummaryResult:
    summary: str
    keywords: list[str]   # empty list if summarizer doesn't extract keywords
```

Configured via `config.summarization.provider`. The application selects one summarizer at startup. LLM-based summarizers return keywords alongside the summary; non-LLM summarizers return an empty keyword list (word-frequency extraction fills the gap).

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
    keywords: list[str]  # merged: word-frequency always, LLM keywords when available
    topic: str

@dataclass
class Report:
    date: date
    articles: list[Article]   # deduplicated across topics
    topics: list[str]         # ordered topic list (from config) — drives section ordering in the report
```

`Report` is the artifact that flows into delivery. `Article.text` is in-memory only — not persisted to disk. `Article.keywords` are persisted to `run_manifest.json` for use by the feedback loop on subsequent runs.

## Orchestration (agent.py)

`agent.py` owns topic iteration and cross-topic deduplication:

```
gathered = gather_news(config)        # dict[topic, dict[url, snippet]]
seen_urls = set()
all_articles = []
for topic in config.search_topics:
    urls = gathered.get(topic, {})
    new_urls = {u: s for u, s in urls.items() if u not in seen_urls}
    seen_urls.update(new_urls)
    articles = fetch_articles(topic, new_urls)   # parallel fetch
    for article in articles:
        result = summarizer.summarize(article.title, article.text, article.snippet)
        article.summary = result.summary
        freq_keywords = extract_keywords(article.text or article.snippet)
        article.keywords = result.keywords or freq_keywords  # LLM wins if available
    all_articles.extend(articles)
report = build_report(all_articles, config.search_topics)
```

## Concurrency

`fetch_articles()` downloads and parses articles in parallel using `ThreadPoolExecutor`. Summarization runs sequentially after fetching — this keeps LLM API calls controlled (no concurrent rate-limit pressure) and makes the pipeline easier to reason about. All other stages are also sequential.

## Resilience Rules

1. A failed article fetch returns a sentinel `Article` with empty `text` and `summary` (the `snippet` from news gathering is preserved). It is included in the report only if it has a title; otherwise dropped silently.
2. If the summarizer raises, log and return `SummaryResult(summary="Summary unavailable.", keywords=[])` — never propagate.
3. Each delivery channel is wrapped in try/except. Log failures; continue to next channel.
4. `FileChannel` runs last so other channels have had their chance, but always runs.
5. `apply_feedback()` is optional — if `feedback.json` or `run_manifest.json` is absent, skip silently.
6. `config.py` validates config at startup and exits with a clear error message if required fields are missing or malformed. Fail loudly at startup, not silently mid-run.

## What This Is Not

- Not a web service
- Not a multi-user system
- Not a database-backed application
- Not async (no `asyncio`) — `ThreadPoolExecutor` is sufficient and simpler
