#!/usr/bin/env bash
# task-ledger Stop gate — refuse to end a round while the ledger still has unfinished work.
#
# This is the hard-enforcement half of hooks/task-ledger. `ledger.py check` exits 2 while any task is
# todo/doing, any task is marked done without evidence, or any inbox item is untriaged. This shim turns
# that exit code into a Stop-hook block, so "all tasks complete" is a machine check rather than the
# agent's own recollection.
#
# Contract (matches hooks/review-gate/scripts/gate.sh so the two Stop hooks compose):
#   empty stdout + exit 0  -> allow the stop
#   {"decision":"block"}   -> force the agent to keep working
#   any internal failure   -> fail OPEN (allow), never wedge the user's session
#
# Config: .agent/ledger/task-ledger.conf in the project, or $HOME/.claude/hooks/task-ledger/task-ledger.conf
#   enabled=1          # 0 disables the gate entirely
#   max_rounds=6       # consecutive blocks before the gate degrades to a warning (loop guard)
set -uo pipefail

_self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_ledger_py="$_self_dir/ledger.py"

# Fail open when the pieces we need are absent. A missing dependency must not block a user's turn.
command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
[ -f "$_ledger_py" ] || exit 0

payload="$(cat 2>/dev/null || true)"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"
sid="$(printf '%s' "$payload" | jq -r '.session_id // "nosess"' 2>/dev/null || echo nosess)"
[ -n "$cwd" ] && [ -d "$cwd" ] && cd "$cwd" 2>/dev/null || true

read_conf() {
  local key="$1" default="$2" val=""
  for f in ".agent/ledger/task-ledger.conf" "$HOME/.claude/hooks/task-ledger/task-ledger.conf"; do
    [ -f "$f" ] || continue
    val="$(sed -n "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*\([^#[:space:]]*\).*/\1/p" "$f" | head -1)"
    [ -n "$val" ] && { printf '%s' "$val"; return; }
  done
  printf '%s' "$default"
}

[ "$(read_conf enabled 1)" = "1" ] || exit 0
max_rounds="$(read_conf max_rounds 6)"

# `check` is the single source of truth, so a ledger that fails to parse can never be mistaken for an
# absent one. Exit codes: 0 = no round open, or the round is complete. 2 = work remains. 1 = the ledger
# itself is unreadable.
report="$(python3 "$_ledger_py" check 2>&1)"
rc=$?
[ "$rc" -eq 0 ] && exit 0

if [ "$rc" -ne 2 ]; then
  # Fail CLOSED on a corrupt ledger, fail OPEN on anything else. The distinction matters: a broken
  # interpreter must not wedge the session, but an unreadable ledger is exactly the case where letting
  # the round end would hide unfinished work.
  case "$report" in
    ledger:*|*"task-ledger: v1"*|*"unknown status"*)
      printf '%s\n\n%s\n' "The task ledger for this round could not be read, so the gate cannot confirm the round is finished." "$report" \
        | jq -Rs '{decision:"block", reason:.}' 2>/dev/null || exit 0
      exit 0 ;;
    *) exit 0 ;;
  esac
fi

# Loop guard. The honest escape is always available (mark an item blocked or dropped with a reason), so a
# run of consecutive blocks means the agent is stuck rather than working. Degrade to a warning instead of
# looping forever, and say plainly that the round did NOT complete.
state_dir="${TL_STATE_DIR:-$HOME/.claude/task-ledger-state}"
mkdir -p "$state_dir" 2>/dev/null || true
rounds_file="$state_dir/${sid}.rounds"
rounds=$(( $(cat "$rounds_file" 2>/dev/null || echo 0) + 1 ))
printf '%s' "$rounds" > "$rounds_file" 2>/dev/null || true

if [ "$rounds" -gt "$max_rounds" ]; then
  printf '%s\n\n%s\n' "$report" \
"── loop guard ──
This gate has blocked ${rounds} times in a row, which means the round is stuck, not progressing.
Stopping is now allowed, but the round is NOT complete. Before you end the turn, tell the user
plainly which items are unfinished and why, and mark each one:
    ledger.py block <TID> --reason '<what is missing>'
so the ledger records the truth rather than an implied success." \
    | jq -Rs '{hookSpecificOutput:{hookEventName:"Stop", additionalContext:.}}' 2>/dev/null || exit 0
  rm -f "$rounds_file" 2>/dev/null || true
  exit 0
fi

printf '%s' "$report" | jq -Rs '{decision:"block", reason:.}' 2>/dev/null || exit 0
