## Always-on verification (code-verifier + research-critic)

For ANY task involving code execution, test claims, scripts producing numbers, or research-result claims, two skills are always-on gates:

1. **`code-verifier`** — invoke (`Skill` tool) BEFORE any "tests pass" / "build works" / "training converges" / "code runs" claim. Detects FAKE-RUN patterns (hardcoded results, `assert True`, mocks-only tests, swallowed exceptions, fabricated numbers, dead-code short-circuits). Three-layer gate: real run? genuine? exercises the claim?

2. **`research-critic`** — invoke at every research step (hypothesis design, experiment setup, result interpretation, conclusion writing) and BEFORE any "method A beats B" / "results show X" / "we observe Y" / "transfer ratio is Z%" claim. Six-question audit: falsifiability · design-matches-hypothesis · fair comparison · leakage · proportional conclusion · alternatives ruled out.

Both are TEXT-only audits — cheap. Use generously, not sparingly.

**Workflow integration**:

- Before any "tests pass" / "build works" / "training converges" / "code runs" claim → invoke `code-verifier`.
- Before any "method A beats B" / "results show X" / "we observe Y" / "transfer ratio is Z%" claim → invoke `research-critic`.

See `skills/general/code-verifier/SKILL.md` + `skills/general/research-critic/SKILL.md` (in `agent-harness`) for the full skills.
