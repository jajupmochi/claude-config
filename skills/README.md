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

The `setup/init-agent-config` skill (P8) does this automatically based on project type.

Once available, Claude can invoke a skill via the `Skill` tool, or the user via `/<skill-name>`.

## Skill index

23 skills, plus [`setup/init-agent-config`](../setup/init-agent-config/SKILL.md), which lives under `setup/`. The 24 together are `inventory.skills` in [`adapters/manifest.source.json`](../adapters/manifest.source.json), the list [`bin/deploy-skills.mjs`](../bin/deploy-skills.mjs) symlinks into each agent's native skill directory. A skill left out of that list is never deployed, however long its directory has existed.

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
| [`figma-design-fetch`](figma-design-fetch/SKILL.md) | general | auto on figma.com URL / `/figma-fetch <node-url>` | Full Figma→code pipeline via the official MCP: OAuth connect, pre-fetch design lint, 5-step flow (extract → map to design-system tokens → implement → visual self-check gate → report), gitignored `.design-imports/`; ships `scripts/visual-diff.mjs` (pixelmatch objective gate) + the 6 tested gotchas |
| [`figma-authoring-constraints`](figma-authoring-constraints/SKILL.md) | general | auto (designer asks / empty variables / pixel-snapshot output) | The 20 Figma-side authoring constraints (variables/tokens, auto layout, components/variants, naming, Dev Mode/Code Connect, no raster placeholders) that make a design cleanly code-able — the design half of the figma-design-fetch pipeline |
| [`linux-freeze-triage`](general/linux-freeze-triage/SKILL.md) | general | auto / `/linux-freeze-triage` | Find the real cause of a Linux freeze/black-screen by evidence (rule out sleep, NVIDIA driver kernel/userspace mismatch from auto-upgrades, OOM, PCIe link, DPMS hang); bundles a near-zero-cost watchdog + read-only diagnostic battery |
| [`autopilot`](general/autopilot/SKILL.md) | general | `/autopilot` | Set up or manage the daily autonomous project driver — a system timer that starts one fresh autorun session a day to advance a project, passing review-gate, re-planning, estimating effort formally, and self-healing when stuck |
| [`doc-writing`](doc-writing/SKILL.md) | general | auto on any human-facing document / `/doc-writing` | Document preferences mined from two real project sessions (define every term in place, prove every claim and say how a tester re-proves it, full clickable links, a diagram where one helps). Ships [`scripts/doccheck.py`](doc-writing/scripts/doccheck.py), a linter for the mechanically checkable subset |
| [`task-orchestrator`](task-orchestrator/SKILL.md) | general | auto / `/task-orchestrator` | Research → Design → Plan → Execute → Verify pipeline for every atomic task. Adapts how strict the plan template is to the detected model capability, and records better approaches back into the templates |
| [`task-relationship-analysis`](task-relationship-analysis/SKILL.md) | general | auto before any 3+ task request | Map how the requested tasks relate (synergies, conflicts, shared substrate, ordering) before executing, so three tasks that share one piece are not built three separate times. Scaffolds a pairwise matrix and a synthesis checklist |
| [`memory-flywheel`](memory-flywheel/SKILL.md) | general | auto / `/memory-flywheel` | Per-project cross-session working memory so a long session does not lose detail to context compaction. Records each round to a project memory directory, reads a coarse index first, then opens only what keyword recall points at |
| [`prompt-library`](prompt-library/SKILL.md) | general | `/prompt-library` | Save and reuse good prompts across projects and agents, and mine past ones out of local Claude Code / Codex / Copilot / opencode history into browsable, greppable Markdown |
| [`agent-update-watcher`](agent-update-watcher/SKILL.md) | general | auto / `/agent-update-watcher` | Track the agent ecosystem (new or updated CLIs, plugins, skills) without constant polling. Checks a declared source list only after a minimum interval, then reports only what changed against the recorded version |
| [`tui-installer`](tui-installer/SKILL.md) | general | `/tui-installer` | Install, or only plan, the terminal stack for driving several coding agents on Ubuntu (zellij + claude-squad + lazygit + delta). Dry-run by default; `--apply` asks per tool. Companion to [`recommendations/tui-for-agents.md`](../recommendations/tui-for-agents.md) |
| [`agent-config-adapter`](agent-config-adapter/SKILL.md) | general | auto / `/agent-config-adapter` | Adapt an agent configuration or plugin to another agent or model route — Claude Code, Codex, Gemini, Cursor, local models, or a non-native backend such as DeepSeek |
| [`init-codex-config`](init-codex-config/SKILL.md) | general | `/init-codex-config` | Scaffold or migrate a project to use agent-harness from Codex through `AGENTS.md`, `.codex/hooks.json`, and `.agents/skills`, leaving the original Claude setup untouched |
| [`end-of-turn-marker`](end-of-turn-marker/SKILL.md) | general | auto at end of turn | Close every turn with a visible divider header and numbered summary items carrying `[END:FINAL]`, `[END:WAIT]`, or `[END:NEEDS_USER]`. The skill half of the [`end-of-turn-marker`](../rules/end-of-turn-marker/RULE.md) rule |

Future buckets (populated in P7 with templates):

- `research-pkg/` — skills for Python research packages (`new-adapter`, `new-experiment`, …)
- `static-site/` — skills for static personal sites (`new-round`, `deploy-round`, `i18n-sync`)

## Adding a new skill

See [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md) §"Adding a skill".
