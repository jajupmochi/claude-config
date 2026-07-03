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

## Modes (how the user invokes you)

- **`/autopilot setup <proj>`** (or "用 autopilot 跑 …") — the intake below: ask, confirm, install timers,
  **record THIS session as the project's home session**, then arm the daily in-session cron and offer to
  run once now. This is the default when no project is configured yet.
- **`/autopilot run <proj>`** — run the directive **right now, in this session** (visible, in context):
  read `PROMPT.md` + the plan docs and execute until the ≥30-min floor. No new session, no `claude -p`.
- **`/autopilot status <proj>`** — read `~/.claude/autopilot/<proj>/cron_state.json` + the newest
  `runs/` log + the latest `daily-runs/<date>.md`, and report **plainly, with clickable links**, what
  the last run did and whether the daily cron is armed/healthy.
- **`/autopilot skip <proj>`** (or "跳过今晚 / 暂停 X 的定时任务") — skip the scheduled run without unarming
  anything. Run `bash ~/.claude/autopilot/bin/skip.sh <proj> today` (skip today, resume tomorrow),
  `... until <YYYY-MM-DD>` (skip until a date), `... resume` (un-skip now), or `... status`. It writes
  `paused_until` into `cron_state.json`; `cycle_status.py` then reports the covered cycles as
  complete+skipped, so a fired run self-skips at PROMPT step 0, the idempotent guard skips, and the
  watchdog does NOT try to recover them — the cron can stay armed, and it auto-resumes on the date.

The daily run is an **in-session cron** (you arm it with CronCreate), NOT a hidden headless `claude -p`.
It lives in the user's always-open, phone-remote-controlled session so they can watch it.

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
   - Install support timers: `bash scripts/install.sh <proj>` → systemd `--user` units `autopilot-watch`
     (failed/empty-run detector), `autopilot-summary`, and the global `autopilot-resurrect` (every 30 min,
     relaunches the home session in tmux after a crash/reboot — needs `tmux`).
   - **Arm the daily in-session cron + record the home session.** With `CronCreate`, create a recurring
     durable cron (schedule from the run time, e.g. `0 22 * * *`). Cron **prompt**: "autopilot daily run
     for [<proj>]: FIRST run `python3 ~/.claude/skills/autopilot/scripts/update_check.py <proj>` (cheap,
     code-only) — if it prints `UPDATED`, re-run `scripts/install.sh <proj>` and re-arm this cron with the
     latest config (refreshing `configured_with_version`) BEFORE working; then read
     ~/.claude/skills/autopilot/PROMPT.md and execute the directive for <proj> now." Write
     `~/.claude/autopilot/<proj>/cron_state.json` with `home_session_id` = THIS session's id, `cron_id`,
     `last_armed` = today, `schedule`, and **`configured_with_version`** = the contents of
     `~/.claude/skills/autopilot/VERSION` (so `update_check.py` can detect a later autopilot update cheaply).
     (The SessionStart hook re-arms it after restarts; you self-renew before day 6 to dodge the 7-day
     `CronCreate` cap — see `<resilience>` in PROMPT.md.)
   - Confirm with `systemctl --user list-timers 'autopilot-*'` and `CronList`.
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

**The daily run happens IN the user's always-open session** (not a hidden `claude -p`). The in-session
cron you armed fires daily and runs the `PROMPT.md` directive until the **≥30-min floor** (`floor.py`),
committing each increment (review-gate-passed), re-planning, updating time estimates, writing the per-run
doc, and posting a **plain-language, fully-linked** summary — all visible to the user (and on their phone
via remote-control). Resilience is three layers: (1) the in-session cron = the run; (2) the **SessionStart
hook** (`session_check.sh`) re-arms the cron after any restart and surfaces an unshown failed run, plus
your **>5-day self-renew** dodges the 7-day cron cap; (3) the global **resurrector** (`resurrect.sh`,
every 30 min) relaunches the home session in tmux if the machine rebooted or the session crashed. The
**watchdog** (`watch.py`) flags any run that ended without meeting the floor (`last-error` newer than
`last-done`), so a silent empty run never passes as success. (The headless `run.sh` stays in `scripts/`
as an optional fallback for users with no always-open session.)

## Manage
- Pause: `systemctl --user disable --now autopilot-daily.timer`
- Status: `systemctl --user list-timers 'autopilot-*'` · run-state under `~/.claude/autopilot/<proj>/`
- Run once now (test): `bash ~/.claude/autopilot/bin/run.sh <proj>`

## Guarantees it relies on
review-gate (mandatory on every code turn) · code discipline (minimal module/change/impact, modular,
tests + commits + docs, git per increment) · claude-config skills + Chrome/visual tools as needed ·
system-level crash-proofing (systemd Persistent + watchdog).
