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
# systemd --user services run with a MINIMAL PATH (they do NOT source ~/.zshrc/~/.profile), so the
# `claude` CLI (in ~/.local/bin) and its child tools (node/npx/git/rg) aren't found → a bare `claude -p`
# fails "command not found" ×cap → ~1s empty "success". Restore a full PATH + resolve claude absolutely.
# [fix 2026-06-26: root cause of empty 0-min autopilot runs — claude: command not found]
NODE_BIN="$(ls -d "$HOME"/.nvm/versions/node/*/bin 2>/dev/null | sort -V | tail -1)"
export PATH="$HOME/.local/bin:$HOME/.claude/local:$HOME/.npm-global/bin:$HOME/.bun/bin:$HOME/bin${NODE_BIN:+:$NODE_BIN}:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"
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
# Fail LOUD if claude can't be found — never silently loop to the attempt cap and fake a "done".
if [ ! -x "$CLAUDE_BIN" ] && ! command -v claude >/dev/null 2>&1; then
  echo "[run.sh] FATAL: claude CLI not found (PATH=$PATH)" >>"$LOG"
  date +%s > "$BASE/last-error"; exit 127
fi
rm -f "$BASE/last-error"                                # clear stale failure marker before a real attempt
"$PY" "$HERE/floor.py" "$PROJ" start; heartbeat
[ -n "$REPO" ] && cd "$REPO" 2>/dev/null
attempt=0; floor_met=0; fast_fail=0
while :; do
  attempt=$((attempt + 1)); heartbeat
  # Keep the heartbeat fresh DURING the (possibly long) claude -p call so the watchdog reads a
  # true liveness signal and never false-positives a healthy long run as "stuck".
  ( while :; do date +%s > "$BASE/heartbeat"; sleep 120; done ) & hb_pid=$!
  t0=$(date +%s)
  "$CLAUDE_BIN" -p --dangerously-skip-permissions ${MODEL:+--model "$MODEL"} \
    --append-system-prompt "$PROMPT" \
    "autopilot daily run for [$PROJ]. Execute the autopilot directive now (attempt $attempt)." \
    >>"$LOG" 2>&1
  rc=$?; kill "$hb_pid" 2>/dev/null; heartbeat
  "$PY" "$HERE/floor.py" "$PROJ" check && { floor_met=1; break; }   # floor met -> done for today
  # A real autorun runs for minutes; a <15s non-zero exit = claude failed to launch/auth (not real work).
  # Abort after 3 such fast-fails instead of silently burning all 24 attempts in ~1s and faking success.
  if [ "$rc" -ne 0 ] && [ $(( $(date +%s) - t0 )) -lt 15 ]; then
    fast_fail=$((fast_fail + 1))
    echo "[run.sh] claude -p exited rc=$rc in <15s (fast-fail $fast_fail/3, attempt $attempt)" >>"$LOG"
    [ "$fast_fail" -ge 3 ] && { echo "[run.sh] ABORT: 3 consecutive fast failures — claude not launching" >>"$LOG"; break; }
  else
    fast_fail=0
  fi
  [ "$attempt" -ge 24 ] && { echo "[run.sh] attempt cap reached" >>"$LOG"; break; }
done
if [ "$floor_met" = "1" ]; then
  date +%s > "$BASE/last-done"; rm -f "$BASE/last-error"
  echo "[run.sh] autopilot run complete (floor met) $(date -Iseconds)" >>"$LOG"
else
  date +%s > "$BASE/last-error"
  echo "[run.sh] autopilot run ENDED WITHOUT meeting floor (attempts=$attempt fast_fail=$fast_fail) — watchdog will flag $(date -Iseconds)" >>"$LOG"
  exit 1
fi
