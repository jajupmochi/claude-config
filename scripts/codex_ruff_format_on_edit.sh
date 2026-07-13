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

format_file() {
  local file="$1"
  case "$file" in
    *.py) ;;
    *) return 0 ;;
  esac
  [ -f "$file" ] || return 0

  if command -v ruff >/dev/null 2>&1; then
    ruff format "$file" >/dev/null 2>&1 || true
    ruff check --fix "$file" >/dev/null 2>&1 || true
    return 0
  fi

  if command -v uv >/dev/null 2>&1 && uv run --no-sync ruff --version >/dev/null 2>&1; then
    uv run --no-sync ruff format "$file" >/dev/null 2>&1 || true
    uv run --no-sync ruff check --fix "$file" >/dev/null 2>&1 || true
    return 0
  fi

  if command -v uvx >/dev/null 2>&1; then
    uvx ruff format "$file" >/dev/null 2>&1 || true
    uvx ruff check --fix "$file" >/dev/null 2>&1 || true
  fi
}

extract_paths | sort -u | while IFS= read -r file; do
  [ -n "$file" ] && format_file "$file"
done
