#!/usr/bin/env bash
# Tests for install-tui.sh (detection + plan; never installs). Run: bash test_install_tui.sh
# Uses TUI_FAKE_INSTALLED to control detection so the real system is not touched.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
S="$HERE/install-tui.sh"
pass=0; fail=0
ctn(){ if printf '%s' "$2" | grep -qF "$3"; then echo "  ok: $1"; pass=$((pass+1)); else echo "  FAIL: $1 (missing '$3')"; fail=$((fail+1)); fi; }
no(){ if printf '%s' "$2" | grep -qF "$3"; then echo "  FAIL: $1 (unexpected '$3')"; fail=$((fail+1)); else echo "  ok: $1"; pass=$((pass+1)); fi; }

# 1. syntax
bash -n "$S" && { echo "  ok: syntax"; pass=$((pass+1)); } || { echo "  FAIL: syntax"; fail=$((fail+1)); }

# 2. --check with two tools faked installed -> those 'ok', others 'MISSING'
out="$(TUI_FAKE_INSTALLED='zellij delta' bash "$S" --check 2>&1)"
ctn "check: zellij installed"        "$out" "ok       zellij"
ctn "check: delta installed"         "$out" "ok       delta"
ctn "check: claude-squad missing"    "$out" "MISSING  claude-squad"
ctn "check: 2 of 4 missing"          "$out" "2 of 4 recommended tools missing"

# 3. dry-run prints install PLAN commands for missing, and installs nothing (says so)
out="$(TUI_FAKE_INSTALLED='zellij' bash "$S" 2>&1)"
ctn "dryrun: plan for delta"         "$out" "PLAN     delta — would run: cargo install git-delta"
ctn "dryrun: manual tool noted"      "$out" "MANUAL"
ctn "dryrun: nothing installed note" "$out" "nothing installed"

# 4. all faked installed -> 0 missing, no PLAN lines
out="$(TUI_FAKE_INSTALLED='zellij claude-squad lazygit delta' bash "$S" --check 2>&1)"
ctn "all installed -> 0 missing"     "$out" "0 of 4 recommended tools missing"
no  "all installed -> no MISSING"    "$out" "MISSING"

# 5. unknown option -> exit 2
TUI_FAKE_INSTALLED='' bash "$S" --bogus >/dev/null 2>&1; rc=$?
if [ "$rc" -eq 2 ]; then echo "  ok: unknown option -> exit 2"; pass=$((pass+1)); else echo "  FAIL: unknown option rc=$rc"; fail=$((fail+1)); fi

echo
if [ "$fail" -eq 0 ]; then echo "install-tui.sh: all $pass checks PASS"; else echo "install-tui.sh: $fail FAIL / $pass pass"; fi
[ "$fail" -eq 0 ]
