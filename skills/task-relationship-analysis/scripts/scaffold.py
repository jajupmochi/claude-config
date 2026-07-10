#!/usr/bin/env python3
# task-relationship-analysis · version: 0.1.0
"""Deterministic scaffold for pre-execution inter-task relationship analysis (overhaul task 15).

Given a list of task labels (args or stdin, one per line), emit a Markdown scaffold the agent fills in
BEFORE executing multi-step work: an upper-triangular pairwise matrix (every unordered pair once) plus a
checklist for shared substrate, conflicts, mergeable work, and ordering. The LLM does the analysis; this
script only guarantees every pair is considered (nothing silently skipped) and the shape is consistent.

    scaffold.py "task A" "task B" "task C"
    printf 'A\nB\nC\n' | scaffold.py

Relationship legend (fill each pair with one): SYN (synergy / share substrate) · CONF (conflict / contend)
· SEQ (one must precede the other) · INDEP (independent).
"""
import sys

LEGEND = "SYN=synergy/share · CONF=conflict · SEQ=ordering dep · INDEP=independent"


def scaffold(tasks):
    tasks = [t.strip() for t in tasks if t.strip()]
    n = len(tasks)
    out = ["# Pre-execution task-relationship analysis", ""]
    if n == 0:
        out.append("_No tasks provided._")
        return "\n".join(out) + "\n"
    out += ["## Tasks", ""]
    out += [f"{i + 1}. {t}" for i, t in enumerate(tasks)]
    out += ["", "## Pairwise matrix", "", f"Fill EACH pair with one of: {LEGEND}. Every unordered pair is listed once — do not skip any.", ""]
    out += ["| # | pair | relationship | note (why / how to coordinate) |", "|---|---|---|---|"]
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            k += 1
            out.append(f"| {k} | ({i + 1}) × ({j + 1}) | ? | |")
    out += [
        "",
        f"Pairs to consider: {k}.",
        "",
        "## Synthesis checklist (answer before executing in order)",
        "",
        "1. **Shared substrate** — which tasks should be built on ONE shared piece instead of N copies? (e.g. several 'add a sub-agent' asks = one framework.)",
        "2. **Conflicts** — any pair that would fight if done independently? Resolve the design first.",
        "3. **Mergeable** — any pair better done as a single change than two?",
        "4. **Ordering / DAG** — from the SEQ pairs, what is the dependency order? What can run in parallel?",
        "5. **Cross-cutting constraints** — rules/red-lines that apply to ALL (do these first).",
        "",
        "> Do NOT start executing tasks in listed order until this table + checklist are filled. Mechanical",
        "> in-order execution that ignores SYN/CONF/SEQ is exactly what this step prevents.",
    ]
    return "\n".join(out) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    tasks = argv if argv else sys.stdin.read().splitlines()
    sys.stdout.write(scaffold(tasks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
