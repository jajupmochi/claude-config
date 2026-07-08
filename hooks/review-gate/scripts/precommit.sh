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
# Detect the git SUBCOMMAND robustly — even PAST global options AND quoted args that contain spaces — so
# `git -C <path> push`, `git -C "/tmp/my repo" push`, `git --git-dir=<x> push`, `git -c "k=v x" push`,
# `/usr/bin/git push` are NOT a bypass. (The ai-studio session found the old contiguous `*"git push"*`
# match missed `git -C /tmp/fe-merge push`; Copilot then flagged that quoted spaced args still slipped.)
# _OPT = one global-option token: a `-flag` with an optional arg that may be "double"- or 'single'-quoted
# (spaces allowed inside quotes) or bare. push/commit must then follow as a whole word. Deliberately does
# NOT match `git log --grep push`, `git show HEAD:push.txt`, `echo pushing` (all verified in test_precommit).
_OPT="[[:space:]]+-[^[:space:]]+([[:space:]]+(\"[^\"]*\"|'[^']*'|[^-[:space:]][^[:space:]]*))?"
_RXP="(^|[^[:alnum:]_-])git(${_OPT})*[[:space:]]+push([[:space:]]|\$)"
_RXC="(^|[^[:alnum:]_-])git(${_OPT})*[[:space:]]+commit([[:space:]]|\$)"
kind=""
if   [[ "$cmd" =~ $_RXP ]]; then kind="push"
elif [[ "$cmd" =~ $_RXC ]]; then kind="commit"
fi
case "$cmd" in
  *"gh pr create"*|*"gh pr merge"*|*"gh release create"*) kind="push" ;;   # remote-publishing, no git
esac
[ -n "$kind" ] || exit 0

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
# one-shot override: the USER explicitly authorized THIS single push WITHOUT whitelisting the project.
# Armed by `touch "$HD/allow-push-once"` (do that ONLY on an explicit user push request); consumed here so
# it permits exactly one push and never persists — the project stays off the whitelist.
if [ -f "$HD/allow-push-once" ]; then
  rm -f "$HD/allow-push-once"
  echo "[review-gate] one-shot override consumed — allowing this SINGLE remote-publishing command (git push / gh pr create|merge / gh release create; project NOT added to the whitelist). Re-arm 'touch $HD/allow-push-once' for another one-off." >&2
  exit 0
fi

echo "[review-gate] Remote publishing (git push / gh pr create|merge / gh release create) is blocked for this project (not on the push-whitelist). DELIBERATE safety rule, NOT an error — skip this command and CONTINUE the rest of your work (not publishing blocks nothing else).
  - If the USER explicitly told you to publish THIS time WITHOUT whitelisting (e.g. \"直接推送，但不要加进白名单\"): run 'touch $HD/allow-push-once' then retry the command once. It is consumed after a single remote-publishing command and does NOT whitelist the project. Do this ONLY on an explicit user request, never on your own initiative.
  - To allow remote-publishing here permanently: add this project's path to $wl (or answer yes to the push-whitelist question when setting up autopilot).
  - The user can also do it manually." >&2
exit 2
