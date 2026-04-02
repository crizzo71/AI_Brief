# AI News Agent — Specs

A CLI tool that finds, summarizes, and delivers AI news. These specs are the source of truth for what the system is and how it should behave.

## Quick Overview

**Default experience:** `uv run agent "AI Agents"` → headlines and snippets print to your terminal.

**Full experience:** configure topics, LLM summarization, email delivery, and adaptive feedback via `agent init`.

## Spec Index

### System

| Document | What It Covers |
|----------|---------------|
| [Vision](vision.md) | Purpose, core properties, current gaps |
| [Architecture](architecture.md) | Pipeline, modules, extension points, NFRs (uv, structlog, rich), resilience rules |
| [Config](config.md) | Optional config file, `agent init`, schema, env vars, CLI override precedence |

### Features

| Spec | Feature | Key Decisions |
|------|---------|--------------|
| [01 — News Gathering](features/01-news-gathering.md) | NewsAPI queries, source strategy | Two-tier sources (IDs + domains), keyword-filtered queries |
| [02 — Article Processing](features/02-article-processing.md) | Fetch (parallel) + summarization (sequential) | Passthrough default; Anthropic/OpenAI/Vertex via native SDKs |
| [03 — Delivery](features/03-delivery.md) | Report format, delivery channels | Stdout default (rich); file/Gmail opt-in |
| [04 — Feedback Loop](features/04-feedback-loop.md) | Ratings → keyword weights | run_manifest.json persists keywords; feedback.json for ratings |
| [05 — CLI](features/05-cli.md) | typer commands, args, flags, UX | `agent [TOPICS]`, `agent init`, `agent feedback` |

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| CLI (typer/rich) | ❌ | Raw `sys.argv` only |
| News gathering | ⚠️ | Wrong source format; wrong NewsAPI parameter for domains |
| Article fetching | ✅ | |
| Summarization | ❌ | Placeholder only; no LLM providers wired |
| Keyword extraction | ❌ | Not implemented |
| Report generation | ⚠️ | Works; missing deduplication and title display |
| Stdout delivery | ❌ | Not implemented |
| File delivery | ✅ | (but always-on; should be opt-in) |
| Gmail delivery | ⚠️ | Crashes if `credentials.json` absent |

| Run manifest | ❌ | |
| Feedback loop | 🚧 | Implemented, commented out; needs manifest + feedback.json |
| Config validation | ❌ | |
| Structured logging | ❌ | |

## NFRs (Cross-Cutting)

- **Package management:** `uv` only. `pyproject.toml` is the source of truth.
- **Observability:** `structlog` with domain-oriented events and colored console output.
- **CLI UX:** `typer` + `rich` for a polished terminal experience.
- **No litellm.** Each LLM provider uses its native SDK.
