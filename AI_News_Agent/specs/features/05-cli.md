# Feature: CLI Interface

## Framework

`typer` for commands/args/flags. `rich` for terminal output formatting.

## Commands

### `brief [TOPICS...]`

The default command. Runs the pipeline.

```
# Topics from CLI — no config needed
$ uv run brief "Agentic Engineering" "Context Engineering"

# Topics from config.json
$ uv run brief

# Override days
$ uv run brief --days 3

# Enable LLM summarization
$ uv run brief --summarize

# Write to file
$ uv run brief --output report.md

# Deliver via Gmail
$ uv run brief --deliver gmail

# JSON logs for cron
$ uv run brief --log-format json
```

**Argument resolution:**
- If `TOPICS` are provided on the CLI, they are used (config topics ignored for this run).
- If no `TOPICS` and no config file, exit with an error and suggest `brief init`.
- If no `TOPICS` but config file exists, use `config.search_topics`.
- `--days`, `--summarize`, `--output`, `--deliver` override config equivalents.

### `brief init`

Interactive config scaffold using `rich` prompts:

1. **Topics** — "What topics do you want to track?" (comma-separated, at least one required)
2. **Sources** — "Any preferred news sources?" (show common NewsAPI source IDs as suggestions, optional)
3. **Domains** — "Any specific domains to include?" (optional)
4. **Summarization** — "Enable LLM summarization? [y/N]"
   - If yes: "Which provider? [anthropic/openai/vertex]"
   - Validate the corresponding API key env var is set
5. **Delivery** — "Set up Gmail delivery? [y/N]"
   - If yes: walk through Gmail config
6. Write `config.json`, confirm path.

If `config.json` already exists, warn and ask to overwrite.

### `brief rate`

Interactive article rating using `rich`. Requires `config.json` and `run_manifest.json`.

Shows each article from the last run with its title and snippet, and prompts for a 1–5 rating:

```
Rate articles from your last brief (April 2, 2026)
Skip any article by pressing Enter.

  New Framework for Building AI Agents
  techcrunch.com — A new open-source framework simplifies
  building autonomous AI agents that can...

  Rating [1-5]:  5

  Claude Adds Tool Use Support
  anthropic.com — Anthropic announced native tool use...

  Rating [1-5]:  4

  What Is Machine Learning?
  coursera.org — Machine learning is a subset of...

  Rating [1-5]:  ⏎ (skipped)

Saved 2 ratings. They'll be applied on your next run.
```

- Reads article titles, snippets, and URLs from `run_manifest.json`.
- Writes ratings to `feedback.json` (only rated articles, skipped ones omitted).
- If `config.json` is missing: exit with "Run `brief init` first — ratings need a config file to persist."
- If `run_manifest.json` is missing: exit with "No recent run found. Run `brief` first."

## Terminal Output (rich)

Default output uses `rich` panels and tables:

```
╭─ AI News Brief — April 2, 2026 ─────────────────────╮
│ 12 articles across 4 topics                          │
╰──────────────────────────────────────────────────────╯

Agentic Engineering
━━━━━━━━━━━━━━━━━━━
  New Framework for Building AI Agents
  techcrunch.com
  A new open-source framework simplifies building
  autonomous AI agents that can use tools and...

  Claude Adds Tool Use Support
  anthropic.com
  Anthropic announced native tool use capabilities...

Context Engineering
━━━━━━━━━━━━━━━━━━━
  ...
```

With `--summarize`, the snippet text is replaced by the LLM-generated summary.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (even if some articles failed to fetch) |
| 1 | Fatal error (no API key, invalid config, no topics) |
| 2 | No articles found for any topic |
