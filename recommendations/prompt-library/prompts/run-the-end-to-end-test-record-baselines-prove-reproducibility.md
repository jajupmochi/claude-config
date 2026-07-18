---
title: Run the end-to-end test, record baselines, prove reproducibility
scenarios: testing,verification,research-code
tags: e2e,baseline,reproducibility,report
source: copilot-vscode
session:
date: 2026-03-05
---

# Run the end-to-end test, record baselines, prove reproducibility

> Use for research code where a number only counts if it reproduces.

## Original

```text
Now perform the following tasks:

- Run e2e pipeline test for <dataset> + <model> with and without <feature>. Record the results in baselines, and rerun the test to check if the results are the same. Give me a report for the test.
- If the aforementioned test passes, commit the current changes.
- I have tested <model> with <feature> on <dataset>, which performs very bad. Please check the cause of it. If it is due to bugs, fix them. If not, give me suggestions to improve the performance, and compare with the following revision:
  - The current <feature> is designed to be added to the input directly, which may introduce noise to <downstream step>. Consider applying it after <downstream step> instead, i.e., per unit rather than per time step.
  Analyze and tell me which revision is better, and then implement the better one (for <model> only, you may need to create a new model to wrap it). You may need to do some research on how other papers or libraries design <feature> for models of this family. Please give me references for that as well.
  Notice, keep the current variant as well, since it is still useful for comparison.
```

## Optimized

```text
Three tasks, in order. Report after each.

1. Run the end-to-end pipeline for <dataset> + <model>, both with and without <feature>. Record the
   numbers as baselines, then run it AGAIN and confirm the numbers match. Report both runs. A result
   that does not reproduce is a failure, not a rounding detail.
2. If step 1 reproduces, commit.
3. <feature> performs badly on <dataset>. Diagnose it. If the cause is a bug, fix it. If it is not a
   bug, propose improvements and evaluate them against this specific alternative:
   <state the alternative design and the mechanism you think makes it better>.
   Say which is better and why BEFORE implementing, then implement the better one, scoped to <model>
   only (a wrapper is fine). Look at how comparable work handles this and cite what you find.
   Keep the existing variant in place — it is the comparison point.
```

## When to use

Use for research code where a number only counts if it reproduces. The rerun-and-compare step is the
load-bearing part: it catches nondeterminism, leaked state and stale caches before they become a
result you have to retract.

- Before committing a change that moves a metric.
- When a configuration performs badly and you cannot yet tell bug from genuine effect.
- When you already have a specific alternative in mind and want it evaluated rather than assumed.

## When NOT to use

Skip the double run for a pipeline that is legitimately stochastic and not seeded. You will chase
variance instead of bugs. Fix seeding first, or compare distributions rather than values.

Do not use it when a full end-to-end run is expensive. Reproduce a cheap deterministic slice instead.

Do not bundle the commit step into an unattended run on a shared branch.
