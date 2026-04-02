# Feature: Article Processing & Summarization

## What It Does

Two separate stages:
1. **Fetch** — download full article text for a set of URLs (parallel)
2. **Summarize** — pass each fetched article through the configured summarizer (sequential)

## Fetch

`fetch_articles(topic: str, urls: dict[url, snippet]) -> list[Article]`

Uses `newspaper3k` to download and parse each URL in parallel (`ThreadPoolExecutor`). On failure (network error, paywall, parse error), return a sentinel `Article` with empty `title` and `text` — the `snippet` from news gathering is preserved. Articles with empty titles are excluded from the report.

`agent.py` calls `fetch_articles()` once per topic, passing the topic string so it can be set on each `Article`. Cross-topic deduplication happens in `agent.py` before calling this function.

`Article.text` is held in memory only — used for summarization and keyword extraction, never written to disk.

## Summarize

Runs sequentially after all fetching is complete. This keeps LLM API calls controlled — no concurrent rate-limit pressure.

```python
@dataclass
class SummaryResult:
    summary: str
    keywords: list[str]   # empty if summarizer doesn't extract keywords

class Summarizer(Protocol):
    def summarize(self, title: str, text: str, snippet: str = "") -> SummaryResult: ...
```

### PassthroughSummarizer (default)

Returns the NewsAPI snippet as the summary (or title if snippet is empty). Returns an empty keyword list — word-frequency extraction provides the keywords instead.

This is the default. It requires no API key, no config, no network calls beyond what's already done. It's what you get when you run `uv run brief "AI Agents"`.

### LLM Summarizers

Activated via `--summarize` CLI flag or `config.summarization.provider`. Each uses its provider's native SDK. No litellm.

**Supported providers:**

| Provider | SDK | Env Var | Config Value |
|----------|-----|---------|-------------|
| Anthropic (Claude) | `anthropic` | `ANTHROPIC_API_KEY` | `anthropic` |
| OpenAI (GPT) | `openai` | `OPENAI_API_KEY` | `openai` |
| Vertex AI (Gemini) | `google-cloud-aiplatform` | Application Default Credentials | `vertex` |

All LLM summarizers follow the same pattern:

Prompt (full text available):
```
Summarize the following article in 2-4 sentences.
Focus on what happened, why it matters, and any key organizations or people involved.
Also return 5 keywords that best capture the article's subject matter.

Respond in JSON: {"summary": "...", "keywords": ["...", ...]}

Title: {title}

Article:
{text[:8000]}
```

Prompt (snippet fallback):
```
Summarize the following article snippet in 1-2 sentences.
Also return 5 keywords that best capture the article's subject matter.

Respond in JSON: {"summary": "...", "keywords": ["...", ...]}

Title: {title}

Snippet:
{snippet}
```

- Truncate `text` to 8000 characters to stay within token limits.
- If both `text` and `snippet` are empty, return `SummaryResult(summary="Full article text unavailable.", keywords=[])` without calling the API.
- If the API call fails, log the error and return `SummaryResult(summary="Summary unavailable.", keywords=[])`.
- Model is configurable via `config.summarization.model`. Each provider has a sensible default.

## Keyword Merging

After summarization, `agent.py` merges keywords:
- Word-frequency extraction always runs (on `text`, falling back to `snippet`).
- If the summarizer returned keywords (LLM-based), those take priority.
- Final `Article.keywords` is the LLM keywords if available, otherwise word-frequency keywords.

## Concurrency

Fetching is parallel (`ThreadPoolExecutor`). Summarization is sequential. These are separate stages — not combined in the same executor.
