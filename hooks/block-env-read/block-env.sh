#!/usr/bin/env bash
# block-env-read — PreToolUse hook. Denies reading `.env` / `.env.*` / `*.env` files so secrets never land in
# the transcript. Exit 2 blocks the tool call and tells Claude why. Deterministic, no LLM.
#
# Reads the target path from the PreToolUse payload (Read tool `file_path`; falls back to $1 for tests).
# NOTE: this covers the Read tool. Reading .env via a Bash command (`cat .env`) is out of scope here — pair with
# a permissions allowlist that keeps `cat`/`grep` off dotenv files if you need that too.
set +e
command -v jq >/dev/null 2>&1 || { [ -n "$1" ] || exit 0; }

IN="$(cat 2>/dev/null)"
f="$(printf '%s' "$IN" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null)"
[ -n "$f" ] || f="$1"
[ -n "$f" ] || exit 0
base="$(basename "$f" 2>/dev/null)"

case "$base" in
  .env | .env.* | *.env)
    echo "Blocked reading '$base': dotenv files are denied to keep secrets out of the transcript. If you need a value from it, ask the user for that specific value." >&2
    exit 2
    ;;
esac
exit 0
