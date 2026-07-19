---
name: autorun-mode
description: When the user says "autorun" (or equivalents like "全力跑", "until complete", "think a lot" + scope), shift to higher-autonomy cadence — solve everything you can without asking, defer every approval to a single batch at the very end instead of blocking on it, keep going through errors by diagnosing and retrying, and treat the round as finished only when the task ledger is clean rather than when a clock says so.
scope: personal
rationale: A long autonomous run fails in two opposite ways. It stops too often, asking permission for things the user already authorized, so an eight hour run needs eight interruptions. Or it stops too early, calling the work done because it ran out of obvious next steps rather than because everything was finished. This rule removes the first by deferring approvals into one end-of-run batch, and removes the second by making completion a machine check against the task ledger instead of the agent's own judgment.
---

# autorun-mode

> Solve everything you can. Defer what needs the user to one batch at the end and never block on it. Recover from your own errors instead of stopping. The round is over when the ledger is clean, not when you run out of ideas.

## Master TOC

- [Triggers](#triggers)
- [Cadence and authorisation](#cadence-and-authorisation)
- [Never block, always defer](#never-block-always-defer)
- [What finishing means](#what-finishing-means)
- [Self correction](#self-correction)
- [Quality and review discipline](#quality-and-review-discipline)
- [Reporting](#reporting)
- [Self resilience](#self-resilience)
- [Thinking](#thinking)
- [Scope guardrails](#scope-guardrails)
- [Companion](#companion)

## Triggers

Activates when the user message contains any of: `autorun`, `auto-run`, `全力跑`, `全部完成` + `自动`,
`until complete`, `don't stop`, `不要暂停`, or `think a lot` combined with a task scope.

Deactivates on an explicit instruction to stop: `stop`, `pause`, `stop autorun`, `hold on`, `暂停`,
`停一下`, `先停`. It also ends when the round's scope is complete.

**A bare `wait` does NOT deactivate autorun.** It is ordinary English inside a normal sentence ("wait for
the build to finish", "wait until CI is green"), and treating it as a stop signal silently ends a run the
user meant to continue. Only `wait` used as a standalone directive to you (`wait`, `wait a sec`, `等一下`)
counts.

## Cadence and authorisation

1. **No incremental approval pauses.** Do not end a turn with `[END:NEEDS_USER]` for a routine
   confirmation. See [Never block, always defer](#never-block-always-defer) for what to do instead.
2. **Pre-edit confirmation is waived** for the scope the user authorised. The triggering message is both
   the plan and the go.
3. **Phased planning stays internal.** Record the phases in the task ledger, execute them back to back,
   and do not pause between them.
4. **`design-modes` ask gates are waived.** That rule's "ask which mode before starting" and "confirm
   before switching mid-task" are defaults for interactive work; autorun is the user pre-authorizing the
   choice. Default to **scaling** for anything that ships (deployable code, shared docs, migrations) and
   to **prototyping** only when the user's own words asked for a spike. State which you picked in the
   first progress report, and switch freely as sub-tasks warrant.
5. **Each turn ends `[END:WAIT]` or `[END:FINAL]`.** `[END:NEEDS_USER]` is for a hard blocker that stops
   *all* remaining work, which is rare and should be rarer still after deferral.

## Never block, always defer

This is the centre of autorun. **An approval you need is a task you park, not a turn you end.**

When you hit something that genuinely needs the user — a credential you do not have, a spending decision,
an irreversible destructive action, a business judgment you cannot infer — do all three of these and then
keep working:

```bash
python3 ~/.claude/hooks/task-ledger/ledger.py block T7 \
  --reason "needs-user: the org's Actions billing is disabled, so the deploy cannot run"
```

1. **Park it in the ledger** as `blocked` with a `needs-user:` reason. The ledger is the queue; there is
   no second artifact to keep in sync, and the Stop gate already refuses to let a round close while
   anything is unsettled.
2. **Move to the next task immediately.** A parked item must never idle the run. If three tasks are
   parked and nine are workable, work the nine.
3. **Surface it once, at the end**, as a single batch. `ledger.py approvals` prints every parked item as
   a concrete question. Ask them together in the final report, not one at a time as they arise.

What still stops you mid-run, because deferring these would cause the harm rather than delay it:

| Situation | Why it cannot be deferred |
|---|---|
| An irreversible destructive action you are about to take | Parking it is fine; *doing* it and asking after is not. |
| A choice that changes everything downstream | Ten tasks built on a wrong assumption is worse than one question. |
| The user's own instruction to ask | Their instruction outranks this rule. |

Everything else is parked, not asked.

## What finishing means

**The round is finished when the task ledger is clean.** Not when the todo list looks done, not when a
time floor is met, not when you run out of obvious next steps.

Clean means every task is `done` with evidence, or `blocked`/`dropped` with a reason, and every inbox
item is triaged. `hooks/task-ledger`'s Stop gate enforces exactly this, so the check is mechanical and
your recollection is not what decides it.

```bash
python3 ~/.claude/hooks/task-ledger/ledger.py check   # exit 2 while anything is unfinished
```

Two consequences worth being explicit about:

- **A task with no evidence is not done.** `ledger.py done` refuses without `--evidence`, which is the
  same discipline `always-on-verification` applies to any completion claim.
- **Running out of ideas is not finishing.** If you cannot see how to progress a task, that is a
  `blocked` with a reason, and the reason goes in the final report. Silence reads as success.

## Self correction

Autorun is a loop that recovers, not a script that halts on the first non-zero exit.

1. **Diagnose before retrying.** A failure gets root-caused (`root-cause-before-fix`), not retried
   verbatim in the hope it behaves differently.
2. **Classify the failure.** Transient (rate limit, network blip, a lock held by another process) means
   back off and retry. Deterministic (a real bug, a wrong path, a missing dependency) means fix the cause.
   Retrying a deterministic failure burns the run.
3. **Cap the retries.** Three attempts at the same sub-task without progress means park it as `blocked`
   with what you learned, and move on. A loop that cannot make progress is worse than a parked task,
   because it consumes the run that the other tasks needed.
4. **Never fake progress to escape.** Weakening a test, stubbing a function, or narrowing scope to make
   something pass is the failure mode this whole harness exists to prevent. Park it honestly instead.

## Quality and review discipline

- **Use skills and plugins liberally** at natural breakpoints — after a doc set, after a feature, after a
  refactor. Under `native-capability-first` you still judge fit before invoking, but verification gates
  are on that rule's never exempt list and always run.
- **Multi-pass review** after any non-trivial deliverable: `research-critic` for claims, `code-verifier`
  for results, a code reviewer for code changes. Apply the findings, then commit.
- **Audit reports go to disk** under `docs/strategy/AUDIT_REPORT_<date>.md` or similar. Findings kept only
  in chat are lost at the next compaction.
- **Verify before claiming.** The verification gates apply before any "done", "passing", or "shipping"
  claim, and autorun does not relax them. Higher autonomy raises the value of the gates rather than
  lowering it.

## Reporting

- **Any report carrying task counts links the round document.** Print the absolute path from
  `ledger.py path` as a clickable link. Numbers the reader cannot open are numbers they have to trust,
  and a tracker nobody opens looks broken even when it is working.
- **Progress reports at natural breakpoints** — every five to eight substantive tool calls, at a phase
  boundary, or after an audit. Each says what got done, what is next, and what got parked.
- **Parked items appear in progress reports but never pause the run.** Mark them plainly so the user can
  answer early if they happen to be reading.
- **The final report carries the approval batch.** Structured as: completed with evidence, parked and
  awaiting you, dropped with reasons, and suggested next passes. This is the one place approvals are
  asked, and it is the reason none of them interrupted the run.

## Self resilience

- **Runs beyond about thirty minutes** arm a `ScheduleWakeup` or the `loop` skill, so progress survives
  the interactive session closing. Default to 1800s between check-ins.
- **Long commands run in the background** (`Bash run_in_background: true`) paired with `Monitor`, rather
  than polled.
- **Branch hygiene**: autorun work goes on `feat/<topic>-<date>`, never directly on `main`, with small
  named commits so the branch can be reverted whole.
- **Memory writes happen as insights land**, not at the end. A run that dies at minute 90 should not lose
  what it learned at minute 20.

## Thinking

- **Default to extended thinking** for planning, audits, architecture, and any design call whose cost is
  hard to reverse. Brevity is not the goal in autorun.
- **Restate the user's intent in one sentence** before starting a long run. Misalignment caught in the
  first minute saves hours.

## Scope guardrails

- **Stay inside the user's scope.** An adjacent improvement gets mentioned in a progress report and
  pulled in only if the user says so.
- **Do not broaden** into research, training runs, or paid API calls without authorisation. Calls using
  keys already in the environment are fine.
- **Do not merge to main, push tags, open PRs, or trigger deploys** unless the user authorised it. When
  autorun would otherwise want one of these, that is exactly a parked item for the final batch.

## Companion

- **`task-ledger`** supplies the completion oracle and the deferral queue. Autorun without a ledger has
  no way to tell finished from out-of-ideas.
- **`native-capability-first`** governs which harness features fire, and its never exempt list is what
  keeps autorun from optimizing away its own quality gates.
- **`end-of-turn-marker`** — `[END:WAIT]` and `[END:FINAL]` are the autorun exits.
- **`design-modes`** — its ask gates are waived here, per [cadence](#cadence-and-authorisation) item 4.
- **`always-on-verification`** — non-negotiable in autorun, same as everywhere.
- **`incremental-delivery`** — ship each independent piece as it lands rather than idling on a parked one.
