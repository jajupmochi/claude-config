---
description: "Update agent-harness, show what changed (recommend the bits relevant to the current task, ask before applying), and activate its latest rules in THIS session without a restart"
argument-hint: ""
allowed-tools: ["Bash", "Read", "Skill", "AskUserQuestion"]
---

# /harness-sync

Bring agent-harness up to date, **surface what changed and recommend the bits relevant to the current task
(ask before applying)**, and **activate the latest rules in the CURRENT session without a restart**. Run these
with the Bash tool and report each step.

## 1. Pull, and compute exactly what changed since last sync

```bash
cd ~/.claude/agent-harness 2>/dev/null || git clone https://github.com/jajupmochi/agent-harness ~/.claude/agent-harness
OLD=$(git -C ~/.claude/agent-harness rev-parse HEAD)
git -C ~/.claude/agent-harness pull --ff-only
NEW=$(git -C ~/.claude/agent-harness rev-parse HEAD)
# what changed, grouped by kind (skills / rules / commands / hooks / config)
git -C ~/.claude/agent-harness log --oneline "$OLD..$NEW"
git -C ~/.claude/agent-harness diff --name-status "$OLD..$NEW" | grep -E '^\S+\s+(skills|rules|commands|hooks|adapters/models)'
```

If `OLD == NEW`, say "already up to date" and skip to step 4 (still re-activate rules in this session).

## 2. RECOMMEND — relevant to the CURRENT task, not a raw dump

Look at what the user is doing THIS session, then from the changed items above pick the ones that matter and
present a short recommendation. For each: what it is, why it's relevant now, and the action to adopt it. E.g.:

- new/updated **skill** relevant to the current work → "adopt = deploy its symlink **and `cat` its `SKILL.md`
  into this session now → usable IMMEDIATELY (follow it + run its scripts directly; the `Skill()` tool is only a
  convenience wrapper, not required)"
- new/changed **rule** (e.g. the `tool-proactivity` skill trigger map) → "adopt = I read it into this session's
  context so it applies now"
- new **command** / **hook** → name it + one line on when to use it

Keep it to what's genuinely relevant; note (don't expand) the rest as "also changed: …".

## 3. ASK the user to confirm before applying

Use the AskUserQuestion tool (or a plain question) to confirm WHICH of the recommended changes to adopt now —
never auto-apply new rules/skills silently. Only after a yes:

```bash
node ~/.claude/agent-harness/bin/deploy-skills.mjs --apply --agent claude   # deploy (idempotent, non-clobbering)
```

## 4. ACTIVATE the current rules in THIS session (no restart)

```bash
cat ~/.claude/agent-harness/rules/tool-proactivity/RULE.md   # the skill trigger map (must-fire, conditional)
ls ~/.claude/skills/                                          # skills available to invoke
# For each NEWLY added skill the user adopted this turn, read its body into context so it is usable NOW
# (the Skill() tool wrapper only registers next session, but the SKILL.md + its scripts work immediately):
# cat ~/.claude/skills/<new-skill>/SKILL.md
```

For the rest of THIS session, FOLLOW the trigger map — when a trigger holds this turn (3+ tasks →
`task-relationship-analysis`; publishing/committing → `privacy-redact`; "tests pass" → `code-verifier`; a
research claim → `research-critic`; a long/multi-session project → `memory-flywheel`; disk full →
`system-cleanup`; a heavy/decomposable task or long context → `task-orchestrator` sub-agent routing at the
resolved model tier), invoke the tool instead of doing its job from memory. Fire only when the trigger matches.

## 5. Report + honest caveat

- **Rules** read in this turn are active NOW (they are in this session's context).
- A **newly added skill IS usable in THIS session** — a skill is just a `SKILL.md` + scripts, so once you have
  `cat`-ed its `SKILL.md` into context (step 4) you can follow it and run its scripts directly right now. The
  only thing that waits for the **next** session is the `Skill(<name>)` **auto-wrapper** (Claude Code fixes the
  Skill-tool list at session start) — that is a convenience, not the capability. If you specifically want the
  new skill in the Skill-tool list without a full restart, `/clear` starts a fresh conversation that re-scans
  skills (but drops the current context); reading the `SKILL.md` keeps your context and loses nothing functional.

For a full plugin (re)install (marketplace + `/commands`), see `docs/PLUGIN_INSTALL.md`; this command is the
lightweight "pull → recommend → confirm → activate rules in place" path.
