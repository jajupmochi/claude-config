#!/usr/bin/env bash
set -euo pipefail

input="$(cat || true)"

extract_paths() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$input" | jq -r '
      [
        .tool_input.file_path?,
        .tool_input.filePath?,
        .tool_input.path?,
        .tool_input.args.file_path?,
        .tool_input.args.filePath?,
        .tool_input.args.path?,
        .tool_response.file_path?,
        .tool_response.filePath?,
        .file_path?,
        .filePath?,
        .path?
      ]
      | .[]
      | select(type == "string" and length > 0)
    ' 2>/dev/null || true

    printf '%s' "$input" | jq -r '
      [
        .tool_input.patch?,
        .patch?
      ]
      | .[]
      | select(type == "string")
      | split("\n")[]
      | capture("^\\*\\*\\* (?:Add|Update) File: (?<path>.+)$").path?
    ' 2>/dev/null || true
  else
    printf '%s\n' "$input" | sed -n 's/.*"file[Pp]ath"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p'
    printf '%s\n' "$input" | sed -n 's/^\*\*\* \(Add\|Update\) File: \(.*\)$/\2/p'
  fi
}

validate_file() {
  local file="$1"
  case "$file" in
    */locales/*.json|*/data/*.json) ;;
    *) return 0 ;;
  esac
  [ -f "$file" ] || return 0
  command -v jq >/dev/null 2>&1 || return 0

  local err
  err="$(jq empty "$file" 2>&1 >/dev/null || true)"
  if [ -n "$err" ]; then
    jq -n --arg f "$file" --arg err "$err" '{
      systemMessage: ("Invalid JSON in " + $f + ": " + $err),
      decision: "block",
      reason: "Fix JSON syntax before proceeding."
    }'
    exit 1
  fi
}

extract_paths | sort -u | while IFS= read -r file; do
  [ -n "$file" ] && validate_file "$file"
done
