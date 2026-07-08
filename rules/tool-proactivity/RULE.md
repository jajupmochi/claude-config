---
name: tool-proactivity
description: Installed plugin / skill / MCP / subagent fires without asking when the task matches; announce briefly before firing. Destructive ops and SEO audits still need explicit approval.
scope: personal
rationale: Asking "should I use chrome-devtools?" every time wastes a round-trip when the user has already pre-authorized "use installed tools when they fit." But destructive ops and expensive audits should still pause.
---

# tool-proactivity

> Installed tools fire without re-asking when the task matches. Destructive ops and expensive audits remain explicit-approval.

## Master TOC

- [Rule](#rule)
- [Why](#why)
- [Default-fire examples](#default-fire-examples)
- [Always-ask exceptions](#always-ask-exceptions)
- [Format](#format)

## Rule

**Invoke installed skills, plugins, subagents, and MCP tools proactively** when they match the task. Don't wait for the user to type the slash command — if `chrome-devtools` is relevant to a visual-verify task, just run it. Briefly announce which tool you're using and why (one sentence) before firing, so the user can veto.

This rule still respects `plugin-preflight` (verify installed + not deprecated) for first-time-this-session invocations.

## Codex Plugins

For Codex-specific plugin recommendations, see [`recommendations/codex-plugins.md`](../../recommendations/codex-plugins.md). The same auto-invocation rules apply to Codex plugins (superpowers, chrome-devtools, figma, replayio, etc.).

## Why

If the user has installed `frontend-design`, `chrome-devtools`, `playwright`, etc., they have already implicitly authorized "use these when they fit." Asking each time is friction that compounds across a long session.

The "I don't remember my tools" excuse is not valid — before picking an approach, check the current skill / plugin / agent list. If something better than raw tool calls exists, prefer it.

## Default-fire examples

- Visual verify task → `chrome-devtools` MCP fires
- Need to commit + push + open PR → `/commit-push-pr` fires
- Code review → `/code-review` or `coderabbit` plugin fires
- Format Python → ruff via the configured `PostToolUse` hook fires (deterministic; no announce needed)

## Always-ask exceptions

These OVERRIDE the proactivity default — always ask first:

1. **Destructive git / file ops** (`git reset --hard`, `rm -rf`, `git push --force`, branch deletion) — explicit approval only.
2. **SEO audit skills/plugins** (`searchfit-seo:seo-audit`, manual SEO audits of HTML files) — produce long reports that bloat context. Always ask "要不要跑一次 SEO audit？" / "Run an SEO audit?".
3. **Long-running expensive ops** (full-repo scan, multi-page WebFetch sequence, large model invocation) — flag estimated cost first.

## Format

Before firing:

```
我用 <tool-name> 来 <one-line purpose>。
[tool invocation]
```

This single sentence gives the user the chance to interrupt before the tool runs.
