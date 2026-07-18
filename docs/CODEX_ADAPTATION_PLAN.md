# Codex Adaptation Plan

Date: 2026-07-14
Branch: `fix/codex-runtime-adapter`

## Locations

- Claude Code installed skill path: `~/.claude/skills/agent-harness`
- Local Git repository: `~/.claude/agent-harness`
- Git remote: `https://github.com/jajupmochi/agent-harness.git`
- Codex manual used for this plan: `/tmp/openai-docs-cache/codex-manual.md`

`~/.claude/skills/agent-harness` is a symlink to the repository.

## Current Function Inventory

| Area | Current items | Claude-specific behavior | Codex adaptation |
|---|---:|---|---|
| Plugin manifest | `.claude-plugin/plugin.json` | Claude Code plugin manifest | Add separate `.codex-plugin/plugin.json`; do not change Claude manifest semantics. |
| Setup skill | `setup/init-agent-config` | Generates `CLAUDE.md`, `.claude/settings.json`, `.claude/skills` | Add `init-codex-config` wrapper that generates `AGENTS.md`, `.codex/hooks.json`, and `.agents/skills` guidance. |
| General skills | 20 tested user links | Some tool names and workflows assume Claude Code | Install an explicit name-to-source map under `~/.agents/skills`; keep plugin skills as an additional discovery surface. |
| Workflow rules | 16 in inventory | Rules target `CLAUDE.md` imports and Claude Code editing conventions | Keep source rules; expose through Codex setup as AGENTS.md guidance and through `agent-config-adapter`. |
| Hook recipes | 3 commands | `.claude/settings.json`, matcher `Write|Edit`, Claude hook stdin fields | Keep root `hooks.json` as a source template and render absolute commands into user or project Codex hooks. |
| Recommendations | 15 active lists plus 2 references | Names emphasize Claude Code plugins and marketplaces | Keep lists; add adapter workflow to re-evaluate agent-specific recommendation files before use. |
| Tooling | 3 categories | Mostly agent-neutral, with Claude settings-local examples | Reuse as references; map permissions examples to Codex approval/sandbox guidance where relevant. |
| Templates | 2 project starters | Include `CLAUDE.template.md` and `.claude/settings.template.json` | Leave intact for Claude; Codex setup uses them as content source and emits Codex-side files. |
| Maintainer skills | 4 under `.claude/skills` | Claude slash-command style | Keep Claude-only; document how to port later if needed. |
| NPM installer | `bin/install.js` | Installs to `~/.claude` and symlinks Claude skill | Add Codex install script rather than overloading the Claude installer. |

## Research Findings

Codex manual findings:

- Skills are discovered from `.agents/skills` in repo/user/admin/system scopes and can also be bundled in plugins.
- Codex plugin manifests must live at `.codex-plugin/plugin.json`.
- Local plugins are surfaced through a marketplace file, commonly `~/.agents/plugins/marketplace.json` or repo `.agents/plugins/marketplace.json`.
- Installed plugin skills can be selected through `/skills`; direct user skills in `~/.agents/skills` also appear in `/skills`.
- Codex hooks are loaded from user/project `hooks.json`, `config.toml`, or enabled plugins. Current plugin docs default to `hooks/hooks.json` unless the manifest declares another path; a root `hooks.json` is not implicitly bundled.
- Hook commands execute with the session working directory. Relative `./scripts/...` commands are therefore templates, not safe installed commands.
- Standalone custom Agents are discovered from `~/.codex/agents/*.toml` and can set model, effort, sandbox, and instructions for spawned sessions.
- A personal marketplace entry with `INSTALLED_BY_DEFAULT` can appear as **Admin Installed** with no enable control. `codex plugin list` is the authoritative local status check.
- The public `openaiDeveloperDocs` MCP endpoint needs no OAuth. `Status=enabled` with `Auth=Unsupported` means OAuth login is unavailable, not that the transport failed.
- `apply_patch` matchers can use `Edit` or `Write`, but robust scripts should also handle `apply_patch` and multiple event JSON field shapes.

Local validator findings:

- `.codex-plugin/plugin.json` may use `skills: "./skills/"`.
- The tested local architecture deliberately keeps hooks user-scoped rather than also declaring plugin hooks, preventing duplicate lifecycle execution.
- The validator checks only immediate subdirectories under `skills/`; every immediate skill directory needs `SKILL.md`.

## Architecture Decision

Use one branch and one repository, with agent-specific entrypoints:

- Claude Code keeps `.claude-plugin/`, `CLAUDE.md`, `setup/init-agent-config`, `.claude/skills`, and Claude hook snippets.
- Codex gets `.codex-plugin/` for policy-installed plugin skills; an explicit 20-skill user set; `codex/` user guidance and custom Agents; and root `hooks.json` rendered to absolute user/project commands.
- Shared knowledge stays in `rules/`, `recommendations/`, `tooling/`, `templates/`, and source skill bodies.

Alternatives considered:

| Option | Pros | Cons | Decision |
|---|---|---|---|
| One branch per agent | Strong isolation; no accidental cross-agent load | Hard to compare, merge, publish, or share common fixes; README branch selection adds agent burden | Reject for now |
| One branch with mixed files | Simple repo operations; shared docs stay in sync | Can increase context and accidental loading if entrypoints are not separated | Accept with strict agent-specific entrypoints |
| Separate adapter plugin | Clean reusable workflow for future agents/models | Needs an extra artifact and install step | Implement as `agent-config-adapter` skill inside the Codex plugin first |

## Execution Tasks

1. Create Codex plugin manifest.
2. Add Codex-compatible skill wrappers:
   - `init-codex-config`
   - `agent-config-adapter`
   - wrappers for the seven reusable skills
   - `general` aggregator to satisfy validator for the existing `skills/general` directory
3. Add Codex `hooks.json` with robust ruff and jq hook commands.
4. Add scripts:
   - `scripts/install-codex-local.js` for user-scope `/skills` discovery and personal marketplace setup.
   - `scripts/verify-codex-adapter.js` for structural validation.
5. Update README/USAGE/INVENTORY references without changing Claude-specific install paths.
6. Validate:
   - plugin validator passes
   - every top-level Codex skill has valid frontmatter
   - `hooks.json` parses and contains supported Codex events
   - install script dry-run reports the intended symlinks/marketplace entry
   - Git diff shows Claude manifest/source paths are preserved

## 2026-07-14 Runtime Reconciliation

The deployed machine is the behavioral baseline. The adapter uses one Codex surface per responsibility:

| Source item | Codex surface | Rewrite/install rule | Verification | Isolation risk |
|---|---|---|---|---|
| Plugin manifest and top-level skills | personal marketplace + `.codex-plugin/plugin.json` | Keep `INSTALLED_BY_DEFAULT`; do not ask users to enable an Admin Installed entry | `codex plugin list`, `/plugins`, `/skills` | Does not change Claude manifest |
| Tested skill set | `~/.agents/skills` | Install the explicit 20-entry name-to-source map, including nonuniform paths | isolated-HOME installer test | User files with different targets are not overwritten |
| Global behavior | `~/.codex/AGENTS.md` | Copy concise `codex/AGENTS.md`; skip different content unless `--force` | byte comparison in installer test | Project rules stay in nearest project `AGENTS.md` |
| Lifecycle enforcement | `~/.codex/hooks.json` | Render root template commands to absolute repository paths | ruff red→green test, jq synthetic event, review-gate test | Do not also declare plugin hooks |
| Custom subagents | `~/.codex/agents/*.toml` | Install four canonical profiles from `codex/agents/` | isolated install + TOML parse; runtime model identity may remain unobservable | Parent approval/sandbox remains authoritative |
| Model tiers | `adapters/models.config.json` + reviewed `config.toml` | high=`sol/xhigh`, mid=`terra/high`, small=`luna/medium`; reviewer is terra/xhigh | `scripts/test_resolve_model.mjs` | Installer does not overwrite `config.toml` |
| Official Docs MCP | reviewed `config.toml` | Anonymous Streamable HTTP endpoint; no OAuth login step | `codex mcp list`, `/mcp` | MCP config stays separate from AGENTS.md |
| Existing task fallback | prompt context + explicit scripts | Trust does not prove an old task rebuilt hooks/MCP/Agent catalogs | temporary lifecycle event plus direct script check | New task remains the only full startup-chain proof |

The current-session `harness_explorer` test proved subagent creation and read-only task completion. The collaboration runtime did not expose the spawned model or custom profile, so it is not evidence that `gpt-5.6-terra/high` was selected. The file schema and future fresh-session behavior remain separately verifiable.

## Future Agent/Model Adaptation Protocol

When adapting this configuration to another agent or to a non-native model routed through an agent:

1. Identify the host agent surfaces: durable instructions, skills, plugin/package format, hooks, MCP/tools, approvals, and install discovery.
2. Identify model gaps: weak tool-calling, no implicit skill selection, limited context, poor long-horizon planning, or missing structured outputs.
3. Build a minimal adapter skill first; use it to drive the migration rather than pasting all rules into global context.
4. Convert only the entrypoints needed by that agent. Keep shared content as references.
5. Add explicit fallback routes for non-native models:
   - prefer explicit skill invocation if implicit matching is weak
   - use smaller wrapper prompts around large references
   - require concrete verification commands before success claims
   - keep model-specific instructions in the adapter, not in shared rules
6. Validate with structural checks and at least one task prompt per major function.

## Current Verification Status

Completed locally on 2026-07-14:

- `npm run verify:codex` passed.
- `python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py ~/.claude/agent-harness` passed.
- Hook synthetic-event test passed:
  - ruff hook exits 0 on a Python file event.
  - jq hook exits 0 on valid JSON.
  - jq hook exits non-zero with a `decision: "block"` payload on invalid JSON.
- `scripts/install-codex-local.js` completed idempotently:
  - The tested 20-skill user set is symlinked under `~/.agents/skills`.
  - Plugin root is symlinked at `~/plugins/agent-harness`.
  - Personal marketplace entry exists at `~/.agents/plugins/marketplace.json`.
  - User AGENTS/hooks and four custom Agent profiles match the canonical sources after activation.
- `codex plugin list` reports `agent-harness@personal` as `installed, enabled`; the UI's Admin Installed label is expected.
- `codex mcp list` reports `openaiDeveloperDocs` as `enabled`; `Auth=Unsupported` is expected for the anonymous endpoint.
- Current-task native hook dispatch was not observable after late trust, while direct hook events passed. Documentation now requires a real lifecycle event or a new task before claiming native activation.
