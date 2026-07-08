#!/usr/bin/env bash
# autopilot/session_check.sh — SessionStart hook (self-heal).  [2026-06-27]
#
# Wired via ~/.claude/settings.json (hooks.SessionStart). On every session start (cold start, /resume,
# or a resurrected tmux session) it prints a short ACTION block to stdout, which Claude Code injects
# into the session. Claude then acts on it: for each autopilot project whose "home session" is THIS
# session, make sure the daily in-session cron is armed and not about to hit the 7-day CronCreate cap.
#
# This is layer 2 of the dual-timer design (see docs/autopilot/README.md):
#   - In-session CronCreate cron = the daily run, lives in the user's always-open session.
#   - CronCreate auto-expires after ~7 days -> we re-arm before day 6 (cron_state.json `last_armed`).
#   - A new process (restart / resurrect) has no in-session cron -> this hook tells Claude to re-arm it.
# Must NEVER fail the session start: best-effort, always exit 0.

# Skip inside an autopilot headless run (run.sh exports this) so it doesn't clobber cron_state.
[ -n "${AUTOPILOT_HEADLESS:-}" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0

BASE="$HOME/.claude/autopilot"
[ -d "$BASE" ] || exit 0
TODAY="$(date +%F 2>/dev/null)" || exit 0

# Read this session's id from the hook stdin JSON (best-effort).
SID=""
if [ ! -t 0 ]; then
  IN="$(cat 2>/dev/null)"
  command -v jq >/dev/null 2>&1 && SID="$(printf '%s' "$IN" | jq -r '.session_id // empty' 2>/dev/null)"
fi

emitted=0
for cfg in "$BASE"/*/config.yaml; do
  [ -f "$cfg" ] || continue
  proj="$(basename "$(dirname "$cfg")")"
  state="$BASE/$proj/cron_state.json"
  # Read home_session_id + last_armed + cron_id + schedule from cron_state.json (if present).
  vals="$(python3 - "$state" <<'PY' 2>/dev/null
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    d = {}
print(d.get("home_session_id","") , "||", d.get("last_armed","") , "||", d.get("cron_id","") , "||", d.get("schedule","0 22 * * *") , "||", d.get("configured_with_version","") , "||", d.get("paused_until",""))
PY
)"
  home="$(printf '%s' "$vals" | awk -F' \\|\\| ' '{print $1}')"
  last_armed="$(printf '%s' "$vals" | awk -F' \\|\\| ' '{print $2}')"
  cron_id="$(printf '%s' "$vals" | awk -F' \\|\\| ' '{print $3}')"
  sched="$(printf '%s' "$vals" | awk -F' \\|\\| ' '{print $4}')"
  cfgver="$(printf '%s' "$vals" | awk -F' \\|\\| ' '{print $5}')"
  pausedu="$(printf '%s' "$vals" | awk -F' \\|\\| ' '{print $6}')"

  # Only act for the project whose home session is THIS session (if we know both ids). If home is
  # unknown (e.g. first setup not done yet) we still surface it so /autopilot setup can record it.
  if [ -n "$home" ] && [ -n "$SID" ] && [ "$home" != "$SID" ]; then
    continue
  fi

  # autopilot updated since this cron was armed? (configured_with_version != installed VERSION) -> re-arm
  curver="$(cat "$HOME/.claude/skills/autopilot/VERSION" 2>/dev/null | head -1 | tr -d ' ')"
  verstale="no"; [ -n "$curver" ] && [ "$cfgver" != "$curver" ] && verstale="yes"

  # days since last_armed (>=6 => renew to dodge the 7-day cap)
  renew="unknown"
  if [ -n "$last_armed" ]; then
    renew="$(python3 - "$last_armed" "$TODAY" <<'PY' 2>/dev/null
import datetime, sys
try:
    a=datetime.date.fromisoformat(sys.argv[1][:10]); t=datetime.date.fromisoformat(sys.argv[2])
    print("renew" if (t-a).days >= 6 else "ok")
except Exception:
    print("unknown")
PY
)"
  fi

  # PAUSED (skip.sh set a still-future paused_until): don't nag to re-arm — a fired run self-skips via
  # cycle_status and it auto-resumes on/after that date. Surface it and move on.
  if [ -n "$pausedu" ]; then
    earlier="$(printf '%s\n%s\n' "$TODAY" "$pausedu" | sort | head -1)"
    if [ "$earlier" = "$TODAY" ] && [ "$TODAY" != "$pausedu" ]; then
      echo "NOTE (autopilot '${proj}'): PAUSED until ${pausedu} (via skip.sh) — leaving the cron as-is; runs auto-resume on/after ${pausedu}. Resume now with: skip.sh ${proj} resume."
      continue
    fi
  fi

  if [ "$emitted" -eq 0 ]; then
    echo "[AUTOPILOT SELF-HEAL | ${TODAY}] (re-arm the in-session daily cron so it survives restarts + the 7-day cap)"
    emitted=1
  fi
  echo "ACTION (autopilot '${proj}'): run CronList. If NO cron with schedule '${sched}' for this project is listed (new/restarted session), OR renew=${renew}, OR verstale=${verstale} (autopilot updated: cron_state configured_with_version='${cfgver}' != installed VERSION='${curver}'), then: CronDelete the old cron '${cron_id}' if it still exists, CronCreate a recurring durable cron (schedule '${sched}', prompt: \"autopilot daily run for [${proj}]: read ~/.claude/skills/autopilot/PROMPT.md and execute the directive for ${proj} now\"), and write ${state} with home_session_id=${SID:-<this session>}, cron_id=<new id>, last_armed=${TODAY}, schedule=${sched}, configured_with_version='${curver}'. If the cron is alive AND renew=ok AND verstale=no, do nothing."
done

# Surface the most recent finished/failed run that the user has not seen yet, per project.
for d in "$BASE"/*/; do
  proj="$(basename "$d")"; [ "$proj" = "bin" ] && continue
  err="$d/last-error"; done="$d/last-done"
  if [ -f "$err" ] && { [ ! -f "$done" ] || [ "$err" -nt "$done" ]; }; then
    echo "NOTE (autopilot '${proj}'): the last run did NOT finish (last-error newer than last-done). Read $d/runs/ newest log and tell the user plainly what blocked it, with clickable links."
  fi
  # A background recovery run left a summary the user hasn't seen — surface it into THIS session.
  pend="${d%/}/pending-summary.md"    # strip any trailing slash from the glob dir, then join explicitly
  if [ -f "$pend" ]; then
    echo "NOTE (autopilot '${proj}'): a background recovery run left ${pend}. Post its contents to the user (labelled '🛟 后台恢复补跑的总结'), SendUserFile any screenshot paths it lists, then delete the file."
  fi
done
exit 0
