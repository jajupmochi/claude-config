#!/usr/bin/env bash
# autopilot install.sh <proj> — install the autopilot timers for a project.
# Prereq: the /autopilot intake has written ~/.claude/autopilot/<proj>/config.yaml with keys:
#   role_scope, repo, model, run_time (HH:MM), floor_min (default 30), watch_min (default 10).
# Copies the tooling to a STABLE path (~/.claude/autopilot/bin, not the /media mount) and
# generates+enables systemd --user timers (Persistent = crash/shutdown-proof). Idempotent.
set -euo pipefail
PROJ="${1:?usage: install.sh <proj>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python3.12 || command -v python3 || echo /usr/local/bin/python3)"
BASE="$HOME/.claude/autopilot/$PROJ"; CFG="$BASE/config.yaml"
BIN="$HOME/.claude/autopilot/bin"; UNIT="$HOME/.config/systemd/user"
[ -f "$CFG" ] || { echo "missing $CFG — run the /autopilot intake first"; exit 1; }

mkdir -p "$BIN" "$UNIT"
cp "$HERE"/*.py "$HERE"/*.sh "$BIN/" && chmod +x "$BIN"/*.sh "$BIN"/*.py
cp "$HERE/../PROMPT.md" "$BIN/PROMPT.md" 2>/dev/null || true
cp "$HERE/../VERSION" "$BIN/VERSION" 2>/dev/null || true   # for update_check.py (self-update detection)

val(){ "$PY" -c "import yaml;print((yaml.safe_load(open('$CFG')) or {}).get('$1','') or '$2')"; }
RUN_TIME="$(val run_time 03:00)"; WATCH_MIN="$(val watch_min 10)"; FLOOR="$(val floor_min 30)"
"$PY" "$BIN/floor.py" "$PROJ" set "$FLOOR" >/dev/null || true

gen(){  # $1 kind  $2 timer-stanza  $3 ExecStart
  cat > "$UNIT/autopilot-$1-$PROJ.service" <<EOF
[Unit]
Description=autopilot $1 ($PROJ)
[Service]
Type=oneshot
ExecStart=$3
Nice=10
EOF
  cat > "$UNIT/autopilot-$1-$PROJ.timer" <<EOF
[Unit]
Description=autopilot $1 timer ($PROJ)
[Timer]
$2
Persistent=true
[Install]
WantedBy=timers.target
EOF
}
RESURRECT_MIN="$(val resurrect_min 30)"
# Per-project timers: watchdog (detects stuck / failed / empty runs) + summary. The daily RUN is NO
# LONGER a systemd-spawned headless `claude -p` — it is an IN-SESSION CronCreate cron the agent arms,
# re-armed by the SessionStart hook (session_check.sh) and kept alive by the resurrector. See README §2.
gen watch   "OnBootSec=5min"$'\n'"OnUnitActiveSec=${WATCH_MIN}min" "$PY $BIN/watch.py $PROJ"
gen summary "OnCalendar=*-*-* ${RUN_TIME}:00"$'\n'"RandomizedDelaySec=2h" "$PY $BIN/summary.py $PROJ emit"

# Global resurrector timer (ONE for all projects): every ${RESURRECT_MIN} min, relaunch a project's
# home session in tmux if it died (crash / reboot). Persistent = fires after a missed reboot window.
cat > "$UNIT/autopilot-resurrect.service" <<EOF
[Unit]
Description=autopilot resurrector (all projects)
[Service]
Type=oneshot
ExecStart=/bin/bash $BIN/resurrect.sh
Nice=10
EOF
cat > "$UNIT/autopilot-resurrect.timer" <<EOF
[Unit]
Description=autopilot resurrector timer
[Timer]
OnBootSec=2min
OnUnitActiveSec=${RESURRECT_MIN}min
Persistent=true
[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
for k in watch summary; do systemctl --user enable --now "autopilot-$k-$PROJ.timer"; done
systemctl --user enable --now autopilot-resurrect.timer
echo "=== installed autopilot timers for $PROJ (+ global resurrector @ ${RESURRECT_MIN}min) ==="
echo "NOTE: the daily RUN is an in-session cron the agent arms; the SessionStart hook (session_check.sh)"
echo "      re-arms it after restarts. Wire that hook once in ~/.claude/settings.json (see README §2)."
systemctl --user list-timers "autopilot-*" --no-pager 2>/dev/null || true
