---
name: root-cause-before-fix
description: Before fixing any bug, establish WHY it happens and WHY NOW — reproduce and locate the exact failure, read the failing line's history (git log -L / blame), compare against the baseline branch to classify regression vs pre-existing latent fragility, trace the bad value to its true origin, then fix at the correct layer. Never patch-first. A guard that hides an upstream regression is the wrong layer.
scope: personal
rationale: Jumping straight to a patch fixes the symptom at whatever layer you happened to be looking, not the cause. Five to ten minutes of history plus baseline comparison routinely changes what the correct fix even is — a defensive guard, a revert of the introducing commit, or a fix at the data/caller are all "the fix" for different root causes, and only the classification tells you which.
---

# root-cause-before-fix

> When a bug is reported, do NOT jump to a patch. First establish *why it happens* and *why now*, then fix at the correct layer.

## Master TOC

- [Rule](#rule)
- [The mandatory steps](#the-mandatory-steps)
- [Choosing the right layer](#choosing-the-right-layer)
- [Relation to other rules](#relation-to-other-rules)

## Rule

For **every** bug fix, however small, run the root-cause routine before editing. Skipping it because the fix
"looks obvious" is exactly when you patch the wrong layer.

## The mandatory steps

1. **Reproduce + locate** the exact failure — `file:line`, stack, the offending expression.
2. **History** — `git log -L <line>,<line>:<file>` (or `git blame`) on the failing line: was it always this way, or
   introduced/changed recently? Note the commit.
3. **Compare with the baseline branch** (usually remote `main`, or the deployed branch): does the baseline have the
   *same* code? **Same → pre-existing latent bug, NOT a regression from your branch. Different → your branch
   introduced it; read the introducing commit.**
4. **"Why now?"** — if the code was always fragile, identify what *changed* to start triggering it: data (e.g. a
   datasource switch leaving a field empty), config, a dependency, or a new caller. Explicitly classify:
   **code-regression vs data/config-triggered latent fragility.**
5. **Trace the data/call flow** to the true origin of the bad value (where does the `undefined` / wrong value
   actually come from?).
6. **Record the finding** — pre-existing-vs-regression, root cause, and why-now — in the commit message and the
   report, so the fix is *explained*, not just applied.

## Choosing the right layer

Fix at the RIGHT layer, and say which + why:

- **Defensive guard** — when the fragility is legitimate and the trigger is a valid state.
- **Revert / fix of the introducing commit** — a true regression.
- **Fix at the data / caller** — when the value should never have been bad.

A guard that hides a real upstream regression is the wrong layer.

## Relation to other rules

- `regression-test-on-bugfix` — once the root cause is fixed, lock it with a red→green regression test.
- `fallback-discipline` — a fallback that hides a regression is the wrong layer (this rule tells you which layer is
  right).
