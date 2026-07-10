# typecheck-on-edit

> `PostToolUse:Write|Edit` hook. After Claude writes/edits a `.ts`/`.tsx` file, `prettier --write` it, then
> typecheck its project with `tsc --noEmit`. **Type errors exit 2 → the turn is blocked and the errors are
> shown to Claude**, so a type-broken edit can't pass silently. Deterministic, no LLM.

## What it does

1. Reads the edited file path from the `PostToolUse` payload.
2. No-op unless the file is `.ts`/`.tsx` **and** sits in a project with a `tsconfig.json` **and** a usable `tsc`.
3. `prettier --write <file>` (project-local prettier, best-effort — never blocks).
4. `tsc --noEmit -p tsconfig.json` at the project root. On type errors: prints them and **`exit 2`** (blocks).

Uses the **project-local** `node_modules/.bin/tsc` (falls back to a global `tsc`); it never auto-downloads, and
a project with no TypeScript is a **no-op** (won't block). `TSC` / `PRETTIER` are env-overridable (used by tests).

## Why

This is the "deterministic quality spine" of the Figma→code pipeline (see the `figma-design-fetch` skill): the
reliability of design-to-code comes less from the MCP than from (a) a token-mapped component library, (b) a
fixed agent workflow with a mandatory verification gate, and (c) **non-LLM deterministic hooks** like this one.
A typecheck that blocks on `exit 2` keeps generated UI code compiling as the agent iterates.

## Install

Merge `settings.snippet.json` into your project's `.claude/settings.json` (or `~/.claude/settings.json`). Adjust
the script path if agent-harness is not at `~/.claude/agent-harness`.

## Test

```bash
bash hooks/typecheck-on-edit/test_typecheck.sh
```

Verifies the `exit 2` wiring with an injected fake `tsc`, and (best-effort, needs network to install
`typescript`) an end-to-end run against real `tsc`: a genuine type error exits 2, a clean file exits 0.
