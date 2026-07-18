---
title: Triage a failure batch into a plan table before touching code
scenarios: bug-triage,planning,research-code
tags: triage,non-goals,reference-lookup,table
source: copilot-vscode
session:
date: 2026-03-19
---

# Triage a failure batch into a plan table before touching code

> Use when a batch of failures shares one apparent cause and the obvious general fix would paper over per-case differences you have not looked at yet.

## Original

```text
First let's handle P0: fix <failure class> first (<N> failed runs). Do not add <the tempting general fix> for <specific cases>. Instead, make a plan for the following:

- List all <units> and the related <configurations> that have <the error> in a Markdown table here.
- For each of these <units>, check in the <reference project> to find out: if there is a <setting> such as <example values>; if there is, what is the value of this setting; if not, what is the default setting for this <unit>? List the reference code / files in a Markdown table here.
- Give plans on how to fix the <setting> for each of these pairs, based on the reference you find. Make a detailed plan for each pair, and list the expected fixes in a Markdown table here.
```

## Optimized

```text
Handle <failure class> first — it accounts for <N> failed runs.

Explicit non-goal: do NOT add <the general fix that looks obvious>. I do not want that abstraction
yet. Instead produce a plan, as three Markdown tables in your reply, before changing any code.

1. Every affected <unit> and <configuration> pair showing <the error>.
2. For each affected unit, what <reference project> does: does it define <setting>, what value, and if
   not, what default applies? Cite the reference file and line for each row.
3. The proposed fix per pair, derived from row 2, with the expected outcome.

Stop after the tables. I will confirm before you implement.
```

## When to use

Use when a batch of failures shares one apparent cause and the obvious general fix would paper over
per-case differences you have not looked at yet.

- Many failing runs or tests with a common symptom.
- A reference implementation exists that already answers "what should this value be".
- You want the evidence laid out per case before a fix is generalized, which the three tables force.

The non-goal line is what makes this work. Without it an agent will implement the general
normalization you were trying to avoid.

## When NOT to use

Skip it when there really is one root cause and you know it. Three tables to document a one-line fix is
ceremony.

Skip it when no reference implementation exists — table 2 becomes speculation dressed as evidence.

Do not use it under time pressure on a production incident. This is a deliberate slow path; mitigate
first, triage after.
