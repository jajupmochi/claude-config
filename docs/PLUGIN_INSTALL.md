# Installing agent-harness in Claude Code

agent-harness can reach Claude Code two ways. **Pick ONE — running both double-loads every skill.**

| | **A. Plugin install (default, recommended)** | **B. Piecemeal symlinks** |
|---|---|---|
| Skills | the plugin (auto-discovered from `skills/`) | one `~/.claude/skills/<name>` symlink each (`bin/deploy-skills.mjs`) |
| Hooks | `~/.claude/settings.json` (same in both) | `~/.claude/settings.json` |
| Rules | your `~/.claude/CLAUDE.md` (same in both) | your `~/.claude/CLAUDE.md` |
| Switch cost | one install command | one deploy script |

Only **skills** differ between the two. Hooks live in `settings.json` and rules live in `CLAUDE.md` in
BOTH cases — CC plugins do **not** carry rules (verified: `claude plugin details` lists Skills/Agents/Hooks/
MCP/LSP, never rules) and this plugin ships **no** hooks on purpose (a plugin hook would double-fire the
review-gate that `settings.json` already wires). So the ONLY thing to de-duplicate when you switch is the
per-skill symlinks.

## Why the plugin.json looked broken before

CC's `plugin.schema.json` rejects the shapes an earlier manifest used. The installer's own errors were:
`repository: expected string, received object` · `skills: Invalid input` · `hooks: Invalid input`. The
projector (`adapters/claude.mjs`) now emits a **string** `repository`, **omits** `hooks` (settings.json owns
them), and **omits** the explicit `skills` list so CC auto-discovers each `skills/*/SKILL.md` exactly once
(listing them explicitly AND letting CC auto-discover loaded every skill twice — 31 skills / ~3.6k tok vs the
clean 20 skills / ~2.0k tok).

## A. Plugin install (recommended)

```bash
# 1. add this repo as a local marketplace (once)
claude plugin marketplace add ~/.claude/agent-harness      # or the repo path

# 2. install
claude plugin install agent-harness@agent-harness

# 3. DE-DUPLICATE: remove the per-skill symlinks so skills don't load twice.
#    (leave any ~/.claude/skills/<name> that is a REAL directory — that's your own standalone skill.)
for s in ~/.claude/skills/*; do
  [ -L "$s" ] && readlink "$s" | grep -q agent-harness && rm "$s"
done
```

Skills now come only from the plugin; hooks stay in `settings.json`; rules stay in `CLAUDE.md`.

## B. Piecemeal symlinks (alternative)

```bash
claude plugin uninstall agent-harness@agent-harness   # if previously installed
node ~/.claude/agent-harness/bin/deploy-skills.mjs --apply --agent claude
```

## Verify (either method)

```bash
claude plugin details agent-harness     # method A: Skills (20), ~2.0k always-on tok, no dup names
ls -l ~/.claude/skills/ | grep -c 'agent-harness'   # method B: symlink count; method A: expect 0 (deduped)
```

A skill is usable once its name shows in `claude plugin details` (method A) or resolves under
`~/.claude/skills/` (method B). Skills self-activate from their `SKILL.md` `description` when a task matches;
you can also invoke one explicitly by name.

## Using it in ANOTHER session that may already have an OLD copy loaded

A different session (or machine) may have a stale plugin or the old whole-repo `~/.claude/skills/claude-config`
symlink. Reset cleanly, then install:

```bash
# 1. clear stale delivery
rm -f ~/.claude/skills/claude-config ~/.claude/skills/init-claude-config   # old whole-repo / renamed-skill links
claude plugin uninstall agent-harness@agent-harness 2>/dev/null            # old plugin, if any
claude plugin marketplace remove agent-harness 2>/dev/null                 # old marketplace, if any

# 2. point at the current repo and install fresh
git -C ~/.claude/agent-harness pull --ff-only        # bring the install copy up to date
claude plugin marketplace add ~/.claude/agent-harness
claude plugin install agent-harness@agent-harness

# 3. de-duplicate skills (as in section A step 3) and verify
for s in ~/.claude/skills/*; do [ -L "$s" ] && readlink "$s" | grep -q agent-harness && rm "$s"; done
claude plugin details agent-harness
```

Changes take effect in the **next** Claude Code session (plugins load at session start). To confirm they are
active, start a new session and check that a bundled skill (e.g. `memory-flywheel`) is offered when relevant,
or run `claude plugin list` and see `agent-harness@agent-harness … enabled`.

> Codex and opencode are separate: Codex uses `codex plugin add agent-harness@personal` (copy-cache — re-run
> after each repo update); opencode reads skills from `~/.config/opencode/skills/` (symlinks via
> `deploy-skills.mjs`). Neither is affected by the Claude plugin install.
