---
name: task-relationship-analysis
description: Use BEFORE executing any multi-step or multi-feature request (3+ tasks). Forces a pre-execution pass that maps how the tasks relate — synergies, conflicts, shared substrate, ordering — so you don't mechanically execute them in listed order and miss that several should be built on one shared piece, or that two conflict. Scaffolds a pairwise matrix + synthesis checklist.
policy:
  allow_implicit_invocation: true
---

# task-relationship-analysis

Overhaul task 15. Some agents/models execute a numbered task list **mechanically, in order**, and miss the
cross-task picture — e.g. three separate "add a sub-agent" asks that should be **one** framework, or two tasks
that **conflict** if done independently. This skill makes the relationship analysis a required first step.

## When

Any request with **3+ tasks**, or multiple logically separable features, before you start executing.

## Do this first

1. List the tasks, then scaffold the analysis:
   ```
   python3 scripts/scaffold.py "task A" "task B" "task C" …      # or pipe one per line on stdin
   ```
   It emits every **unordered pair** exactly once (nothing skipped) + a synthesis checklist.
2. Fill each pair with one relationship: **SYN** (synergy / share substrate) · **CONF** (conflict) ·
   **SEQ** (ordering dependency) · **INDEP** (independent).
3. Answer the checklist: shared substrate to unify · conflicts to resolve in design · mergeable work ·
   ordering/DAG from the SEQ pairs · cross-cutting constraints to do first.
4. Only THEN execute — in the order the DAG implies, unifying what the matrix flagged.

## Why deterministic scaffold + LLM analysis

`scaffold.py` is pure code: it guarantees the shape and that **every pair is considered**. The model does the
actual judgement (which pair is SYN vs CONF). LLM-as-component, not the core.

## Example payoff (this repo's own overhaul)

The 16-point overhaul's matrix surfaced that tasks 2/3/10a (three "sub-agent" asks) were the SAME framework,
and tasks 3/4/5 were ONE memory subsystem — recorded in `docs/strategy/…/00-program-plan.md §3` before any
code. That is the analysis this skill scaffolds.

Status: v0.1 (pairwise matrix + checklist), tested (`test_scaffold.py`, 6/6). Planned: auto-ingest a task
list from a plan file; a graph export of the SEQ edges.
