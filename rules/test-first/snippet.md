## Test first

Every code change runs in this order: **feature design → test design → test implementation → code**. Design the cases from the spec, before the implementation exists, and expect them to fail first.

- **Test every level the change touches** — unit (each changed function alone, including error and boundary inputs), integration (the changed units wired to their real neighbors, not mocks alone), regression (the whole suite).
- **Run the FULL suite and report the delta** — the pass/fail count before and after. Re-running only the test you were fixing is not enough, because a change that removes one failure and adds another is a net regression. A newly failing test must be proven pre-existing (stash, re-run) before you dismiss it.
- **Document every test** so a reader can see what it checks, expected, actual, why it matters, and the effect if it fails. Keep that next to the test as a docstring, a comment, or a short table. A test whose purpose you cannot state is a test you cannot trust.
- **Fake-run bans** — no `assert True` or tautologies, no test with zero assertions, no bare `except: pass` that hides a failure, no mocking the function under test itself, no hardcoded literal standing in for a computed result.
- **No "works" / "passes" / "results show X" claim** without running the exact command this turn and reading its real output and exit code.
- **Every code change, however small.** Trivial one-liners still get a real run, and non-trivial units still get designed tests first. Prototyping may defer the breadth of tests, never the real run behind a "works".
