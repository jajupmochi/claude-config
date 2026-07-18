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
chk "  module heuristic fired (form 12 present)" "$r" "yes"
echo "$out" | grep -q "Bug fix → regression test" && r=yes || r=no
chk "  regression-test-on-bugfix (form 11 present)" "$r" "yes"

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

# 7. REGRESSION: RG_BRIEF_FILE keeps the brief OUT of the reason.
#    Before the fix the whole ~3KB brief was the Stop reason, and Claude Code renders that verbatim into
#    the user's terminal, so every code-changing turn dumped the internal review forms into their
#    transcript. The brief must now go to a file and stdout must carry only a short pointer.
T="$(mktemp -d)"; mkdir -p "$T/state" "$T/work"
printf 'package p\nfunc H() {}\n' > "$T/work/c.go"; echo "$T/work/c.go" > "$T/state/s7.changed"
brief="$T/state/s7.brief.md"
out="$(RG_STATE_DIR="$T/state" RG_SID=s7 RG_BRIEF_FILE="$brief" bash "$CORE")"
[ -n "$out" ] && r=yes || r=no; chk "brief mode: still blocks (non-empty stdout)" "$r" "yes"
[ "$(printf '%s' "$out" | wc -c)" -lt 600 ] && r=yes || r=no
chk "brief mode: reason is short (<600 bytes)" "$r" "yes"
printf '%s' "$out" | grep -q "Review forms and tools" && r=no || r=yes
chk "brief mode: the forms list is NOT in the reason" "$r" "yes"
printf '%s' "$out" | grep -q "Present your review IN CHINESE" && r=no || r=yes
chk "brief mode: the presentation boilerplate is NOT in the reason" "$r" "yes"
printf '%s' "$out" | grep -qF "$brief" && r=yes || r=no
chk "brief mode: reason names the brief file" "$r" "yes"
[ -s "$brief" ] && r=yes || r=no; chk "brief mode: brief file written and non-empty" "$r" "yes"
grep -q "Review forms and tools" "$brief" && r=yes || r=no
chk "brief mode: the full forms survive in the file" "$r" "yes"
grep -q "Per-function/module AI review" "$brief" && r=yes || r=no
chk "brief mode: form 12 survives in the file" "$r" "yes"

# 8. Backward compatibility: with RG_BRIEF_FILE unset the output must be unchanged, because core.sh is
#    shared with the Codex and opencode shims which have not opted in.
T="$(mktemp -d)"; mkdir -p "$T/state" "$T/work"
printf 'package p\nfunc I() {}\n' > "$T/work/d.go"; echo "$T/work/d.go" > "$T/state/s8.changed"
out="$(run_core "$T" s8)"
printf '%s' "$out" | grep -q "Review forms and tools" && r=yes || r=no
chk "no RG_BRIEF_FILE -> full inline brief (unchanged behaviour)" "$r" "yes"

# 9. Fail-safe: an unwritable brief path must fall back to the FULL inline brief, never to silence.
#    Degrading toward more enforcement is correct; losing the review would not be.
T="$(mktemp -d)"; mkdir -p "$T/state" "$T/work"
printf 'package p\nfunc J() {}\n' > "$T/work/e.go"; echo "$T/work/e.go" > "$T/state/s9.changed"
out="$(RG_STATE_DIR="$T/state" RG_SID=s9 RG_BRIEF_FILE=/proc/nope/nope/brief.md bash "$CORE" 2>/dev/null)"
printf '%s' "$out" | grep -q "Review forms and tools" && r=yes || r=no
chk "unwritable brief path -> falls back to full inline brief" "$r" "yes"

# 10. REGRESSION: a path containing a space must stay splittable in the changed-files list.
#     It used to be space-joined (`tr '\n' ' '`), so the reader could not tell where one path ended and
#     the next began. This harness's own checkout lives under "New Volume1", so the bug was live here.
T="$(mktemp -d)"; mkdir -p "$T/state" "$T/work dir"
printf 'package p\nfunc L() {}\n' > "$T/work dir/f.go"
printf 'package p\nfunc M() {}\n' > "$T/work/plain.go" 2>/dev/null || mkdir -p "$T/work" && printf 'package p\nfunc M() {}\n' > "$T/work/plain.go"
printf '%s\n' "$T/work dir/f.go" "$T/work/plain.go" > "$T/state/s10.changed"
out="$(run_core "$T" s10)"
# `--` is required: the pattern starts with "- ", and grep (ugrep here) otherwise parses it as an option.
printf '%s' "$out" | grep -qF -- "- $T/work dir/f.go" && r=yes || r=no
chk "space-containing path is listed on its own line" "$r" "yes"
n="$(printf '%s' "$out" | sed -n '/^\*\*Changed files:\*\*/,/^\*\*Review forms/p' | grep -c '^- ')"
chk "  exactly 2 changed-file entries, not 3 from a split path" "$n" "2"

echo
if [ "$fail" -eq 0 ]; then echo "core.sh: all $pass checks PASS"; else echo "core.sh: $fail FAIL / $pass pass"; fi
[ "$fail" -eq 0 ]
