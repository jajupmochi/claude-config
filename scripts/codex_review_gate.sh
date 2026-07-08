#!/usr/bin/env bash
set -euo pipefail
input="$(cat || true)"

branch="$(git branch --show-current 2>/dev/null || echo "unknown")"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

# Gather state
staged="$(git diff --cached --name-only 2>/dev/null)"
unstaged="$(git diff --name-only 2>/dev/null)"
untracked="$(git ls-files --others --exclude-standard 2>/dev/null)"
total_changes=$( (echo "$staged"; echo "$unstaged"; echo "$untracked") | grep -c . || true )

# Destructive ops check
destructive_ops=""
if git log --oneline -5 --all 2>/dev/null | grep -qiE 'rm -rf|git reset --hard|force push|DROP TABLE|DELETE FROM' 2>/dev/null; then destructive_ops="yes"; fi

# Protected branch
protected="no"
case "$branch" in main|master|production|release/*) protected="yes" ;; esac

# Build formatted output
divider="━━━━━━━━━━━━━━━━━━━━━━━━━━"
items=""
count=0
marker="[END:FINAL]"

# Item 1: session summary
count=$((count + 1))
items="${items}${count}. Session complete on branch \`${branch}\`"

# Item 2: change audit
if [ "$total_changes" -gt 0 ]; then
  count=$((count + 1))
  items="${items}
${count}. Uncommitted changes: ${total_changes} file(s)"
  if [ -n "$staged" ]; then items="${items}
   Staged: $(echo "$staged" | head -3 | tr '\n' ' ' | sed 's/ $//')"; fi
  if [ -n "$unstaged" ]; then items="${items}
   Modified: $(echo "$unstaged" | head -3 | tr '\n' ' ' | sed 's/ $//')"; fi
  marker="[END:NEEDS_USER]"
else
  count=$((count + 1))
  items="${items}
${count}. Working tree clean ✓"
fi

# Item 3: destructive ops
if [ "$destructive_ops" = "yes" ]; then
  count=$((count + 1))
  items="${items}
${count}. ⚠️  Recent destructive git operations detected — review before pushing"
  marker="[END:NEEDS_USER]"
fi

# Item 4: protected branch
if [ "$protected" = "yes" ]; then
  count=$((count + 1))
  items="${items}
${count}. Protected branch (\`${branch}\`) — force push disabled, review required"
  marker="[END:NEEDS_USER]"
fi

# Item 5: commit message check
recent_msg="$(git log --oneline -1 --format='%s' 2>/dev/null || echo "")"
count=$((count + 1))
if [ -n "$recent_msg" ]; then
  if echo "$recent_msg" | grep -qE '^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(\([^)]+\))?: .'; then
    items="${items}
${count}. Last commit: \`${recent_msg}\` ✓ (conventional format)"
  else
    items="${items}
${count}. Last commit: \`${recent_msg}\` ⚠️ (non-conventional format)"
    marker="[END:NEEDS_USER]"
  fi
fi

# Build the full message
msg="${divider}\n🔍 review-gate 审查\n${divider}\n\n${items}\n\n${divider}\n${marker}"

# Emit
jq -n --arg msg "$msg" '{
  systemMessage: $msg,
  decision: (if $msg | contains("[END:NEEDS_USER]") then "block" else "" end)
}'
