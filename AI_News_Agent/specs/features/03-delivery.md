# Feature: Report Generation & Delivery

## Report Format (Markdown)

Used for file output and email body:

```markdown
# AI News Brief — April 2, 2026
_12 articles across 4 topics_

---

## Agentic Engineering

### Article Title
**Source:** [domain.com](url)
Summary text here.

---
```

- Articles are deduplicated across topics by `agent.py` before report generation (first topic wins).
- Topics with zero successful articles are omitted.
- The `Report` object (date + articles list + ordered topics) is passed to all active delivery channels.

## Delivery Channels

### StdoutChannel (default)

The primary interface. Uses `rich` for formatted, colored terminal output (panels, section headers, styled text). See `features/05-cli.md` for the output format.

Always active unless explicitly suppressed. No config needed.

### FileChannel

Writes the Markdown report to a file. Activated by `--output <path>` CLI flag or `config.delivery.file.path`.

### GmailChannel

Sends via Gmail API (OAuth 2.0). Activated by `--deliver gmail` or `config.delivery.gmail.enabled`.

- Requires `credentials.json` in the project directory.
- Produces `token.json` on first run (cached OAuth token).
- If `credentials.json` is absent or auth fails: log the error, skip — do not crash.
- Subject: `AI News Brief — <date>`

## Channel Interface

```python
class DeliveryChannel(Protocol):
    def deliver(self, report: Report) -> None: ...
```

Channels are instantiated at startup based on CLI flags and config. Each `deliver()` call is wrapped in try/except — a failing channel is logged and skipped. Other channels continue.

## Adding a New Channel

1. Create `delivery/mychannel.py` implementing `DeliveryChannel`.
2. Add it to `config.delivery` schema.
3. Wire it in `agent.py` startup — no other changes needed.
