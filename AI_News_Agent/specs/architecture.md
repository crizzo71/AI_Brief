# Architecture

## Guiding Principles

**Domain-Driven Design + Hexagonal Architecture (Ports & Adapters)**

The core domain logic — what constitutes a good article, how preferences are learned, how a report is structured — must be independent of any external service. NewsAPI, Gmail, Anthropic, and `newspaper3k` are all implementation details. They plug in via adapters; the domain never imports them.

This makes the system testable without network calls, and swappable without rewriting business logic.

---

## Bounded Contexts

### 1. Discovery Context
Responsible for finding article URLs relevant to user topics and preferences.

- **Domain**: `Topic`, `SearchQuery`, `KeywordWeights`, `DiscoveredArticle`
- **Port** (outbound): `ArticleDiscoveryPort` — "given a query, return a list of URLs"
- **Adapters**: `NewsAPIAdapter` (current), `RSSFeedAdapter` (future), `HackerNewsAdapter` (future)

### 2. Ingestion Context
Responsible for fetching full article content from a URL.

- **Domain**: `RawArticle` (url, title, text)
- **Port** (outbound): `ArticleFetcherPort` — "given a URL, return raw content"
- **Adapters**: `NewspaperAdapter` (current), `PlaywrightAdapter` (future, for JS-heavy sites)

### 3. Summarization Context
Responsible for distilling raw text into a human-readable summary.

- **Domain**: `ArticleSummary`
- **Port** (outbound): `SummarizerPort` — "given title + text, return a summary string"
- **Adapters**: `ClaudeAdapter`, `OpenAIAdapter`, `ExtractiveSummaryAdapter` (no LLM fallback)

### 4. Digest Context
The core domain. Assembles discovered + ingested + summarized articles into a `Digest` (the report). Owns the data model that flows through the system.

- **Domain**: `Digest`, `DigestSection`, `DigestEntry`
- No outbound ports — pure transformation logic.

### 5. Delivery Context
Responsible for getting the `Digest` to the user.

- **Domain**: None (pure side-effect boundary)
- **Port** (outbound): `DeliveryPort` — "given a Digest, deliver it"
- **Adapters**: `FileAdapter` (always-on), `GmailAdapter`, `SMTPAdapter`, `SlackAdapter`, `WebhookAdapter`
- Multiple adapters can be active simultaneously.

### 6. Preference Context
Responsible for persisting and evolving user preferences based on feedback.

- **Domain**: `UserPreferences`, `ArticleRating`, `KeywordWeights`
- **Port** (inbound): `FeedbackPort` — "accept ratings for articles in a digest"
- **Port** (outbound): `PreferenceStorePort` — "load/save preferences"
- **Adapters**: `JsonFilePreferenceStore` (current), `SQLitePreferenceStore` (future)

---

## Directory Structure (Target)

```
ai_news_agent/
├── domain/
│   ├── discovery.py        # Topic, SearchQuery, KeywordWeights, DiscoveredArticle
│   ├── ingestion.py        # RawArticle
│   ├── digest.py           # Digest, DigestSection, DigestEntry, ArticleSummary
│   └── preferences.py      # UserPreferences, ArticleRating
│
├── ports/
│   ├── discovery.py        # ArticleDiscoveryPort (Protocol)
│   ├── fetcher.py          # ArticleFetcherPort (Protocol)
│   ├── summarizer.py       # SummarizerPort (Protocol)
│   ├── delivery.py         # DeliveryPort (Protocol)
│   └── preferences.py      # PreferenceStorePort, FeedbackPort (Protocols)
│
├── adapters/
│   ├── discovery/
│   │   └── newsapi.py      # NewsAPIAdapter
│   ├── fetcher/
│   │   └── newspaper.py    # NewspaperAdapter
│   ├── summarizer/
│   │   ├── claude.py       # ClaudeAdapter
│   │   └── extractive.py   # ExtractiveSummaryAdapter (no LLM fallback)
│   ├── delivery/
│   │   ├── file.py         # FileAdapter
│   │   ├── gmail.py        # GmailAdapter
│   │   └── smtp.py         # SMTPAdapter
│   └── preferences/
│       └── json_file.py    # JsonFilePreferenceStore
│
├── application/
│   └── agent.py            # Orchestration: wires ports+adapters, runs the loop
│
└── config.py               # Config loading, validation, schema
```

---

## Data Flow

```
Config + Env
    │
    ▼
[Application Layer — agent.py]
    │
    ├── ArticleDiscoveryPort ──► NewsAPIAdapter ──► newsapi.org
    │        │ (urls per topic)
    │        ▼
    ├── ArticleFetcherPort ────► NewspaperAdapter ──► HTTP
    │        │ (RawArticle)
    │        ▼
    ├── SummarizerPort ────────► ClaudeAdapter ──► Anthropic API
    │        │ (ArticleSummary)
    │        ▼
    ├── [Domain] Build Digest
    │        │ (Digest)
    │        ▼
    ├── DeliveryPort ──────────► FileAdapter (always)
    │                       └──► GmailAdapter (if configured)
    │                       └──► SlackAdapter (if configured)
    │        ▼
    └── FeedbackPort ◄──────────── feedback.json (if present)
             │
             ▼
        PreferenceStorePort ──► JsonFilePreferenceStore ──► config.json
```

---

## Dependency Rule

```
adapters → ports ← domain
               ↑
          application
```

- `domain/` has zero external imports (stdlib only).
- `ports/` imports only from `domain/` and `typing`.
- `adapters/` imports from `ports/` and third-party libraries.
- `application/` imports from `ports/` and `adapters/` — wires everything together.

The domain never imports an adapter. Adapters never import each other.

---

## Configuration

`config.json` is loaded and validated at startup by `config.py` into a typed `Config` dataclass. The application layer passes slices of this config to relevant adapters. Raw dicts are not passed around inside the system.

See `specs/config.md` for the full schema.

---

## Concurrency

Parallelism is an application-layer concern, not a domain concern. The application layer may run `ArticleFetcherPort.fetch()` calls concurrently using `asyncio` or `ThreadPoolExecutor`. Ports and adapters are expected to be thread-safe or used statelessly.

---

## Resilience

- Each adapter call is wrapped at the application layer; failures are caught, logged, and produce a sentinel result (e.g., empty `RawArticle`) rather than propagating.
- Delivery adapters are invoked independently — a failed `GmailAdapter` does not prevent `FileAdapter` from running.
- The agent always exits cleanly; partial results are better than no results.
