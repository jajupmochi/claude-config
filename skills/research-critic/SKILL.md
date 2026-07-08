---
name: research-critic
description: Critique research hypotheses, experiment design, results, ablations, baselines, and paper claims before committing them.
policy:
  allow_implicit_invocation: true Use for ML or scientific reasoning claims.
---

# research-critic

Read `../general/research-critic/SKILL.md` completely before using this skill.

Codex-specific requirements:

1. Tie criticism to the current artifact: paper draft, experiment script,
   result table, plot, or benchmark output.
2. Separate empirical evidence, interpretation, and speculation.
3. Check falsifiability, fair comparison, leakage, ablation design, statistical
   support, and proportional conclusions.
4. If evidence is missing or indirect, mark the claim as unproven and propose
   the smallest check that would resolve it.
