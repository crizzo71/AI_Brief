# Feature: CLI Interface

## Framework

`typer` for commands/args/flags. `rich` for terminal output formatting.

## Commands

### `agent [TOPICS...]`

The default command. Runs the pipeline.

```
# Topics from CLI — no config needed
$ uv run agent "Agentic Engineering" "Context Engineering"

# Topics from config.json
$ uv run agent

# Override days
$ uv run agent --days 3

# Enable LLM summarization
$ uv run agent --summarize

# Write to file instead of (or alongside) stdout
$ uv run agent --output report.md

# Deliver via configured channel
$ uv run agent --deliver gmail

# JSON logs for cron
$ uv run agent --log-format json
```

**Argument resolution:**
- If `TOPICS` are provided on the CLI, they are used (config topics ignored for this run).
- If no `TOPICS` and no config file, exit with an error and suggest `agent init`.
- If no `TOPICS` but config file exists, use `config.search_topics`.
- `--days`, `--summarize`, `--output`, `--deliver` override config equivalents.

### `agent init`

Interactive config scaffold using `rich` prompts:

1. **Topics** — "What topics do you want to track?" (comma-separated, at least one required)
2. **Sources** — "Any preferred news sources?" (show common NewsAPI source IDs as suggestions, optional)
3. **Domains** — "Any specific domains to include?" (optional)
4. **Summarization** — "Enable LLM summarization? [y/N]"
   - If yes: "Which provider? [anthropic/openai/vertex]"
   - Validate the corresponding API key env var is set
5. **Delivery** — "Set up email delivery? [y/N]"
   - If yes: walk through Gmail config
6. Write `config.json`, confirm path.

If `config.json` already exists, warn and ask to overwrite.

### `agent feedback`

Convenience command. Opens `feedback.json` in `$EDITOR` pre-populated with URLs from the latest `run_manifest.json`:

```json
{
  "https://example.com/article-1": null,
  "https://example.com/article-2": null
}
```

User replaces `null` with ratings (1–5), saves, exits. Ratings are applied on the next `agent` run.

If `run_manifest.json` doesn't exist, print a message: "No recent run found. Run `agent` first."

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
