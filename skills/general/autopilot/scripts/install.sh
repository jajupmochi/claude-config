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
cp "$HERE"/*.py "$HERE/run.sh" "$BIN/" && chmod +x "$BIN"/*.sh "$BIN"/*.py
cp "$HERE/../PROMPT.md" "$BIN/PROMPT.md" 2>/dev/null || true

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
gen daily   "OnCalendar=*-*-* ${RUN_TIME}:00"               "/bin/bash $BIN/run.sh $PROJ"
gen watch   "OnBootSec=5min"$'\n'"OnUnitActiveSec=${WATCH_MIN}min" "$PY $BIN/watch.py $PROJ"
gen summary "OnCalendar=*-*-* ${RUN_TIME}:00"$'\n'"RandomizedDelaySec=2h" "$PY $BIN/summary.py $PROJ emit"

systemctl --user daemon-reload
for k in daily watch summary; do systemctl --user enable --now "autopilot-$k-$PROJ.timer"; done
echo "=== installed autopilot timers for $PROJ ==="
systemctl --user list-timers "autopilot-*-$PROJ.timer" --no-pager 2>/dev/null || true
