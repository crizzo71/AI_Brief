# Vision

## What This Is

A CLI tool that finds recent articles on topics you care about and presents them in your terminal. Optionally, it can summarize them with an LLM and deliver the digest to email, Slack, or wherever.

## The Simplest Use

```
$ export NEWS_API_KEY=...
$ uv run agent "Agentic Engineering"
```

Headlines and snippets print to your terminal. No config file. No LLM key. No setup beyond the one env var.

## The Full Experience

```
$ uv run agent init          # interactive config scaffold
$ uv run agent               # daily run: topics from config, LLM summaries, email delivery
```

Over time, rate the articles you liked. The agent adjusts future searches to match your interests.

## The Pipeline

```
search → fetch → summarize → report → deliver → (feedback → adjust)
```

## Core Properties

- **CLI-first** — runs in the terminal, outputs to stdout by default. Rich formatting for a good UX.
- **Config is optional** — topics can come from CLI args. Config file unlocks advanced features (keyword weights, delivery, LLM settings). `init` command scaffolds one interactively.
- **Runs on a schedule** — the user sets up a cron job locally. No daemon, no cloud.
- **Resilient** — a failed article, missing credential, or bad API call never crashes the whole run. Partial results are fine.
- **Self-improving** — keyword weights in `config.json` accumulate based on user ratings.

## What Is Currently Missing or Broken

| Item | Status |
|------|--------|
| CLI interface (typer/rich) | Not implemented — raw `sys.argv` only |
| LLM summarization | Not implemented — placeholder text only |
| `preferred_sources` | Wrong format — domain names instead of NewsAPI source IDs |
| `other_domains` | Missing from config; wrong NewsAPI parameter in code |
| Feedback loop | Implemented but commented out |
| Delivery resilience | Gmail crashes if `credentials.json` absent |
| Config validation | None |
| Structured logging | None |
