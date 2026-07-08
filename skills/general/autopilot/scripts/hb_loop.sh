#!/usr/bin/env bash
# hb_loop.sh <proj> — background liveness heartbeat for an IN-SESSION autopilot run.
#
# The in-session run launches this DETACHED at startup (see PROMPT.md):
#     setsid bash ~/.claude/autopilot/bin/hb_loop.sh <proj> >/dev/null 2>&1 &
#
# Why: the PR #10 in-session cron model has no run.sh wrapper, so nothing proves the run is alive while the
# main transcript is momentarily quiet (e.g. during a long subagent). This loop writes "<cycle_ts> <now_ts>"
# to run-heartbeat every INTERVAL; watch.py reads it as the SECOND liveness signal (transcript mtime being
# the first).
#
# Two hard rules:
#   1. AUTO-STOP THE MOMENT THE CYCLE COMPLETES. As soon as cycle_status.py says complete (exit 0) the loop
#      removes the heartbeat and exits — a finished run must leave NO lingering "alive" signal.
#   2. HARD CAP at MAX_TICKS. A run that DIED can't tell the loop to stop, so the loop self-terminates after
#      MAX_TICKS and clears the heartbeat, bounding how long a zombie heartbeat can look "fresh".
set +e
PROJ="$1"; [ -n "$PROJ" ] || exit 0
case "$PROJ" in */*|*..*) exit 0 ;; esac                 # defensive: no path escape
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="$HOME/.claude/autopilot/$PROJ"; [ -d "$BASE" ] || exit 0
HB="$BASE/run-heartbeat"
PY="$(command -v python3 || echo python3)"
INTERVAL="${AUTOPILOT_HB_INTERVAL:-300}"                 # 5 min between beats
MAX_TICKS="${AUTOPILOT_HB_MAX_TICKS:-18}"                # 18 * 5 min = 90 min hard cap

# Resolve THIS cycle's id once so the heartbeat is attributable to this cycle (watch.py checks it matches).
cyc="$("$PY" "$HERE/cycle_status.py" "$PROJ" 2>/dev/null \
        | "$PY" -c 'import json,sys
try:
    print(json.load(sys.stdin).get("cycle_ts", ""))
except Exception:
    print("")' 2>/dev/null)"

i=0
while [ "$i" -lt "$MAX_TICKS" ]; do
  # Rule 1: stop the instant the cycle is complete (cycle_status exit 0). Remove the heartbeat and leave.
  if "$PY" "$HERE/cycle_status.py" "$PROJ" >/dev/null 2>&1; then
    rm -f "$HB"; exit 0
  fi
  printf '%s %s\n' "${cyc:-0}" "$(date +%s)" > "$HB"
  i=$((i + 1))
  sleep "$INTERVAL"
done
# Rule 2: hard cap hit — clear the heartbeat so a dead run's beat can't look "fresh" past the cap.
rm -f "$HB"
exit 0
