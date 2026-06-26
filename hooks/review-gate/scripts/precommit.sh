#!/usr/bin/env bash
# review-gate / precommit.sh  —  PreToolUse(Bash) hook.  [v3 2026-06-26]
#
# Policy (deliberately simple):
#   - `git commit` and EVERYTHING else: ALLOWED. The AI review still runs at Stop (gate.sh) and
#     surfaces findings, but committing is never blocked — UNLESS the user opted in
#     (review-gate.conf: block_commit=1), in which case commits are denied the same NON-FATAL way.
#   - remote-publishing (`git push`, `gh pr create|merge`, `gh release create`): HARD-blocked, UNLESS
#     the current project is on the push-whitelist.
#
# A block is NON-FATAL by design: exit 2 denies ONLY that one command and feeds the reason back to
# Claude, which then CONTINUES the rest of its work. Not pushing / not committing blocks nothing else,
# so a blocked command must NOT halt the turn (the agent may simply not know the rule, or slipped).
# Fail-open: jq missing / parse failure -> exit 0 (allow).
set +e
command -v jq >/dev/null 2>&1 || exit 0
HD="$HOME/.claude/hooks/review-gate"
IN="$(cat 2>/dev/null)"
cmd="$(printf '%s' "$IN" | jq -r '.tool_input.command // empty' 2>/dev/null)"

# Classify. Anything not commit/remote-publishing is always allowed.
case "$cmd" in
  *"git push"*|*"gh pr create"*|*"gh pr merge"*|*"gh release create"*) kind="push" ;;
  *"git commit"*) kind="commit" ;;
  *) exit 0 ;;
esac

# --- commit: free by default; denied (non-fatal) only if the user opted in ---
if [ "$kind" = "commit" ]; then
  bc=0
  [ -f "$HD/review-gate.conf" ] && bc="$(sed -n 's/^[[:space:]]*block_commit[[:space:]]*=[[:space:]]*\([0-9][0-9]*\).*/\1/p' "$HD/review-gate.conf" | head -1)"
  [ "$bc" = "1" ] || exit 0
  echo "[review-gate] git commit is blocked by your opt-in setting (block_commit=1). DELIBERATE rule, NOT an error — skip the commit and CONTINUE the rest of your work (you/the user can commit manually). Turn off: set block_commit=0 in $HD/review-gate.conf" >&2
  exit 2
fi

# --- push / remote-publishing: blocked unless this project is whitelisted ---
cwd="$(printf '%s' "$IN" | jq -r '.cwd // empty' 2>/dev/null)"; [ -n "$cwd" ] || cwd="$PWD"
wl="$HD/push-whitelist.txt"
if [ -f "$wl" ]; then
  while IFS= read -r entry; do
    case "$entry" in ''|'#'*) continue ;; esac
    entry="${entry%/}"
    case "$cwd" in "$entry"|"$entry"/*) exit 0 ;; esac   # cwd == or under a whitelisted path -> allow
  done < "$wl"
fi
echo "[review-gate] Remote push is blocked for this project (not on the push-whitelist). DELIBERATE safety rule, NOT an error — skip this push and CONTINUE with the rest of your work; not pushing does not block anything else. To allow pushes here: add this project's path to $wl (or answer yes to the push-whitelist question when setting up autopilot). The user can also push manually." >&2
exit 2
