---
name: test-first
description: For any code change, design and write tests BEFORE (or alongside) the implementation, at every level the change touches (unit → integration → regression). Document each test — what it checks, expected, actual, why, effect — and run the FULL suite with a before/after delta, not just the target test. Never claim "works/passes" without a real run.
scope: personal
rationale: Tests written after code test what the code does, not what it should do. A documented, full-suite, delta-checked run is the only honest basis for a "done" claim, and it catches the "fixed A, silently broke B" class.
---

# test-first

> Feature design → test design → test implementation → code. Document every test. Run the WHOLE suite with a delta. No "works" without a real run.

## The order (every code change)

1. **Feature design** — state what the unit should do (inputs → outputs, edge cases, error behavior).
2. **Test design** — enumerate the cases that would prove it: happy path, boundaries, adversarial inputs, error paths. Design them from the SPEC, before the implementation exists.
3. **Test implementation** — write the tests. They should fail (or not compile against the missing unit) first.
4. **Code** — implement until the tests pass. Add tests for anything you discover mid-implementation.

## Levels (test what the change touches)

- **Unit** — each changed function/module in isolation, including error and boundary inputs.
- **Integration** — the changed units wired to their real neighbors (not mocks-only).
- **Regression** — the WHOLE suite, with the **pass/fail count and the delta vs before**. Re-running only the test you were "fixing" is insufficient — a change that removes one failure but adds another is a net regression. A newly-failing test must be proven pre-existing (stash + re-run) before it is dismissed.

## Test documentation (required)

For each test, a reader should be able to see: **what it checks · expected · actual · why it matters · effect if it fails**. Keep it next to the test (a docstring, a comment, or a short table). A test whose purpose you can't state is a test you can't trust.

Suggested table for a change's test doc:

| test | what it checks | expected | actual | why | effect if broken |
|---|---|---|---|---|---|

## Hard bans (fake-run — pairs with the `code-verifier` skill)

- No `assert True` / tautologies; no test with zero assertions; no bare `except: pass` that hides a failure.
- No mocking the very function under test; no hardcoded literal standing in for a computed result.
- No "works / passes / results show X" claim without running the exact command this turn and reading its real output + exit code.

## When

Every code change, however small. Trivial one-liners still get a real run; non-trivial units get designed tests first. Prototyping mode may defer *breadth* of tests, but never the real run behind a "works" claim.
