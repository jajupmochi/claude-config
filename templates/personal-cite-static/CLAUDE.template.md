# CLAUDE.md

> **Language:** English | [中文](CLAUDE.zh.md)

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Master TOC

- [Project](#project)
- [Main files](#main-files)
- [Iterative workflow (mixed mode)](#iterative-workflow-mixed-mode)
- [Hard rules](#hard-rules)
- [Preview](#preview)
- [Git / deploy](#git--deploy)
- [Workflow rules (imported)](#workflow-rules-imported)

## Project

`<SITE_NAME>` — `<DESCRIPTION>`. Hosted on GitHub Pages (`<AUTHOR_GITHUB>/<REPO>`). Pure static HTML/CSS/JS — no build system, no bundler. Deployed at `<DEPLOY_URL>`.

## Main files

- `index.html` — the deployed site
- `locales/{en,zh,...}.json` — i18n translations loaded by `index.html`
- `data/*.json` — site data (citations, projects, etc.) loaded at runtime
- `css/main.css` — main stylesheet
- `js/main.js` — main script (i18n loader, theme switcher, etc.)
- `docs/` — project docs (PLAN.md, UPDATES.md if used; setup guides)

## Iterative workflow (mixed mode)

- **Small edits** (copy tweak, single style fix, typo): edit `index.html` directly.
- **Large edits** (new section, redesign, feature): create `index_v{N}_round{M}.html` as a working copy. Three rounds per version — round1 core change, round2 refinement, round3 polish. When round3 is approved, copy its contents to `index.html`.
- The next version `N` is one greater than the highest existing `index_v{N}_round*.html`.
- Old `v{N}_round{M}.html` files are intentional — do not delete them without asking.

The `/new-round` skill (in `.claude/skills/`) automates the version detection. The `/verify-visual` skill is required between rounds.

## Hard rules

- **Visual verification is required.** Every UI-affecting change must be verified in a real browser via `chrome-devtools` MCP plugin (navigate, snapshot, inspect) before being marked done. Passing code review or a successful edit alone is not enough.
- **JSON validity.** `locales/*.json` and `data/*.json` must stay valid JSON — a syntax error breaks the deployed site (CORS-loaded JSON returns 500). The `jq-validate-json` hook (in `.claude/settings.json`) catches this at edit time.
- **i18n key parity.** All `locales/*.json` files must have identical key trees. Use `/i18n-sync` to check parity. If you add a key to one, add it to all.
- **Bilingual docs.** Repo-level human-facing docs ship as `NAME.md` (English, canonical) + `NAME.zh.md` (Chinese mirror). See the imported `bilingual-docs` rule below. Exceptions: this `CLAUDE.md` (Claude is the primary reader; English-only is fine), `CLAUDE.local.md` (private).

## Preview

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000/index.html`. **Do not use `file://`** — it breaks `fetch()` calls (CORS-loaded JSON fails). Use the dev server.

## Git / deploy

- Remote: `<DEPLOY_URL>` (GitHub Pages, deploys from `main` branch automatically — no CI config needed)
- Before committing: run `git status` and `git diff` so the user can review. Do not commit unless explicitly asked.
- Commit messages: `feat:`, `fix:`, `style:`, `docs:`, `chore:` (Conventional Commits).

## Workflow rules (imported)

This project follows the workflow rules from [agent-harness](https://github.com/jajupmochi/agent-harness). Pick consumption mode and uncomment:

```markdown
<!-- Option 1: Raw URL imports (always live, requires network) -->
<!--
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/pre-edit-confirmation/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/phased-planning/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/plugin-preflight/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/ui-iteration-loop/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/output-brevity/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/tool-proactivity/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/no-reread-files/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/chinese-output/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/bilingual-docs/snippet.md
-->

<!-- Option 2: Local clone of agent-harness to ~/.claude/agent-harness -->
<!--
@~/.claude/agent-harness/rules/pre-edit-confirmation/snippet.md
@~/.claude/agent-harness/rules/phased-planning/snippet.md
@~/.claude/agent-harness/rules/plugin-preflight/snippet.md
@~/.claude/agent-harness/rules/ui-iteration-loop/snippet.md
@~/.claude/agent-harness/rules/output-brevity/snippet.md
@~/.claude/agent-harness/rules/tool-proactivity/snippet.md
@~/.claude/agent-harness/rules/no-reread-files/snippet.md
@~/.claude/agent-harness/rules/chinese-output/snippet.md
@~/.claude/agent-harness/rules/bilingual-docs/snippet.md
-->

<!-- Option 3: Plugin install (P10+) — /plugin install jajupmochi/agent-harness -->
```

The `setup/init-agent-harness` skill picks one option and uncomments.
