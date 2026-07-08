---
name: end-of-turn-marker
description: Every turn MUST end with one of three markers in a visible divider block: [END:FINAL], [END:WAIT], or [END:NEEDS_USER]. The marker format uses box-drawing characters for visibility.
policy:
  allow_implicit_invocation: true
---

# end-of-turn-marker

> Every user-facing turn ends with exactly one marker in a visible divider block.

Source rule: `rules/end-of-turn-marker/RULE.md`

## The three markers

Display each marker in its own prominent block at the very end of EVERY turn:

### [END:FINAL] — Task complete

```
━━━━━━━━━━━━━━━━━━━━
✅ 完成 · Complete
━━━━━━━━━━━━━━━━━━━━
[END:FINAL]
```

### [END:WAIT] — Background work continues

```
━━━━━━━━━━━━━━━━━━━━
⏳ 等待中 · Waiting
<what is being awaited>
━━━━━━━━━━━━━━━━━━━━
[END:WAIT]
```

### [END:NEEDS_USER] — User input required

```
━━━━━━━━━━━━━━━━━━━━
🤚 需要用户 · Needs User
<what decision is needed>
━━━━━━━━━━━━━━━━━━━━
[END:NEEDS_USER]
```

## Usage

After every turn, add the appropriate marker block as the LAST content. Never put text after it. Never use multiple markers in one turn.

## Integration

- The `review-gate` Stop hook automatically emits a formatted review block with the correct marker
- Codex should append the marker block at the end of every visible turn output
- The marker helps the user and downstream automation understand session state
