---
name: verify
description: Run the project's CI gate locally — ruff lint, ruff format check, mypy, and fast pytest (excluding slow/download markers). Use before opening a PR or marking work done.
---

# /verify

Run the full verification gate for this `<PROJECT_NAME>` repo. Stop on first failure and report it plainly.

```bash
uv run ruff check <PACKAGE_NAME>/ tests/
uv run ruff format --check <PACKAGE_NAME>/ tests/
uv run mypy <PACKAGE_NAME>/
uv run pytest -m "not slow and not download" -v
```

## Notes for the agent

- Stop on first failure. Report which step failed and the relevant tool output.
- These mirror the GitHub Actions lint + test-core jobs (when CI is set up).
- `mypy` runs in strict mode (`disallow_untyped_defs = true`) — missing type annotations on public APIs will fail.
- If `ruff format --check` fails, run `uv run ruff format <PACKAGE_NAME>/ tests/` to fix, then re-run `/verify`.
- Pytest config is in `pyproject.toml` (`[tool.pytest.ini_options]`) — `slow` and `download` markers are excluded by default.

## Customization

Adjust the source paths if your package structure differs:

- Single package: `<PACKAGE_NAME>/ tests/`
- Plugins folder: `<PACKAGE_NAME>/ tests/ plugins/`
- Multi-package monorepo: list each separately

## Companion

- Generic template: `agent-harness/skills/general/verify-template/SKILL.md`
- Hook: ruff format-on-edit auto-runs after Claude edits — `/verify` covers the broader gate (mypy + pytest)
