#!/usr/bin/env bash
# Tests for precommit.sh v3 decision logic. Self-contained (temp HOME + temp whitelist).
# Run: bash test_precommit.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PC="$HERE/precommit.sh"
command -v jq >/dev/null 2>&1 || { echo "SKIP: jq not installed"; exit 0; }
pass=0; fail=0
chk(){ if [ "$2" = "$3" ]; then pass=$((pass+1)); else echo "  FAIL: $1 (got $2 want $3)"; fail=$((fail+1)); fi; }

T="$(mktemp -d)"; HD="$T/.claude/hooks/review-gate"; mkdir -p "$HD"
WL="/tmp/rg-test-code-repo"                       # a fake whitelisted project path
printf '%s\n' "$WL" > "$HD/push-whitelist.txt"

ec(){ jq -cn --arg c "$1" --arg w "$2" '{tool_input:{command:$c}, cwd:$w, session_id:"s"}' \
        | HOME="$T" bash "$PC" >/dev/null 2>&1; echo $?; }

# block_commit=0 (default)
printf 'block_commit=0\n' > "$HD/review-gate.conf"
chk "commit free"               "$(ec 'git commit -m x' /tmp)"            0
chk "git status free"           "$(ec 'git status' /tmp)"                 0
chk "non-git free"              "$(ec 'ls -la' /tmp)"                     0
chk "push not-wl -> deny"       "$(ec 'git push origin main' /tmp)"       2
chk "push wl -> allow"          "$(ec 'git push origin main' "$WL")"      0
chk "push cwd-under-wl -> allow" "$(ec 'git push' "$WL/sub/dir")"         0
chk "gh pr create not-wl -> deny" "$(ec 'gh pr create -B main' /tmp)"     2
chk "gh pr merge wl -> allow"   "$(ec 'gh pr merge 1 --squash' "$WL")"    0

# git with GLOBAL OPTIONS must NOT bypass the push gate (the ai-studio-session bypass: `git -C x push`)
chk "git -C <path> push not-wl -> deny"  "$(ec 'git -C /tmp/fe push origin' /tmp)"  2
chk "git --git-dir push not-wl -> deny"  "$(ec 'git --git-dir=/x/.git push' /tmp)"  2
chk "git -c k=v push not-wl -> deny"     "$(ec 'git -c user.name=x push' /tmp)"     2
chk "git -C <path> push wl -> allow"     "$(ec 'git -C /p push' "$WL")"             0
# QUOTED global-option args with SPACES + absolute-path git must also NOT bypass (Copilot #26 edge cases)
chk "git -C \"quoted path\" push -> deny" "$(ec 'git -C "/tmp/my repo" push' /tmp)"  2
chk "git -c \"quoted k=v\" push -> deny"  "$(ec 'git -c "user.name=a b" push' /tmp)" 2
chk "/usr/bin/git push not-wl -> deny"    "$(ec '/usr/bin/git push' /tmp)"           2
# ...and non-push git commands that merely CONTAIN 'push' must stay allowed (no false-positive block)
chk "git log --grep push -> allow"       "$(ec 'git log --grep push' /tmp)"         0
chk "git show HEAD:push.txt -> allow"    "$(ec 'git show HEAD:push.txt' /tmp)"       0

# one-shot remote-publishing override: user-authorized single publish WITHOUT whitelisting
touch "$HD/allow-push-once"
chk "push not-wl + token -> allow"      "$(ec 'git push origin main' /tmp)"   0
chk "token consumed after one push"     "$([ -f "$HD/allow-push-once" ] && echo present || echo gone)" gone
chk "push not-wl after consume -> deny" "$(ec 'git push origin main' /tmp)"   2

# block_commit=1 (opted in)
printf 'block_commit=1\n' > "$HD/review-gate.conf"
chk "commit deny (opt-in)"      "$(ec 'git commit -m x' /tmp)"            2
chk "non-git still free"        "$(ec 'echo hi' /tmp)"                    0

rm -rf "$T"
if [ "$fail" -eq 0 ]; then echo "precommit.sh: all $pass tests PASS"; else echo "precommit.sh: $fail FAIL / $pass pass"; fi
[ "$fail" -eq 0 ]
