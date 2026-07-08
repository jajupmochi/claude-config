---
name: end-of-turn-marker
description: Every turn MUST end with a visible divider header followed by numbered summary items. Use [END:FINAL], [END:WAIT], or [END:NEEDS_USER] embedded in the divider.
policy:
  allow_implicit_invocation: true
---

# end-of-turn-marker

Every user-facing turn ends with a divider block. The divider is the SECTION HEADER. Numbered summary items follow below it.

## Format

```
━━━━━━━━━━━━━━━━━━━━
✅ 完成 · Complete
━━━━━━━━━━━━━━━━━━━━
1. First change or fix
2. Second change or fix
3. Third change or fix
```

OR:

```
━━━━━━━━━━━━━━━━━━━━
🤚 需要用户 · Needs User
━━━━━━━━━━━━━━━━━━━━
1. 需要确认：merge 到 main？
2. 有 3 个文件未提交，是否推送？
```

OR:

```
━━━━━━━━━━━━━━━━━━━━
⏳ 等待中 · Waiting
━━━━━━━━━━━━━━━━━━━━
1. dev server 运行在 port 3000
2. 等待测试完成后继续
```

## Rules

1. The divider block is ALWAYS at the very end of the turn
2. Numbered items follow the divider, one per line
3. Use [END:FINAL], [END:WAIT], or [END:NEEDS_USER] as the LAST line after all items
4. Never put content AFTER the [END:*] marker
5. If review-gate fires, its output replaces/supplements the summary items

## Integration with review-gate
The review-gate Stop hook output should format neatly with the marker divider.
