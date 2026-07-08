# Skills

> On-demand skills following the Claude Code SKILL.md spec. Buckets follow mattpocock's convention: `general/`, `research-pkg/`, `static-site/`, `productivity/`, `personal/`.

## Master TOC

- [How to use](#how-to-use)
- [Skill index](#skill-index)
- [Adding a new skill](#adding-a-new-skill)

## How to use

Three ways to make a skill available to Claude in a downstream project:

1. **Symlink** — `ln -s ~/.claude/agent-harness/skills/general/<name> <project>/.claude/skills/<name>`
2. **Copy** — copy the directory verbatim
3. **Plugin** (P10+) — `/plugin install jajupmochi/agent-harness` registers all skills

The `setup/init-agent-harness` skill (P8) does this automatically based on project type.

Once available, Claude can invoke a skill via the `Skill` tool, or the user via `/<skill-name>`.

## Skill index

| Skill | Bucket | Trigger | Purpose |
|---|---|---|---|
| [`verify-template`](general/verify-template/SKILL.md) | general | `/verify` | Run CI gates locally (ruff + mypy + pytest); customize body per project |
| [`preview-template`](general/preview-template/SKILL.md) | general | `/preview` | Start local dev server; customize per project type |
| [`long-running-tasks`](general/long-running-tasks/SKILL.md) | general | auto / `/long-running-tasks` | Decision tree for handling long-running operations (background subagent vs Monitor vs explicit timeout) |
| [`verify-visual`](general/verify-visual/SKILL.md) | general | auto on UI changes | Use chrome-devtools MCP to screenshot + verify visual changes match a reference |
| [`privacy-redact`](general/privacy-redact/SKILL.md) | general | `/privacy-redact <file>` | Scan a file for usernames, absolute paths, secrets, project codenames; redact with placeholders |
| [`code-verifier`](general/code-verifier/SKILL.md) | general | auto / `/code-verifier` | Three-layer gate before any "tests pass" / "code works" / "results show X" claim — detects FAKE-RUN patterns (hardcoded results, `assert True`, mocks-only tests, etc.) |
| [`research-critic`](general/research-critic/SKILL.md) | general | auto / `/research-critic` | Six-question audit on every research claim (falsifiability, design, fair comparison, leakage, proportional conclusion, alternatives ruled out) |
| [`system-cleanup`](general/system-cleanup/SKILL.md) | general | auto / `/system-cleanup` | Diagnose a full Linux disk then give a prioritized, risk-tagged cleanup (safe user-level deletions + sudo items for the user); covers VS Code WebStorage bloat, old kernels, snap/journal/apt/docker, NTFS data-disk write failures. Ships `cleanup.sh`. |
| [`autoresearch-toolfinder`](general/autoresearch-toolfinder/SKILL.md) | general | auto / `/autoresearch-toolfinder` | Find the right autoresearch / research-agent tool from a local cached index of two awesome-autoresearch lists (alvinreal + yibie, 545 entries); `query.py` returns only the matching few (never loads the whole catalog into context); weekly systemd auto-refresh + SHA-based upstream update tracking |

Future buckets (populated in P7 with templates):

- `research-pkg/` — skills for Python research packages (`new-adapter`, `new-experiment`, …)
- `static-site/` — skills for static personal sites (`new-round`, `deploy-round`, `i18n-sync`)

## Adding a new skill

See [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md) §"Adding a skill".
