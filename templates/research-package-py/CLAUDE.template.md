# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Master TOC

- [Project](#project)
- [Build & Run](#build--run)
- [Code Style](#code-style)
- [Architecture](#architecture)
- [Workflow rules (imported)](#workflow-rules-imported)
- [Authoritative references](#authoritative-references)

## Project

`<PROJECT_NAME>` — `<DESCRIPTION>`.

## Build & Run

```bash
# Setup (Python 3.12+, uv as package manager)
uv sync --python 3.12 --no-cache
uv pip install -e ".[dev]"

# CLI (if exposed via [project.scripts])
<PROJECT_NAME> --help

# Tests
uv run pytest -m "not slow and not download" -v
uv run pytest -k 'test_name' -v   # single test

# Lint & format
uv run ruff check <PACKAGE_NAME>/ tests/
uv run ruff format <PACKAGE_NAME>/ tests/

# Type-check (if mypy configured)
uv run mypy <PACKAGE_NAME>/
```

For a one-shot CI gate run, use `/verify` (defined in `.claude/skills/verify/SKILL.md`).

## Code Style

- **Formatter**: `ruff format` — single quotes, line-length 88, target py312
- `from __future__ import annotations` in every module
- Google-style docstrings (Args, Returns, Raises)
- Type annotations on all public function signatures
- Imports: stdlib > third-party > local, each group separated by a blank line

See `pyproject.toml` `[tool.ruff]` for the canonical config.

## Architecture

`<DESCRIBE THE LAYER BOUNDARY OR KEY INVARIANT — replace with project specifics>`

Layer → directory map:

- `<PACKAGE_NAME>/` — main package
- `tests/` — pytest test suite
- `experiments/` — per-experiment configs + runners (separate from tests)
- `manifests/*.yaml` — data manifests (if applicable)

## Workflow rules (imported)

This project follows the workflow rules from the author's [agent-harness](https://github.com/jajupmochi/agent-harness) library. Pick the consumption mode (raw URL / local clone / plugin) and uncomment the matching block:

```markdown
<!-- Option 1: Raw URL imports (always live, requires network) -->
<!--
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/pre-edit-confirmation/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/phased-planning/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/plugin-preflight/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/output-brevity/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/tool-proactivity/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/no-reread-files/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/chinese-output/snippet.md
-->

<!-- Option 2: Local clone of agent-harness to ~/.claude/agent-harness (faster, offline) -->
<!--
@~/.claude/agent-harness/rules/pre-edit-confirmation/snippet.md
@~/.claude/agent-harness/rules/phased-planning/snippet.md
@~/.claude/agent-harness/rules/plugin-preflight/snippet.md
@~/.claude/agent-harness/rules/output-brevity/snippet.md
@~/.claude/agent-harness/rules/tool-proactivity/snippet.md
@~/.claude/agent-harness/rules/no-reread-files/snippet.md
@~/.claude/agent-harness/rules/chinese-output/snippet.md
-->

<!-- Option 3: Plugin install (P10+) — /plugin install jajupmochi/agent-harness -->
<!-- (rules are auto-loaded via the plugin) -->
```

The `setup/init-agent-harness` skill picks one option and uncomments.

## Authoritative references

- Project-specific docs go in `docs/` (architecture, ADRs, etc.)
- Code style / build commands: this CLAUDE.md (above)
- Workflow conventions: imported from `agent-harness` (above)
