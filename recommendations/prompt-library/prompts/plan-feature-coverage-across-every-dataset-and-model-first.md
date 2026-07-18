---
title: Plan feature coverage across every dataset and model first
scenarios: research,planning,coverage
tags: generalization,plan-first,confirmation-gate,experiment-matrix
source: copilot-vscode
session:
date: 2026-02-17
---

# Plan feature coverage across every dataset and model first

> Use when a feature was built against one dataset or model and you are about to assume it generalizes.

## Original

```text
Now we have built a lot of features, but can they all be integrated to all <datasets> and <models> we have in <project>? One important part is: can we use these <feature> for other <models> and <datasets> besides <the one it was built on>?

Please make a detailed and thorough list of all features we have, and a detailed plan of how to adapt them to all <models> and <datasets>. This plan should include detailed tests and documentation, and a thorough, academic-paper-level experiment to compare all these <datasets> on all these <models> under different interesting settings, and then generate a report. Please do this last part carefully with sub-plans.

Write this plan first, then wait for my confirmation to continue.
```

## Optimized

```text
We have built a number of features against <the original dataset and model>. Before adding more, I
want to know whether they generalize.

Produce a plan, not an implementation:

1. An inventory of every feature we currently have, with the datasets and models each one is known to
   work on today.
2. For each feature, what adapting it to every other dataset and model would require. Be specific
   about which combinations are blocked and why, rather than assuming uniform effort.
3. The tests and documentation each adaptation needs.
4. An experiment matrix at the standard of a paper: every dataset against every model, under the
   settings that are actually informative, plus the report it produces. Break this into sub-plans —
   it is the part most likely to be underestimated.

Write the plan and stop. Wait for my confirmation before implementing anything.
```

## When to use

Use when a feature was built against one dataset or model and you are about to assume it generalizes.
The inventory usually shows that some combinations are blocked for reasons nobody had noticed.

- Before scaling a research codebase from one working configuration to a full matrix.
- When the eventual output is a paper-grade comparison and the experiment matrix drives the compute
  budget.
- Whenever you want a cost estimate before committing, which the explicit stop-and-confirm provides.

## When NOT to use

Skip it when the matrix is small enough to just try. Two datasets and two models do not need a plan
document.

Skip it when the features are known to be dataset-specific by construction. The plan will spend its
length explaining why each cell is empty.

Do not use it when you intend the agent to keep going. The confirmation gate is the point; if you will
not read the plan, you have added a delay and nothing else.
