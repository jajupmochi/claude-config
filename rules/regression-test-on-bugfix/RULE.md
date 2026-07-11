---
name: regression-test-on-bugfix
description: Every bug fix MUST ship with a regression test that FAILS on the old (buggy) code and PASSES after the fix. Prove both the before (red) and after (green). No behavioral bug fix is "done" without a test that locks the bug out.
scope: universal
rationale: A fix with no test that reproduces the bug is an unverified claim and an open door for the same bug to silently come back. The failing-then-passing test is the proof the fix is real AND the guard against recurrence — it converts "I think I fixed it" into "here is the bug reproduced and here is it gone."
---

# regression-test-on-bugfix

> Fix a bug → add a test that reproduces it. The test must **fail before** the fix and **pass after**. Show both.

## Master TOC

- [Rule](#rule)
- [Why](#why)
- [How (the red → green proof)](#how-the-red--green-proof)
- [Exceptions](#exceptions)
- [Relation to other rules](#relation-to-other-rules)

## Rule

For **any bug fix** to code, in the **same change** add a **regression test** that:

1. **Reproduces the bug** — it targets the exact wrong behavior (specific input → observed wrong output / crash),
   at the layer where the bug actually lives (unit if a unit bug; integration if a wiring bug).
2. **Fails on the pre-fix code** (red) and **passes after the fix** (green). Demonstrate the red → green — run it
   against the old behavior (or a captured repro) to confirm it genuinely catches the bug, not just any green.
3. **Stays in the suite** so the bug can never silently return.

A behavioral bug fix without such a test is **not done**.

## Why

- **Proof, not assertion.** "Fixed" is only credible when a test that used to fail now passes. Without the red
  step, you can't tell the test actually exercises the bug (a test that was already green proves nothing).
- **Anti-recurrence.** The most common regression is re-breaking a bug someone quietly fixed months ago. The
  pinned test is the tripwire.
- **Documents the bug.** The test name + assertion record what went wrong and what "correct" means.

## How (the red → green proof)

- Name the test after the bug / the failing case (`test_<thing>_handles_<bad-input>`), not after the fix.
- Assert the **specific** wrong→right transition (the exact input and the exact corrected output / exit code /
  state), not a vague "it works now".
- **Show red → green:** run the new test against the buggy code first (stash the fix, or run the captured repro)
  → it FAILS; apply the fix → it PASSES. If you can't easily reproduce red (e.g. a hard-to-revert change), state
  how you confirmed the test genuinely covers the bug.
- Run the **full** suite before/after (per `test-first`) so the fix didn't break something else.

## Exceptions

- **Non-behavioral changes** — a typo in a doc/comment, pure formatting, a rename with no behavior change — need
  no test.
- **Genuinely untestable at reasonable cost** (e.g. a fix that only fires in a specific production environment):
  do not skip silently — state *why* it's untestable and what manual verification stood in for the test.

## Relation to other rules

- `test-first` — the general "write tests before/alongside code, at every level, run the full suite with a
  before/after delta." This rule is its **mandatory bug-fix specialization**: the test must reproduce the bug
  (red) first.
- `root-cause-before-fix` — find *why* the bug happens (history + baseline) before fixing. This rule adds: once
  fixed, lock it with a test.
- `code-verifier` / `always-on-verification` — audit that the test RUN is genuine (no fake-green) before
  claiming the fix passes.
- The **review-gate** hook enforces this per code-changing turn (form: "bug fix → regression test present").
