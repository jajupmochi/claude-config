#!/usr/bin/env bash
# typecheck-on-edit — PostToolUse hook. After a .ts/.tsx Write/Edit: prettier --write the file (best-effort),
# then typecheck its project with `tsc --noEmit`. TYPE ERRORS EXIT 2 → Claude Code blocks the turn and shows
# the errors, so a type-broken edit cannot pass silently. Deterministic, no LLM.
#
# Design (part of the Figma→code pipeline's "deterministic hooks" spine — see the figma-design-fetch skill):
#   - Reads the edited file path from the PostToolUse JSON on stdin (falls back to $1 for testing).
#   - No-op unless the file is .ts/.tsx AND lives in a project with a tsconfig.json AND a usable tsc.
#   - Uses the PROJECT-LOCAL tsc (node_modules/.bin/tsc); never auto-downloads. If no tsc is reachable, it is a
#     NO-OP (does not block a project that has no TypeScript).
#   - TSC / PRETTIER are overridable (env) so the exit-2 wiring is unit-testable without a real toolchain.
set +e
command -v jq >/dev/null 2>&1 || { [ -n "$1" ] || exit 0; }

IN="$(cat 2>/dev/null)"
f="$(printf '%s' "$IN" | jq -r '.tool_response.filePath // .tool_input.file_path // empty' 2>/dev/null)"
[ -n "$f" ] || f="$1"                       # arg fallback (tests)
case "$f" in *.ts | *.tsx) ;; *) exit 0 ;; esac
[ -f "$f" ] || exit 0

# find the nearest tsconfig.json walking up from the file
dir="$(cd "$(dirname "$f")" 2>/dev/null && pwd)"
root=""
while [ -n "$dir" ] && [ "$dir" != "/" ]; do
  [ -f "$dir/tsconfig.json" ] && { root="$dir"; break; }
  dir="$(dirname "$dir")"
done
[ -n "$root" ] || exit 0                     # not a TS project → no-op

# prettier (best-effort, never blocks)
PRETTIER="${PRETTIER:-$root/node_modules/.bin/prettier}"
[ -x "$PRETTIER" ] || PRETTIER="$(command -v prettier 2>/dev/null)"
[ -n "$PRETTIER" ] && "$PRETTIER" --write "$f" >/dev/null 2>&1

# typecheck: project-local tsc, else global, else no-op (do NOT block a project without TypeScript)
TSC="${TSC:-$root/node_modules/.bin/tsc}"
[ -x "$TSC" ] || TSC="$(command -v tsc 2>/dev/null)"
[ -n "$TSC" ] || exit 0

out="$(cd "$root" && "$TSC" --noEmit -p tsconfig.json 2>&1)"
if [ $? -ne 0 ]; then
  {
    echo "tsc reported type errors (blocking — fix before continuing):"
    printf '%s\n' "$out" | head -30
  } >&2
  exit 2
fi
exit 0
