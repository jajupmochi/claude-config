#!/usr/bin/env bash
# Tests for session_check.sh decision logic (self-renew + failed-run surfacing). Run: bash test_session_check.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SC="$HERE/session_check.sh"
command -v jq >/dev/null 2>&1 || { echo "SKIP: jq not installed"; exit 0; }
pass=0; fail=0
chk(){ if printf '%s' "$2" | grep -qF "$3"; then echo "  ok: $1"; pass=$((pass+1)); else echo "  FAIL: $1"; fail=$((fail+1)); fi; }
chkno(){ if printf '%s' "$2" | grep -qF "$3"; then echo "  FAIL: $1 (unexpected)"; fail=$((fail+1)); else echo "  ok: $1"; pass=$((pass+1)); fi; }

T="$(mktemp -d)"; A="$T/.claude/autopilot/proj1"; mkdir -p "$A/runs"
old="$(python3 -c 'import datetime;print(datetime.date.today()-datetime.timedelta(days=7))')"
fresh="$(python3 -c 'import datetime;print(datetime.date.today()-datetime.timedelta(days=2))')"
printf 'role_scope: t\n' > "$A/config.yaml"
run_sc(){ printf '{"session_id":"%s"}' "$1" | HOME="$T" bash "$SC" 2>/dev/null; }

# 1. stale cron (armed 7d ago) + matching home session -> ACTION says renew
printf '{"home_session_id":"sid-1","last_armed":"%s","cron_id":"c1","schedule":"0 22 * * *"}' "$old" > "$A/cron_state.json"
out="$(run_sc sid-1)"
chk "stale cron -> ACTION emitted"      "$out" "ACTION (autopilot 'proj1')"
chk "stale cron -> renew=renew"          "$out" "renew=renew"

# 2. fresh cron (armed 2d ago) -> renew=ok (no forced renew)
printf '{"home_session_id":"sid-1","last_armed":"%s","cron_id":"c1","schedule":"0 22 * * *"}' "$fresh" > "$A/cron_state.json"
out="$(run_sc sid-1)"
chk "fresh cron -> renew=ok"             "$out" "renew=ok"

# 3. different session id -> not this session's home -> no ACTION for proj1
out="$(run_sc some-other-sid)"
chkno "non-home session -> no re-arm ACTION" "$out" "ACTION (autopilot 'proj1')"

# 4. failed run (last-error newer than last-done) -> NOTE surfaced
printf '%s' "$fresh" > "$A/cron_state.json"   # any state
printf '{"home_session_id":"sid-1","last_armed":"%s"}' "$fresh" > "$A/cron_state.json"
: > "$A/last-done"; sleep 1; : > "$A/last-error"
out="$(run_sc sid-1)"
chk "failed run -> NOTE surfaced"        "$out" "did NOT finish"
rm -f "$A/last-error"

# 5. autopilot updated (configured_with_version != installed VERSION) -> ACTION says verstale=yes
mkdir -p "$T/.claude/skills/autopilot"; printf 'v-new\n' > "$T/.claude/skills/autopilot/VERSION"
printf '{"home_session_id":"sid-1","last_armed":"%s","cron_id":"c1","schedule":"0 22 * * *","configured_with_version":"v-old"}' "$fresh" > "$A/cron_state.json"
out="$(run_sc sid-1)"
chk "version mismatch -> verstale=yes"   "$out" "verstale=yes"

# 6. matching version -> verstale=no
printf '{"home_session_id":"sid-1","last_armed":"%s","cron_id":"c1","schedule":"0 22 * * *","configured_with_version":"v-new"}' "$fresh" > "$A/cron_state.json"
out="$(run_sc sid-1)"
chk "version match -> verstale=no"       "$out" "verstale=no"

# 7. a background recovery left pending-summary.md -> session_check surfaces it
: > "$A/pending-summary.md"
out="$(run_sc sid-1)"
chk "pending-summary -> surfaced NOTE"   "$out" "pending-summary.md"
rm -f "$A/pending-summary.md"

rm -rf "$T"
if [ "$fail" -eq 0 ]; then echo "session_check.sh: all $pass checks PASS"; else echo "session_check.sh: $fail FAIL / $pass pass"; fi
[ "$fail" -eq 0 ]
