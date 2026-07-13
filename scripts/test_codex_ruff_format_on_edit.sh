#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hook="$repo_root/scripts/codex_ruff_format_on_edit.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/bin"
python_file="$tmp/sample.py"
log_file="$tmp/ruff.log"
printf 'items=[1,2,3]\n' > "$python_file"

# Regression setup: uv exists but cannot resolve the project-local ruff command.
# The hook must continue to uvx instead of returning a false success.
printf '#!/usr/bin/env bash\nexit 127\n' > "$tmp/bin/uv"
printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$*" >> "$FAKE_RUFF_LOG"\n' > "$tmp/bin/uvx"
chmod +x "$tmp/bin/uv" "$tmp/bin/uvx"

event="$(jq -cn --arg path "$python_file" '{tool_input:{file_path:$path}}')"
printf '%s' "$event" | \
  PATH="$tmp/bin:/usr/bin:/bin" FAKE_RUFF_LOG="$log_file" \
  "$hook"

grep -Fx "ruff format $python_file" "$log_file" >/dev/null
grep -Fx "ruff check --fix $python_file" "$log_file" >/dev/null

printf 'codex_ruff_format_on_edit.sh: uvx fallback PASS\n'
