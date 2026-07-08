---
name: verify-template
description: Run project verification from Codex before claiming work is done. Use before marking a phase complete, opening a PR, or saying tests/lint/build pass.
---

# verify-template

Read `../general/verify-template/SKILL.md`, then adapt it to Codex:

1. Prefer commands documented in `AGENTS.md`, package manifests, Makefiles, or
   CI config over generic defaults.
2. Run only relevant checks for the files changed.
3. If a command needs network, dependency installation, or writes outside the
   workspace, use Codex approval flow.
4. Report exact commands run and whether each passed, failed, or was skipped.
5. Do not claim success from intended commands or stale output.

For Python, start with `uv run ruff check`, `uv run ruff format --check`,
`uv run mypy`, and `uv run pytest` when the project supports them.

For Node, start with package scripts such as `lint`, `typecheck`, `test`, and
`build`. Do not invent scripts that are not in `package.json`.
