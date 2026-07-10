# agent-harness overhaul — delivery summary

A 16-task overhaul turning agent-harness into a multi-agent (Claude Code · Codex · opencode) harness with
token/memory/model tooling. This is the one-page map of what shipped, how to use it, and what remains.

## What shipped (by task)

| # | Task | Delivered |
|---|---|---|
| 1 | Multi-agent architecture | 3 per-agent manifests generated from ONE canonical source (`adapters/manifest.source.json` + `adapters/*.mjs` projectors, byte-parity CI gate `build.mjs --check`); 16 skills deployed cross-agent (`bin/deploy-skills.mjs`). *(`.agent/` tree-move descoped — see gaps.)* |
| 2 | Token / sub-agents | `task-orchestrator` model-tier sub-agent routing; research delegated to sub-agents throughout. |
| 3/4/5 | Memory & context | `memory-flywheel` skill: `mem.py` record/index/**IDF recall** + `--fuzzy` + graph (`link`/`--graph`) + eval harness (`mem_eval.py`) + **supervising hook** (`supervise.py`, auto-record, off by default); real-data eval recall@5 = 1.00; design paper (`docs/papers/memory-flywheel-design.md`). |
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

## Known gaps — ALL RESOLVED (2026-07-10 real-machine pass)

1. ~~**`.agent/` whole-tree move** (task 1)~~ — **DESCOPED (best-outcome decision).** The multi-agent goal
   ("configure all 3 agents from ONE source") is already met by the manifest projectors, and each agent reads
   its config from its own runtime location (`~/.claude/`, codex plugin cache, `~/.config/opencode/`) via a
   separate DEPLOY step — not from the repo's internal folder layout. So physically moving skills/rules/hooks
   under `.agent/` is cosmetic reorganization with low value and high path-churn risk; not worth doing.
2. ~~**Machine configuration**~~ — **DONE.** All 3 agents configured + verified on the real workstation:
   review-gate de-forked & deployed (Claude hooks redeployed; codex plugin installed+enabled; opencode plugin
   dir fixed & runtime-verified), and all 16 skills deployed cross-agent (`bin/deploy-skills.mjs`): Claude 7
   appeared live in the session Skill catalog, opencode `debug skill` 5→32 (16/16 resolve), codex plugin cache
   holds them. The agents were wired to a stale pre-overhaul install clone; that clone was safe-synced (+26
   commits). NOTE: codex's cache is COPY-based — re-run `codex plugin remove/add` after each clone update;
   Claude & opencode use symlinks and auto-update.
3. ~~**Supervising hook** (task 5)~~ — **DONE.** `skills/memory-flywheel/scripts/supervise.py` — a Stop hook
   that auto-records each turn's verbatim round; OFF by default, non-fatal, dedup-guarded; 7 tests + validated
   against a real 27k-line transcript.
4. ~~**opencode hook real-machine verification** (task 11)~~ — **DONE.** Verified against the real opencode
   1.3.17 binary (`opencode debug config` shows `loading plugin`). Fixed a real bug: the plugin shipped in
   `.opencode/plugins/` (plural) but opencode only auto-discovers `.opencode/plugin/` (singular).
5. ~~**Eval on real data**~~ — **DONE.** Ran recall@5 over the 15 real cross-session memory files with honest
   gold labels: 0.92 exact / 0.83 fuzzy, with a systematic miss. Diagnosed it (raw TF swamped by common words)
   and fixed recall with IDF weighting → **1.00 exact and fuzzy**. Turned an eval into a shipped improvement.

## File map (new/changed homes)

`adapters/` (projectors + model config) · `build.mjs` · `hooks/review-gate/scripts/{core,gate}.sh` +
`scripts/codex_review_gate.sh` + `.opencode/plugin/` · `skills/{memory-flywheel,prompt-library,
task-relationship-analysis,agent-update-watcher,tui-installer}/` · `rules/{test-first,design-modes}/` ·
`recommendations/tui-for-agents.md` · `docs/{MULTI_AGENT_GUIDE,papers/memory-flywheel-design,OVERHAUL_DELIVERY}.md`.
