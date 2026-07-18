---
title: Port code from a reference project verbatim, with a provenance map
scenarios: porting,refactor,research-code
tags: adaptation,provenance,traceability,minimal-diff
source: copilot-vscode
session:
date: 2026-02-09
---

# Port code from a reference project verbatim, with a provenance map

> Use when adapting a reference implementation — a paper's released code, a sibling repo, an upstream library — and correctness depends on matching the original rather than improving it.

## Original

```text
There is a big problem. There are a lot of classes (e.g., models), functions, parts that you can actually just copy-paste from the reference projects and just use a wrapper, but you made a lot of modification. Which is not good. I want you to stop the current procedure.

Revise the adaptation process to add the following:

- If a class (e.g., a model), function, or code part can be copy-pasted from a reference project to the target project, then its content should not be modified except naming, comments, variable type hints, format, etc.
- After each step, a file must be given to show, in the adapted code, which part is related to / copied from / revised from which parts of the reference projects. Links should be given for the code so that users can easily check the difference.

After that, restart the adaptation. If some revised parts follow these given rules, you can keep them; otherwise revise or rewrite them.
```

## Optimized

```text
Stop the current adaptation. It rewrote code that should have been copied.

New rules for porting from <reference project> into <target project>:

1. If a class, function or block CAN be copied verbatim and adapted with a wrapper, copy it verbatim.
   The only edits allowed are renaming, comments, type hints and formatting. Behaviour must not change.
2. Any genuine deviation needs a one-line reason recorded at the point of deviation.
3. After each step, produce a provenance file mapping every ported unit to its origin: target symbol,
   source project, source path and line range, a link to the source, and one of copied / wrapped /
   rewritten. I have to be able to diff any pair in one click.

Then restart the adaptation. Keep the parts of the existing work that already satisfy these rules;
redo the rest.
```

## When to use

Use when adapting a reference implementation — a paper's released code, a sibling repo, an upstream
library — and correctness depends on matching the original rather than improving it.

- Reproducing published results, where a silent "improvement" invalidates the comparison.
- Porting many units at once, where you will not review every diff by hand.
- After you have caught an agent rewriting what it should have copied. The provenance file is the
  control that makes the next round auditable.

## When NOT to use

Do not use it when the reference code is known-bad, or written for a framework version you are not on.
Verbatim copying then imports the bugs, and the rules fight the work.

Do not use it for a clean-room reimplementation, where copying is precisely what you must not do for
licensing or independence reasons.

Skip the provenance file for a handful of functions you will review individually. It earns its cost at
scale.
