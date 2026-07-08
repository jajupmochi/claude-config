---
name: verify-visual
description: Use chrome-devtools MCP to screenshot the local site (or a specific element) and visually verify it matches the design intent. Required after every UI-affecting change before marking work done.
---

# /verify-visual

Visually verify a UI change against the design intent or a reference.

## Pre-flight

- Confirm `chrome-devtools` MCP plugin is installed (per `plugin-preflight` rule)
- Confirm dev server is running (use `/preview` first if not — site needs HTTP, not `file://`)

## Steps

1. **Acknowledge** what you're verifying — re-state the change and the reference (1 line).
2. **Navigate** to `http://localhost:8000/<page>.html` via chrome-devtools `navigate`.
3. **Screenshot** the relevant element (or full page) via `take_screenshot`.
4. **Self-critique** on the 4 axes (per `ui-iteration-loop` rule):
   - **Color** — palette, contrast, accent
   - **Typography** — font, weight, size, line-height
   - **Spacing** — padding, margin, gap, rhythm
   - **Ornamentation** — borders, shadows, decorations
5. **Show user** the screenshot + 1-line verdict (match / off / specific axis).

## Output format

```
Verifying <change> against <reference> — 4 axes:
- Color: ✓
- Typography: ✓
- Spacing: ⚠ tighter than reference
- Ornamentation: ✓

Screenshot: <path>
Verdict: 80% match. Tighten rhythm next?
```

## When NOT to use

- Micro-edits (single property tweak, copy fix) — skip per `output-brevity` rule
- Themes other than default need separate verification — verify each theme that's affected

## Round-file context

When iterating via `index_v{N}_round{M}.html` files (per the iterative workflow):
- Always serve the round file: `http://localhost:8000/index_v{N}_round{M}.html`
- Compare against the previous round file or against `index.html` (current deployed)
- Don't promote `round3` to `index.html` until visual verification on round3 passes

## Lighthouse integration

For performance / SEO / a11y audits beyond visual, use chrome-devtools MCP's `lighthouse_audit` (Chrome's built-in Lighthouse — zero install). For headless / CI runs, see `agent-harness/recommendations/web-auditing.md`.

## Companion rules

- `ui-iteration-loop` — when user provides a visual reference, run the autonomous 8-iteration loop
- `plugin-preflight` — verify chrome-devtools MCP installed before first invocation
- `tool-proactivity` — fire automatically on UI-affecting tasks (with announcement)
