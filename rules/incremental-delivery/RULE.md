---
name: incremental-delivery
description: Ship completed, independent pieces as they finish — verify, deploy to staging, and report each — instead of idle-waiting for a whole batch. If a unit of work is not directly interdependent with what is still running, close it out (test → push develop/staging → remote+visual verify → report) so the user can validate early and progress is visible. Only genuinely dependent work waits.
scope: universal
rationale: Batching every deliverable behind "wait for everything" hides finished, verifiable value and delays the user's ability to validate. Most work items are independent; blocking a done fix on an unrelated in-flight task wastes wall-clock and defers feedback. Shipping the moment a piece is verified surfaces progress, catches integration issues on the smallest change, and lets the user course-correct early.
---

# incremental-delivery

> A piece is done → verify it, ship it to staging, report it. Do not idle-wait for the batch.
> Only wait when the next piece genuinely depends on the one still running.

## Master TOC

- [Rule](#rule)
- [Why](#why)
- [How](#how)
- [When to hold instead](#when-to-hold-instead)
- [Relation to other rules](#relation-to-other-rules)

## Rule

When a unit of work reaches a verifiable "done" state and is **not directly interdependent** with
work still in flight:

1. **Verify it for real** — run the relevant tests/build; do not assert.
2. **Ship it** — commit and push to the working branch (`develop`), let it deploy to **staging**.
3. **Verify remotely, including visually** — hit the deployed endpoint/route; for a user-facing
   change, capture a screenshot of the actual result on staging.
4. **Report the finished piece** to the user with the evidence (test numbers, URL, screenshot), so
   they can validate it immediately.

Do this **per piece**, not once per batch. Multiple independent fixes finishing near each other
still each get shipped + reported rather than pooled behind the slowest one.

## Why

Finished, verified value that sits unshipped behind an unrelated in-flight task is invisible and
un-validatable. Shipping each independent piece the moment it is verified: surfaces progress, lets
the user catch a wrong direction on the smallest possible change, and keeps the deployed staging in
step with the work.

## How

- Track pieces as they complete; when one is green and standalone, close it out immediately.
- Respect the deploy gate for the environment (staging, not production/main) and the project's
  push protocol.
- Keep the report tight: what shipped, the evidence (tests + URL + screenshot), what is next.

## When to hold instead

- The next piece **reads or builds on** the one still running (shared file, shared schema, a fix
  that only makes sense atop another) — let it land first, then ship the combined result.
- The change is **not independently verifiable** yet (needs another in-flight change to be testable).
- Shipping would cross an **authorization boundary** (production, `main`, an irreversible action) —
  that still needs the user's explicit go, per the project's rules.

## Relation to other rules

- Pairs with `regression-test-on-bugfix` and the verification rules: "ship each piece" only after it
  is genuinely verified.
- Complements `parity-restoration`: a large parity sweep is itself decomposed into per-component
  pieces that ship as each is fixed.
