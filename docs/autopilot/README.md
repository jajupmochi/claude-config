# autopilot — daily autonomous project-driver (design)

A claude-config plugin that **drives a project forward autonomously, once per day, for ≥30 min per run**,
treating the project as an industrial-grade deployable product. It plans, executes (feature/bugfix/
refactor/design/docs), passes review-gate, re-plans, estimates time formally, self-heals when stuck,
and reports — all without waiting for a human. The per-run prompt is [`PROMPT.md`](PROMPT.md) (the
`[ROLE & SCOPE]` block is swapped per session).

Researched 2026-06-24. Builds on: WorkNRoll's systemd-timer pattern, review-gate, the autoresearch
finder, and the `neobanker-agent/docs` documentation convention.

## 1. Component map

| Component | Form | Role |
|---|---|---|
| **`/autopilot` intake** | skill (`skills/general/autopilot/`) | asks requirements + daily time + min-duration → **summarize & confirm** + offer optimization → writes config + installs timers |
| **daily driver** | `skills/general/autopilot/scripts/run.sh` + `autopilot-daily.{service,timer}` | system-level systemd --user timer (Persistent) → spawns a **fresh `claude -p` autorun** session seeded with `PROMPT.md` |
| **min-duration tracker** | `skills/general/autopilot/scripts/floor.py` (record + CLI) | enforces the ≥30 min floor **without the agent's judgment** (timestamp record + `floor.py check`) |
| **watchdog** | `autopilot-watch.{service,timer}` + `watch.py` | every ~10 min: detect stuck/crash/pause, recover (Ralph-loop), or notify; feeds the **playbook** |
| **problem-playbook** | skill + `playbook/` docs | collected problems → proven fixes, reused by the watchdog + the run prompt |
| **plan-reevaluator** | invoked in-run (`<reflect_and_replan>`) + `replan.py` helper | post-run re-plan, web research, archive old plans |
| **time-estimator** | `skills/general/autopilot/scripts/estimate.py` + `time/` docs | formal PERT + agent-rounds + Monte-Carlo + data calibration; team-reportable doc |
| **summary-concat** | `skills/general/autopilot/scripts/summary.py` + a separate timer | in-session md-table summary + 7-day concat rule; dodges the 7-day limit |
| **docs** | `docs/autopilot/` + the per-project plan root | this design + the prompt + per-run/plan/time/playbook docs |

## 2. Daily execution (system-level, crash-proof)

Mirrors WorkNRoll's proven pattern (systemd `--user`, `Persistent=true`, `linger=yes`) so it survives
session close, crash, and shutdown (Persistent → a missed run fires at next boot):

```
autopilot-daily.timer  (OnCalendar=<user time>, Persistent=true)
  -> autopilot-daily.service (oneshot)
     -> skills/general/autopilot/scripts/run.sh
        1. floor.py start                     # record run start time
        2. loop:
             claude -p --model <m> --dangerously-skip-permissions \
               --append-system-prompt "$(cat PROMPT.md with [ROLE&SCOPE] filled)"  \
               "Continue the autopilot run."   # FRESH session (not --resume; resume of a giant
                                               # transcript times out — WorkNRoll finding)
             if floor.py check == not-met AND work remains: continue loop (next item)
             else: break
        3. summary.py emit ; watchdog done-marker
```

**Why fresh `claude -p`:** replaying a huge transcript via `--resume` times out (>240 s, WorkNRoll). A
fresh session seeded with `PROMPT.md` + the plan docs is fast and grounded. Context comes from the
**docs** (specification engineering), not from a live transcript.

## 3. Min-duration floor (≥30 min, agent-independent)  — `floor.py`

The agent must not be trusted to time itself. `floor.py` keeps a record and answers a CLI:

```
floor.py start            # writes ~/.claude/autopilot/<proj>/run-<ts>.start
floor.py check            # exit 0 if (now - start) >= floor_minutes else exit 1; prints elapsed
floor.py set 30           # configure floor (default 30)
```

`run.sh` (the harness, not the prompt) loops the session until `floor.py check` passes AND the current
unit is clean. If a unit finishes early, the loop starts the next item. No upper cap.

## 4. Watchdog + self-healing  — `watch.py` (Ralph-loop)

Separate systemd timer, **interval = 10 min** during an active run (rationale: a run is ≥30 min, so
10 min catches a stall in ≤⅓ of the floor without false-positives on normal long reasoning; cheaper
than 5 min, faster than 15). Plus a **daily post-window check** (e.g., start+90 min) that the run
happened and completed.

Each tick `watch.py`:
1. Reads the run's done-marker + heartbeat. `run.sh` writes the heartbeat at each attempt **and** runs a
   background loop refreshing it every ~2 min *during* the (possibly long) `claude -p` call, so the
   heartbeat is a true liveness signal — `STUCK_AFTER_S = 20 min` (≈2 ticks) never false-positives a
   healthy long run (the fix for the gui-design review's heartbeat-during-attempt bug). The proj arg is
   also path-guarded (`/`/`..` rejected) so it can't escape `~/.claude/autopilot/`.
2. **Detect**: no heartbeat for >2 ticks → stuck; service dead but no done-marker → crashed/closed;
   known pause signatures (tool-content-leak pause, `/goal` not auto-continuing on mobile → needs a
   "继续") → paused.
3. **Recover (Ralph-loop) — marked TODO, wired on first real deployment** (it spawns live sessions, so it
   must not run during build/test): kill the wedged session if needed, then **re-spawn a fresh `claude -p`
   reinjecting `PROMPT.md` into a clean context**, with the accumulated `playbook/` learnings appended so
   it doesn't repeat the failure. For the `/goal`-needs-继续 case, re-issue a "继续" continuation.
   **Prerequisite before wiring:** confirm no live `claude` process for this run (`pgrep`) so recovery
   never kills a healthy session.
4. **Learn:** append `{problem signature, context, fix that worked}` to `playbook/`. Reuse next time.
5. **Escalate:** if N recovery attempts fail, write a clear in-session note + a notification (WorkNRoll
   `notify-send`/Telegram path) for the human. Always collect the problem either way.

This is packaged so the playbook + recovery logic can also stand alone as a skill (`autopilot-watch`).

## 5. Time-estimator  — `estimate.py` (formal, numeric, calibrated)

No guessing. Hybrid of the methods the research converged on:

1. **Per-task PERT 3-point**: expected `tE = (O + 4M + P)/6`, std `σ = (P − O)/6`.
2. **Agent-rounds model** (avoids human-time anchoring, which makes agents overestimate): estimate
   tool-call **rounds** per minimal module (think→write→run→verify→fix = 1 round), × a per-category
   **risk coefficient**, convert to wall-clock **only at the end** using measured seconds/round.
3. **Roll-up via Monte-Carlo** over historical velocity → probability distribution → "P(MVP done by
   <date>)", week/month/quarter/year burn-up. (Needs ≥2–3 real samples before trusting; until then,
   report wide intervals + "low-data" flag.)
4. **Data calibration (the core):** every task logs `{category, estimate, actual, ai_seconds,
   human_seconds, human_kind∈{code,design,prompt,review}, rounds_est, rounds_actual}`. Each run updates
   per-category coefficients from estimated-vs-actual; tracks the **human:agent time ratio** as a
   health metric (drift > ~10:1 → flag).

Outputs (under `time/`): a **team/management-reportable** progress doc (level-by-level task estimates;
week/month/quarter/year; per-MVP completion dates with confidence; the methods + formulas + the reason
for each adjustment) and an in-session **md-table** summary. Adjust future estimates each run, with
stated reasons.

Data schema, formulas, and the calibration update rule are implemented in `estimate.py` (stdlib;
optional LLM/agent assist for decomposition + risk-coefficient priors).

## 6. Plan re-evaluation  — `<reflect_and_replan>` + `replan.py`

After each run: reconcile state, update `planning/` (live long-term plan + change log), append
`daily-runs/<date>.md`, and — when warranted — web-research SOTA/competitors/reusable OSS and fold in.
Always archive the superseded plan to `_archive/<date>-plan.md` (never overwrite history).

## 7. Session-summary + 7-day concatenation  — `summary.py`

- Every run emits an in-session **markdown-table** summary.
- A **review marker** records whether the human has reviewed. Each run, if the prior run is unreviewed,
  `summary.py` prepends prior summaries (≤7 days). Once the concat exceeds 7 days, it archives the block
  to `time/summary-archive/<range>.md` and the new summary carries a one-line digest + link.
- The in-session popup uses a **separate autopilot summary timer** (decoupled from any 7-day-capped
  scheduling mechanism) + the WorkNRoll notify/Telegram path, so summaries surface even across the limit.

## 8. Doc structure (per `neobanker-agent/docs`, improved)

`docs/<project-plan-root>/`: `_source/` (roadmap+milestones SoT) · `_archive/` (versioned plans) ·
`audiences/{ceo,caio,engineering,compliance,user,marketing}/` · `releases/<YYYY-MM>.md` ·
`developer-updates/weekly-<date>.md` · `standards/` (code discipline + claude-code-enforcement) ·
`brainstorm/` · `images/` · **+ autopilot:** `planning/`, `daily-runs/<date>.md`, `time/`, `playbook/`.
Bilingual (`*.md` + `*.en.md`) for human-facing docs.

## 9. Intake (`/autopilot`)

On invocation: ask (1) the long-term work/requirements, (2) daily auto-run time, (3) min duration/run,
(+ model, project path). Then **summarize the inputs back and ask for confirmation** (guard against
misreading), AND propose optimization suggestions and ask whether to accept. On confirm: write
`~/.claude/autopilot/<proj>/config.yaml`, install the systemd timers (daily + watchdog + summary), and
seed the plan root.

## 10. Integration & guarantees
- **review-gate** runs on every code turn (mandatory). Code discipline: minimal module/change/impact,
  modular, tests + commits + docs complete, git per increment.
- Uses claude-config skills (code-verifier, research-critic, impeccable, …) + existing agent
  skills/plugins; auto-invokes Chrome/visual tools; retries real blockers (no laziness/misjudgment).
- **autorun** throughout. Crash-proof via systemd Persistent + watchdog. Escape hatch: disable the
  timers (`systemctl --user disable --now autopilot-daily.timer`).

## 11. References
Prompt design: [IBM 2026](https://www.ibm.com/think/prompt-engineering) · [4 disciplines](https://aetherlink.ai/en/ai-prompt-engineering-2026) · [agentic guide](https://sarifulislam.com/blog/prompt-engineering-2026/) · [loop engineering](https://tosea.ai/blog/loop-engineering-ai-agents-complete-guide-2026) · [10 patterns](https://paxrel.com/blog-ai-agent-prompts).
Estimation: [agent-estimation (rounds)](https://github.com/ZhangHanDong/agent-estimation) · [PairCoder 400-task study](https://paircoder.ai/blog/estimation-reality/) · [METR time-horizons](https://metr.org/time-horizons/) · [PERT→Monte-Carlo](https://dev.to/_jeongyuhyeon_03de1/scientific-schedule-estimation-from-pert-to-monte-carlo-4pcd) · [Monte-Carlo agile](https://agileseekers.com/blog/using-monte-carlo-simulations-to-predict-delivery-timelines).
Reliability: [self-healing LLM agents (arXiv 2605.06737)](https://arxiv.org/abs/2605.06737) · [Ralph loop / self-healing](https://www.buildmvpfast.com/blog/debugging-ai-agents-production-error-recovery-self-healing-2026) · [graceful degradation](https://zylos.ai/research/2026-02-20-graceful-degradation-ai-agent-systems/).
Internal: `neobanker-agent/docs` (structure), WorkNRoll (`2026.06.11_worknroll`, timers), [`../ai-code-review/`](../ai-code-review/README.md) (review-gate), [[autoresearch-toolfinder]].

## 12. Status
Design + prompt complete (this doc + `PROMPT.md`). The skill is **self-contained** under
`skills/general/autopilot/`: `SKILL.md` (intake), `PROMPT.md` (the per-run prompt), and `scripts/`
(`run.sh`, `floor.py`, `watch.py`, `estimate.py`, `summary.py`, `install.sh`, `test_watch.py` +
systemd unit templates). It installs to `~/.claude/skills/autopilot/` so `/autopilot` is usable in any
session, and `install.sh` copies the scripts to the stable `~/.claude/autopilot/bin/` path. The
per-project plan root is created by `/autopilot` intake (the first planning pass can be run at install
time, on confirmation). `floor.py` / `estimate.py` / `watch.py` are tested (`test_watch.py`); recovery
(kill+respawn) stays a marked TODO until first real deployment. Build status tracked in this folder's commits.
