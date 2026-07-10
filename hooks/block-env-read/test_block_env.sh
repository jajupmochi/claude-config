#!/usr/bin/env bash
# Tests for block-env.sh. Run: bash hooks/block-env-read/test_block_env.sh
set -u
HOOK="$(cd "$(dirname "$0")" && pwd)/block-env.sh"
n=0; fail=0; ok(){ n=$((n+1)); echo "  ok: $1"; }; bad(){ fail=1; echo "  FAIL: $1"; }

check() { # <path> <expected-rc>
  echo '{"tool_input":{"file_path":"'"$1"'"}}' | bash "$HOOK" >/dev/null 2>&1
  local rc=$?
  [ "$rc" -eq "$2" ] && ok "$1 → exit $2" || bad "$1 expected $2 got $rc"
}
check "/proj/.env" 2
check "/proj/.env.local" 2
check "/proj/.env.production" 2
check "/proj/config.env" 2
check "/proj/src/index.ts" 0
check "/proj/README.md" 0
check "/proj/environment.md" 0        # not a dotenv → allowed
# secret-free templates are readable (agents need them to learn required vars)
check "/proj/.env.example" 0
check "/proj/.env.sample" 0
check "/proj/.env.template" 0
check "/proj/.env.dist" 0
check "/proj/.env.local.example" 0    # .env.*.example

echo ""
[ "$fail" -eq 0 ] && { echo "block-env.sh: all $n checks PASS"; exit 0; } || { echo "FAILURES"; exit 1; }
