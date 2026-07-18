# CLI Tools

> System-level and Python-user CLIs. **Context:** mostly `always`; specialized tools have explicit context tags.

## Master TOC

- [System / shell CLIs](#system--shell-clis)
- [Python user-installed CLIs (uv-managed)](#python-user-installed-clis-uv-managed)
- [Optional / nice-to-have](#optional--nice-to-have)

## System / shell CLIs

| Tool | Context | Why | Install |
|---|---|---|---|
| `jq` | `always` | JSON CLI processor (every CC hook uses it) | `sudo apt install jq` (Debian/Ubuntu) / `brew install jq` (macOS) |
| `gh` | `always` | GitHub CLI; CC monitors GitHub Actions via this | `sudo apt install gh` / `brew install gh` |
| `ripgrep` (`rg`) | `always` | Fast grep alternative; CC wraps `rg` as a built-in tool. For interactive shell: install separately | `sudo apt install ripgrep` |
| `pre-commit` | `research-pkg` | Git pre-commit hook framework | `uv tool install pre-commit` |
| `shellcheck` | `always` (when bash scripts present) | Shell script linter | `sudo apt install shellcheck` |

## Python user-installed CLIs (uv-managed)

The author's canonical Python toolchain — install only what the project needs.

| Tool | Context | Why | Install |
|---|---|---|---|
| `uv` | `research-pkg` (always for Python) | Canonical Python package manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `ruff` | `research-pkg` | Linter + formatter (replaces black + flake8 + isort) | `uv tool install ruff` |
| `mypy` | `research-pkg` (when strict typing) | Static type checker | `uv tool install mypy` |
| `huggingface_hub[cli]` (`hf` / `huggingface-cli`) | `ml-research` | HF Hub access | `uv tool install huggingface-hub` (or `pip install -U "huggingface_hub[cli]"`) |
| `gpustat` | `ml-research` | Compact `nvidia-smi` alternative | `uv tool install gpustat` |
| `mkdocs` + `mkdocs-material` | `docs-site` | Markdown → HTML site generator | `uv pip install mkdocs mkdocs-material` (project-local) |
| `httpie` | `optional` | Friendly HTTP CLI | `uv tool install httpie` |

**Why uv (not pip)**: 10–100× faster, manages Python versions, handles project envs, replaces `pipx` for tool installs. The author's three Python projects all use uv.

## Optional / nice-to-have

These improve the dev loop but aren't required. **Context:** `optional` for all — install only when you'll use them often.

| Tool | Why | Install |
|---|---|---|
| `fd-find` (`fd`) | Faster `find` with friendlier syntax | `sudo apt install fd-find` (binary is `fdfind`; alias to `fd`) |
| `bat` | `cat` with syntax highlighting + git diff awareness | `sudo apt install bat` |
| `fzf` | Interactive fuzzy finder; pairs well with shell history search | `sudo apt install fzf` |
| `delta` | Better `git diff` viewer | Cargo or `.deb` from `dandavison/delta` GitHub releases |
| `lazygit` | TUI git client | `.deb` from `jesseduffield/lazygit` releases |
| `hyperfine` | CLI benchmarker | `sudo apt install hyperfine` |
| `act` | Run GitHub Actions locally — useful for debugging GHA workflows offline | `gh extension install nektos/gh-act` (or `nektos/act` binary). **Note**: download is sizable; ask user before installing. CC can also monitor real GHA runs via `gh run list / view`. |

**Install context decision**: by default, `setup/init-agent-config` (P8) installs only the `always` and matching-project-type tools. Optional tools are installed only when the user opts in.
