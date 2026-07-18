#!/usr/bin/env bash
# task-ledger UserPromptSubmit capture — write every mid-round user prompt into the ledger's Inbox.
#
# This is the half that fixes forgetting. On a long round the user adds a requirement in passing at turn 30;
# by turn 60 it is far outside the working context and the agent has no idea it was ever said. Capturing at
# the hook makes it mechanical: the requirement is on disk the moment it is typed, and `ledger.py check`
# refuses to close the round while it sits untriaged. The agent cannot forget what the gate is holding.
#
# Contract: capture is best effort and NEVER blocks or edits the prompt. Empty stdout, always exit 0.
set -uo pipefail

_self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_ledger_py="$_self_dir/ledger.py"

command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
[ -f "$_ledger_py" ] || exit 0

payload="$(cat 2>/dev/null || true)"
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty' 2>/dev/null || true)"
prompt="$(printf '%s' "$payload" | jq -r '.prompt // empty' 2>/dev/null || true)"
[ -n "$prompt" ] || exit 0
[ -n "$cwd" ] && [ -d "$cwd" ] && cd "$cwd" 2>/dev/null || true

# A bare slash command is a UI action, not a requirement. Anything with an argument still counts, because
# "/loop keep fixing the flaky test" IS a requirement.
case "$prompt" in
  /*) [ "$(printf '%s' "$prompt" | wc -w)" -le 1 ] && exit 0 ;;
esac

python3 "$_ledger_py" inbox --text "$prompt" >/dev/null 2>&1 || true
exit 0
