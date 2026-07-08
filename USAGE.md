# USAGE — Operation Guide

> Step-by-step walkthroughs for the most common scenarios with `agent-harness`.

> **Language:** English | [中文](USAGE.zh.md)

## Master TOC

- [0. Install agent-harness (once per machine)](#0-install-agent-harness-once-per-machine)
- [1. Bootstrap a new Python research project](#1-bootstrap-a-new-python-research-project)
- [2. Bootstrap a new static personal site](#2-bootstrap-a-new-static-personal-site)
- [3. Add agent-harness to an existing project](#3-add-agent-harness-to-an-existing-project)
- [4. Customize a rule for one project](#4-customize-a-rule-for-one-project)
- [5. Add a new rule / skill / hook to the lib](#5-add-a-new-rule--skill--hook-to-the-lib)
- [6. Update agent-harness to the latest version](#6-update-agent-harness-to-the-latest-version)
- [7. Publish a new version (maintainer)](#7-publish-a-new-version-maintainer)
- [Troubleshooting](#troubleshooting)

## 0. Install agent-harness (once per machine)

Pick one of **6 Claude Code methods**, or use the separate Codex path below. Quick guide:

| Method | Best for | Network at session start | Update mechanism |
|---|---|---|---|
| **A) npx** ⭐ recommended | Fastest one-liner from a terminal | none | `npx ...` again |
| **B) `/plugin` interactive** | Browse-and-install from inside Claude Code | partial | `/plugin update` |
| **C) `/plugin install` direct** | If you already know the plugin name | partial | `/plugin update` |
| **D) Local `git clone`** | Manual control / offline-friendly | none | `git pull` |
| **E) Raw URL `@imports`** | No install at all — just URLs in CLAUDE.md | required | automatic (live) |
| **F) Copy-paste prompt** | Hands-off — let CC do everything | none | re-run prompt |

### A) `npx` (recommended)

The fastest path. Zero config:

```bash
npx github:jajupmochi/agent-harness
```

This runs [`bin/install.js`](https://github.com/jajupmochi/agent-harness/blob/main/bin/install.js) which:
1. Clones the lib to `~/.claude/agent-harness/`
2. Symlinks the `init-agent-harness` skill into `~/.claude/skills/` so `/init-agent-harness` becomes available globally
3. Prints next steps

To update later: `npx github:jajupmochi/agent-harness` again (it detects existing install and prints `git pull` instructions).

### B) `/plugin` interactive (inside Claude Code)

Browse the plugin marketplace and pick agent-harness:

```
/plugin marketplace add jajupmochi/agent-harness
/plugin
# Browse and install agent-harness
```

After install, `/init-agent-harness` is available in any project.

### C) `/plugin install` direct (inside Claude Code)

If you already know the plugin name:

```
/plugin install jajupmochi/agent-harness
```

(Works once the plugin spec stabilizes — the manifest at [`.claude-plugin/plugin.json`](https://github.com/jajupmochi/agent-harness/blob/main/.claude-plugin/plugin.json) is ready.)

### D) Local `git clone` (canonical)

For full manual control:

```bash
git clone https://github.com/jajupmochi/agent-harness.git ~/.claude/agent-harness

# Symlink the init skill so /init-agent-harness is available globally:
ln -s ~/.claude/agent-harness/setup/init-agent-harness ~/.claude/skills/init-agent-harness
```

Update with `cd ~/.claude/agent-harness && git pull`.

### E) Raw URL `@imports` (no install)

You don't install anything. Instead, your project's `CLAUDE.md` has `@import` lines pointing at GitHub raw URLs:

```markdown
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/pre-edit-confirmation/snippet.md
```

Always live, but requires network on session start. The `/init-agent-harness` slash command won't be available globally — you'd manually compose `CLAUDE.md` rather than using the scaffold skill.

### F) Copy-paste prompt to Claude Code

Open Claude Code in any directory (no install needed). Paste this prompt verbatim and Claude will execute the install for you:

> Please install agent-harness from https://github.com/jajupmochi/agent-harness:
>
> 1. Run: `git clone https://github.com/jajupmochi/agent-harness.git ~/.claude/agent-harness`
> 2. Run: `mkdir -p ~/.claude/skills && ln -s ~/.claude/agent-harness/setup/init-agent-harness ~/.claude/skills/init-agent-harness`
> 3. Confirm done and tell me to run `/init-agent-harness` in my project.

Or in Chinese:

> 请帮我从 https://github.com/jajupmochi/agent-harness 安装 agent-harness：
>
> 1. 跑：`git clone https://github.com/jajupmochi/agent-harness.git ~/.claude/agent-harness`
> 2. 跑：`mkdir -p ~/.claude/skills && ln -s ~/.claude/agent-harness/setup/init-agent-harness ~/.claude/skills/init-agent-harness`
> 3. 确认完成后告诉我在项目里跑 `/init-agent-harness`。

This works because Claude Code can execute shell commands and reads the GitHub URL from the prompt.

---

### Codex local activation

Codex uses separate discovery locations from Claude Code. This path does not change `~/.claude` or the Claude plugin install.

```bash
cd ~/.claude/agent-harness
npm run verify:codex
npm run activate:codex
```

The activation script:

1. Symlinks Codex wrapper skills into `~/.agents/skills/`.
2. Symlinks this repository to `~/plugins/agent-harness`.
3. Creates or updates `~/.agents/plugins/marketplace.json`.

Restart Codex or start a new session, then use `/skills` for `init-codex-config` or `agent-config-adapter`. Use `/plugins` to inspect the local plugin entry.

If Codex CLI update fails with `Could not find Codex package or platform npm release assets`, run `npm run update:codex`. The wrapper retries the official installer with an explicit `CODEX_RELEASE` when the latest release metadata and assets are briefly out of sync.

---

## 1. Bootstrap a new Python research project

### Scenario

You're starting a new ML / scientific computing project and want all the conventions from `liulian-python` / `swiss-river-network-benchmark` style: uv + ruff + pytest, optional torch / data / logging extras, mkdocs for docs, ruff format-on-edit hook.

### Steps

```bash
# 1. Create the empty project directory and enter it
mkdir my-research-pkg
cd my-research-pkg

# 2. Open Claude Code
claude

# 3. Run the scaffold skill
/init-agent-harness
```

When prompted, answer:

| Q | Pick |
|---|---|
| Project type | Python research package |
| Bilingual | English only (or EN+zh if you ship Chinese docs) |
| Final-output language | Chinese (or English) |
| Context tags | `always`, `research-pkg`, `docs-site` (skip ui-project, ml-research only if doing ML) |
| Consumption mode | local clone (recommended) |
| Personal preferences | output-brevity, tool-proactivity, no-reread-files |

### Result

```
my-research-pkg/
├── CLAUDE.md                       ← composed from template + chosen rules
├── README.md                       ← from template
├── pyproject.toml                  ← from template, research extras
├── .gitignore                      ← Python + research outputs
├── .claude/
│   ├── settings.json               ← ruff format-on-edit hook
│   ├── settings.local.json         ← permissions allowlist (gitignored)
│   ├── skills/
│   │   ├── verify/SKILL.md         ← project-specific verify
│   │   ├── long-running-tasks/     ← from agent-harness (symlink)
│   │   ├── privacy-redact/         ← from agent-harness (symlink)
│   │   └── verify-visual/          ← from agent-harness (symlink)
└── (your code goes here)
```

### Post-setup commands

Replace placeholders, install deps, verify:

```bash
# Replace placeholders
find . -type f \( -name "*.md" -o -name "*.toml" \) -exec sed -i \
  -e "s/<PROJECT_NAME>/my-research-pkg/g" \
  -e "s/<PACKAGE_NAME>/my_research_pkg/g" \
  -e "s/<DESCRIPTION>/My ML research project/g" \
  -e "s/<AUTHOR_NAME>/Your Name/g" \
  -e "s/<AUTHOR_EMAIL>/you@example.com/g" \
  {} +

# Bootstrap with uv
uv sync --python 3.12
uv pip install -e ".[dev]"

# Initialize git
git init -b main
git add .
git commit -m "chore: initialize from agent-harness research-package-py template"

# Verify
/verify
```

---

## 2. Bootstrap a new static personal site

### Scenario

You're building a personal academic site / portfolio (HTML / CSS / JS, no build step), want bilingual docs, i18n via JSON, deployed via GitHub Pages, with chrome-devtools MCP for visual verification.

### Steps

```bash
# 1. Create the project (typically as <yourhandle>.github.io for GitHub Pages)
mkdir myhandle.github.io
cd myhandle.github.io

# 2. Open Claude Code + run scaffold
claude
/init-agent-harness
```

Answer:

| Q | Pick |
|---|---|
| Project type | Static personal/portfolio site (HTML/CSS/JS) |
| Bilingual | EN+zh (recommended for international audience) |
| Final-output language | Chinese (your preference) |
| Context tags | `always`, `static-site`, `web-perf`, `ui-project` (if you'll use animation libs) |
| Consumption mode | local clone |
| Personal preferences | All three (output-brevity, tool-proactivity, no-reread-files) |

### Result

```
myhandle.github.io/
├── CLAUDE.md / CLAUDE.zh.md (if bilingual)
├── README.md / README.zh.md
├── index.html                        ← from template, i18n-aware
├── locales/
│   ├── en.json                       ← from template
│   └── zh.json                       ← from template (key parity with en)
├── .gitignore
└── .claude/
    ├── settings.json                 ← jq-validate-json hook
    ├── skills/
    │   ├── preview/SKILL.md          ← python3 -m http.server
    │   ├── verify-visual/SKILL.md    ← chrome-devtools MCP
    │   ├── i18n-sync/SKILL.md        ← locale parity check
    │   ├── long-running-tasks/       ← from agent-harness
    │   └── privacy-redact/           ← from agent-harness
```

### Post-setup commands

```bash
# Replace placeholders
find . -type f \( -name "*.html" -o -name "*.json" -o -name "*.md" \) -exec sed -i \
  -e "s/<SITE_NAME>/My Site/g" \
  -e "s/<DESCRIPTION>/My description/g" \
  -e "s/<AUTHOR_NAME>/Your Name/g" \
  -e "s/<AUTHOR_GITHUB>/myhandle/g" \
  -e "s|<DEPLOY_URL>|https://myhandle.github.io|g" \
  {} +

# Run dev server
/preview
# Opens http://localhost:8000/index.html

# Verify visually after edits
/verify-visual

# Initialize git + push to GitHub
git init -b main
git add .
git commit -m "chore: initialize from agent-harness personal-cite-static template"
gh repo create myhandle/myhandle.github.io --public --source=. --push
```

---

## 3. Add agent-harness to an existing project

### Scenario

You already have a working project. You want to retrofit it with `agent-harness`'s conventions without overwriting your code.

### Steps

```bash
cd my-existing-project
claude
/init-agent-harness
```

The skill detects the existing project (has manifest files / has CLAUDE.md / has .git):

- **No `CLAUDE.md`**: Skill creates a new one with `@import` lines.
- **Has `CLAUDE.md`**: Skill asks: merge / back up first / skip CLAUDE.md and only do `.claude/`. Default: **merge** (additive — new rules added, existing rules untouched).

For context tags, pick those matching the existing project's nature. Skill won't copy the template scaffold (since the project already has source).

### What gets added

- `CLAUDE.md` (or amended): `@import` lines for chosen rules
- `.claude/settings.json`: hook recipes for chosen contexts
- `.claude/settings.local.json`: permissions allowlist
- `.claude/skills/`: relevant general skills (long-running-tasks, privacy-redact, verify-visual)

### What's NOT touched

- Your source code
- Your existing `pyproject.toml` / `package.json`
- Your existing `.gitignore` (only appended-to if missing agent-harness patterns)
- Your existing `README.md`

---

## 4. Customize a rule for one project

### Scenario

You like the `output-brevity` rule generally, but for *this specific project* you want Claude to be more verbose (e.g., a new code reader needs more context).

### Option A: Drop the rule for this project only

Edit the project's `CLAUDE.md`, comment out the offending `@import`:

```markdown
<!-- @~/.claude/agent-harness/rules/output-brevity/snippet.md -->
```

Done. Other rules still apply.

### Option B: Override the rule with a project-specific note

Below the imports in `CLAUDE.md`:

```markdown
## Project-specific overrides

Override `output-brevity`: For this project, **do** include end-of-batch summaries because the user is onboarding to a new codebase. Two paragraphs max.
```

Project-specific text appears AFTER the imported snippets, so it wins.

### Option C: Customize globally (affects all consumers)

If the rule itself is wrong (not just project-specific), submit a PR to `agent-harness` with the correction. See section 5.

---

## 5. Add a new rule / skill / hook to the lib

### Scenario

You discover a new behavior worth standardizing (e.g., "always run `prettier --check` before committing JS files").

### Steps

```bash
cd ~/.claude/agent-harness
claude

# For a rule:
/new-rule prettier-check-before-commit

# For a skill:
/new-skill general/format-staged

# For a hook:
/new-hook prettier-format-on-edit
```

Each meta-skill scaffolds the right files (with frontmatter + body templates), reminds you to update `INVENTORY.md` in the same edit batch, and asks for confirmation before committing.

After commit, push:

```bash
git push origin main
```

If you want to cut a release, see section 7.

---

## 6. Update agent-harness to the latest version

### Local clone (Option B install)

```bash
cd ~/.claude/agent-harness
git pull origin main
```

If you have raw-URL `@imports` in projects, they auto-update on next session start (no action needed).

### Plugin install (Option A)

```bash
/plugin update
```

### Pinning a version

To lock to a specific version in a downstream project:

```markdown
<!-- Pin to v0.1.0 instead of main -->
@https://raw.githubusercontent.com/jajupmochi/agent-harness/v0.1.0/rules/<rule>/snippet.md
```

For local clones: `git checkout v0.1.0` in `~/.claude/agent-harness/`.

---

## 7. Publish a new version (maintainer)

```bash
cd ~/.claude/agent-harness
claude
/publish minor
```

The `/publish` skill (under `.claude/skills/publish/SKILL.md`):

1. Verifies clean working tree + on `main` + `gh` authenticated
2. Determines current version from `git tag --list 'v*'`
3. Computes new version (patch / minor / major bump)
4. Generates release notes from git log (grouped by Conventional Commit type)
5. Runs pre-release verification (`jq empty` on JSON, privacy-redact scan)
6. Creates git tag, pushes branch + tag
7. Creates GitHub release with notes

---

## Troubleshooting

### `/init-agent-harness` not found

The setup skill isn't in your CC environment yet:

- **Plugin install**: rerun `/plugin install jajupmochi/agent-harness`
- **Local clone**: symlink the skill into `~/.claude/skills/`:

  ```bash
  ln -s ~/.claude/agent-harness/setup/init-agent-harness ~/.claude/skills/init-agent-harness
  ```

- **Raw URL** (advanced): manual since SKILL.md isn't auto-loaded. Easier to clone or install the plugin.

### Rules don't take effect

Check that:

1. Your project's `CLAUDE.md` actually has the `@import` lines (or the snippets inlined)
2. The path resolves correctly (`@~/.claude/agent-harness/rules/...` for local clone — note the tilde)
3. CC has restarted after CLAUDE.md changes (sometimes needed for `@import` resolution)

### Hook not firing

```bash
# Check the hook is in settings.json:
cat .claude/settings.json | jq '.hooks'

# Manually trigger the matching tool (e.g., Edit a *.py file)
# Then check Claude Code's logs — failed hooks print errors
```

If the hook errors at runtime (e.g., `uv run` not found), make sure `uv` is in `PATH` at the time CC starts. nvm-managed Node also needs the right shell init for CC to see it.

### Need help

- Issue tracker: https://github.com/jajupmochi/agent-harness/issues
- Existing discussions: see closed issues for common questions
