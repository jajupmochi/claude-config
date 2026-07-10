---
name: memory-flywheel
description: Use to persist and recall per-project cross-session working memory so long or multi-project sessions don't lose detail to context compaction. Record each round of progress (verbatim I/O + reasoning + metadata) into a project memory dir, read a coarse INDEX first, then open only what keyword recall points at. Deterministic, grep-native, LLM-as-component.
policy:
  allow_implicit_invocation: true
---

# memory-flywheel

A per-project, cross-session memory built as an iterating **data flywheel** (WS-B; overhaul tasks 3/4/5).
It complements the raw JSONL logs and the compaction-summary memory: JSONL is too bulky to load whole,
and `/compact` is **lossy** (it keeps file states + decisions but drops intermediate reasoning and rejected
approaches — verified). The flywheel keeps the **verbatim** detail in grep-native files with a coarse→fine
index, so nothing important is silently lost and recall is cheap.

**Design (see `docs/strategy/agent-harness-overhaul-2026-07-09/00-research.md` §B):** integrative of Zep's
episodic→semantic tiers, MemWalker's descend-a-summary-tree, A-MEM's keyword/graph overlay, and Anthropic's
memory-tool + Skills progressive disclosure. The novel niche is a *coding-agent, per-project, grep-native file*
memory combining verbatim leaves + control metadata + a descended coarse→fine index + keyword recall.

## Layout (under `--root`, default `.agent-memory/`)

```
<root>/<project>/
    rounds/NNNN-<kind>.md   one file per round: frontmatter (id, kind, title, ts, keywords) + VERBATIM body
    INDEX.md                coarse layer — a table of every round; READ THIS FIRST
```

## The loop (each substantive round)

1. **Record** the round verbatim (raw input/output/decision), tagged with a kind + keywords:
   `python3 scripts/mem.py record --project P --kind design --title "…" --keywords a,b < body`
   (auto-refreshes `INDEX.md`.)
2. **Recall** before acting, progressively — never load everything:
   - read `INDEX.md` (coarse), then
   - `python3 scripts/mem.py recall --project P --query "terms"` → ranked round files; open only those.
   - or plain `grep -ri terms <root>/P/rounds/` (it's just files).
3. The store grows and recall improves as you use it — the flywheel.

## Why LLM-as-component

record / index / recall are pure deterministic code (no model call). The model only *writes the round content*
and *reads what recall returns*. This keeps memory cheap, reproducible, and front-end-inspectable.

## Status

Extra recall knobs: `recall --fuzzy` matches similar/variant keywords (memory↔memories); `link --from A --to B`
records a graph edge and `recall --graph` pulls in rounds linked to a keyword hit (1 hop) so related context
surfaces without a shared keyword.

v0.2 (record / index / recall + `--fuzzy` + `link` & `--graph` overlay), tested (`test_mem.py`, 9/9). Planned:
a supervising hook that reminds the agent to record, and a `--ts`-driven eval harness (LongMemEval/LoCoMo-style:
recall, lossiness-delta, tokens) — designed in the research doc, not yet built.
