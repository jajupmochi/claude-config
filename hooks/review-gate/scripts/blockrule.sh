#!/usr/bin/env bash
# blockrule.sh — emit the exact rule line, or the whole opening, for a named block type.
#
# Why this exists: telling a model "fence the block with eight emoji" is an instruction it follows
# approximately, and the drift is always the same handful of shapes. Observed in the wild:
#   - a heading with no rule at all
#   - an emoji rule on top and a ━ bar underneath, both present
#   - the title line missing its `## ` so it renders as body text, not a heading
#   - a stray rule line with no block under it, left over from the previous block
# Formatting that must be identical every time should be GENERATED, not retyped. Same reason statsbar.sh
# exists.
#
# The emoji ALTERNATE WITHIN THE LINE — 🎉🥳🎉🥳🎉🥳🎉🥳 — not across turns. That is what makes the
# opening and closing rules identical strings by construction, so a mismatched pair is impossible and no
# counter or state file is needed.
#
# Titles vary per block ("进度报告", "进展 · 数据基础与三种模式", "状态"), so --title overrides the
# default while the emoji stay bound to the block TYPE.
#
# The block TYPE is inferred from the title, because an agent writes whatever title the moment calls for
# and should not also have to decide which of four buckets it belongs in. A title that matches nothing
# still gets a rule — there is no title this can refuse.
#
#   blockrule.sh --title 本轮完成 --heading           # type inferred: done
#   blockrule.sh --title 进展 · 数据基础与三种模式 --heading   # inferred: progress
#   blockrule.sh --title 部署清单 --heading           # nothing matched: neutral rule, still works
#   blockrule.sh review --heading                    # explicit type, default title
#   blockrule.sh review --heading --title 复审第二轮   # explicit type overrides inference
#
# The closing rule is the SAME command as the opening rule: `blockrule.sh <type>`.
set -uo pipefail

WIDTH="${BR_WIDTH:-8}"

# The type is optional and positional, so only claim $1 when it is not a flag. Claiming it
# unconditionally swallowed the first flag, which made `blockrule.sh --title X` fail on X.
type_name=""
case "${1:-}" in
  ""|--*) ;;
  *) type_name="$1"; shift ;;
esac
heading=0
closing=0
title_override=""
while [ $# -gt 0 ]; do
  case "$1" in
    --heading) heading=1; shift ;;
    --title)
      if [ $# -lt 2 ]; then printf 'blockrule: --title needs a value\n' >&2; exit 1; fi
      title_override="$2"; shift 2 ;;
    --close) closing=1; shift ;;
    *) printf 'blockrule: unknown argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done

# A closing separator is a heavy bar, not emoji. Emoji open a block and carry its title; a bar ends it.
# Making the two ends visually different is what stops one block's tail reading as the next block's head.
# The bar is sized to match the emoji rule's rendered width: emoji are two columns each, bars are one.
if [ "$closing" -eq 1 ]; then
  case "$WIDTH" in ''|*[!0-9]*) printf 'blockrule: BR_WIDTH must be a number\n' >&2; exit 1 ;; esac
  [ "$WIDTH" -lt 1 ] && { printf 'blockrule: BR_WIDTH must be at least 1\n' >&2; exit 1; }
  b=""; k=0
  while [ "$k" -lt $((WIDTH * 2)) ]; do b="$b━"; k=$((k + 1)); done
  printf '%s\n' "$b"
  exit 0
fi

# Infer the block type from the title. Heuristic and multi-keyword: the title is split on the separators
# an agent actually writes (spaces, ·, dashes, slashes, colons, brackets, commas), every keyword is
# matched against both the whole title and each token, and the type with the most hits wins. Accumulating
# hits rather than taking the first match means "第三轮复审结果与后续进度" lands on the type it mentions
# most, not on whichever keyword the case statement happened to list first.
#
# When NOTHING matches, this does NOT invent a neutral block. It exits 3 and asks the caller to pick one
# of the four by the title's nature. A neutral fallback would quietly turn every unrecognised title into a
# fifth visual category, which is the opposite of what the emoji are for.
_score_type() {
  # $1 = haystack (title, lowercased), $2.. = keywords. Prints the number of keywords present.
  local hay="$1"; shift
  local n=0 kw
  for kw in "$@"; do
    case "$hay" in *"$kw"*) n=$((n + 1)) ;; esac
  done
  printf '%s' "$n"
}

infer_type() {
  local raw="$1"
  # Lowercase for the ASCII keywords; CJK is unaffected. Separators become spaces so tokens are visible
  # to the same substring matching, which is what makes a compound title like "进展 · 数据基础" work.
  # Lowercase with ${,,} rather than tr: tr operates on BYTES, so it corrupts any CJK character whose
  # UTF-8 bytes fall in the A-Z range. That silently broke 状态, which then matched nothing at all.
  local hay="${raw,,}"
  hay="$(printf '%s' "$hay" | sed 's/[·—–\/:,;()[]{}<>|_]/ /g')"

  local s_review s_progress s_decision s_done
  s_review=$(_score_type "$hay"   审查 复审 评审 审阅 核查 检查 走查 校验 质检 复核 review audit inspect lint)
  s_progress=$(_score_type "$hay" 进度 进展 状态 进程 阶段 现状 情况 目前 当前 报告 progress status update ongoing report)
  s_decision=$(_score_type "$hay" 决策 需要你 待你 确认 批准 授权 等待 待定 待批 请示 抉择 选择 阻塞 decision approval approve confirm needs blocked pending)
  s_done=$(_score_type "$hay"     完成 收尾 小结 总结 结束 交付 完毕 搞定 落地 上线 done complete completed finished summary wrap delivered)

  local best=0 pick=""
  # Order breaks ties deliberately: a title naming both a review and progress is more useful filed as a
  # review, and a decision outranks a summary because it is the one that needs the reader to act.
  if [ "$s_review" -gt "$best" ];   then best="$s_review";   pick=review;   fi
  if [ "$s_decision" -gt "$best" ]; then best="$s_decision"; pick=decision; fi
  if [ "$s_progress" -gt "$best" ]; then best="$s_progress"; pick=progress; fi
  if [ "$s_done" -gt "$best" ];     then best="$s_done";     pick=done;     fi

  [ -n "$pick" ] || return 1
  printf '%s' "$pick"
}

if [ -z "$type_name" ] && [ -n "$title_override" ]; then
  if ! type_name="$(infer_type "$title_override")"; then
    printf 'blockrule: cannot infer a block type from %s\n' "$title_override" >&2
    printf '  Pick the closest of the four by what the block is FOR, and pass it explicitly:\n' >&2
    printf '    review    👨🏻‍⚕️🔍👩🏻‍⚕️  examining work for defects\n' >&2
    printf '    progress  🚀🏎️      where things stand mid-flight\n' >&2
    printf '    decision  🔔⏰      something needs the reader to act\n' >&2
    printf '    done      🎉🥳      a round or deliverable finished\n' >&2
    printf '  e.g. blockrule.sh progress --title %s\n' "$title_override" >&2
    exit 3
  fi
fi

case "$type_name" in
  review)   set -- "👨🏻‍⚕️" "🔍" "👩🏻‍⚕️"; title="review-gate 审查" ;;
  progress) set -- "🚀" "🏎️";             title="进度报告" ;;
  decision) set -- "🔔" "⏰";              title="需要你决策" ;;
  done)     set -- "🎉" "🥳";              title="本轮完成" ;;
  "")       printf 'blockrule: give a type (review|progress|decision|done) or a --title to infer one from\n' >&2; exit 1 ;;
  *)        printf 'blockrule: unknown block type %s (have: review, progress, decision, done)\n' "$type_name" >&2; exit 1 ;;
esac

[ -n "$title_override" ] && title="$title_override"

case "$WIDTH" in ''|*[!0-9]*) printf 'blockrule: BR_WIDTH must be a number\n' >&2; exit 1 ;; esac
[ "$WIDTH" -lt 1 ] && { printf 'blockrule: BR_WIDTH must be at least 1\n' >&2; exit 1; }

n=$#
rule=""
k=0
while [ "$k" -lt "$WIDTH" ]; do
  idx=$(( (k % n) + 1 ))
  rule="$rule${!idx}"
  k=$((k + 1))
done

# The heading always leads with the FIRST emoji of the type, so the type is recognisable from the title
# line alone even when the rule above it has scrolled off.
lead="$1"

if [ "$heading" -eq 1 ]; then
  printf '%s\n\n## %s %s\n\n%s\n' "$rule" "$lead" "$title" "$rule"
else
  printf '%s\n' "$rule"
fi
