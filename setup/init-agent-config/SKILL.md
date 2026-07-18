---
name: init-agent-config
description: Scaffold a new project with the relevant subset of agent-harness rules, hooks, skills, recommendations, and templates. Asks about project type, language preferences, and context tags, then composes a project-specific CLAUDE.md, .claude/settings.json, and starter files. Use in a fresh or existing project to apply agent-harness conventions.
---

# /init-agent-config

Compose `agent-harness` into a project — interactive scaffold that asks about project type and selects the right subset.

## Master TOC

- [Pre-flight](#pre-flight)
- [Step 1: Detect the current project state](#step-1-detect-the-current-project-state)
- [Step 2: Ask the user 6 questions](#step-2-ask-the-user-6-questions)
- [Step 3: Resolve consumption mode](#step-3-resolve-consumption-mode)
- [Step 4: Compose the project](#step-4-compose-the-project)
- [Step 5: Post-setup verification](#step-5-post-setup-verification)
- [Step 6: Show summary + next steps](#step-6-show-summary--next-steps)
- [Idempotency](#idempotency)

## Pre-flight

Verify (per `plugin-preflight` rule):

- `agent-harness` is locally cloned at `~/.claude/agent-harness/` OR the user has internet access for raw-URL imports OR the plugin is installed
- The current directory is writable and the user is OK adding `CLAUDE.md` / `.claude/` / etc.

If `agent-harness` is not yet cloned and the user wants the local-clone consumption mode:

```bash
git clone https://github.com/jajupmochi/agent-harness.git ~/.claude/agent-harness
```

Ask the user before running this.

## Step 1: Detect the current project state

```bash
# Check if directory is empty
ls -A | wc -l

# Check if it's a git repo
git rev-parse --is-inside-work-tree 2>/dev/null

# Check for existing CLAUDE.md
ls CLAUDE.md 2>/dev/null

# Detect language / framework hints
ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null
```

Branches:

- **Empty directory** → fresh scaffold from a `agent-harness` template
- **Existing project, no CLAUDE.md** → add `CLAUDE.md` + `.claude/` on top of existing code
- **Existing project, with CLAUDE.md** → ask the user: merge with existing? back up first? skip CLAUDE.md and only do `.claude/`?

## Step 2: Ask the user 6 questions

Use `AskUserQuestion` to gather:

1. **Project type** (single-select):
   - Python research package
   - Static personal/portfolio site (HTML/CSS/JS)
   - Frontend application (React / Vue / etc.)
   - Other / custom (skip template, just add rules + tooling)

2. **Bilingual policy** (single-select):
   - Bilingual (EN canonical + zh mirror) for top-level docs
   - English only
   - Chinese only
   - Other / let me decide later

3. **Final-output language preference** (single-select):
   - Chinese (中文) — apply `chinese-output` rule
   - English — skip the rule
   - Other / let me decide later

4. **Context tags** (multi-select — only the matching items get installed):
   - `always` (universal rules: pre-edit-confirmation, phased-planning, plugin-preflight)
   - `research-pkg` (Python tooling: uv + ruff + pytest)
   - `ui-project` (JS/UI/animation/build/test/style)
   - `static-site` (HTML/CSS/JS, i18n, Lighthouse via chrome-devtools)
   - `ml-research` (HF Hub, datasets, gpustat, orchestra-ml-skills)
   - `web-perf` (Lighthouse + a11y tooling)
   - `image-or-video-work` (sharp, ffmpeg, etc.)
   - `docs-site` (mkdocs)
   - `electron-or-desktop` (Electron + electron-builder)

5. **Consumption mode** (single-select):
   - Raw URL imports — always live, requires network
   - Local clone (`~/.claude/agent-harness/`) — fast, offline
   - Plugin install (P10+) — most native; only if `/plugin install jajupmochi/agent-harness` was run

6. **Personal-preference rules** (multi-select):
   - `output-brevity` — no end-of-batch recap, no echo, prefer Edit over Write
   - `tool-proactivity` — fire installed tools without asking
   - `no-reread-files` — trust in-session memory of file contents

## Step 3: Resolve consumption mode

Build the `@import` paths based on the user's choice:

- **Raw URL**: `@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/<path>`
- **Local clone**: `@~/.claude/agent-harness/<path>`
- **Plugin**: (no `@import` lines — plugin auto-loads)

## Step 4: Compose the project

Based on choices, do:

### 4.1 Copy the template (if a project type was selected)

```bash
# Python research:
cp -r ~/.claude/agent-harness/templates/research-package-py/. ./

# Static site:
cp -r ~/.claude/agent-harness/templates/personal-cite-static/. ./
```

### 4.2 Substitute placeholders

Ask the user for:
- `<PROJECT_NAME>`, `<PACKAGE_NAME>`, `<DESCRIPTION>`, `<AUTHOR_NAME>`, `<AUTHOR_EMAIL>` (research)
- `<SITE_NAME>`, `<DESCRIPTION>`, `<AUTHOR_NAME>`, `<AUTHOR_GITHUB>`, `<DEPLOY_URL>` (static)

Then run `find ... -exec sed -i ...` to replace.

### 4.3 Generate the project's CLAUDE.md

Take the template's `CLAUDE.template.md`, then:

- Uncomment the chosen consumption mode block
- Remove the other consumption mode comments
- Filter `@import` lines to only those matching:
  - The user's selected context tags (Step 2.4)
  - The user's personal-preference rules (Step 2.6)
  - The user's language preference (Step 2.3 — include `chinese-output` only if Chinese)
  - The user's bilingual choice (Step 2.2 — include `bilingual-docs` only if bilingual)

Save as `CLAUDE.md`.

### 4.4 Set up .claude/settings.json

Start from the template's `.claude/settings.template.json` (rename → `settings.json`).

Add hook snippets based on context tags:

- `research-pkg` → ruff-format-on-edit hook (already in research-package-py template)
- `static-site` → jq-validate-json hook (already in personal-cite-static template)

Merge with `jq -s '.[0] * .[1]'` if multiple snippets need to combine.

### 4.5 Set up .claude/settings.local.json (per-user, gitignored)

Apply `tooling/permissions-allowlist/settings.local.snippet.json` — common safe Bash patterns.

### 4.6 Install bundled skills

For the chosen template, the project-specific skills (`verify`, `preview`, `verify-visual`, `i18n-sync`) come from the template directly.

For general skills (long-running-tasks, privacy-redact), symlink or copy from `~/.claude/agent-harness/skills/general/`:

```bash
# Symlink (if local clone consumption):
mkdir -p .claude/skills
for skill in long-running-tasks privacy-redact verify-visual; do
  ln -s ~/.claude/agent-harness/skills/general/$skill .claude/skills/$skill
done

# Or copy (if raw-URL or plugin consumption — symlinks won't work for distribution):
for skill in long-running-tasks privacy-redact verify-visual; do
  cp -r ~/.claude/agent-harness/skills/general/$skill .claude/skills/$skill
done
```

### 4.7 Apply tooling templates (if matching context tags)

- `research-pkg` selected → reference `tooling/python-uv-ruff/pyproject.template.toml` (already in research-package-py template)
- `ui-project` selected → reference `tooling/node-nvm/`
- `always` → permissions-allowlist already applied in 4.5

### 4.8 Add recommendations note

Append to the project's `README.md`:

```markdown
## Tooling references

This project follows conventions from [agent-harness](https://github.com/jajupmochi/agent-harness). For tool selection guidance, see:

- [recommendations/cli-tools.md](https://github.com/jajupmochi/agent-harness/blob/main/recommendations/cli-tools.md)
- [recommendations/<context-specific-files>.md](...)
```

(Filter the list to context tags the user picked.)

## Step 5: Post-setup verification

Run:

```bash
# JSON validity for all settings.json files
for f in .claude/settings.json .claude/settings.local.json; do
  [ -f "$f" ] && jq empty "$f" || echo "Invalid: $f"
done

# CLAUDE.md is non-empty and well-formed
head -20 CLAUDE.md

# (For research-pkg) pyproject is valid
[ -f pyproject.toml ] && python3 -c 'import tomllib; tomllib.load(open("pyproject.toml","rb"))'

# git status
git status --short 2>/dev/null
```

If anything fails, surface the error and ask the user how to proceed.

## Step 6: Show summary + next steps

Output something like:

```
✓ /init-agent-config complete

Composed:
- Project type: <selected>
- Consumption mode: <selected>
- Rules applied: <list>
- Hooks: <list>
- Skills: <list>

Next steps:
1. Replace remaining <PLACEHOLDERS> in CLAUDE.md / pyproject.toml / README.md
2. (Research) uv sync --python 3.12 && uv pip install -e ".[dev]"
3. (Static) python3 -m http.server 8000
4. git init && git add . && git commit -m "chore: initialize from agent-harness"
```

## Idempotency

If `/init-agent-config` is run a second time in the same project:

- Detect existing `CLAUDE.md` and `.claude/settings.json`
- Ask: "merge new selections / overwrite / skip"
- Default to merge (additive — new rules added, existing rules untouched)

This makes the skill safe to re-run when adding new context tags later (e.g., a research project that grows a UI dashboard).

## Companion

- The `templates/` directory provides the actual scaffolds
- `recommendations/README.md` defines the context tags this skill uses
- `rules/README.md` lists the workflow rules this skill composes
