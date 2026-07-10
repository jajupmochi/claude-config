#!/usr/bin/env bash
# Tests for typecheck.sh. Run: bash hooks/typecheck-on-edit/test_typecheck.sh
# Covers the exit-2 wiring deterministically (injected fake tsc) and, if a real tsc can be installed, an
# end-to-end run against real TypeScript.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
HOOK="$HERE/typecheck.sh"
n=0; fail=0
ok() { n=$((n + 1)); echo "  ok: $1"; }
bad() { fail=1; echo "  FAIL: $1"; }

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# 1. non-.ts file → no-op exit 0
echo '{"tool_input":{"file_path":"'"$tmp"'/x.md"}}' | bash "$HOOK" >/dev/null 2>&1
[ $? -eq 0 ] && ok "non-ts file → exit 0" || bad "non-ts should be 0"

# 2. .ts file NOT in a TS project (no tsconfig) → no-op exit 0
mkdir -p "$tmp/plain"; echo 'const a=1' > "$tmp/plain/a.ts"
echo '{"tool_input":{"file_path":"'"$tmp"'/plain/a.ts"}}' | bash "$HOOK" >/dev/null 2>&1
[ $? -eq 0 ] && ok "ts file, no tsconfig → exit 0 (no-op)" || bad "no-tsconfig should be 0"

# set up a minimal TS project (has tsconfig.json)
proj="$tmp/proj"; mkdir -p "$proj"; echo '{"compilerOptions":{"noEmit":true,"strict":true}}' > "$proj/tsconfig.json"
echo 'export const x: number = 1' > "$proj/a.ts"

# fake tsc that FAILS (simulates a type error)
faketsc_fail="$tmp/tsc-fail.sh"; printf '#!/usr/bin/env bash\necho "a.ts(1,1): error TS2322: bad type"; exit 1\n' > "$faketsc_fail"; chmod +x "$faketsc_fail"
# fake tsc that PASSES
faketsc_ok="$tmp/tsc-ok.sh"; printf '#!/usr/bin/env bash\nexit 0\n' > "$faketsc_ok"; chmod +x "$faketsc_ok"

# 3. injected failing tsc → hook EXIT 2, error surfaced on stderr
err="$(echo '{"tool_input":{"file_path":"'"$proj"'/a.ts"}}' | TSC="$faketsc_fail" PRETTIER=/bin/true bash "$HOOK" 2>&1 >/dev/null)"
rc=$?
[ "$rc" -eq 2 ] && ok "type error → EXIT 2 (blocks)" || bad "failing tsc must exit 2, got $rc"
printf '%s' "$err" | grep -q "TS2322" && ok "error text surfaced to stderr" || bad "error not surfaced"

# 4. injected passing tsc → exit 0
echo '{"tool_input":{"file_path":"'"$proj"'/a.ts"}}' | TSC="$faketsc_ok" PRETTIER=/bin/true bash "$HOOK" >/dev/null 2>&1
[ $? -eq 0 ] && ok "clean typecheck → exit 0" || bad "passing tsc should be 0"

# 5. END-TO-END with REAL tsc (best-effort — needs network to install typescript). Non-fatal if unavailable.
if npm install --prefix "$proj" --no-save --silent typescript >/dev/null 2>&1 && [ -x "$proj/node_modules/.bin/tsc" ]; then
  # a genuine type error
  echo 'export const y: number = "not a number"' > "$proj/bad.ts"
  rc2=$(echo '{"tool_input":{"file_path":"'"$proj"'/bad.ts"}}' | PRETTIER=/bin/true bash "$HOOK" >/dev/null 2>&1; echo $?)
  [ "$rc2" -eq 2 ] && ok "REAL tsc: genuine type error → EXIT 2" || bad "real tsc type error should exit 2, got $rc2"
  # fix it → clean
  echo 'export const y: number = 42' > "$proj/bad.ts"
  echo 'export const x: number = 1' > "$proj/a.ts"
  rc3=$(echo '{"tool_input":{"file_path":"'"$proj"'/bad.ts"}}' | PRETTIER=/bin/true bash "$HOOK" >/dev/null 2>&1; echo $?)
  [ "$rc3" -eq 0 ] && ok "REAL tsc: clean file → exit 0" || bad "real tsc clean should exit 0, got $rc3"
else
  echo "  skip: real-tsc end-to-end (could not install typescript offline) — injected-tsc cases already prove exit-2 wiring"
fi

echo ""
[ "$fail" -eq 0 ] && { echo "typecheck.sh: all $n checks PASS"; exit 0; } || { echo "typecheck.sh: FAILURES"; exit 1; }
