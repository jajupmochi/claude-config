---
name: autopilot
description: Set up or manage the autopilot daily autonomous project-driver — a system-level timer that, once a day, runs a fresh ≥30-min autorun Claude session to advance a project (features, bug fixes, refactors, design, docs) as an industrial-grade deployable product, passing review-gate, re-planning, estimating time formally, and self-healing when stuck. Use when the user wants to "set up autopilot", "auto-drive project X daily", schedule autonomous daily work, or configure/inspect the autopilot tool. Full design: docs/autopilot/README.md; the run prompt: docs/autopilot/PROMPT.md.
version: 0.1.0
license: MIT
tags: [autopilot, autonomous, daily-driver, autorun, scheduling, project-management]
---

# autopilot — intake & setup

You configure and install the **autopilot** daily autonomous project-driver. This skill is
self-contained: the per-run prompt is `PROMPT.md` and all scripts are under `scripts/`, both bundled
beside this file (so the live copy under `~/.claude/skills/autopilot/` runs without the source repo).
Full design + every sub-tool spec: `docs/autopilot/README.md` in the claude-config repo.

## Intake flow (do this in order)

1. **Ask** the user for:
   - **Long-term work / requirements** — what should autopilot drive (the `[ROLE & SCOPE]` block of `PROMPT.md`)?
   - **Daily auto-run time** (e.g. `03:00`).
   - **Minimum duration per run** (default **30 min**, no upper cap).
   - Project path (repo root) and model (default the session model).
2. **Summarize the inputs back and ask for explicit confirmation** — restate everything you captured
   so there is no misreading. Wait for a clear "yes" before installing.
3. **Offer optimization suggestions** — based on the project + the design doc, propose improvements
   (e.g. better run time to avoid peak hours, scoping the first MVP, enabling the STRICT review layer,
   watchdog interval) and ask whether to accept each.
4. **On confirm, install:**
   - Write config: `~/.claude/autopilot/<proj>/config.yaml` (role/scope, time, floor, model, repo).
   - Seed the plan root under the project's `docs/<plan-root>/` (per the neobanker structure) if absent.
   - Install timers: `bash scripts/install.sh <proj>` (from this skill's dir) → systemd `--user` units
     `autopilot-daily` (run time), `autopilot-watch` (every 10 min), `autopilot-summary`.
   - Confirm with `systemctl --user list-timers 'autopilot-*'`.
   - **Review-gate scope (ask — review-gate gates git, see `hooks/review-gate/`):**
     - **(once, only if `~/.claude/hooks/review-gate/review-gate.conf` is absent)** — "Also block `git commit`? Default **no**: commits stay free (the AI review at Stop still runs and surfaces findings, it just won't block committing); **yes** denies commits the same NON-FATAL way as push." Write `block_commit=0|1` to that conf.
     - **(this project)** — "Add this project to the **push-whitelist**? `git push` / `gh pr create|merge` are blocked by default (the autopilot red-line is *never push* anyway); whitelist only a code project you actually intend to push from. Pure-docs / low-impact → recommend leaving it blocked." If yes, append the repo root path to `~/.claude/hooks/review-gate/push-whitelist.txt`. A block is non-fatal — the agent keeps working, it just can't push.
5. **Offer the first planning pass NOW (ask y/n).** The first timer fire may be hours away, so ask:
   "Do the first planning pass now?" If **yes**, do it in this session — run the `<startup_sequence>`
   *Perceive* step (read the project's docs + code + recent `git log`), CREATE the long-term plan under
   the plan root (`docs/<plan-root>/planning/`), then present the **first-run contract** output: a
   markdown-table overview of the plan (one row per phase/MVP — goal · effort estimate · status) **and a
   clickable link to the full plan doc**, so the user can approve the whole plan at a glance. If **no**,
   the first timer fire produces the same table + link unattended.

## What it then does (autonomously, no human input)

Each day the timer runs the installed `run.sh` (`~/.claude/autopilot/bin/run.sh <proj>`), which loops a
**fresh** `claude -p` **autorun** session seeded with `PROMPT.md` until the **≥30-min floor** (`floor.py`,
agent-independent) is met and the current unit is committed + review-gate-passed. It then re-plans,
updates formal time estimates, writes a per-run doc, and emits an in-session markdown-table summary (with
the 7-day concat rule) — **the first run leads with a plan-overview table + a link to the full plan doc
for approval.** The **watchdog** (`watch.py`) detects stuck/crashed/paused sessions and self-heals
(Ralph-loop), recording problems→fixes to the playbook. run.sh keeps a background heartbeat fresh during
each long `claude -p` call so the watchdog never false-positives a healthy long run as stuck.

## Manage
- Pause: `systemctl --user disable --now autopilot-daily.timer`
- Status: `systemctl --user list-timers 'autopilot-*'` · run-state under `~/.claude/autopilot/<proj>/`
- Run once now (test): `bash ~/.claude/autopilot/bin/run.sh <proj>`

## Guarantees it relies on
review-gate (mandatory on every code turn) · code discipline (minimal module/change/impact, modular,
tests + commits + docs, git per increment) · claude-config skills + Chrome/visual tools as needed ·
system-level crash-proofing (systemd Persistent + watchdog).
