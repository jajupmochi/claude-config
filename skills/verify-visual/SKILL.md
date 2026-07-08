---
name: verify-visual
description: >-
  Visual verification for UI changes using Playwright screenshots and native
  model vision (GPT-5.5, Claude). For models without vision (DeepSeek), uses
  Playwright screenshot capture with pixel comparison for regression detection.
  BackstopJS available as optional regression tool.
policy:
  allow_implicit_invocation: false
---

# verify-visual

## Detection: vision capability

| Model | Vision | Backend |
|---|---|---|
| GPT-5, GPT-5.5 | ✅ native | Model-based screenshot analysis |
| Claude Opus 4+ | ✅ native | Model-based + chrome-devtools MCP |
| DeepSeek V3, DeepSeek R1 | ❌ none | Playwright screenshot capture + pixel comparison |

## Backend 1: Native model vision (GPT-5.5, Claude)

When the model has vision capability, screenshots are captured and analyzed
directly by the model. No external API needed.

## Backend 2: Playwright screenshots (always available)

The `scripts/codex_visual_verify.sh` script captures screenshots at
specified viewports using Playwright or headless Chrome. Works with ANY model.

```bash
VISUAL_VERIFY_URL=https://localhost:3000 bash scripts/codex_visual_verify.sh
```

Output goes to `.visual-verify/YYYY-MM-DD_HHMMSS/` with a `results.json`.

## Backend 3: BackstopJS (pixel-level regression)

BackstopJS compares screenshots pixel-by-pixel against reference images.
No model needed. Good for CI regression testing.

```bash
npx backstopjs init
# Configure backstop.json then:
npx backstopjs test
```

## Workflow

```mermaid
graph TD
    START["/verify-visual &lt;url&gt;"] --> DETECT{"Model has<br/>vision?"}
    DETECT -->|"✅ GPT-5.5, Claude"| VISION["Native model vision<br/>analyze screenshots directly"]
    DETECT -->|"❌ DeepSeek"| SCREENSHOT["Playwright screenshot capture<br/>multiple viewports"]
    SCREENSHOT --> CHOOSE{"Need regression?"}
    CHOOSE -->|"Yes"| BACKSTOP["BackstopJS pixel comparison<br/>against reference images"]
    CHOOSE -->|"No"| REPORT["Return screenshot paths<br/>for manual review"]
    VISION --> REPORT2["Report visual issues<br/>layout, contrast, readability"]
    BACKSTOP --> REPORT2
```

## Configuration

Optional `~/.config/agent-harness/visual-verify.json`:

```json
{
  "viewports": ["1280x720", "375x812", "1920x1080"],
  "reference_dir": "./.visual-verify/reference"
}
```
