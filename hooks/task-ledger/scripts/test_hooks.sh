#!/usr/bin/env bash
# Tests for the task-ledger hook shims. Run: bash test_hooks.sh
#
# ledger.py has its own test suite; this one covers the shell layer that actually does the enforcing —
# the Stop gate's decision JSON and the UserPromptSubmit capture. An untested shim is where hard
# enforcement silently stops enforcing, so every case here drives the real script with a real payload.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="$HERE/gate.sh"
CAPTURE="$HERE/capture.sh"
LEDGER="$HERE/ledger.py"

command -v jq >/dev/null 2>&1 || { echo "SKIP: jq not installed"; exit 0; }

n=0
ok() { n=$((n + 1)); echo "  ok: $1"; }
fail() { echo "  FAIL: $1"; echo "       $2"; exit 1; }

ROOT="$(mktemp -d)"
export TL_STATE_DIR="$ROOT/state"
mkdir -p "$ROOT/proj/.agent/ledger"
PROJ="$ROOT/proj"
trap 'rm -rf "$ROOT"' EXIT

payload() { jq -nc --arg cwd "$PROJ" --arg sid "$1" --arg p "${2:-}" \
  '{cwd:$cwd, session_id:$sid, prompt:$p}'; }

led() { (cd "$PROJ" && python3 "$LEDGER" "$@"); }

# 1. No active round: the gate must stay out of the way entirely.
out="$(payload s1 | bash "$GATE")"; rc=$?
[ "$rc" -eq 0 ] && [ -z "$out" ] || fail "no round should allow silently" "rc=$rc out=$out"
ok "gate: no active round -> empty output, exit 0"

# 2. An open task must produce a real block decision naming the task.
led open --title "Hook test" --task "Wire the gate|it blocks" >/dev/null
out="$(payload s1 | bash "$GATE")"
[ "$(printf '%s' "$out" | jq -r '.decision')" = "block" ] || fail "open task must block" "$out"
printf '%s' "$out" | jq -r '.reason' | grep -q "T1" || fail "block reason must name T1" "$out"
printf '%s' "$out" | jq -r '.reason' | grep -q "ROUND NOT COMPLETE" || fail "missing headline" "$out"
ok "gate: an open task returns {decision:block} naming the task"

# 3. A settled round is allowed through.
led done T1 --evidence "bash test_hooks.sh passes" >/dev/null
out="$(payload s1 | bash "$GATE")"; rc=$?
[ "$rc" -eq 0 ] && [ -z "$out" ] || fail "settled round should pass" "rc=$rc out=$out"
ok "gate: every task settled -> allowed"

# 4. An untriaged mid-round requirement blocks on its own.
led inbox --text "also handle the empty state" >/dev/null
out="$(payload s1 | bash "$GATE")"
[ "$(printf '%s' "$out" | jq -r '.decision')" = "block" ] || fail "untriaged inbox must block" "$out"
printf '%s' "$out" | jq -r '.reason' | grep -q "untriaged inbox" || fail "reason must say why" "$out"
ok "gate: an untriaged inbox item blocks on its own"
led triage I1 --drop "covered by T1" >/dev/null

# 5. A corrupt ledger fails CLOSED. This is the case where failing open would hide unfinished work.
doc="$PROJ/.agent/ledger/$(cat "$PROJ/.agent/ledger/ACTIVE")"
cp "$doc" "$ROOT/doc.bak"
printf '# Round: tampered\n\nmarker removed\n' > "$doc"
out="$(payload s1 | bash "$GATE")"
[ "$(printf '%s' "$out" | jq -r '.decision')" = "block" ] || fail "corrupt ledger must fail closed" "$out"
printf '%s' "$out" | jq -r '.reason' | grep -qi "could not be read" || fail "must explain" "$out"
cp "$ROOT/doc.bak" "$doc"
ok "gate: an unreadable ledger fails CLOSED, not open"

# 6. enabled=0 turns the gate off without uninstalling it.
led add --title "Reopen it" --acceptance "x" >/dev/null
printf 'enabled=0\n' > "$PROJ/.agent/ledger/task-ledger.conf"
out="$(payload s1 | bash "$GATE")"; rc=$?
[ "$rc" -eq 0 ] && [ -z "$out" ] || fail "enabled=0 should disable" "rc=$rc out=$out"
rm -f "$PROJ/.agent/ledger/task-ledger.conf"
ok "gate: enabled=0 disables enforcement"

# 7. Loop guard: repeated blocks degrade to a warning rather than wedging the session forever.
printf 'max_rounds=2\n' > "$PROJ/.agent/ledger/task-ledger.conf"
for i in 1 2; do payload s9 | bash "$GATE" >/dev/null; done
out="$(payload s9 | bash "$GATE")"; rc=$?
[ "$rc" -eq 0 ] || fail "loop guard should exit 0" "rc=$rc"
[ "$(printf '%s' "$out" | jq -r '.hookSpecificOutput.hookEventName')" = "Stop" ] \
  || fail "loop guard should emit additionalContext" "$out"
printf '%s' "$out" | jq -r '.hookSpecificOutput.additionalContext' | grep -q "NOT complete" \
  || fail "loop guard must still say the round is unfinished" "$out"
rm -f "$PROJ/.agent/ledger/task-ledger.conf"
ok "gate: loop guard degrades to a warning that still reports the round unfinished"

# 8. Capture writes a mid-round prompt into the inbox and never blocks.
before="$(led status --json | jq '.inbox | length')"
out="$(payload s1 "please also add a dark mode toggle" | bash "$CAPTURE")"; rc=$?
[ "$rc" -eq 0 ] && [ -z "$out" ] || fail "capture must never block" "rc=$rc out=$out"
after="$(led status --json | jq '.inbox | length')"
[ "$after" -eq $((before + 1)) ] || fail "prompt not captured" "before=$before after=$after"
led status --json | jq -r '.inbox[-1].text' | grep -q "dark mode toggle" || fail "wrong text captured" ""
ok "capture: a mid-round prompt lands in the inbox, hook stays silent"

# 9. A bare slash command is a UI action, not a requirement.
before="$(led status --json | jq '.inbox | length')"
payload s1 "/compact" | bash "$CAPTURE" >/dev/null
[ "$(led status --json | jq '.inbox | length')" -eq "$before" ] || fail "/compact should be ignored" ""
ok "capture: a bare slash command is ignored"

# 10. A slash command WITH an argument is a real requirement and must be captured.
payload s1 "/loop keep fixing the flaky test" | bash "$CAPTURE" >/dev/null
[ "$(led status --json | jq '.inbox | length')" -eq $((before + 1)) ] || fail "slash+args should capture" ""
ok "capture: a slash command with arguments is captured"

# 11. With no round open, capture is a silent no-op rather than an error.
led close --force >/dev/null
out="$(payload s1 "stray prompt" | bash "$CAPTURE")"; rc=$?
[ "$rc" -eq 0 ] && [ -z "$out" ] || fail "capture with no round must no-op" "rc=$rc out=$out"
ok "capture: no active round -> silent no-op"

echo ""
echo "task-ledger hooks: all $n tests PASS"
