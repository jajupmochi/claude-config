## Regression test on bug fix

Every bug fix ships, in the same change, with a regression test that reproduces the bug. A behavioral bug fix without one is **not done**.

- **Reproduce the bug** — target the exact wrong behavior (the specific input, the observed wrong output or crash) at the layer where the bug actually lives (unit for a unit bug, integration for a wiring bug).
- **Show red → green** — run the new test against the buggy code first (stash the fix, or run a captured repro) so it FAILS, then apply the fix so it PASSES. A test that was already green proves nothing about the bug. When red is hard to reproduce, say how you confirmed the test covers the bug rather than skipping the proof.
- **Name it after the bug, not after the fix** (`test_<thing>_handles_<bad_input>`), and assert the specific wrong→right transition — the exact input and the exact corrected output, exit code, or state, never a vague "it works now".
- **Leave it in the suite** so the bug cannot silently return, and run the full suite before and after (per `test-first`) so the fix did not break something else.
- **Exceptions** — non-behavioral changes (a doc or comment typo, pure formatting, a rename with no behavior change) need no test. When a fix is untestable at reasonable cost, do not skip silently — state why it is untestable and what manual verification stood in for the test.
- Pairs with `root-cause-before-fix` (establish why the bug happens before fixing it) and `code-verifier` (audit that the test run is genuine). The review-gate hook checks for this on every turn that changes code.
