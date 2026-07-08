# Template: personal-cite-static

> Static personal academic site starter. Based on the patterns in `<personal-site>` (HTML/CSS/JS, no build, i18n via JSON, GitHub Pages deploy, bilingual docs, chrome-devtools MCP visual verification).

## What you get

| File | Purpose |
|---|---|
| `CLAUDE.template.md` | Project's `CLAUDE.md` with bilingual + Master TOC + visual verification rules + iterative round files convention |
| `README.template.md` | Project README skeleton |
| `index.template.html` | Minimal HTML5 starter with i18n placeholders (`data-i18n` attributes) |
| `locales/en.template.json` + `locales/zh.template.json` | i18n translation skeletons |
| `.gitignore` | Standard ignores + .claude local state |
| `.claude/settings.template.json` | PostToolUse:Write\|Edit hook running `jq empty` on locales/data JSON files |
| `.claude/skills/preview/SKILL.md` | `/preview` — start `python3 -m http.server` |
| `.claude/skills/verify-visual/SKILL.md` | `/verify-visual` — chrome-devtools MCP screenshot + 4-axis critique |
| `.claude/skills/i18n-sync/SKILL.md` | `/i18n-sync` — check key parity across `locales/*.json`, add missing keys |

## Placeholders to replace

After copying:

| Placeholder | Replace with |
|---|---|
| `<SITE_NAME>` | Site title (e.g., "Linlin Jia") |
| `<DESCRIPTION>` | Site description / tagline |
| `<AUTHOR_NAME>` | Your name |
| `<AUTHOR_GITHUB>` | Your GitHub handle |
| `<DEPLOY_URL>` | Deployed URL (e.g., `https://<handle>.github.io`) |

Quick replace:

```bash
find . -type f \( -name "*.md" -o -name "*.html" -o -name "*.json" \) -exec sed -i \
  -e "s/<SITE_NAME>/My Site/g" \
  -e "s/<DESCRIPTION>/My description/g" \
  -e "s/<AUTHOR_NAME>/Real Name/g" \
  -e "s/<AUTHOR_GITHUB>/myhandle/g" \
  -e "s|<DEPLOY_URL>|https://myhandle.github.io|g" \
  {} +
```

## Required post-setup steps

```bash
# 1. (Optional) Move .claude/settings.template.json → .claude/settings.json
mv .claude/settings.template.json .claude/settings.json

# 2. (Optional) Initialize git
git init -b main
git add .
git commit -m "chore: initialize from agent-harness personal-cite-static template"

# 3. Run dev server
python3 -m http.server 8000
# Open http://localhost:8000/index.html

# 4. (Optional) Add additional locales
# - Copy locales/en.template.json → locales/<lang>.json
# - Translate the values (keep the keys identical to en.json)
# - Update <html lang="..."> in index.html if needed
```

## Imports applied

The `CLAUDE.template.md` is configured to `@import` these rules from `agent-harness`:

- `pre-edit-confirmation` (universal)
- `phased-planning` (universal)
- `plugin-preflight` (universal)
- `ui-iteration-loop` (ui-project — critical for static sites)
- `output-brevity` (personal)
- `tool-proactivity` (personal)
- `no-reread-files` (personal)
- `chinese-output` (personal — only if user wants Chinese final output)
- `bilingual-docs` (optional — strongly recommended for personal sites with international audience)

## Companion

- `hooks/jq-validate-json/` — the JSON validity hook used in `.claude/settings.template.json`
- `skills/general/preview-template/SKILL.md` — generic; `.claude/skills/preview/SKILL.md` here is the static-site customization
- `skills/general/verify-visual/SKILL.md` — generic; `.claude/skills/verify-visual/SKILL.md` here is the static-site customization with the iterative-round-file context
- `recommendations/web-auditing.md` — Lighthouse via chrome-devtools MCP for performance / SEO / a11y
