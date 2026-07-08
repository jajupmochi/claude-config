#!/usr/bin/env bash
# Install autoresearch-toolfinder into the user-level Claude skills dir and enable the
# weekly index-refresh timer. Idempotent. The live copy lives on ~ (stable), not /media.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.claude/skills/autoresearch-toolfinder"
PY="$(command -v python3.12 || command -v python3 || echo /usr/local/bin/python3)"

echo "==> installing skill to $DEST"
mkdir -p "$DEST/data"
cp -r "$SRC/scripts" "$SRC/systemd" "$SRC/SKILL.md" "$SRC/README.md" "$DEST/"

echo "==> building index (live copy)"
"$PY" "$DEST/scripts/update_index.py"

echo "==> installing + enabling weekly user timer"
UNIT="$HOME/.config/systemd/user"
mkdir -p "$UNIT"
cp "$DEST/systemd/autoresearch-index.service" "$UNIT/"
cp "$DEST/systemd/autoresearch-index.timer" "$UNIT/"
if systemctl --user daemon-reload 2>/dev/null; then
    systemctl --user enable --now autoresearch-index.timer
    systemctl --user list-timers autoresearch-index.timer --no-pager || true
else
    echo "[note] no user systemd bus here; enable later with:"
    echo "       systemctl --user daemon-reload && systemctl --user enable --now autoresearch-index.timer"
fi
echo "==> done"
