# block-env-read

> `PreToolUse:Read` hook. Denies reading `.env` / `.env.*` / `*.env` files so secrets never enter the
> transcript. Blocking edits happen via `exit 2`; Claude is told why. Deterministic, no LLM.

## What it does

On a `Read` tool call, if the target's basename is `.env`, `.env.<something>`, or `*.env`, it prints a reason
and **`exit 2`** (blocks the read). Any other path is a no-op.

## Why

Part of the Figma→code pipeline's deterministic-hook spine (see the `figma-design-fetch` skill): design-to-code
work touches real frontend repos that carry API keys in dotenv files. A hard block keeps them out of context.

## Scope

Covers the **Read** tool (the common vector). Reading `.env` via a Bash command (`cat .env`) is not covered
here — pair with a permissions allowlist if you need that. **Secret-free templates are allowed**:
`.env.example`, `.env.sample`, `.env.template`, `.env.dist`, and `.env.*.example` are readable (the agent often
needs them to learn which variables a project expects); real dotenv files (`.env`, `.env.local`,
`.env.production`, …) are blocked.

## Install

Merge `settings.snippet.json` into your project's `.claude/settings.json`. Adjust the script path if
agent-harness is not at `~/.claude/agent-harness`.

## Test

```bash
bash hooks/block-env-read/test_block_env.sh
```
