#!/usr/bin/env bash
# Tests for ssh-guard.sh. Each case feeds a PreToolUse-shaped JSON on stdin and asserts the exit code
# (0 = allow, 2 = block). Uses a throwaway state dir so it never touches real host history.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
HOOK="$HERE/ssh-guard.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export SSH_GUARD_STATE="$TMP/state"
export SSH_GUARD_WINDOW=1800

pass=0; fail=0
run() { # cmd -> prints exit code
  printf '{"tool_input":{"command":%s}}' "$(printf '%s' "$1" | jq -Rs .)" | bash "$HOOK"; echo "$?"; }
check() { # label expected actual
  if [ "$2" = "$3" ]; then pass=$((pass+1)); echo "ok   - $1 (exit $3)";
  else fail=$((fail+1)); echo "FAIL - $1: expected $2 got $3"; fi; }

reset() { rm -rf "$SSH_GUARD_STATE"; }

# 1. non-ssh command -> allow
check "non-ssh command allowed" 0 "$(run 'ls -la /tmp && echo done')"

# 2. first ssh to a host -> allow (records the user)
reset
check "first ssh user allowed" 0 "$(run 'ssh -p 2222 deploy-user@203.0.113.20 whoami')"

# 3. same user again -> allow (retry, not probing)
check "same-user retry allowed" 0 "$(run 'ssh deploy-user@203.0.113.20 hostname')"

# 4. DIFFERENT user, same host, within window -> BLOCK
check "2nd distinct username blocked" 2 "$(run 'ssh root@203.0.113.20 id')"

# 5. yet another different user -> still BLOCK
check "3rd distinct username blocked" 2 "$(run 'ssh admin@203.0.113.20 id')"

# 6. override file -> allow once, then block again
touch "$SSH_GUARD_STATE/allow-ssh-user-once"
check "override allows once" 0 "$(run 'ssh deploy@203.0.113.20 id')"
check "override consumed, blocks again" 2 "$(run 'ssh oracle@203.0.113.20 id')"

# 7. different host -> allow (fresh history)
check "different host allowed" 0 "$(run 'ssh someone@other.example.com uptime')"

# 8. git author email inside a commit (with ssh push elsewhere) is not treated as an ssh user
reset
check "email in git author not probing" 0 "$(run 'git commit -m x --author "A B <a@b.com>" && ssh git@github.com info')"
# a 2nd DISTINCT real ssh user to github after the above should block (proves github@ was recorded, a@b.com ignored)
check "email ignored, real ssh user tracked" 2 "$(run 'ssh other@github.com info')"

# 9. bare ssh host (no user@) -> allow (nothing to judge)
reset
check "bare ssh host allowed" 0 "$(run 'ssh myserver uptime')"

# 10. malformed / empty input -> allow (fail-open)
check "empty stdin allowed" 0 "$(printf '%s' '' | bash "$HOOK"; echo $?)"
check "non-json stdin allowed" 0 "$(printf '%s' 'not json' | bash "$HOOK"; echo $?)"

echo "----"
echo "PASS=$pass FAIL=$fail"
[ "$fail" -eq 0 ]
