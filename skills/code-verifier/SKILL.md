---
name: code-verifier
description: Audit whether code, tests, scripts, or reported results are genuine before claiming success. Use before saying tests pass, code works, a script ran, training converged, or results show a conclusion.
policy:
  allow_implicit_invocation: true
---

# code-verifier

Read `../general/code-verifier/SKILL.md` completely before using this skill.

Codex-specific requirements:

1. Treat command output, file contents, and test artifacts as evidence only
   after inspecting them in the current run.
2. Look for fake-run patterns in tests, scripts, and pipelines before trusting
   green output.
3. If the verification scope is narrower than the claim, narrow the claim.
4. Surface blockers plainly when required commands cannot run.
5. Do not rely on memory, intent, or stale logs as proof.
