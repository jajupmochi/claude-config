#!/usr/bin/env bash
# Tests for statsbar.sh. Run: bash test_statsbar.sh
#
# The tool exists to make counts legible at a glance, so the tests that matter most are the ones about
# legibility: bars must start at the same column even with CJK labels, and a non-zero count must never
# render as an empty bar.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SB="$HERE/statsbar.sh"
pass=0; fail=0
chk(){ if [ "$2" = "$3" ]; then echo "  ok: $1"; pass=$((pass+1)); else echo "  FAIL: $1 (got '$2' want '$3')"; fail=$((fail+1)); fi; }

# 1. md format is fenced and carries no ANSI; ansi format is the reverse.
out="$(bash "$SB" --format md --title T --stat "OK:2:green")"
printf '%s' "$out" | grep -q '^```$' && r=yes || r=no; chk "md: fenced" "$r" "yes"
printf '%s' "$out" | grep -q $'\033' && r=yes || r=no; chk "md: no ANSI escapes" "$r" "no"
out="$(bash "$SB" --format ansi --title T --stat "OK:2:green")"
printf '%s' "$out" | grep -q $'\033\[32m' && r=yes || r=no; chk "ansi: colour emitted" "$r" "yes"
printf '%s' "$out" | grep -q '^```$' && r=yes || r=no; chk "ansi: not fenced" "$r" "no"

# 2. CJK alignment — the reason dispw() exists. Labels of different character counts but rendered widths
#    must still put every bar at the same column. ${#s} would get this wrong.
out="$(bash "$SB" --format md --stat "无问题:1:green" --stat "已修:1:yellow" --stat "OK:1:blue")"
cols="$(printf '%s' "$out" | grep -n '█' | sed 's/.*//' )"
a="$(printf '%s' "$out" | grep '无问题' | sed 's/█.*//' | LC_ALL=C wc -c)"
b="$(printf '%s' "$out" | grep '已修'   | sed 's/█.*//' | LC_ALL=C wc -c)"
# byte prefixes differ (CJK is 3 bytes/char), so compare RENDERED width instead
wa="$(printf '%s' "$out" | grep '无问题' | sed 's/█.*//')"; wa=$(( ( ${#wa} + $(printf '%s' "$wa" | LC_ALL=C wc -c) ) / 2 ))
wb="$(printf '%s' "$out" | grep '已修'   | sed 's/█.*//')"; wb=$(( ( ${#wb} + $(printf '%s' "$wb" | LC_ALL=C wc -c) ) / 2 ))
chk "CJK labels of different length align to the same bar column" "$wa" "$wb"

# 3. A non-zero count must never render an empty bar — that would read as "none of these".
out="$(bash "$SB" --format md --total 1000 --stat "rare:1:red" --stat "common:999:green")"
printf '%s' "$out" | grep 'rare' | grep -q '█' && r=yes || r=no
chk "count=1 of 1000 still shows at least one filled cell" "$r" "yes"

# 4. --total defaults to the sum of the stats.
out="$(bash "$SB" --format md --unit files --title T --stat "a:3:green" --stat "b:1:red")"
printf '%s' "$out" | grep -q '4 files' && r=yes || r=no; chk "total defaults to the sum" "$r" "yes"

# 5. An explicit --total drives the percentages, so a partial breakdown reads correctly.
out="$(bash "$SB" --format md --total 10 --stat "done:5:green")"
printf '%s' "$out" | grep -q '5/10   50%' && r=yes || r=no; chk "explicit --total drives the percentage" "$r" "yes"

# 6. NO_COLOR strips the escapes but keeps the layout (https://no-color.org).
out="$(NO_COLOR=1 bash "$SB" --format ansi --stat "OK:1:green")"
printf '%s' "$out" | grep -q $'\033' && r=yes || r=no; chk "NO_COLOR: no escapes" "$r" "no"
printf '%s' "$out" | grep -q '█' && r=yes || r=no; chk "NO_COLOR: bar still drawn" "$r" "yes"

# 7. Bad input is refused with a reason rather than rendering something misleading.
bash "$SB" --format md --stat "OK:notanumber:green" >/dev/null 2>&1; chk "non-numeric count -> exit 1" "$?" "1"
bash "$SB" --format md --total x --stat "OK:1" >/dev/null 2>&1;      chk "non-numeric total -> exit 1" "$?" "1"
bash "$SB" --format sideways --stat "OK:1" >/dev/null 2>&1;          chk "unknown format -> exit 1" "$?" "1"
bash "$SB" --format md >/dev/null 2>&1;                              chk "no --stat -> exit 1" "$?" "1"
bash "$SB" --bogus x --stat "OK:1" >/dev/null 2>&1;                  chk "unknown flag -> exit 1" "$?" "1"

# 8. A zero total must not divide by zero.
out="$(bash "$SB" --format md --total 0 --stat "none:0:grey" 2>&1)"; rc=$?
chk "total=0 -> exit 0, no division error" "$rc" "0"
printf '%s' "$out" | grep -q '0/0     0%' && r=yes || r=no; chk "total=0 renders 0%" "$r" "yes"

# 9. Piped output (not a TTY) defaults to md, so a review never gets raw escapes pasted into it.
out="$(bash "$SB" --title T --stat "OK:1:green" | cat)"
printf '%s' "$out" | grep -q '^```$' && r=yes || r=no; chk "auto format off a TTY -> md" "$r" "yes"

# 10. An omitted colour falls back to grey rather than erroring.
out="$(bash "$SB" --format ansi --stat "plain:1")"; rc=$?
chk "omitted colour -> exit 0" "$rc" "0"
printf '%s' "$out" | grep -q $'\033\[90m' && r=yes || r=no; chk "omitted colour -> grey" "$r" "yes"

echo
if [ "$fail" -eq 0 ]; then echo "statsbar.sh: all $pass checks PASS"; else echo "statsbar.sh: $fail FAIL / $pass pass"; fi
[ "$fail" -eq 0 ]
