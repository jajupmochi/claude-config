#!/usr/bin/env bash
# Tests for is_transient.sh. Run: bash test_is_transient.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; IT="$HERE/is_transient.sh"
pass=0; fail=0
chk(){ if [ "$2" = "$3" ]; then echo "  ok: $1"; pass=$((pass+1)); else echo "  FAIL: $1 (got $2 want $3)"; fail=$((fail+1)); fi; }
T="$(mktemp -d)"

# the exact error the user hit -> transient (exit 0)
printf 'working...\nAPI Error: Server is temporarily limiting requests (not your usage limit) · Rate limited\n' > "$T/a.log"
bash "$IT" "$T/a.log"; chk "real rate-limit -> transient" "$?" "0"

printf 'Error: overloaded_error 529\n' > "$T/b.log"; bash "$IT" "$T/b.log"; chk "overloaded 529 -> transient" "$?" "0"

# a normal failure -> NOT transient (exit 1)
printf 'run.sh: line 40: claude: command not found\n' > "$T/c.log"; bash "$IT" "$T/c.log"; chk "command-not-found -> NOT transient" "$?" "1"

# a clean run -> NOT transient
printf 'committed dbfee54 to dev\nBUILD SUCCESS\n' > "$T/d.log"; bash "$IT" "$T/d.log"; chk "clean run -> NOT transient" "$?" "1"

# missing file -> NOT transient (exit 1, no crash)
bash "$IT" "$T/nope.log"; chk "missing log -> NOT transient" "$?" "1"

rm -rf "$T"
if [ "$fail" -eq 0 ]; then echo "is_transient.sh: all $pass tests PASS"; else echo "is_transient.sh: $fail FAIL"; fi
[ "$fail" -eq 0 ]
