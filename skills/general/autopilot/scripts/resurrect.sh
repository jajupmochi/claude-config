#!/usr/bin/env bash
# autopilot/resurrect.sh — layer-3 external resurrector.  [2026-06-27]
#
# Run by a systemd --user timer every ~30 min (Persistent, survives reboot). For each autopilot
# project that opted into auto-resurrect, it makes sure the project's "home" Claude session is alive
# inside a NAMED tmux session; if the machine rebooted or the session crashed and the tmux session is
# gone, it relaunches `claude` with the user's standard flags. On start, the SessionStart hook
# (session_check.sh) re-arms the daily in-session cron — so the loop continues in the same kind of
# session the user watches (remote-controlled to their phone), NOT a hidden headless run.
#
# Dependency: tmux (so an interactive --remote-control claude can persist with no terminal attached).
# If tmux is absent, this logs and exits 0 (layers 1+2 still work; only auto-resurrect needs tmux).
set +e

BASE="$HOME/.claude/autopilot"
[ -d "$BASE" ] || exit 0
LOG="$BASE/resurrect.log"
log(){ echo "$(date '+%F %T') $*" >> "$LOG"; }

if ! command -v tmux >/dev/null 2>&1; then
  log "tmux not installed — auto-resurrect skipped (run: sudo apt install tmux). Layers 1+2 unaffected."
  exit 0
fi

# Standard interactive flags (the user's usual launch). Overridable per-project via config.yaml resurrect_flags.
DEFAULT_FLAGS="--enable-auto-mode --remote-control --dangerously-skip-permissions --chrome --effort max"
CLAUDE_BIN="$(command -v claude || echo "$HOME/.local/bin/claude")"

cfg(){ python3 -c "import yaml,sys;print((yaml.safe_load(open('$1')) or {}).get('$2','') or '')" 2>/dev/null; }

for cfgf in "$BASE"/*/config.yaml; do
  [ -f "$cfgf" ] || continue
  proj="$(basename "$(dirname "$cfgf")")"

  # opt-in: resurrect: true in config.yaml (default off — only projects that asked for it)
  [ "$(cfg "$cfgf" resurrect)" = "True" ] || [ "$(cfg "$cfgf" resurrect)" = "true" ] || continue

  sess="autopilot-$proj"
  if tmux has-session -t "$sess" 2>/dev/null; then
    continue   # home session already alive — nothing to do
  fi

  repo="$(cfg "$cfgf" repo)"
  flags="$(cfg "$cfgf" resurrect_flags)"; [ -n "$flags" ] || flags="$DEFAULT_FLAGS"
  cd_part=""; [ -n "$repo" ] && cd_part="cd \"$repo\"; "

  log "home session '$sess' not alive -> relaunching claude ($flags)"
  # Detached tmux session keeps the interactive claude persistent with no attached terminal. The user
  # attaches with: tmux attach -t $sess  (or controls it from their phone via --remote-control).
  tmux new-session -d -s "$sess" "${cd_part}exec $CLAUDE_BIN $flags" 2>>"$LOG" \
    && log "relaunched '$sess' (attach: tmux attach -t $sess)" \
    || log "FAILED to relaunch '$sess' (see tmux error above)"
done
exit 0
