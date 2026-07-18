#!/usr/bin/env bash
# statsbar.sh — render a counted breakdown as an aligned, coloured bar chart.
#
# Why this exists: a review or a task round reports things like "12 files changed, 10 clean, 1 fixed,
# 1 open". Written as prose that is a sentence to parse; as a bar it is understood at a glance. This is
# the shared renderer so review-gate, task-ledger, and anything else report the same shape.
#
# Two output formats, because the numbers are read in two places:
#   ansi  ANSI colour for a terminal or a zsh prompt. The default when stdout is a TTY.
#   md    A fenced monospace block for a markdown review. Colour comes from emoji, since ANSI escapes
#         would render as literal garbage in a markdown reader. The default when stdout is NOT a TTY.
# NO_COLOR (https://no-color.org) forces plain ansi output with no escapes.
#
# Usage:
#   statsbar.sh --title "review-gate" --unit files --total 12 \
#               --stat "OK:10:green" --stat "fixed:1:yellow" --stat "open:1:red"
#
#   --total  omitted => the sum of the stats
#   colour   green | yellow | red | blue | grey  (omitted => grey)
set -uo pipefail

title=""; unit=""; total=""; format="auto"; width=20
stats=()

while [ $# -gt 0 ]; do
  case "$1" in
    --title)  title="${2:-}"; shift 2 ;;
    --unit)   unit="${2:-}"; shift 2 ;;
    --total)  total="${2:-}"; shift 2 ;;
    --format) format="${2:-}"; shift 2 ;;
    --width)  width="${2:-}"; shift 2 ;;
    --stat)   stats+=("${2:-}"); shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) printf 'statsbar: unknown argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done

[ "${#stats[@]}" -gt 0 ] || { printf 'statsbar: at least one --stat is required\n' >&2; exit 1; }
case "$width" in ''|*[!0-9]*) printf 'statsbar: --width must be a number\n' >&2; exit 1 ;; esac

if [ "$format" = "auto" ]; then
  if [ -t 1 ]; then format="ansi"; else format="md"; fi
fi
case "$format" in ansi|md) ;; *) printf 'statsbar: --format must be ansi or md\n' >&2; exit 1 ;; esac

# Sum first so --total may be omitted, and so a percentage has a denominator.
sum=0
for s in "${stats[@]}"; do
  n="$(printf '%s' "$s" | cut -d: -f2)"
  case "$n" in ''|*[!0-9]*) printf 'statsbar: bad count in --stat "%s"\n' "$s" >&2; exit 1 ;; esac
  sum=$((sum + n))
done
[ -n "$total" ] || total="$sum"
case "$total" in ''|*[!0-9]*) printf 'statsbar: --total must be a number\n' >&2; exit 1 ;; esac

ansi_for() {
  [ -n "${NO_COLOR:-}" ] && { printf ''; return; }
  case "$1" in
    green)  printf '\033[32m' ;; yellow) printf '\033[33m' ;; red) printf '\033[31m' ;;
    blue)   printf '\033[34m' ;; *)      printf '\033[90m' ;;
  esac
}
emoji_for() {
  case "$1" in
    green) printf '✅' ;; yellow) printf '🔧' ;; red) printf '⚠️ ' ;; blue) printf 'ℹ️ ' ;; *) printf '·' ;;
  esac
}
reset() { [ -n "${NO_COLOR:-}" ] && printf '' || printf '\033[0m'; }

# Display width of a label, in terminal columns. Neither ${#s} (characters) nor wc -c (bytes) is the
# answer: a CJK character is one character, three UTF-8 bytes, and TWO columns wide. For a string of
# ASCII plus 3-byte CJK the columns come out as (chars + bytes) / 2 — an ASCII char contributes
# (1+1)/2 = 1 and a CJK char (1+3)/2 = 2. Labels here are words, not emoji, so that identity holds.
# Getting this wrong misaligns every bar, which defeats the only reason this tool exists.
dispw() {
  local s="$1" chars bytes
  chars=${#s}
  bytes=$(printf '%s' "$s" | LC_ALL=C wc -c)
  printf '%s' $(( (chars + bytes) / 2 ))
}

# Pad a label to a target column width. printf's %-*s pads by characters, so it cannot be used here.
pad() {
  local s="$1" target="$2" w out
  w=$(dispw "$s"); out="$s"
  while [ "$w" -lt "$target" ]; do out="$out "; w=$((w + 1)); done
  printf '%s' "$out"
}

# Widest label, so every bar starts at the same column.
labelw=0
for s in "${stats[@]}"; do
  l="$(printf '%s' "$s" | cut -d: -f1)"
  n=$(dispw "$l")
  [ "$n" -gt "$labelw" ] && labelw="$n"
done

# Header
if [ "$format" = "ansi" ]; then
  hdr="$title"
  [ -n "$unit" ] && hdr="$hdr — $total $unit"
  [ -n "$hdr" ] && printf '%s%s%s\n' "$(ansi_for blue)" "$hdr" "$(reset)"
else
  [ -n "$title" ] && printf '**%s**%s\n\n' "$title" "$([ -n "$unit" ] && printf ' — %s %s' "$total" "$unit")"
  printf '```\n'
fi

for s in "${stats[@]}"; do
  label="$(printf '%s' "$s" | cut -d: -f1)"
  count="$(printf '%s' "$s" | cut -d: -f2)"
  colour="$(printf '%s' "$s" | cut -d: -f3)"; [ -n "$colour" ] || colour=grey

  if [ "$total" -gt 0 ]; then
    filled=$(( count * width / total ))
    pct=$(( count * 100 / total ))
  else
    filled=0; pct=0
  fi
  # A non-zero count must never render as an empty bar — that reads as "none of these".
  [ "$count" -gt 0 ] && [ "$filled" -eq 0 ] && filled=1
  [ "$filled" -gt "$width" ] && filled="$width"

  bar=""
  i=0; while [ "$i" -lt "$filled" ]; do bar="$bar█"; i=$((i + 1)); done
  while [ "$i" -lt "$width" ]; do bar="$bar░"; i=$((i + 1)); done

  if [ "$format" = "ansi" ]; then
    printf '  %s%s%s %s%s%s %3s/%-3s %3s%%\n' \
      "$(ansi_for "$colour")" "$(pad "$label" "$labelw")" "$(reset)" \
      "$(ansi_for "$colour")" "$bar" "$(reset)" "$count" "$total" "$pct"
  else
    printf '%s %s %s %3s/%-3s %3s%%\n' "$(emoji_for "$colour")" "$(pad "$label" "$labelw")" "$bar" "$count" "$total" "$pct"
  fi
done

[ "$format" = "md" ] && printf '```\n'
exit 0
