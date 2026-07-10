#!/usr/bin/env bash
# codex_review_gate.sh — Codex Stop-hook.
# Now delivers the SAME 12-form review as Claude (via the shared review-gate core.sh) AND keeps Codex's
# git working-tree guards. Blocks the stop when a code review is due OR a guard trips.
# The forms LOGIC lives in hooks/review-gate/scripts/core.sh (shared, agent-neutral); this shim only
# feeds it Codex's git-detected changes and wraps the result in Codex's native systemMessage/decision JSON.
set -uo pipefail
input="$(cat || true)"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root" || exit 0
branch="$(git branch --show-current 2>/dev/null || echo "unknown")"

# --- session id for round-tracking: from the hook payload if present, else a per-branch key. filesystem-safe.
sid=""
if command -v jq >/dev/null 2>&1; then sid="$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null)"; fi
[ -n "$sid" ] || sid="codex-$branch"
sid="$(printf '%s' "$sid" | tr -c 'A-Za-z0-9._-' '_')"

# --- hand Codex's changed files (staged + unstaged + untracked, absolute) to core.sh via its state file
state_dir="$HOME/.codex/review-state"; mkdir -p "$state_dir" 2>/dev/null || true
{ git diff --cached --name-only; git diff --name-only; git ls-files --others --exclude-standard; } 2>/dev/null \
  | sort -u | grep . | sed "s#^#$repo_root/#" > "$state_dir/$sid.changed" 2>/dev/null || true

# --- forms review from the SHARED core (agent-neutral). Empty stdout => no forms review due this turn.
core="${RG_CORE:-$repo_root/hooks/review-gate/scripts/core.sh}"
forms=""
[ -f "$core" ] && forms="$(RG_STATE_DIR="$state_dir" RG_SID="$sid" bash "$core" 2>/dev/null || true)"

# --- Codex git working-tree guards (preserved) ---
staged="$(git diff --cached --name-only 2>/dev/null || true)"
unstaged="$(git diff --name-only 2>/dev/null || true)"
untracked="$(git ls-files --others --exclude-standard 2>/dev/null || true)"
total_changes=$( { printf '%s\n' "$staged"; printf '%s\n' "$unstaged"; printf '%s\n' "$untracked"; } | grep -c . || true )
destructive_ops=""
if git log --oneline -5 --all 2>/dev/null | grep -qiE 'rm -rf|git reset --hard|force push|DROP TABLE|DELETE FROM'; then destructive_ops="yes"; fi
protected="no"; case "$branch" in main|master|production|release/*) protected="yes" ;; esac
recent_msg="$(git log --oneline -1 --format='%s' 2>/dev/null || echo "")"

count=0; block="no"; guard_items=""
count=$((count+1)); guard_items="${count}. Session on branch \`${branch}\`"
if [ "$total_changes" -gt 0 ]; then
  count=$((count+1)); guard_items="${guard_items}
${count}. Uncommitted changes: ${total_changes} file(s)"; block="yes"
else
  count=$((count+1)); guard_items="${guard_items}
${count}. Working tree clean ✓"
fi
if [ "$destructive_ops" = "yes" ]; then count=$((count+1)); guard_items="${guard_items}
${count}. ⚠️  Recent destructive git operations — review before pushing"; block="yes"; fi
if [ "$protected" = "yes" ]; then count=$((count+1)); guard_items="${guard_items}
${count}. Protected branch (\`${branch}\`) — review required"; block="yes"; fi
if [ -n "$recent_msg" ]; then count=$((count+1))
  if printf '%s' "$recent_msg" | grep -qE '^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\([^)]+\))?: .'; then
    guard_items="${guard_items}
${count}. Last commit: \`${recent_msg}\` ✓ (conventional)"
  else
    guard_items="${guard_items}
${count}. Last commit: \`${recent_msg}\` ⚠️ (non-conventional format)"; block="yes"
  fi
fi

# --- combine: forms review (if due) + git guards; block if either applies ---
div="━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -n "$forms" ]; then
  block="yes"
  msg="${forms}

${div}
**Codex git-guards**
${div}
${guard_items}"
else
  msg="${div}
🔍 review-gate 审查 · Review
${div}

${guard_items}

${div}"
fi
marker="[END:FINAL]"; [ "$block" = "yes" ] && marker="[END:NEEDS_USER]"
msg="${msg}
${marker}"

if command -v jq >/dev/null 2>&1; then
  jq -n --arg msg "$msg" --arg block "$block" '{systemMessage:$msg, decision:(if $block=="yes" then "block" else "" end)}'
else
  printf '%s\n' "$msg"
fi
