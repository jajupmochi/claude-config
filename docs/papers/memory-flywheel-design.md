# A Per-Project, Grep-Native Memory Flywheel for Coding Agents

**Status: DESIGN DRAFT (v0.1).** Design + evaluation *design* only — no experiments have been run yet.
Citations marked ⚠ are 2026 preprints not yet verified as peer-reviewed and must be confirmed (or dropped to
"supporting") before submission. This draft corresponds to the `memory-flywheel` skill in this repo.

## Abstract

Long-running and multi-project coding-agent sessions lose detail two ways: raw interaction logs (JSONL) are
too large to load into context, and context *compaction* is a lossy LLM summarization that discards
intermediate reasoning and rejected approaches. We propose a **memory flywheel**: a per-project, grep-native
file store that records each round of work verbatim (raw I/O + reasoning + control metadata) under a
coarse→fine index the agent *descends* on demand, augmented with keyword (and, planned, graph) overlays, and
maintained by a supervising component so it improves as it is used. Unlike vector-recall memory, retrieval is
a deterministic tree descent over plain files, reproducible and usable by native tools (`grep`). We give the
design, position it against prior art, and specify (design-only) an evaluation over recall, answer accuracy,
token cost, a *lossiness delta* versus raw logs, *descent efficiency*, and *flywheel gain* over rounds.

## 1. Introduction

- **Problem.** Coding agents accrue long histories. Two failure modes: (a) raw JSONL logs cannot be reloaded
  wholesale into a bounded context window; (b) summarization/compaction is *inherently lossy* — it preserves
  file states and decisions but drops intermediate reasoning and rejected approaches, so later rounds cannot
  recover "why we did / didn't do X."
- **Gap.** Existing agent-memory systems mostly extract/summarize (lossy) or use vector recall (opaque,
  non-reproducible, poor fit for `grep`-centric coding workflows). None combine, for a *coding agent, per
  project*: verbatim leaves + control metadata + a *descended* coarse→fine index + keyword/graph overlays +
  a supervising flywheel.
- **Contribution.** (1) the design of such a system; (2) a positioning that isolates the specific novel
  combination; (3) an evaluation design with metrics tailored to the lossiness and descent-efficiency claims.

## 2. Related work (to verify before submission)

- **Zep / Graphiti** — hierarchical episodic(raw)→semantic→community tiers + temporal knowledge graph;
  explicitly non-lossy. Closest on *architecture*.
- **MemWalker** — builds a summary tree and *descends* it at query time. Closest on the *retrieval act*.
- **A-MEM** ⚠ — agentic memory with keyword/tag + graph links + self-evolution. Closest on *overlays*.
- **Generative Agents** (peer-reviewed) — a memory stream of raw observations + reflection + a learning loop.
- **Anthropic memory tool + Agent Skills progressive disclosure** — grep-native files + coarse→fine loading;
  the closest *mechanism* and a shippable base.
- Also: MemGPT/Letta, mem0/mem0g, LangMem, Reflexion, RAPTOR (recursive summary tree), and the CoALA
  cognitive-architecture taxonomy. *(Full survey table + URLs in the internal research note; peer-review
  status to be confirmed per source.)*

## 3. The memory flywheel

### 3.1 Storage model
- `<root>/<project>/rounds/NNNN-<kind>.md` — one file per round: frontmatter control metadata (id, kind,
  title, timestamp, keywords) + the **verbatim** body (raw input/output/decision). Leaves are never summarized.
- `<root>/<project>/INDEX.md` — the coarse layer: a table of all rounds. Read first; it is small.

### 3.2 Retrieval by descent (not top-k vectors)
Read `INDEX.md` (coarse) → select candidate rounds by keyword recall → open only those leaves. Recall is
deterministic keyword scoring (exact + optional similar-keyword/prefix), so it is reproducible and equivalent
to `grep -ri`. Planned: a graph overlay (edges between rounds sharing entities) to expand recall along links.

### 3.3 The flywheel
Each substantive round is recorded; the store and its index grow; recall quality rises with coverage. A
supervising component (planned: a hook) reminds the agent to record, closing the loop.

### 3.4 LLM as component
`record` / `index` / `recall` are pure deterministic code. The model only *writes* round content and *reads*
what recall returns — keeping memory cheap, reproducible, and front-end-inspectable.

## 4. Novelty

Each surveyed system holds 1–3 of the four pillars; none holds all four for a *coding-agent, per-project,
grep-native file* memory: ① verbatim-I/O leaves with JSONL-style control metadata, ② a coarse→fine index the
agent *descends* (not top-k vector recall), ③ keyword + (planned) graph overlays, ④ a supervising-plugin
flywheel. The contribution is the *combination and framing* (per-project cross-session coding logs), not a
new primitive.

## 5. Evaluation design (design only — no runs yet)

- **Benchmarks/adaptation:** LongMemEval, LoCoMo, DMR-style dialog memory recall, adapted to per-project
  coding-session logs (synthesize multi-session tasks with facts introduced early and queried later).
- **Metrics:** (a) recall@k and answer accuracy on late queries; (b) **lossiness delta** = accuracy of
  descent-over-verbatim minus accuracy of compaction-summary, on questions about *rejected approaches /
  intermediate reasoning* (where compaction is expected to fail); (c) **token cost** of recall vs loading raw
  logs vs a full summary; (d) **descent efficiency** = leaves opened / leaves relevant; (e) **flywheel gain**
  = accuracy as a function of rounds recorded.
- **Baselines:** raw-log-in-context (upper bound, token-infeasible at scale), compaction-summary (the lossy
  baseline), vector-RAG over rounds, and this system (exact and +similar/+graph ablations).
- **Ablations:** verbatim vs summarized leaves; exact vs similar vs graph recall; with/without the supervising
  reminder.

## 6. Limitations & threats to validity

v0.1 implements only record/index/exact+similar recall; graph overlay, supervising hook, and the eval harness
are unbuilt. Keyword recall can miss paraphrase without the graph/embedding overlay. Per-project scoping does
not address cross-project transfer (a separate mechanism). No experiments yet — all quantitative claims are
hypotheses.

## 7. Conclusion

A deterministic, grep-native, per-project flywheel keeps the verbatim detail that compaction drops, at bounded
retrieval cost, and improves with use. The design is implemented as a working v0.1 core; the evaluation above
is the next step.

---

*Provenance: design distilled from this repo's overhaul research (internal note R3). This file is a public,
privacy-clean draft; the internal note (with machine-specific paths and the full source table) stays local.*
