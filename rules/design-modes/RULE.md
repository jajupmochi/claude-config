---
name: design-modes
description: Before starting a substantial build, ASK which mode to work in — prototyping (agent takes over, minimal HITL, get it running) or scaling/精修 (production-grade: bugs, edges, deployment, stability, heavy HITL). They mix; switching mid-task requires explicit user confirmation. Weak models (e.g. DeepSeek-flash) must use scaling-with-harness, not prototyping.
scope: personal
rationale: The two modes need opposite defaults (autonomy vs HITL, speed vs stability). Guessing wrong wastes a whole build. Asking once up front, and confirming on switch, keeps the agent and the user aligned on how much control the user retains.
---

# design-modes

> Ask up front: prototyping or scaling? Prototyping = agent runs, low HITL, get it working. Scaling = stable/production, high HITL. They mix; switching needs the user's OK.

## The two modes

| | **Prototyping** | **Scaling / 精修** |
|---|---|---|
| Goal | Get a working version fast | Land it: correct, robust, deployable |
| Agent autonomy | High — agent takes over the implementation | Bounded — user stays in the loop |
| HITL | Minimal (approve at milestones) | Heavy (approve edits, review diffs, confirm risky steps) |
| Tests/edges | Breadth may be deferred (never the real run) | Full: bugs, edge cases, boundaries, deployment |
| Change style | Whole-feature strokes | Small, reviewed, reversible steps |
| Fits | New ideas, throwaway spikes, exploration | Real deployment, shared/critical code, refactors |

## The rule

1. **Ask before starting** a substantial build which mode applies. If the user's message already implies one
   (e.g. "just spike it" → prototyping; "harden this for prod" → scaling), state your read and proceed.
2. **They mix.** A prototyping run often needs scaling for one delicate part (a tricky bug, a data boundary);
   a scaling run often needs a quick prototype spike or a bulk auto-refactor. Use the right mode per sub-task.
3. **Switching mode mid-task requires explicit user confirmation** — the HITL level is the user's control
   dial; don't silently drop them out of (or into) the loop.
4. **Capability floor:** models/agents that lack strong autonomous execution (e.g. DeepSeek-flash and similar
   low-tier) MUST run in scaling mode OR be given enough harness (strict templates, per-step verification via
   the task-orchestrator) — never handed a prototyping "take it away" brief they can't safely execute.

## Interaction with other rules

- Pairs with `task-relationship-analysis` (do the cross-task map first) and the `task-orchestrator` capability
  profiling (which sets template strictness by model tier).
- In scaling mode, the pre-edit confirmation / phased-planning discipline is in full force. In prototyping mode
  the user has pre-authorized more autonomy — still never fake a run or skip the real-run gate behind a "works".
