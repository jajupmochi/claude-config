#!/usr/bin/env bash
MSG=$(head -1 "$1")

if echo "$MSG" | grep -qE "^Merge |^Revert "; then exit 0; fi

if ! echo "$MSG" | grep -qE "^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)!?(\([^)]+\))?!?: ."; then
  echo "ERROR: Commit message must follow conventional commit format." >&2
  exit 1
fi

[ -z "$MSG" ] && { echo "ERROR: Empty." >&2; exit 1; }

exit 0
