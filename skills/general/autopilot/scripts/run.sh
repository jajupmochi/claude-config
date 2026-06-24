#!/usr/bin/env bash
# autopilot run.sh <proj> — the daily driver (invoked by the systemd timer).
# Loops a FRESH `claude -p` autorun session seeded with docs/autopilot/PROMPT.md (with the
# [ROLE & SCOPE] block filled from config) until the >= floor-minutes floor is met
# (floor.py — agent-independent) and the current unit is clean. NOT `--resume`: replaying a
# huge transcript times out (WorkNRoll finding); context comes from the plan docs instead.
# Writes a heartbeat (for the watchdog) and a last-done marker.
# NOTE: scaffold — first validated when /autopilot installs + enables it (spawns real sessions).
set +e
PROJ="${1:?usage: run.sh <proj>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3.12 || command -v python3 || echo /usr/local/bin/python3)"
BASE="$HOME/.claude/autopilot/$PROJ"; CFG="$BASE/config.yaml"
PROMPT_FILE="$HERE/../PROMPT.md"; [ -f "$PROMPT_FILE" ] || PROMPT_FILE="$HERE/PROMPT.md"
mkdir -p "$BASE/runs"; LOG="$BASE/runs/$(date +%F_%H%M).log"

cfg(){ "$PY" -c "import yaml;print((yaml.safe_load(open('$CFG')) or {}).get('$1','') or '')" 2>/dev/null; }
REPO="$(cfg repo)"; MODEL="$(cfg model)"; ROLE="$(cfg role_scope)"

# fill the [ROLE & SCOPE] fenced block of the prompt from config
PROMPT="$(ROLE="$ROLE" "$PY" - "$PROMPT_FILE" <<'PY'
import os, re, sys
t = open(sys.argv[1]).read()
role = os.environ.get("ROLE", "").strip()
if role:
    t = re.sub(r"(\[ROLE & SCOPE\].*?```\n).*?(\n```)", r"\g<1>" + role + r"\g<2>", t, flags=re.S, count=1)
sys.stdout.write(t)
PY
)"

heartbeat(){ date +%s > "$BASE/heartbeat"; }
"$PY" "$HERE/floor.py" "$PROJ" start; heartbeat
[ -n "$REPO" ] && cd "$REPO" 2>/dev/null
attempt=0
while :; do
  attempt=$((attempt + 1)); heartbeat
  # Keep the heartbeat fresh DURING the (possibly long) claude -p call so the watchdog reads a
  # true liveness signal and never false-positives a healthy long run as "stuck".
  ( while :; do date +%s > "$BASE/heartbeat"; sleep 120; done ) & hb_pid=$!
  claude -p --dangerously-skip-permissions ${MODEL:+--model "$MODEL"} \
    --append-system-prompt "$PROMPT" \
    "autopilot daily run for [$PROJ]. Execute the autopilot directive now (attempt $attempt)." \
    >>"$LOG" 2>&1
  kill "$hb_pid" 2>/dev/null; heartbeat
  "$PY" "$HERE/floor.py" "$PROJ" check && break        # floor met -> done for today
  [ "$attempt" -ge 24 ] && { echo "[run.sh] attempt cap reached" >>"$LOG"; break; }
done
date +%s > "$BASE/last-done"
echo "[run.sh] autopilot run complete $(date -Iseconds)" >>"$LOG"
