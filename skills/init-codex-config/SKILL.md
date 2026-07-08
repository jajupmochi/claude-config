---
name: init-codex-config
description: Scaffold or migrate a project to use agent-harness from Codex. Use when applying agent-harness in Codex, converting Claude Code setup to AGENTS.md/.codex/.agents, or making a project ready for Codex skills and hooks without changing the original Claude setup.
---

# init-codex-config

Apply `agent-harness` to a project for Codex. This is the Codex counterpart to
`setup/init-agent-harness/SKILL.md`; read that source skill before adapting a
project, then translate only the selected pieces into Codex surfaces.

## Preflight

1. Locate this repository. Prefer the current plugin root; otherwise check
   `~/.claude/agent-harness`.
2. Read:
   - `../../docs/CODEX_ADAPTATION_PLAN.md`
   - `../../INVENTORY.md`
   - `../../rules/README.md`
   - `../../setup/init-agent-harness/SKILL.md`
3. Inspect the target project for existing `AGENTS.md`, `.codex/`,
   `.agents/skills`, `.claude/`, `CLAUDE.md`, package manifests, and Git
   status.
4. Do not edit `.claude/` or `CLAUDE.md` unless the user explicitly asks for
   Claude Code changes too.

## Decide the Codex surfaces

- Durable project guidance goes in `AGENTS.md`, not `CLAUDE.md`.
- Codex project hooks go in `.codex/hooks.json`.
- Repo-scoped Codex skills go in `.agents/skills/<skill-name>/SKILL.md`.
- User-wide Codex skills go in `~/.agents/skills`.
- Reusable distribution goes through `.codex-plugin/plugin.json` and a
  marketplace entry.
- MCP or app integrations belong in Codex MCP/app config, not in AGENTS.md.

## Questions

If the user has not already provided answers, gather these decisions. In plan
mode, use the available user-input tool. Outside plan mode, ask only the
questions that affect file writes.

1. Project type: Python research, static site, frontend app, or custom.
2. Language policy: English, Chinese, bilingual, or leave unchanged.
3. Context tags: `always`, `research-pkg`, `ui-project`, `static-site`,
   `ml-research`, `web-perf`, `image-or-video-work`, `docs-site`,
   `electron-or-desktop`.
4. Which personal rules to include: output brevity, tool proactivity,
   no reread, writing style, human-readable output, autorun mode.
5. Skill scope: repo `.agents/skills` or user `~/.agents/skills`.
6. Hook scope: project `.codex/hooks.json`, plugin bundled hooks, or no hooks.

When the user says `autorun`, choose conservative defaults and continue unless
a file overwrite, dependency install, network call, or destructive operation
needs approval.

## Compose for Codex

1. Preserve any existing `AGENTS.md`; merge additively or create
   `AGENTS.md.bak.<date>` before replacing.
2. Generate `AGENTS.md` with concise instructions. Do not paste the full rule
   library. Include references to selected source rule files, for example:
   `Rules source: ~/.claude/agent-harness/rules/phased-planning/RULE.md`.
3. If hooks are selected, create `.codex/hooks.json` from this plugin's root
   `hooks.json`, then adjust path globs for the target project.
4. If repo skills are selected, copy the relevant top-level Codex wrapper
   skill directories from this repository into `.agents/skills/`.
5. If a template is selected, use the corresponding template directory as a
   source, but translate Claude-specific files:
   - `CLAUDE.template.md` -> summarized `AGENTS.md`
   - `.claude/settings.template.json` -> `.codex/hooks.json`
   - `.claude/skills` -> `.agents/skills`
6. Add a short README note only when the project already has a README and the
   user wants provenance recorded.

## Verification

Run checks proportional to the files written:

- `jq empty` on every JSON file created or changed.
- `python3 -c 'import tomllib; ...'` for TOML files if present.
- `rg -n "CLAUDE|\\.claude" AGENTS.md .codex .agents` to ensure Codex files do
  not accidentally claim to be Claude configuration, except in provenance text.
- `git status --short` to report changed files.

Do not claim that hooks or skills are active in the current Codex session until
they have been installed in a discovered location and a new session or reload
has picked them up.
