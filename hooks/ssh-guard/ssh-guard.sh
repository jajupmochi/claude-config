#!/usr/bin/env bash
# ssh-guard — PreToolUse(Bash) hook. Prevents SSH username-probing: trying several different usernames
# against ONE host in a short burst. That pattern trips fail2ban's sshd jail and IP-bans you from the
# host — and because an agent session and its human share one egress IP, it locks the human out too.
#
# Root cause it exists for (2026-07-17): an agent probed wrong usernames against a prod box; fail2ban
# banned the shared egress IP on the SSH port. Every other port stayed open, so it looked like an
# outage; it was a self-inflicted ban. See rules/no-ssh-username-probing/RULE.md.
#
# Behaviour: blocks the 2nd DISTINCT username to the same host within a window (default 30 min).
# Re-trying the SAME user is always fine (that's a retry, not probing). Deterministic, no LLM.
# Fail-OPEN: any parse/tool error exits 0 (allow) — a guard must never wedge unrelated shell work.
#
# Override for a genuinely-second legitimate account:  touch <state>/allow-ssh-user-once  (consumed once).
set +e

STATE_DIR="${SSH_GUARD_STATE:-$HOME/.claude/agent-harness/hooks/ssh-guard/.state}"
ALLOW_ONCE="$STATE_DIR/allow-ssh-user-once"
WINDOW_SECS="${SSH_GUARD_WINDOW:-1800}"

# jq is how we read the PreToolUse payload; without it (and without a test arg) we can't judge -> allow.
command -v jq >/dev/null 2>&1 || { [ -n "$1" ] || exit 0; }

IN="$(cat 2>/dev/null)"
cmd="$(printf '%s' "$IN" | jq -r '.tool_input.command // empty' 2>/dev/null)"
[ -n "$cmd" ] || cmd="$1"
[ -n "$cmd" ] || exit 0

# Fast path: only ssh/scp/sftp invocations are interesting; everything else passes untouched.
printf '%s' "$cmd" | grep -qE '(^|[;&|[:space:]])(ssh|scp|sftp)([[:space:]]|$)' || exit 0

now="$(date +%s 2>/dev/null)" || exit 0
[ -n "$now" ] || exit 0

# Extract user@host tokens. Skip anything that looks like an email inside quotes/angle brackets
# (git author strings etc.) by ignoring pairs immediately preceded by '<' or '"'.
pairs="$(printf '%s' "$cmd" \
  | grep -oE '(^|[^<"[:alnum:]])[A-Za-z0-9._-]+@[A-Za-z0-9.-]+' 2>/dev/null \
  | grep -oE '[A-Za-z0-9._-]+@[A-Za-z0-9.-]+' 2>/dev/null)"
[ -n "$pairs" ] || exit 0   # no explicit user@host (e.g. bare `ssh host`, or `-l` form) -> nothing to judge

mkdir -p "$STATE_DIR" 2>/dev/null || exit 0

printf '%s\n' "$pairs" | while IFS= read -r p; do
  [ -n "$p" ] || continue
  user="${p%@*}"; host="${p#*@}"
  [ -n "$user" ] && [ -n "$host" ] || continue
  safe="$(printf '%s' "$host" | tr -c 'A-Za-z0-9._-' '_')"
  f="$STATE_DIR/host_${safe}.tsv"   # lines: <epoch>\t<user>

  if [ -f "$f" ]; then
    # A different username used against this host within the window == probing.
    recent_other="$(awk -F'\t' -v u="$user" -v now="$now" -v w="$WINDOW_SECS" \
      '$2!=u && ($1+0)>0 && (now-$1)<=w{c++} END{print c+0}' "$f" 2>/dev/null)"
    if [ "${recent_other:-0}" -gt 0 ]; then
      if [ -f "$ALLOW_ONCE" ]; then
        rm -f "$ALLOW_ONCE" 2>/dev/null   # consume the one-shot override, allow this one
      else
        others="$(awk -F'\t' -v u="$user" -v now="$now" -v w="$WINDOW_SECS" \
          '$2!=u && (now-$1)<=w{print $2}' "$f" 2>/dev/null | sort -u | tr '\n' ' ')"
        echo "Blocked: SSH username-probing on '${host}'. Recently tried user(s) [ ${others}] here; now trying '${user}'. Guessing usernames trips fail2ban and IP-bans you from the host (this locked out the shared egress IP on 2026-07-17). Find the EXACT user first — deploy config, ask the human, or read 'ssh -v' output — do NOT loop. If '${user}' is a genuinely separate legitimate account, run:  touch \"${ALLOW_ONCE}\"  then retry once." >&2
        exit 2
      fi
    fi
  fi
  printf '%s\t%s\n' "$now" "$user" >> "$f" 2>/dev/null
done

# Propagate a block (exit 2) out of the subshell pipeline; otherwise allow.
[ "$?" -eq 2 ] && exit 2
exit 0
