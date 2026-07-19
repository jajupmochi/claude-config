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
title_override=""
while [ $# -gt 0 ]; do
  case "$1" in
    --heading) heading=1; shift ;;
    --title)
      if [ $# -lt 2 ]; then printf 'blockrule: --title needs a value\n' >&2; exit 1; fi
      title_override="$2"; shift 2 ;;
    # Accepted and ignored: the closing rule is identical to the opening one, so callers that still
    # pass --close keep working instead of failing for asking about a distinction that no longer exists.
    --close) shift ;;
    *) printf 'blockrule: unknown argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done

# Infer the block type from the title when no type was given. Keyword sets cover the Chinese and the
# English an agent actually writes; anything unmatched falls through to a neutral pair rather than an
# error, because refusing a title the agent legitimately invented would just push the drift elsewhere.
infer_type() {
  case "$1" in
    *审查*|*复审*|*评审*|*检查*|*review*|*Review*|*REVIEW*|*audit*|*Audit*) printf 'review' ;;
    *进度*|*进展*|*状态*|*进程*|*progress*|*Progress*|*status*|*Status*|*update*|*Update*) printf 'progress' ;;
    *决策*|*需要你*|*待你*|*确认*|*批准*|*授权*|*等待*|*decision*|*Decision*|*approval*|*Approval*|*needs*|*Needs*) printf 'decision' ;;
    *完成*|*收尾*|*小结*|*总结*|*结束*|*交付*|*done*|*Done*|*complete*|*Complete*|*summary*|*Summary*|*finished*) printf 'done' ;;
    *) printf 'note' ;;
  esac
}

if [ -z "$type_name" ] && [ -n "$title_override" ]; then
  type_name="$(infer_type "$title_override")"
fi

case "$type_name" in
  review)   set -- "👨🏻‍⚕️" "🔍" "👩🏻‍⚕️"; title="review-gate 审查" ;;
  progress) set -- "🚀" "🏎️";             title="进度报告" ;;
  decision) set -- "🔔" "⏰";              title="需要你决策" ;;
  done)     set -- "🎉" "🥳";              title="本轮完成" ;;
  note)     set -- "📌" "📎";              title="说明" ;;
  "")       printf 'blockrule: give a type (review|progress|decision|done|note) or a --title to infer one from\n' >&2; exit 1 ;;
  *)        printf 'blockrule: unknown block type %s (have: review, progress, decision, done, note)\n' "$type_name" >&2; exit 1 ;;
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
