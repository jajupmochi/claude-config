#!/usr/bin/env bash
# review-gate / gate.sh — Claude Code Stop-hook SHIM over core.sh (the agent-neutral review logic).
# gate.sh only does the Claude-specific parts: (1) read the session id from Claude's Stop payload,
# (2) point core.sh at Claude's review-state dir, (3) wrap core.sh's markdown in Claude's native
# Stop-hook JSON. The review LOGIC + the FORMS report live in core.sh (shared with the Codex/opencode shims).
set +e
command -v jq >/dev/null 2>&1 || exit 0

IN="$(cat 2>/dev/null)"
sid="$(printf '%s' "$IN" | jq -r '.session_id // empty' 2>/dev/null)"; [ -n "$sid" ] || sid="nosess"
HERE="$(cd "$(dirname "$0")" && pwd)"

# RG_BRIEF_FILE keeps the ~3KB review brief OUT of the user's transcript. Claude Code renders a Stop
# hook's reason string verbatim to the user, so the brief — which is instructions for the model, not a
# message for the user — used to be dumped into their terminal on every code-changing turn. core.sh now
# writes it to this file and returns a short pointer, which is what gets displayed.
reason="$(RG_STATE_DIR="$HOME/.claude/review-state" RG_SID="$sid" \
          RG_BRIEF_FILE="$HOME/.claude/review-state/$sid.brief.md" \
          bash "$HERE/core.sh")"
[ -n "$reason" ] || exit 0   # core decided no review is needed this turn => allow stop

# Deliver the review. DEFAULT (stop_mode=block): `decision:"block"` — BLOCKS the stop to FORCE one review
# round this turn. Enforcement is the whole point of the gate, so it is the default.
# UNAVOIDABLE trade-off in current Claude Code (verified against the official hooks docs):
#   - `decision:"block"` BLOCKS/forces the review, but a BLOCKING Stop hook is labeled "Stop hook error" on
#     CC >= 2.1.174 (it was "Stop hook feedback" on 2.1.150). That label is cosmetic — the review still runs.
#   - `hookSpecificOutput.additionalContext` gets a clean "Stop hook additional context" label BUT the docs
#     confirm it does NOT block ("the conversation continues" = the turn ENDS, Claude uses it next turn) —
#     i.e. the review becomes SKIPPABLE, not enforced. It also needs CC >= 2.1.152 or it is ignored entirely.
# There is NO output that both blocks AND avoids the "error" label. Enforcement wins by default; a user who
# would rather have the clean label and accept a skippable (advisory) review can set stop_mode=feedback.
_conf="$HOME/.claude/hooks/review-gate/review-gate.conf"
smode="block"
[ -f "$_conf" ] && smode="$(sed -n 's/^[[:space:]]*stop_mode[[:space:]]*=[[:space:]]*\([a-z]*\).*/\1/p' "$_conf" | head -1)"
if [ "$smode" = "feedback" ]; then
  printf '%s' "$reason" | jq -Rs '{hookSpecificOutput:{hookEventName:"Stop", additionalContext:.}}' 2>/dev/null || exit 0
else
  printf '%s' "$reason" | jq -Rs '{decision:"block", reason:.}' 2>/dev/null || exit 0
fi
exit 0
