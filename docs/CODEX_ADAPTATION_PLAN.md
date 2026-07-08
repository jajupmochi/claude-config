# Codex Adaptation Plan

Date: 2026-07-08
Branch: `codex-adapter`

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
| Setup skill | `setup/init-agent-harness` | Generates `CLAUDE.md`, `.claude/settings.json`, `.claude/skills` | Add `init-codex-config` wrapper that generates `AGENTS.md`, `.codex/hooks.json`, and `.agents/skills` guidance. |
| General skills | 7 | Some tool names and workflows assume Claude Code | Add top-level Codex-compatible skill wrappers under `skills/<name>/SKILL.md`. |
| Workflow rules | 16 in inventory | Rules target `CLAUDE.md` imports and Claude Code editing conventions | Keep source rules; expose through Codex setup as AGENTS.md guidance and through `agent-config-adapter`. |
| Hook recipes | 2 | `.claude/settings.json`, matcher `Write|Edit`, Claude hook stdin fields | Add Codex `hooks.json` with Codex matcher support and stdin field fallbacks. |
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
- Codex hooks are loaded from `hooks.json`, `config.toml`, project `.codex/`, or enabled plugins. Plugin-bundled hooks can use a root `hooks.json`.
- `apply_patch` matchers can use `Edit` or `Write`, but robust scripts should also handle `apply_patch` and multiple event JSON field shapes.

Local validator findings:

- `.codex-plugin/plugin.json` may use `skills: "./skills/"`.
- The local validator rejects unsupported manifest fields such as `hooks`, so hooks should be bundled as root `hooks.json`, matching existing Codex plugin examples.
- The validator checks only immediate subdirectories under `skills/`; every immediate skill directory needs `SKILL.md`.

## Architecture Decision

Use one branch and one repository, with agent-specific entrypoints:

- Claude Code keeps `.claude-plugin/`, `CLAUDE.md`, `setup/init-agent-harness`, `.claude/skills`, and Claude hook snippets.
- Codex gets `.codex-plugin/`, root `hooks.json`, top-level Codex wrapper skills, and Codex install/verification scripts.
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

Completed locally on 2026-07-08:

- `npm run verify:codex` passed.
- `python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py ~/.claude/agent-harness` passed.
- Hook synthetic-event test passed:
  - ruff hook exits 0 on a Python file event.
  - jq hook exits 0 on valid JSON.
  - jq hook exits non-zero with a `decision: "block"` payload on invalid JSON.
- `scripts/install-codex-local.js` completed idempotently:
  - Codex wrapper skills are symlinked under `~/.agents/skills`.
  - Plugin root is symlinked at `~/plugins/agent-harness`.
  - Personal marketplace entry exists at `~/.agents/plugins/marketplace.json`.
