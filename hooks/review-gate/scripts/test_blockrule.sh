#!/usr/bin/env bash
# Tests for blockrule.sh. Run: bash test_blockrule.sh
#
# Every check below corresponds to a drift shape actually observed in real output:
#   eg1  a heading with no rule at all, and a title the default did not cover
#   eg2  an emoji rule on top and a ━ bar underneath, both present
#   eg3  the title line missing its `## `, so it renders as body text
#   eg4  a stray rule line with no block under it
#   eg5  one block's closing rule butted against the next block's opening
# The design answer to eg4 and eg5 is that the opening and closing rules are the SAME string, produced by
# the same command, so a mismatched or orphaned pair cannot be produced by getting an argument wrong.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BR="$HERE/blockrule.sh"
pass=0; fail=0
chk(){ if [ "$2" = "$3" ]; then echo "  ok: $1"; pass=$((pass+1)); else echo "  FAIL: $1 (got '$2' want '$3')"; fail=$((fail+1)); fi; }
chkTrue(){ if [ "$2" = "yes" ]; then echo "  ok: $1"; pass=$((pass+1)); else echo "  FAIL: $1"; fail=$((fail+1)); fi; }

# 1. Emoji alternate WITHIN the line, which is what was asked for: 🎉🥳🎉🥳…
chk "done alternates in-line"     "$(bash "$BR" done)"     "🎉🥳🎉🥳🎉🥳🎉🥳"
chk "decision alternates in-line" "$(bash "$BR" decision)" "🔔⏰🔔⏰🔔⏰🔔⏰"
chk "progress alternates in-line" "$(bash "$BR" progress)" "🚀🏎️🚀🏎️🚀🏎️🚀🏎️"
chk "review cycles its three"     "$(bash "$BR" review)"   "👨🏻‍⚕️🔍👩🏻‍⚕️👨🏻‍⚕️🔍👩🏻‍⚕️👨🏻‍⚕️🔍"

# 2. eg4/eg5: a block OPENS with emoji and CLOSES with a bar, so the two ends cannot be mistaken for
#    each other and one block's tail can never read as the next block's head.
BAR16="━━━━━━━━━━━━━━━━"
chk "--close emits a bar, not emoji" "$(bash "$BR" --close)" "$BAR16"
chk "the closing bar does not depend on the type" "$(bash "$BR" review --close)" "$(bash "$BR" done --close)"
chk "the closing bar needs no title" "$(bash "$BR" --close)" "$BAR16"
chkTrue "the closing bar carries no emoji" \
  "$(bash "$BR" --close | grep -qE '🎉|🥳|🔍|🚀|🔔' && echo no || echo yes)"
chkTrue "an opening rule carries no bar" \
  "$(bash "$BR" --title 本轮完成 | grep -q '━' && echo no || echo yes)"
chk "closing width matches the emoji rule's rendered width" \
  "$(bash "$BR" --close | wc -m)" "17"
chk "BR_WIDTH scales the bar too" "$(BR_WIDTH=4 bash "$BR" --close)" "━━━━━━━━"

# 3. Output is stateless — no counter file to drift, and repeated calls never change.
before="$(bash "$BR" review)"
for _ in 1 2 3 4 5; do bash "$BR" review >/dev/null; done
chk "stateless: unchanged after five calls" "$(bash "$BR" review)" "$before"
# The old design kept a per-type counter under BR_STATE_DIR. Prove none is written anywhere now —
# and look for the counter FILENAMES, not the substring "blockrule.", which also matches the scripts.
probe="$(mktemp -d)"
BR_STATE_DIR="$probe" bash "$BR" done >/dev/null
BR_STATE_DIR="$probe" bash "$BR" review --heading >/dev/null
chk "stateless: no counter file written" "$(find "$probe" -type f 2>/dev/null | wc -l)" "0"
rm -rf "$probe"

# 4. eg2: a ━ bar must never appear, in any type, in any mode.
out="$(for t in review progress decision done; do bash "$BR" $t; bash "$BR" $t --heading; done)"
chkTrue "no bar in any OPENING rule (the bar belongs to --close only)" \
  "$(printf '%s' "$out" | grep -q '━' && echo no || echo yes)"

# 5. eg3: the title line is a real markdown heading, not body text.
h="$(bash "$BR" review --heading)"
chkTrue "title line starts with '## '" "$(printf '%s\n' "$h" | sed -n '3p' | grep -q '^## ' && echo yes || echo no)"
chkTrue "title line leads with the type's first emoji" "$(printf '%s\n' "$h" | sed -n '3p' | grep -q '^## 👨🏻‍⚕️ ' && echo yes || echo no)"

# 6. eg1: the heading always ships WITH its rules, and the title is overridable because titles vary.
chk "heading block is 5 lines" "$(bash "$BR" done --heading | wc -l)" "5"
chk "line 1 and line 5 are the same rule" \
    "$(bash "$BR" done --heading | sed -n '1p')" "$(bash "$BR" done --heading | sed -n '5p')"
chk "lines 2 and 4 are blank" \
    "$(bash "$BR" done --heading | sed -n '2p;4p' | tr -d '\n')" ""
custom="$(bash "$BR" progress --heading --title '进展 · 数据基础与三种模式')"
chkTrue "custom title is used" "$(printf '%s' "$custom" | grep -q '## 🚀 进展 · 数据基础与三种模式' && echo yes || echo no)"
chkTrue "custom title keeps the type's emoji" "$(printf '%s' "$custom" | grep -q '🚀🏎️🚀🏎️' && echo yes || echo no)"
chkTrue "a title with a space and a middle dot survives intact" \
    "$(printf '%s' "$custom" | grep -q '数据基础与三种模式' && echo yes || echo no)"
chk "default title is used when --title is absent" \
    "$(bash "$BR" done --heading | sed -n '3p')" "## 🎉 本轮完成"

# 7. Width is configurable and the alternation still holds at the boundary.
chk "BR_WIDTH=4" "$(BR_WIDTH=4 bash "$BR" done)" "🎉🥳🎉🥳"
chk "BR_WIDTH=1 yields just the lead emoji" "$(BR_WIDTH=1 bash "$BR" done)" "🎉"
chk "an odd width ends mid-cycle rather than padding" "$(BR_WIDTH=3 bash "$BR" done)" "🎉🥳🎉"

# 8. Bad input is refused with a reason rather than emitting a wrong rule silently.
bash "$BR" nope >/dev/null 2>&1;            chk "unknown type exits 1" "$?" "1"
bash "$BR" >/dev/null 2>&1;                 chk "missing type exits 1" "$?" "1"
bash "$BR" done --sideways >/dev/null 2>&1; chk "unknown flag exits 1" "$?" "1"
bash "$BR" done --title >/dev/null 2>&1;    chk "--title with no value exits 1" "$?" "1"
BR_WIDTH=x bash "$BR" done >/dev/null 2>&1; chk "non-numeric BR_WIDTH exits 1" "$?" "1"
BR_WIDTH=0 bash "$BR" done >/dev/null 2>&1; chk "BR_WIDTH=0 exits 1" "$?" "1"
# Capture before matching: under `set -o pipefail` a pipeline whose PRODUCER exits non-zero returns
# non-zero regardless of whether grep matched, which would silently discard a passing check.
errtext="$(bash "$BR" nope 2>&1 || true)"
case "$errtext" in *"have: review, progress, decision, done"*) r=yes ;; *) r=no ;; esac
chkTrue "the error lists the valid types" "$r"

# 9. Any title adapts, by heuristic multi-keyword scoring rather than a first-match lookup.
infer(){ bash "$BR" --title "$1"; }
REVIEW="👨🏻‍⚕️🔍👩🏻‍⚕️👨🏻‍⚕️🔍👩🏻‍⚕️👨🏻‍⚕️🔍"
PROGRESS="🚀🏎️🚀🏎️🚀🏎️🚀🏎️"
DECISION="🔔⏰🔔⏰🔔⏰🔔⏰"
DONE="🎉🥳🎉🥳🎉🥳🎉🥳"

chk "完成 -> done"           "$(infer '本轮完成')"           "$DONE"
chk "进度 -> progress"       "$(infer '进度报告')"           "$PROGRESS"
chk "审查 -> review"         "$(infer 'review-gate 审查')"   "$REVIEW"
chk "决策 -> decision"       "$(infer '需要你决策')"          "$DECISION"
chk "状态 alone -> progress" "$(infer '状态')"               "$PROGRESS"
# REGRESSION: lowercasing with `tr` operates on BYTES and corrupts any CJK character with a byte in the
# A-Z range, which silently made 状态 match nothing. These are the CJK titles that exercise that path.
chk "CJK survives lowercasing: 状态"   "$(infer '状态')"   "$PROGRESS"
chk "CJK survives lowercasing: 进展"   "$(infer '进展')"   "$PROGRESS"
chk "CJK survives lowercasing: 审查"   "$(infer '审查')"   "$REVIEW"
chk "CJK survives lowercasing: 确认"   "$(infer '确认')"   "$DECISION"
chk "CJK survives lowercasing: 总结"   "$(infer '总结')"   "$DONE"
chk "复审 -> review"         "$(infer '第三轮复审结果')"       "$REVIEW"
chk "授权 -> decision"       "$(infer '等待授权')"            "$DECISION"
chk "Summary -> done"        "$(infer 'Deployment Summary')" "$DONE"
chk "Review (caps) -> review" "$(infer 'Round 2 Review')"    "$REVIEW"

# Splittable titles: separators become token boundaries so a compound title still matches.
chk "middle-dot separator"   "$(infer '进展 · 数据基础与三种模式')" "$PROGRESS"
chk "colon separator"        "$(infer '代码审查:第二轮')"          "$REVIEW"
chk "slash separator"        "$(infer '等待授权 / 阻塞项')"         "$DECISION"
chk "bracket separator"      "$(infer '[进度] 第三阶段')"          "$PROGRESS"

# Multi-keyword accumulation: the type mentioned MOST wins, not the one listed first internally.
# "阶段" and "进度" are both progress, "小结" is done, so progress should win 2 to 1.
chk "accumulates: 2 progress vs 1 done -> progress" "$(infer '阶段小结与后续进度')" "$PROGRESS"
# A single decision keyword beats a single progress keyword by the documented tie-break order.
chk "tie-break: decision outranks progress" "$(infer '进度确认')" "$DECISION"
chk "tie-break: review outranks done"       "$(infer '审查完成')" "$REVIEW"

# 10. An unmatched title is NOT bucketed into a neutral fifth category. It exits 3 and asks for a
#     deliberate choice among the four, because a silent neutral block defeats the point of the emoji.
out="$(bash "$BR" --title '部署清单' 2>&1)"; rc=$?
chk "an unmatched title exits 3" "$rc" "3"
case "$out" in *"cannot infer"*) r=yes ;; *) r=no ;; esac
chkTrue "the message says it could not infer" "$r"
for t in review progress decision done; do
  case "$out" in *"$t"*) r=yes ;; *) r=no ;; esac
  chkTrue "the message offers '$t' as a choice" "$r"
done
case "$out" in *"部署清单"*) r=yes ;; *) r=no ;; esac
chkTrue "the message echoes the title back with a worked example" "$r"
chkTrue "no neutral emoji is emitted on failure" \
  "$(printf '%s' "$out" | grep -q '📌📎📌📎' && echo no || echo yes)"

# An explicit type always works, including for a title nothing can infer.
chk "explicit type rescues an uninferable title" "$(bash "$BR" progress --title '部署清单')" "$PROGRESS"
chk "explicit type overrides a title that WOULD infer" "$(bash "$BR" review --title '本轮完成')" "$REVIEW"
chkTrue "an inferred block keeps its custom title" \
  "$(bash "$BR" --title '进展 · 数据基础与三种模式' --heading | grep -q '## 🚀 进展 · 数据基础与三种模式' && echo yes || echo no)"

bash "$BR" >/dev/null 2>&1; chk "no type and no title exits 1" "$?" "1"

echo
if [ "$fail" -eq 0 ]; then echo "blockrule.sh: all $pass checks PASS"; else echo "blockrule.sh: $fail FAIL / $pass pass"; fi
[ "$fail" -eq 0 ]
