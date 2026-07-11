# Installing agent-harness in Claude Code

Each piece of agent-harness reaches a Claude Code session by a **different** mechanism. They are NOT
alternatives — you want all of them:

| Piece | How it reaches the session | Notes |
|---|---|---|
| **Skills** | `~/.claude/skills/<name>` **symlinks** (`bin/deploy-skills.mjs`) | The **reliable, proven** path — user-level skills are offered to the Skill tool every session (this is how `code-verifier` / `research-critic` work). |
| **Commands** (`/figma-fetch`, `/harness-sync`) | the **plugin** (`agent-harness@agent-harness`) | The plugin's real job. |
| **Rules** | your `~/.claude/CLAUDE.md` (always-on) | CC plugins do **not** carry rules (verified: `claude plugin details` lists Skills/Agents/Hooks/MCP/LSP, never rules). |
| **Hooks** | `~/.claude/settings.json` | The plugin ships no hooks on purpose (a plugin hook would double-fire review-gate). |

> **Important — the plugin does NOT deliver skills to a session.** `claude plugin details` *lists* the plugin's
> skills, but a running session's Skill tool is populated from `~/.claude/skills/`, not the plugin. Verified by
> testing: with skills only in the plugin (no symlinks), the harness skills were NOT offered to sessions; after
> `deploy-skills.mjs` re-created the symlinks, they appeared. So **the symlinks are what make skills usable**;
> the plugin is for the `/commands`. Keeping both is fine — CC de-dupes skills by name (no double-listing).

## Install (do both)

```bash
# 1. update / clone the install copy
if [ -d ~/.claude/agent-harness/.git ]; then git -C ~/.claude/agent-harness pull --ff-only; \
else git clone https://github.com/jajupmochi/agent-harness ~/.claude/agent-harness; fi

# 2. SKILLS — deploy as user-level symlinks (the reliable delivery; idempotent, non-clobbering)
node ~/.claude/agent-harness/bin/deploy-skills.mjs --apply --agent claude

# 3. COMMANDS — install the plugin (for /figma-fetch, /harness-sync)
claude plugin marketplace add ~/.claude/agent-harness      # once
claude plugin install agent-harness@agent-harness

# 4. RULES — copy the harness rules you want into ~/.claude/CLAUDE.md (or scaffold per-project with
#    /init-agent-config, which picks the relevant subset). Rules are always-on; skills are judgment-invoked.
```

## Why the plugin.json had to be fixed to install

CC's `plugin.schema.json` rejects the shapes an earlier manifest used (`repository: expected string, received
object` · `skills: Invalid input` · `hooks: Invalid input`). The projector (`adapters/claude.mjs`) now emits a
**string** `repository`, **omits** `hooks` (settings.json owns them), and **omits** the explicit `skills` list
(CC auto-discovers `skills/*/SKILL.md`; listing them too double-counted them in `plugin details`). This makes
the plugin installable so it can carry the `/commands`.

## Verify

```bash
ls ~/.claude/skills/                                  # skills present as symlinks → usable next session
claude plugin details agent-harness | grep -E "Skills|enabled"   # plugin enabled (for its commands)
```

A skill is usable once it resolves under `~/.claude/skills/` **and** the session has (re)started so the Skill
tool picked it up. Skills self-activate from their `SKILL.md` `description` when a task matches — but see the
`tool-proactivity` rule's **skill trigger map**, which pins the high-value ones to their triggers (they were
being skipped when left purely to judgment).

## Already-running session, or one with an OLD copy — no restart

Run the **`/harness-sync`** command: it pulls the repo, redeploys the skill symlinks, and reads the current
rules (esp. the trigger map) into the session's context so they apply now.

```bash
# clear any stale old-name delivery first (safe if absent)
rm -f ~/.claude/skills/claude-config ~/.claude/skills/init-claude-config
```

Caveat: rules read in this way are active immediately (they are in context); a **newly added skill** becomes
Skill-tool-invocable only in the **next** session (CC fixes the Skill list at session start) — until then run it
manually by reading its `~/.claude/skills/<name>/SKILL.md`. Skills already loaded keep working.

> Codex and opencode are separate: Codex uses `codex plugin add agent-harness@personal` (copy-cache — re-run
> after each repo update); opencode reads skills from `~/.config/opencode/skills/` (symlinks via
> `deploy-skills.mjs`). Neither is affected by the Claude plugin.
