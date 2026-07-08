# Template: research-package-py

> Python research package starter. Based on the patterns in `<research-pkg-A>` and `<research-pkg-C>` (uv + ruff + pytest, optional torch / data / logging extras, manifest-based data, CLI subcommands).

## What you get

| File | Purpose |
|---|---|
| `CLAUDE.template.md` | Project's `CLAUDE.md` skeleton with `@import` lines for relevant rules |
| `README.template.md` | Project README skeleton |
| `pyproject.template.toml` | uv + ruff + mypy + pytest config with research-specific extras (torch, data, logging) |
| `.gitignore` | Standard Python ignores + research-specific (artifacts/, checkpoints/, wandb/, ray_results/) |
| `.claude/settings.template.json` | PostToolUse:Write\|Edit hook running `uv run ruff format` + `ruff check --fix` |
| `.claude/skills/verify/SKILL.md` | Project-specific `/verify` — runs ruff + mypy + pytest |

## Placeholders to replace

After copying:

| Placeholder | Replace with |
|---|---|
| `<PROJECT_NAME>` | Project's name (e.g., `my-research-pkg`) |
| `<PACKAGE_NAME>` | Python module name (e.g., `my_research_pkg`) |
| `<DESCRIPTION>` | One-line description |
| `<AUTHOR_NAME>` | Your name |
| `<AUTHOR_EMAIL>` | Your email |

Quick replace:

```bash
# from project root after copying:
find . -type f \( -name "*.md" -o -name "*.toml" -o -name "*.json" \) -exec sed -i \
  -e "s/<PROJECT_NAME>/my-actual-project/g" \
  -e "s/<PACKAGE_NAME>/my_actual_package/g" \
  -e "s/<DESCRIPTION>/Actual one-line description/g" \
  -e "s/<AUTHOR_NAME>/Real Name/g" \
  -e "s/<AUTHOR_EMAIL>/real@email.com/g" \
  {} +
```

## Required post-setup steps

```bash
# 1. Bootstrap with uv
uv sync --python 3.12

# 2. Install with dev extras
uv pip install -e ".[dev]"

# 3. Verify
uv run pytest -v
uv run ruff check <PACKAGE_NAME>/ tests/

# 4. (Optional) Set up the format-on-edit hook — already in .claude/settings.template.json
mv .claude/settings.template.json .claude/settings.json

# 5. (Optional) Initialize git
git init -b main
git add .
git commit -m "chore: initialize from agent-harness research-package-py template"
```

## Imports applied

The `CLAUDE.template.md` is configured to `@import` these rule snippets (from this lib):

- `pre-edit-confirmation` (universal)
- `phased-planning` (universal)
- `plugin-preflight` (universal)
- `output-brevity` (personal — flip to `optional` if user wants)
- `tool-proactivity` (personal — flip to `optional` if user wants)
- `no-reread-files` (personal)
- `chinese-output` (personal — only if the user wants Chinese final output; setup skill asks)

The `bilingual-docs` rule is **not** included by default (research packages tend to be English-only). Setup skill asks if user wants it.

## Companion

- `tooling/python-uv-ruff/` — same `pyproject.template.toml` philosophy (research extras added here)
- `hooks/ruff-format-on-edit/` — the hook used in `.claude/settings.template.json`
- `skills/general/verify-template/SKILL.md` — generic `/verify` template; `.claude/skills/verify/SKILL.md` here is the research-package customization
