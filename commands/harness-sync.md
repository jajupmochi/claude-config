---
description: "Update agent-harness and activate its latest rules + skills in THIS running session (no restart)"
argument-hint: ""
allowed-tools: ["Bash", "Read", "Skill"]
---

# /harness-sync

Bring agent-harness up to date and **activate its latest rules + skills in the CURRENT session without a
restart**. Run these with the Bash tool and report each:

1. **Update the install copy** (clone if missing):
   ```bash
   if [ -d ~/.claude/agent-harness/.git ]; then git -C ~/.claude/agent-harness pull --ff-only; \
   else git clone https://github.com/jajupmochi/agent-harness ~/.claude/agent-harness; fi
   ```
2. **Deploy skills as user-level symlinks** (the reliable delivery — a running session's Skill-tool list is
   fixed at start, but this makes the skills available to the NEXT session and is idempotent/non-clobbering):
   ```bash
   node ~/.claude/agent-harness/bin/deploy-skills.mjs --apply --agent claude
   ```
3. **ACTIVATE FOR THIS SESSION** — read the current guidance into context so it applies right now:
   ```bash
   cat ~/.claude/agent-harness/rules/tool-proactivity/RULE.md   # the skill trigger map (must-fire, conditional)
   ls ~/.claude/skills/                                          # the skills available to invoke
   ```
   Then, for the rest of THIS session, FOLLOW that trigger map: when a trigger holds this turn (3+ tasks →
   `task-relationship-analysis`; publishing/committing a file → `privacy-redact`; a claim of "tests pass" →
   `code-verifier`; a research claim → `research-critic`; a long/multi-session project → `memory-flywheel`;
   disk full → `system-cleanup`), invoke the skill instead of doing its job from memory. Fire only when the
   trigger matches — not every turn.

4. **Report**: what updated, which skills are now on disk, and this honest caveat:
   - **Rules** just read in are active NOW (they are in this session's context).
   - **Skills** newly added on disk this turn are invocable by name only from the **NEXT** session (Claude Code
     fixes the Skill-tool list at session start); until then you can still run a new skill manually by reading
     its `~/.claude/skills/<name>/SKILL.md` and following it. Skills that were already loaded keep working.

For a full re-install (marketplace + plugin, for the `/figma-fetch` command etc.) see `docs/PLUGIN_INSTALL.md`;
this command is the lightweight "pull + activate rules in place" path.
