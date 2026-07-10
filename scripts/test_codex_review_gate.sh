#!/usr/bin/env bash
# Tests for scripts/codex_review_gate.sh — Codex Stop-hook that now delivers the shared 12-form review
# (via core.sh) plus Codex's git guards. Run: bash test_codex_review_gate.sh
# Uses an isolated temp git repo + a SEPARATE temp HOME (so the gate's state dir is not seen as untracked).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
GATE="$REPO/scripts/codex_review_gate.sh"
CORE="$REPO/hooks/review-gate/scripts/core.sh"
command -v jq >/dev/null 2>&1 || { echo "SKIP: jq not installed"; exit 0; }
command -v git >/dev/null 2>&1 || { echo "SKIP: git not installed"; exit 0; }
pass=0; fail=0
chk(){ if [ "$2" = "$3" ]; then echo "  ok: $1"; pass=$((pass+1)); else echo "  FAIL: $1 (got '$2' want '$3')"; fail=$((fail+1)); fi; }
ctn(){ if printf '%s' "$2" | grep -qF "$3"; then echo "  ok: $1"; pass=$((pass+1)); else echo "  FAIL: $1 (missing '$3')"; fail=$((fail+1)); fi; }

setup(){ T="$(mktemp -d)"; RD="$T/repo"; HD="$T/home"; mkdir -p "$RD" "$HD"
  ( cd "$RD" && git init -q && git config user.email t@t && git config user.name t && git checkout -q -b work ); }
run(){ ( cd "$RD" && printf '{"session_id":"%s"}' "$1" | RG_CORE="$CORE" HOME="$HD" bash "$GATE" 2>/dev/null ); }

# 1. staged code change -> forms review DELIVERED + git-guards + decision block
setup
printf 'package p\nfunc F() int { return 1 }\n' > "$RD/a.go"; ( cd "$RD" && git add a.go )
out="$(run s1)"
chk "staged code -> decision block" "$(printf '%s' "$out" | jq -r '.decision')" "block"
sm="$(printf '%s' "$out" | jq -r '.systemMessage')"
ctn "  forms review present (from core.sh)" "$sm" "review-gate: automatic review"
ctn "  git-guards section present" "$sm" "Codex git-guards"
ctn "  changed file listed" "$sm" "a.go"

# 2. clean tree + conventional commit + non-protected branch -> no block, no forms
setup
printf 'x\n' > "$RD/f.txt"; ( cd "$RD" && git add f.txt && git commit -q -m "feat: initial" )
out="$(run s2)"
chk "clean+conventional -> no block" "$(printf '%s' "$out" | jq -r '.decision')" ""
sm="$(printf '%s' "$out" | jq -r '.systemMessage')"
ctn "  working tree clean noted" "$sm" "Working tree clean"
if printf '%s' "$sm" | grep -qF "review-gate: automatic review"; then echo "  FAIL: forms shown on clean tree"; fail=$((fail+1)); else echo "  ok: no forms on clean tree"; pass=$((pass+1)); fi

# 3. non-conventional last commit -> block
setup
printf 'x\n' > "$RD/f.txt"; ( cd "$RD" && git add f.txt && git commit -q -m "random message" )
out="$(run s3)"
chk "non-conventional commit -> block" "$(printf '%s' "$out" | jq -r '.decision')" "block"

# 4. max-rounds: forms suppressed after 3 rounds, but git-guards still block on staged change
setup
printf 'package p\nfunc H() {}\n' > "$RD/b.go"; ( cd "$RD" && git add b.go )
# first run creates state + does round 1; then force rounds to the cap so the next run suppresses forms
run s4 >/dev/null; echo 3 > "$HD/.codex/review-state/s4.rounds"
out="$(run s4)"
sm="$(printf '%s' "$out" | jq -r '.systemMessage')"
if printf '%s' "$sm" | grep -qF "review-gate: automatic review"; then echo "  FAIL: forms shown after max rounds"; fail=$((fail+1)); else echo "  ok: forms suppressed after max rounds"; pass=$((pass+1)); fi
chk "  but staged change still blocks" "$(printf '%s' "$out" | jq -r '.decision')" "block"

echo
if [ "$fail" -eq 0 ]; then echo "codex_review_gate.sh: all $pass checks PASS"; else echo "codex_review_gate.sh: $fail FAIL / $pass pass"; fi
[ "$fail" -eq 0 ]
