## Native capability first (highest precedence in this harness)

Before invoking or following ANY harness feature — skill, rule, hook, command, template, subagent profile — run a three question fit check:

1. **Necessary?** Does this task have the shape the feature was built for?
2. **Constraining?** Would following it produce a worse result than your own unaided ability?
3. **Which is stronger?** If it does not fit, is your ability demonstrably better here, or is the feature merely inconvenient?

| Gate outcome | Action |
|---|---|
| Necessary, not constraining | Use it as written (the common case). |
| Necessary, partly constraining | Use it, deviate on that part only, say which and why. |
| Not necessary | Use native ability. Say in one clause that you skipped it. |
| Not necessary and native is clearly better | Use native ability **and** file a harness-feedback entry. |
| Uncertain | Use the feature. Uncertainty is not evidence that you are better. |

**Never exempt — these run every time, no gate:** verification gates (`code-verifier`, `research-critic`, real-run-before-claiming); enforcement hooks (`review-gate`, any blocking hook); privacy and secret handling; destructive or outward facing confirmations; the user's own stated instructions (they outrank this rule).

**Feed the mismatch back** so the next session does not pay the same tax:

```bash
node ~/.claude/agent-harness/bin/harness-feedback.mjs --feature <path> \
  --verdict native-better|needs-update|missing-capability \
  --why "<what it cost, what you did instead>" --proposal "<the edit that fixes it>"
```

Filing never blocks the turn. `/harness-sync` drains the queue into real edits.

**Precedence:** user instructions > this rule > everything else in the harness > model defaults.
