#!/usr/bin/env bash
# skip.sh <proj> today | until <YYYY-MM-DD> | resume | status  [reason...]
#
# Skip (pause) an autopilot project's scheduled run(s) via one command. It writes `paused_until` (a date,
# EXCLUSIVE) into the project's cron_state.json; cycle_status.py then reports every cycle whose scheduled
# fire is before that date as complete+skipped, so the daily run self-skips at PROMPT step 0, run.sh's
# idempotent guard skips, AND the watchdog does NOT try to "recover" it. The in-session cron can stay armed
# — a fired run simply self-skips — so this is robust even if the SessionStart hook re-arms the cron.
#
#   skip.sh <proj> today             -> skip today's run (resumes tomorrow)
#   skip.sh <proj> until 2026-07-10  -> skip every run before 2026-07-10 (resumes on the 10th)
#   skip.sh <proj> resume            -> clear the skip (runs resume on the next cron fire)
#   skip.sh <proj> status            -> print the current paused_until (or "not paused")
set +e
PROJ="$1"; CMD="$2"
{ [ -n "$PROJ" ] && [ -n "$CMD" ]; } || {
  echo "usage: skip.sh <proj> today | until <YYYY-MM-DD> | resume | status  [reason...]" >&2; exit 2; }
case "$PROJ" in */*|*..*) echo "invalid proj" >&2; exit 2 ;; esac
CS="$HOME/.claude/autopilot/$PROJ/cron_state.json"
[ -f "$CS" ] || { echo "no cron_state.json for '$PROJ' ($CS)" >&2; exit 2; }
PY="$(command -v python3 || echo python3)"

case "$CMD" in
  status)
    "$PY" -c 'import json,sys;d=json.load(open(sys.argv[1]));pu=d.get("paused_until");print(("paused_until=%s  reason=%s"%(pu,d.get("paused_reason",""))) if pu else "not paused")' "$CS"
    exit 0 ;;
  resume|clear)
    "$PY" -c 'import json,sys;d=json.load(open(sys.argv[1]));d.pop("paused_until",None);d.pop("paused_reason",None);json.dump(d,open(sys.argv[1],"w"),indent=2)' "$CS"
    echo "[skip] '$PROJ' resumed — runs will proceed on the next cron fire."
    exit 0 ;;
  today)
    pu="$("$PY" -c 'import datetime;print((datetime.date.today()+datetime.timedelta(days=1)).isoformat())')"
    reason="${*:3}" ;;
  until)
    pu="$3"; reason="${*:4}"
    echo "$pu" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' || {
      echo "invalid date '$pu' (need YYYY-MM-DD)" >&2; exit 2; } ;;
  *)
    echo "unknown command '$CMD' (use: today | until <YYYY-MM-DD> | resume | status)" >&2; exit 2 ;;
esac

[ -n "$reason" ] || reason="user-requested skip"
"$PY" - "$CS" "$pu" "$reason" <<'P'
import json, sys
cs, pu, reason = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(cs))
d["paused_until"] = pu
d["paused_reason"] = reason
json.dump(d, open(cs, "w"), indent=2)
P
echo "[skip] '$PROJ' paused_until=$pu — cycles before $pu will self-skip (run + idempotent guard + watchdog all leave them alone). Resume with: skip.sh $PROJ resume"
exit 0
