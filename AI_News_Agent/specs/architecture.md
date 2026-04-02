# Architecture

## Guiding Principle

This is a CLI tool, not a platform. Keep it simple. The only structural complexity worth adding is at the natural extension points: **how articles get summarized** and **where the report gets delivered**.

## The Pipeline

```
config.json (if present) + CLI args + env vars
        │
        ▼
   apply_feedback()     → config.json (if feedback.json + manifest exist)
        │
        ▼
   gather_news()        → NewsAPI
        │
        ▼
   fetch_articles()     → newspaper3k (parallel, per topic, deduplicated)
        │
        ▼
   summarize()          → Summarizer (pluggable, sequential; passthrough by default)
        │
        ▼
   extract_keywords()   → always runs (word frequency); LLM keywords merged if available
        │
        ▼
   build_report()       → Report dataclass
        │
        ▼
   deliver()            → stdout by default; optional: file, gmail
        │
        ▼
   save_manifest()      → run_manifest.json (url → title, topic, keywords, snippet)
```

## Module Structure

```
ai_news_agent/
├── cli.py            # typer app: commands, args, flags
├── agent.py          # pipeline orchestration — owns topic iteration and deduplication
├── config.py         # load, validate, merge CLI args over config file
├── news.py           # gather_news(), fetch_articles() — NewsAPI + newspaper3k
├── report.py         # build_report() — assembles the Report
├── feedback.py       # apply_feedback() — reads feedback.json + manifest, updates config
├── keywords.py       # extract_keywords() — word frequency extraction
├── observability.py  # structlog setup, domain probes
├── summarizers/
│   ├── base.py       # Summarizer protocol + SummaryResult
│   ├── passthrough.py  # PassthroughSummarizer (default — returns snippet)
│   ├── anthropic.py  # Anthropic SDK (Claude)
│   ├── openai.py     # OpenAI SDK (GPT)
│   └── vertex.py     # google-cloud-aiplatform SDK (Gemini)
└── delivery/
    ├── base.py       # DeliveryChannel protocol
    ├── stdout.py     # StdoutChannel (default — rich formatted terminal output)
    ├── file.py       # FileChannel (--output flag)
    └── gmail.py      # GmailChannel
```

## Extension Points

### Summarizer

```python
@dataclass
class SummaryResult:
    summary: str
    keywords: list[str]   # empty list if summarizer doesn't extract keywords

class Summarizer(Protocol):
    def summarize(self, title: str, text: str, snippet: str = "") -> SummaryResult: ...
```

**PassthroughSummarizer** is the default. Returns the snippet as the summary, empty keywords. No API key needed.

LLM summarizers activate via `--summarize` flag or `config.summarization.provider`. Each uses its provider's native SDK:
- `anthropic` → Anthropic SDK
- `openai` → OpenAI SDK
- `vertex` → google-cloud-aiplatform SDK

No litellm.

### DeliveryChannel

```python
class DeliveryChannel(Protocol):
    def deliver(self, report: Report) -> None: ...
```

**StdoutChannel** is the default. Uses `rich` for formatted, colored terminal output. Additional channels activate via `--output`, `--deliver`, or config.

## Data Model

```python
@dataclass
class Article:
    url: str
    title: str
    text: str       # full body from newspaper3k; empty if paywall/parse failure
    snippet: str    # short description from NewsAPI response
    summary: str
    keywords: list[str]  # merged: word-frequency always, LLM keywords when available
    topic: str

@dataclass
class Report:
    date: date
    articles: list[Article]   # deduplicated across topics
    topics: list[str]         # ordered topic list — drives section ordering
```

`Article.text` is in-memory only. `Article.keywords` are persisted to `run_manifest.json`.

## Orchestration (agent.py)

`agent.py` owns topic iteration and cross-topic deduplication:

```
gathered = gather_news(config)
seen_urls = set()
all_articles = []
for topic in topics:
    urls = gathered.get(topic, {})
    new_urls = {u: s for u, s in urls.items() if u not in seen_urls}
    seen_urls.update(new_urls)
    articles = fetch_articles(topic, new_urls)
    for article in articles:
        result = summarizer.summarize(article.title, article.text, article.snippet)
        article.summary = result.summary
        freq_keywords = extract_keywords(article.text or article.snippet)
        article.keywords = result.keywords or freq_keywords
    all_articles.extend(articles)
report = build_report(all_articles, topics)
```

## Concurrency

`fetch_articles()` downloads and parses articles in parallel using `ThreadPoolExecutor`. Summarization runs sequentially after fetching. All other stages are also sequential.

## Non-Functional Requirements

### Package Management
`uv` is the sole package manager. `pyproject.toml` is the source of truth for dependencies. No `requirements.txt`, no `pip`.

### Observability
Domain-oriented observability using `structlog`. Log events in domain terms:
- `topic.searched`, `article.fetched`, `article.summarized`, `article.fetch_failed`
- `report.built`, `report.delivered`, `feedback.applied`

Default renderer: `structlog.dev.ConsoleRenderer` (colored, human-readable). Structured JSON available via `--log-format json` for cron/production use.

### CLI UX
`typer` for CLI framework. `rich` for terminal output (tables, panels, colored text). The terminal experience should feel polished — this is the primary interface.

## Resilience Rules

1. A failed article fetch returns a sentinel `Article` with empty `text` and `summary` (the `snippet` from news gathering is preserved). It is included in the report only if it has a title; otherwise dropped silently.
2. If the summarizer raises, log and return `SummaryResult(summary="Summary unavailable.", keywords=[])` — never propagate.
3. Each delivery channel is wrapped in try/except. Log failures; continue to next channel.
4. `apply_feedback()` is optional — if `feedback.json` or `run_manifest.json` is absent, skip silently.
5. `config.py` validates config at startup and exits with a clear error message if required fields are missing or malformed.

## What This Is Not

- Not a web service
- Not a multi-user system
- Not a database-backed application
- Not async — `ThreadPoolExecutor` is sufficient and simpler
