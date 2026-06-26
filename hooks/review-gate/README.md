# review-gate

> Hook-enforced, **un-skippable** review of AI-generated code on **every code-changing turn, in every session**. Closes the gap that skills/rules can't: they are model-discretion (skippable); hooks are harness-run (always execute).

Full landscape, analysis, and tool comparison: [`docs/ai-code-review/`](../../docs/ai-code-review/README.md).

## What it does (3 tiers + 1 opt-in)

| Tier | Hook | Script | Behavior |
|---|---|---|---|
| T0 | `PostToolUse(Write\|Edit)` | `scripts/track.sh` | logs each changed file per session (fail-open) |
| T1 | `Stop` | `scripts/gate.sh` | on code change: run linters (ruff/shellcheck) + force one review round whose feedback is a **Markdown report** (names each review form + tool; mandates **per-function/module AI review by default** when a function/module changed) and requires findings as a **markdown list** in-session; `{"decision":"block"}` until lint-clean + reviewed. Loop-guarded (≤3), fail-open. **Token note:** per-module AI review every code-turn costs more tokens than lint-only — see [`docs/ai-code-review`](../../docs/ai-code-review/README.md#5-deployment-all-sessions--every-edit--never-skip). |
| T2 | `PreToolUse(Bash)` | `scripts/precommit.sh` | **`git commit` is FREE** (T1 review still runs & surfaces findings, it just never blocks committing) — unless the user opted in via `review-gate.conf: block_commit=1`. **Remote-publishing** (`git push` / `gh pr create\|merge` / `gh release create`) is hard-blocked **unless the cwd is on `push-whitelist.txt`**. Every block is **NON-FATAL**: `exit 2` denies only that one command and the agent CONTINUES its other work (not pushing blocks nothing else). Config files: `push-whitelist.txt` (per-project push exemptions) + `review-gate.conf` (`block_commit`). |
| STRICT (opt-in) | `Stop` `type:"agent"` | `strict.snippet.json` | model-judged deep review of the diff (experimental, adds latency) |

PR-level review (CodeRabbit / Greptile / `/code-review` / security GH Action) is **complementary** — review-gate is the local, continuous, enforced layer.

## Install

```bash
# 1) scripts to a stable path (NOT a removable mount)
mkdir -p ~/.claude/hooks/review-gate
cp scripts/*.sh ~/.claude/hooks/review-gate/ && chmod +x ~/.claude/hooks/review-gate/*.sh
# 2) merge the hooks into your settings (all sessions):
#    settings.snippet.json  ->  ~/.claude/settings.json   (user scope = every project)
#    (merge under the single "hooks" object; keep existing event keys as siblings)
# 3) (optional) also merge strict.snippet.json for hook-enforced AI review
```
Verify with `/hooks` in Claude Code (lists configured hooks by event).

## Requirements
`jq` (used for parsing hook input; if absent, every script fails **open** = allows). Optional: `ruff`, `shellcheck` for deterministic checks. `.py` formatting/lint is already handled by the `ruff-format-on-edit` hook.

## Escape hatch
- Disable everything: set `"disableAllHooks": true` in `~/.claude/settings.json`.
- Clear a stuck gate for one session: `rm ~/.claude/review-state/<session_id>.changed`.

## Safety design
All scripts `set +e` and **fail open**: any internal error, missing `jq`, malformed input, or ≥3 block rounds results in `exit 0` (the session is never wedged). The gate only blocks on real lint failures or the once-per-change-set review mandate.

## State
Per-session files under `~/.claude/review-state/`: `<sid>.changed` (changed files), `<sid>.rounds` (loop guard), `<sid>.reviewed` (review-pass marker). Cleared on a clean pass.
