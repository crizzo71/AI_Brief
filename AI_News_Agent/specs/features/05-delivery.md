# Feature: Report Delivery

## Purpose

Deliver the generated report to the user through one or more configurable channels.

## Design: Pluggable Delivery

Delivery is a **port** in the hexagonal architecture sense. The core agent doesn't know or care how the report reaches the user — it hands off a `Report` object to whichever adapters are configured.

Multiple delivery adapters can be enabled simultaneously (e.g., save to file AND send email).

## Delivery Adapters

### `file` (always-on, zero-config)
- Write report to `report.md` in the project directory.
- Serves as a baseline — always works, no credentials needed.
- Also acts as an audit log of past runs (future: append with datestamp rather than overwrite).

### `gmail`
- Send via Gmail API using OAuth 2.0.
- Requires `credentials.json` (Google OAuth client secret) and produces `token.json` on first run.
- Subject: `AI News Brief — <date>`
- Body: report content as plain text (future: HTML rendering of Markdown).
- Graceful degradation: if credentials are missing or auth fails, log the error and skip — do not crash.

### `smtp` (future)
- Generic SMTP for non-Gmail email providers.
- Config: `host`, `port`, `username`, `password` (env var), `from_address`.

### `slack` (future)
- Post to a configured webhook URL.
- Config: `webhook_url` env var, `channel`.

### `webhook` (future)
- HTTP POST to an arbitrary URL with the report as JSON payload.

## Config Schema

```json
{
  "delivery": {
    "file": {
      "enabled": true,
      "path": "report.md"
    },
    "gmail": {
      "enabled": true,
      "recipient": "you@example.com"
    },
    "smtp": {
      "enabled": false
    },
    "slack": {
      "enabled": false
    }
  }
}
```

## Adapter Interface

Each adapter implements a common interface:

```python
class DeliveryAdapter(Protocol):
    def deliver(self, report: Report) -> None:
        ...
```

The agent iterates configured adapters, calls `deliver()`, and catches/logs failures per-adapter without stopping others.

## Current State

Only Gmail is implemented, as a single hard-coded call in `main()`. It will crash if `credentials.json` is absent. This needs to be refactored behind the adapter interface with the file adapter as the always-present fallback.
