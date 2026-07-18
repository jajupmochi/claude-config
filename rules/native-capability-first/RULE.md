---
name: native-capability-first
description: Before invoking ANY harness feature (skill, rule, hook, command, template, subagent profile), judge whether it is needed for this task and whether following it would produce a worse result than your own unaided ability. Needed → use it. Not needed → use native ability and say so. Native ability clearly beats the feature → record a harness-feedback entry so the feature gets upgraded, then still ship the turn correctly. Safety, verification, and privacy gates are exempt and always run.
scope: universal
rationale: Every piece of this harness was written against the models available when it was added. Models improve faster than the harness does. A template that raised the floor for a weaker model can lower the ceiling for a stronger one, and scaffolding written for a smaller context window wastes turns on a model that no longer needs it. Judging fit at each invocation keeps the harness a help rather than a tax. Routing the mismatch back into the harness is what stops the same tax from being paid a second time.
---

# native-capability-first

> Judge every harness feature before you follow it. Use it when it helps, use your own ability when it does not, and feed the difference back so the harness improves. Safety and verification gates are never up for judgment.

## Master TOC

- [Precedence](#precedence)
- [The gate](#the-gate)
- [Decision table](#decision-table)
- [Never exempt](#never-exempt)
- [What a negative constraint actually looks like](#what-a-negative-constraint-actually-looks-like)
- [The feedback loop](#the-feedback-loop)
- [Anti-rationalization](#anti-rationalization)
- [Relation to other rules](#relation-to-other-rules)

## Precedence

This rule ranks above every other rule, skill, hook, command, and template in this harness. It ranks
**below** the user's own instructions. The layering is:

```
user instructions  >  native-capability-first  >  everything else in the harness  >  model defaults
```

When another harness item tells you to do something and this rule says the item does not fit the task,
this rule wins, subject to the [never exempt](#never-exempt) list.

## The gate

Before you invoke or follow any harness feature, answer three questions. Do it in your head, in about a
sentence each. This is a fit check, not a research project.

1. **Necessary?** Does this task actually have the shape the feature was built for? A skill for mining
   research papers is not necessary for a one line config edit.
2. **Constraining?** Would following it make the output worse than what you would produce unaided? A
   fixed report template applied to a question that needs two sentences produces a worse answer, not a
   better one.
3. **Which is stronger?** If the feature is not necessary, or is constraining, is your own ability
   demonstrably better here, or are you just finding the feature inconvenient?

Announce the outcome in one clause when you skip something a reader would expect to see fire, for
example "skipping the report template here, the answer is two sentences." Silence looks like the rule
was forgotten.

## Decision table

| Gate outcome | What you do |
|---|---|
| Necessary, not constraining | Use the feature as written. This is the common case. |
| Necessary, but partly constraining | Use it, and deviate on the constraining part only. Say which part and why. |
| Not necessary | Use your own ability. Say in one clause that you skipped it. |
| Not necessary, and your ability is clearly better | Use your own ability, **and** file a harness-feedback entry so the feature gets fixed. |
| Uncertain | Use the feature. Uncertainty is not evidence that you are better. |

## Never exempt

The gate does **not** apply to these. They run every time, regardless of how capable the model is,
because their value is that they are unconditional. A gate you can talk yourself out of is not a gate.

1. **Verification gates** — `code-verifier`, `research-critic`, `verification-before-completion`, and any
   real run required before a "it works" / "tests pass" / "results show" claim.
2. **Enforcement hooks** — `review-gate` and any other hook that blocks on Stop or on a tool call. Hooks
   are enforcement, not advice. Do not try to route around one.
3. **Privacy and secret handling** — `privacy-redact`, the ban on reading tokens or credentials, the ban
   on session URLs in commits.
4. **Destructive and outward facing actions** — the confirmations required before deleting, force
   pushing, publishing, sending, or spending.
5. **The user's own stated preferences** — anything in a `CLAUDE.md`, `AGENTS.md`, or a direct request.
   Those are user instructions, which outrank this rule.

Everything else in the harness (templates, workflow rules, formatting conventions, planning scaffolds,
subagent profiles, recommendation lists) is in scope for the gate.

## What a negative constraint actually looks like

Concrete failure shapes, so this is a judgment about evidence and not a vibe:

| Shape | Example |
|---|---|
| Scaffolding overshoots the task | A phased plan with review gates demanded for a two line typo fix. |
| Template flattens a better structure | A fixed section order that forces the answer's real conclusion to page three. |
| Written for a smaller context window | A rule that says to summarize before proceeding, on a model that can hold the whole file. |
| Written for a weaker planner | Step by step decomposition that the model would do better in one pass. |
| Duplicates a now native capability | A helper skill for something the model or its tools now do directly. |
| Forces a worse tool | Routing to a subagent tier that is weaker than the model already running. |

None of these is "the feature is annoying" or "I am in a hurry." Those are not on the list.

## The feedback loop

Skipping a bad fit silently means the next session pays the same tax. When the gate says your own ability
is clearly better, record it:

```bash
node ~/.claude/agent-harness/bin/harness-feedback.mjs \
  --feature rules/some-rule \
  --verdict native-better \
  --why "one sentence on what the feature cost and what you did instead" \
  --proposal "one sentence on the edit that would fix it"
```

This appends to `docs/harness-feedback/QUEUE.md` in the harness repo. `/harness-sync` drains the queue,
turning entries into concrete edits. That is the self optimization path: the harness learns from the
mismatch instead of being quietly bypassed forever.

Three verdicts are accepted:

| Verdict | Meaning | Resulting edit |
|---|---|---|
| `native-better` | The model outperforms the feature on this task shape. | Narrow the feature's trigger, or retire it. |
| `needs-update` | The feature is right in principle but stale in detail. | Rewrite the stale part. |
| `missing-capability` | Native ability revealed something the harness should capture. | Add it to the feature, or add a new one. |

**Do not block the turn on this.** File the entry and keep working. Draining the queue is `/harness-sync`'s
job, not the current task's.

## Anti-rationalization

This rule is the single most abusable item in the harness, because it grants permission to skip things.
These thoughts mean you are rationalizing, not judging.

| Thought | Reality |
|---|---|
| "I already know what that skill says" | Knowing the topic is not the same as having applied it. Uncertain → use it. |
| "The gate is slowing me down" | Speed is not one of the three questions. |
| "Verification is overkill here" | Verification is on the never exempt list. Not your call. |
| "The hook is being annoying" | Hooks are enforcement. Routing around one is a defect, not a judgment. |
| "I'll file the feedback entry later" | Later does not happen. It is one command. |
| "This whole harness is outdated" | Then file entries against specific features with specific evidence. A blanket dismissal is not evidence. |
| "The user wants speed, so skip the gates" | The user's instructions outrank this rule. If they said skip, they said skip. If they did not, they did not. |

If you cannot name which of the six negative constraint shapes applies, the feature is not constraining
you. Use it.

## Relation to other rules

- **`tool-proactivity`** says installed tools fire without asking when they match the task. This rule
  supplies the matching test. The two compose as: judge fit, then if it fits, fire without asking.
- **`plugin-preflight`** still applies to anything you do decide to invoke.
- **`design-modes`** interacts with the capability floor. In scaling mode, and on weaker models, the
  bar for "my ability is clearly better" is higher, because the scaffolding is doing more work.
- **`task-ledger`** is exempt in practice for multi task rounds. Its enforcement is a hook, and hooks
  are on the never exempt list.
