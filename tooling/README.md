# Tooling Preferences

> The author's opinionated toolchain choices, with **agent-executable bootstrap commands**. Each subfolder gives a "why this over alternatives" + drop-in template configs.

## Master TOC

- [How to use](#how-to-use)
- [Tooling index](#tooling-index)
- [Adding a new tooling category](#adding-a-new-tooling-category)

## How to use

For a new project, the `setup/init-agent-harness` skill (P8) picks the relevant tooling subfolders based on project type. For manual setup, browse the index below and copy/adapt the templates.

## Tooling index

| Folder | Context | What it gives you |
|---|---|---|
| [python-uv-ruff/](python-uv-ruff/README.md) | `research-pkg` | Python toolchain: `uv` (pkg mgr) + `ruff` (lint+format). Drop-in `pyproject.template.toml` with extras pattern, ruff config, pytest config |
| [node-nvm/](node-nvm/README.md) | `ui-project`, `electron-or-desktop` | Node.js via nvm; `package.json` template; install steps for the canonical Node version (22 LTS) |
| [permissions-allowlist/](permissions-allowlist/README.md) | `always` (selectively) | Common `Bash(...)` allowlist entries from the author's real `settings.local.json` files — paste into project-specific `settings.local.json` to silence repeat permission prompts |

## Adding a new tooling category

See [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md) §"Adding tooling". Each tooling subfolder contains:

- `README.md` — what it is, when to choose it over alternatives, install commands with provenance
- Template config files (`pyproject.template.toml`, `package.template.json`, etc.) using `<PROJECT_NAME>` and similar placeholders
- (Optional) a `bootstrap.sh` for one-shot setup
