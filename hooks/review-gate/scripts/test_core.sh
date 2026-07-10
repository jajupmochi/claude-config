#!/usr/bin/env bash
# Tests for review-gate/core.sh (agent-neutral review computation). Run: bash test_core.sh
# Uses .go sample files: no bundled linter matches them, so lint_fail is deterministically 0
# regardless of whether ruff/shellcheck are installed — the tests exercise the review-round logic itself.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
CORE="$HERE/core.sh"
command -v jq >/dev/null 2>&1 || { echo "SKIP: jq not installed"; exit 0; }
pass=0; fail=0
chk(){ if [ "$2" = "$3" ]; then echo "  ok: $1"; pass=$((pass+1)); else echo "  FAIL: $1 (got '$2' want '$3')"; fail=$((fail+1)); fi; }
run_core(){ RG_STATE_DIR="$1/state" RG_SID="$2" bash "$CORE"; }

# 1. unreviewed code change -> emits the forms report + records a round + sets reviewed
T="$(mktemp -d)"; mkdir -p "$T/state" "$T/work"
printf 'package p\nfunc F() int { return 1 }\n' > "$T/work/a.go"
echo "$T/work/a.go" > "$T/state/s1.changed"
out="$(run_core "$T" s1)"
echo "$out" | grep -q "review-gate: automatic review" && r=yes || r=no
chk "unreviewed change -> emits report" "$r" "yes"
chk "  round recorded = 1" "$(cat "$T/state/s1.rounds" 2>/dev/null)" "1"
[ -f "$T/state/s1.reviewed" ] && r=yes || r=no; chk "  reviewed flag set" "$r" "yes"
echo "$out" | grep -q "Per-function/module AI review" && r=yes || r=no
chk "  module heuristic fired (form 11 present)" "$r" "yes"

# 2. second run on the same state (now reviewed + lint-clean) -> empty stdout (allow stop)
out2="$(run_core "$T" s1)"
[ -z "$out2" ] && r=yes || r=no; chk "reviewed+clean -> allow stop (empty)" "$r" "yes"

# 3. no .changed file at all -> empty
T="$(mktemp -d)"; mkdir -p "$T/state"
out="$(run_core "$T" nope)"
[ -z "$out" ] && r=yes || r=no; chk "no changed-file -> empty" "$r" "yes"

# 4. only a non-code file changed -> empty (filtered out)
T="$(mktemp -d)"; mkdir -p "$T/state" "$T/work"
echo hi > "$T/work/readme.md"; echo "$T/work/readme.md" > "$T/state/s4.changed"
out="$(run_core "$T" s4)"
[ -z "$out" ] && r=yes || r=no; chk "non-code change -> empty" "$r" "yes"

# 5. max rounds reached -> empty (loop guard allows stop)
T="$(mktemp -d)"; mkdir -p "$T/state" "$T/work"
printf 'package p\nfunc G() {}\n' > "$T/work/b.go"; echo "$T/work/b.go" > "$T/state/s5.changed"
echo 3 > "$T/state/s5.rounds"
out="$(run_core "$T" s5)"
[ -z "$out" ] && r=yes || r=no; chk "max rounds -> allow stop (empty)" "$r" "yes"

# 6. RG_STATE_DIR is required (fail-closed on missing env, but fail-open exit)
out="$(RG_SID=x bash "$CORE" 2>/dev/null)"; rc=$?
chk "missing RG_STATE_DIR -> non-zero, empty stdout" "${rc}:${out:-EMPTY}" "1:EMPTY"

echo
if [ "$fail" -eq 0 ]; then echo "core.sh: all $pass checks PASS"; else echo "core.sh: $fail FAIL / $pass pass"; fi
[ "$fail" -eq 0 ]
