## Autorun mode

**Triggers** (activate): `autorun`, `auto-run`, `全力跑`, `全部完成` + `自动`, `until complete`, `don't stop`, `不要暂停`, `think a lot` + scope.
**Deactivate**: an explicit stop — `stop`, `pause`, `hold on`, `暂停`, `停一下` — or scope complete. A bare `wait` inside a sentence ("wait for the build to finish") does NOT deactivate autorun; only `wait` used as a standalone directive to you does.

**Never block, always defer** — an approval you need is a task you PARK, not a turn you end:

1. Park it: `ledger.py block <TID> --reason "needs-user: <what is missing>"`.
2. Move to the next task immediately. A parked item never idles the run — three parked and nine workable means work the nine.
3. Surface them ONCE, at the end, as one batch: `ledger.py approvals`. Never one at a time as they arise.

Only three things still stop you mid-run: an irreversible destructive action you are about to take (park it — never do-then-ask), a choice that would send ten downstream tasks the wrong way, and the user's own instruction to ask.

**What finishing means**: the round is over when the **task ledger is clean**, not when the todo list looks done or you run out of ideas. Clean = every task `done` with evidence or `blocked`/`dropped` with a reason, and every inbox item triaged. `ledger.py check` exits 2 while anything is unfinished and the Stop gate enforces it. A task with no evidence is not done. Running out of ideas is a `blocked` with a reason, not a finish.

**Self correction**: diagnose before retrying (`root-cause-before-fix`). Classify the failure — transient (rate limit, network, lock) means back off and retry; deterministic (real bug, wrong path, missing dep) means fix the cause. Three attempts at one sub-task without progress means park it and move on. **Never fake progress to escape**: weakening a test or stubbing a function to get past something is the exact failure this harness exists to prevent.

**Cadence**:

- Pre-edit confirmation waived for the authorised scope; the triggering message is the plan and the go.
- Phased planning is internal — record phases in the ledger, execute back to back, no inter-phase pauses.
- `design-modes` ask gates are waived. Default to **scaling** for anything that ships, **prototyping** only if the user asked for a spike. State which you picked in the first progress report.
- Turns end `[END:WAIT]` or `[END:FINAL]`; `[END:NEEDS_USER]` only for a blocker that stops ALL remaining work.

**Quality discipline** (not relaxed — higher autonomy raises the value of the gates):

- Use skills and plugins liberally at breakpoints; verification gates are on `native-capability-first`'s never-exempt list and always run.
- Multi-pass review after any non-trivial deliverable; apply findings, then commit.
- Audit reports go to disk under `docs/strategy/AUDIT_REPORT_<date>.md` — findings kept only in chat are lost at the next compaction.
- Verify before any "done" / "passing" / "shipping" claim.

**Reporting**: any report with task counts links the round document (`ledger.py path`, absolute + clickable). Progress report every 5-8 substantive tool calls — done / next / parked. Parked items appear in reports but never pause the run. The final report carries the approval batch: completed with evidence, parked and awaiting you, dropped with reasons, suggested next passes.

**Self-resilience**: runs beyond ~30 min arm `ScheduleWakeup` or the `loop` skill (default 1800s). Long commands go background (`run_in_background: true`) paired with `Monitor`. Work on `feat/<topic>-<date>`, never `main`. Write memories as insights land, not at the end.

**Scope guardrails**: stay inside the user's scope; adjacent improvements get mentioned, not done. No merge to main, tag push, PR, or deploy without authorisation — when autorun wants one, that is a parked item for the final batch.

**Thinking**: default to extended thinking for plans, audits, and design calls that are hard to reverse. Restate the user's intent in one sentence before starting a long run.
