# Feature: Report Generation & Delivery

## Report Format

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

- Articles are deduplicated across topics (same URL in two topics appears once, under the first).
- Topics with zero successful articles are omitted.
- The `Report` object (date + articles list) is passed to all configured delivery channels.

## Delivery Channels

### FileChannel (always-on)
- Writes `report.md` to the project directory.
- Always runs, regardless of config — even if all other channels fail, the report exists on disk.
- No credentials required.

### GmailChannel
- Sends via Gmail API (OAuth 2.0).
- Requires `credentials.json` in the project directory (Google OAuth client secret).
- Produces `token.json` on first run (cached OAuth token).
- If `credentials.json` is absent or auth fails: log the error, skip — do not crash.
- Subject: `AI News Brief — <date>`

### SMTPChannel
- Generic SMTP delivery for non-Gmail providers.
- Requires env vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`.
- Configured recipient from `config.delivery.smtp.recipient`.

## Channel Interface

```python
class DeliveryChannel(Protocol):
    def deliver(self, report: Report) -> None: ...
```

Channels are instantiated at startup. Each `deliver()` call is wrapped in try/except — a failing channel is logged and skipped. `FileChannel` always runs last.

## Adding a New Channel

1. Create `delivery/mychanel.py` implementing `DeliveryChannel`.
2. Add it to `config.delivery` schema.
3. Wire it in `agent.py` startup — no other changes needed.
