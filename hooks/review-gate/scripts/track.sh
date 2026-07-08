#!/usr/bin/env bash
# review-gate / track.sh  —  PostToolUse(Edit|Write) hook.
# Logs each Claude-edited file into a per-session changed-file list so the Stop
# gate can review exactly what changed this turn.
# CONTRACT: must NEVER block or error the session. Always exit 0 (fail-open).
set +e
command -v jq >/dev/null 2>&1 || exit 0
IN="$(cat 2>/dev/null)"
f="$(printf '%s' "$IN" | jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null)"
sid="$(printf '%s' "$IN" | jq -r '.session_id // empty' 2>/dev/null)"
[ -n "$sid" ] || sid="nosess"
[ -n "$f" ] || exit 0
dir="$HOME/.claude/review-state"
mkdir -p "$dir" 2>/dev/null
printf '%s\n' "$f" >> "$dir/$sid.changed" 2>/dev/null
exit 0
