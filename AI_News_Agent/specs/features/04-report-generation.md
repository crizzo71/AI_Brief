# Feature: Report Generation

## Purpose

Compile per-article summaries into a structured, readable Markdown document saved to disk.

## Current Behavior

Produces a flat Markdown file grouped by topic:

```markdown
# AI News Report - YYYY-MM-DD

## Topic Name

- **Source:** <url>
  - **Summary:** <summary text>
```

Articles with empty titles are skipped.

## Required Improvements

- **Deduplication**: If the same URL appears under multiple topics, include it once under the first topic.
- **Article count**: Include a header note like `N articles across M topics`.
- **Empty topic handling**: If a topic produced no successful articles, include a note rather than a blank section.
- **Richer article entry**: Include the article title prominently, not just the URL.

Improved format:
```markdown
# AI News Brief — April 2, 2026
_12 articles across 4 topics_

---

## Agentic Engineering

### Article Title Here
**Source:** [publisher.com](url)
<summary text>

---
```

## Output

- Written to `report.md` in the project directory, overwriting previous run.
- The same string is also returned from `generate_report()` for use by email delivery.
- The file is the canonical artifact of each run; it can be inspected without email access.
