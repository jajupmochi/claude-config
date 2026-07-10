# Making a tool work across all agents (Claude Code · Codex · opencode)

Task 12. agent-harness generalizes each sub-tool to every supported agent with **two proven patterns** plus a
set of **native-format bridges**. Follow this when adding or generalizing a plugin/skill/hook so it is not
Claude-only. All three patterns are already in the repo — copy them.

## Pattern 1 — Config projection (one canonical source → generated per-agent config)

When a tool needs a per-agent *manifest / config file*, do NOT hand-maintain N copies. Declare it once in a
canonical source and **generate** each agent's native file with a projector.

- Canonical source: `adapters/manifest.source.json` (inventory + per-agent blocks) and, for models,
  `adapters/models.config.json`.
- Projectors: `adapters/claude.mjs`, `adapters/codex.mjs`, `adapters/opencode.mjs` — each a pure function
  `render(source) -> string`. `build.mjs` runs them; `build.mjs --check` is the CI drift gate;
  `adapters/test-projection.mjs` asserts byte-parity with the committed output.
- **Add a new agent = add one projector** and wire it into `build.mjs` + the parity test. Nothing else moves.

Consequence: the Claude plugin manifest, the Codex plugin manifest, and `opencode.json` all come from one
place, so they cannot drift.

## Pattern 2 — Shared logic + thin per-agent shims (for hooks / behavior)

When a tool has *behavior* that differs only in delivery per agent (e.g. a Stop-hook review), put the
agent-neutral logic in a **core** and give each agent a thin **shim** that adapts I/O + the native contract.

- Reference: review-gate. `hooks/review-gate/scripts/core.sh` computes the review (agent-neutral, env-driven:
  `RG_STATE_DIR` / `RG_SID`; prints markdown iff a review is due). Shims:
  - Claude: `hooks/review-gate/scripts/gate.sh` → wraps core output in Claude's `decision:block` JSON.
  - Codex: `scripts/codex_review_gate.sh` → feeds core its git-detected changes, wraps in Codex's
    `systemMessage`/`decision` JSON, adds Codex-only git guards.
  - opencode: `.opencode/plugin/review-gate.js` (+ tested `lib/run-core.mjs`) → calls core on `session.idle`.
- **Add a new agent = add one shim** over the same core. The reviewed *logic* lives in exactly one place.

## Native-format bridges (map one artifact to each agent's discovery path)

| Artifact | Claude Code | Codex | opencode |
|---|---|---|---|
| **Skills** | `.claude/skills/<name>/SKILL.md` (+ plugin manifest `skills[]`) | `skills/` glob in `.codex-plugin/plugin.json` | reads `.claude/skills/` **natively** (no translation) |
| **Rules** | plugin manifest `rules[]` | (bundled with skills) | `instructions[]` glob in `opencode.json` |
| **Hooks** | `.claude-plugin` + `settings.json` hook wiring | root `hooks.json` + `scripts/*.sh` | JS plugin in `.opencode/plugin/*.js` (auto-discovered) |
| **Model tiers** | advisory for sub-agent routing (can't switch mid-session) | external tooling (cc-switch) | `model`/`small_model` generated from `models.config.json` |

## Checklist — generalizing a new tool

1. Is it **config** (a file an agent reads) or **behavior** (a hook/action)?
   - Config → Pattern 1 (add to the canonical source; extend/add a projector).
   - Behavior → Pattern 2 (core + one shim per agent).
2. Keep the LOGIC agent-neutral; keep only I/O + native format in the shim.
3. Add a **byte-parity / golden test** for each generated artifact, and a unit test for the core.
4. Note the **preferred LLM tier** per agent (via `models.config.json`) if the tool spawns work.
5. Red line: never auto-configure provider switching for Claude Code (account-ban risk).
6. If the tool ships private-looking data, load it from a **local, un-published** file (see `prompt-library`),
   never hardcode usernames/paths/codenames under content dirs (the CI privacy scan will reject them).

## Status

The two patterns + bridges are live (review-gate across 3 agents; 3 manifest projectors from one source).
Not every legacy tool has been re-expressed through them yet — that migration is ongoing; new tools should be
built this way from the start.
