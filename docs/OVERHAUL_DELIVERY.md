# agent-harness overhaul — delivery summary

A 16-task overhaul turning agent-harness into a multi-agent (Claude Code · Codex · opencode) harness with
token/memory/model tooling. This is the one-page map of what shipped, how to use it, and what remains.

## What shipped (by task)

| # | Task | Delivered |
|---|---|---|
| 1 | Multi-agent architecture | 3 per-agent manifests generated from ONE canonical source (`adapters/manifest.source.json` + `adapters/*.mjs` projectors, byte-parity CI gate `build.mjs --check`). *(Full `.agent/` tree-move pending.)* |
| 2 | Token / sub-agents | `task-orchestrator` model-tier sub-agent routing; research delegated to sub-agents throughout. |
| 3/4/5 | Memory & context | `memory-flywheel` skill: `mem.py` record/index/recall + `--fuzzy` + graph (`link`/`--graph`) + eval harness (`mem_eval.py`); design paper (`docs/papers/memory-flywheel-design.md`). |
| 6 | Adaptive tool discovery | `agent-update-watcher` — interval-guarded ecosystem update checker. |
| 7 | Plugin hygiene | rename leftovers, dead-knob templates, malformed-YAML fixes. |
| 8 | TUI | `recommendations/tui-for-agents.md` (survey) + `tui-installer` (ask-first, dry-run installer). |
| 9 | Prompt library | `prompt-library` — privacy-gated add/index/find/scan. |
| 10 | Adaptive model | `adapters/models.config.json` + `scripts/resolve_model.mjs` (consumed by the opencode projector). |
| 11 | opencode support | `opencode.json` generated from canonical source; `.opencode/plugin/review-gate.js` + tested helper. |
| 12 | Generalize plugins | `docs/MULTI_AGENT_GUIDE.md` (the two patterns + native-format bridges). |
| 13 | Design modes | `rules/design-modes` (prototyping vs scaling). |
| 14 | Codex ecosystem | (done earlier, light). |
| 15 | Inter-task analysis | `task-relationship-analysis` skill (pairwise matrix scaffold). |
| 16 | Test-first | `rules/test-first`. |
| — | review-gate | DE-FORKED across all 3 agents via one shared `hooks/review-gate/scripts/core.sh` + thin shims. |

Repo now has 16 published skills + 20 rules, all generated into the 3 agents' configs from one source.

## How to use (quick starts)

- **Memory:** `python3 skills/memory-flywheel/scripts/mem.py record --project P --kind design --title "…" < body`;
  then `… recall --project P --query "…" --fuzzy --graph`. Eval: `mem_eval.py --fixtures f.json`.
- **Model tiers:** `node scripts/resolve_model.mjs claude research`.
- **Prompt library:** `python3 skills/prompt-library/scripts/plib.py add --title "…" < prompt` (privacy-gated).
- **TUI:** `bash skills/tui-installer/scripts/install-tui.sh --check` then `--apply`.
- **Update watch:** `python3 skills/agent-update-watcher/scripts/check_updates.py --config sources.json …`.
- **Build/verify:** `node build.mjs` (regenerate manifests), `node build.mjs --check` (drift gate).
- **Before a multi-step task:** `python3 skills/task-relationship-analysis/scripts/scaffold.py "task A" "task B" …`.

## Engineering discipline

Every change was test-first, CI-green, and privacy-clean; ~17 test files pass. The LLM is a component
(record/index/recall/resolve/scan/scaffold are deterministic code); model tiers and provider switching keep the
Claude-Code-no-provider-switch red line. Design/research notes live under `docs/strategy/…` (local, machine-path
laden) and `docs/papers/`.

## Known gaps (need conditions beyond a normal edit session)

1. **`.agent/` whole-tree move** (task 1) — the projector must also generate the full `.claude/` tree CC reads;
   substantial, path-resolution-sensitive; do in a fresh, focused context.
2. **Machine configuration** — applying the 3-agent config + install migration on the real workstation is
   live-state work to do with the user present.
3. **Supervising hook** (task 5) — a live Stop/PostToolUse hook (delicate; acts on live turns).
4. ~~**opencode hook real-machine verification** (task 11)~~ — **DONE (2026-07-10).** Verified against the real
   opencode 1.3.17 binary: `opencode debug config --print-logs --log-level DEBUG` shows the plugin
   `loading plugin` and lists it in the resolved `plugin_origins`. This surfaced and fixed a real bug — the
   plugin shipped in `.opencode/plugins/` (plural), but opencode only auto-discovers `.opencode/plugin/`
   (singular), so it had never loaded; renamed the dir and corrected the manifest note + docs.
5. **Eval on real data** — `mem_eval.py` runs on synthetic fixtures; real sessions + gold labels give real numbers.

## File map (new/changed homes)

`adapters/` (projectors + model config) · `build.mjs` · `hooks/review-gate/scripts/{core,gate}.sh` +
`scripts/codex_review_gate.sh` + `.opencode/plugin/` · `skills/{memory-flywheel,prompt-library,
task-relationship-analysis,agent-update-watcher,tui-installer}/` · `rules/{test-first,design-modes}/` ·
`recommendations/tui-for-agents.md` · `docs/{MULTI_AGENT_GUIDE,papers/memory-flywheel-design,OVERHAUL_DELIVERY}.md`.
