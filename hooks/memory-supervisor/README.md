# memory-supervisor

> Records each round into the project's memory automatically, so the flywheel spins without the agent remembering to turn it.

## Master TOC

- [What it does](#what-it-does)
- [Why it is a hook and not a habit](#why-it-is-a-hook-and-not-a-habit)
- [Install](#install)
- [Enabling it](#enabling-it)
- [Where memory lands](#where-memory-lands)

## What it does

A `Stop` hook that reads the stop payload's `transcript_path`, extracts the round deterministically, and
records it through `mem.py`. No model call is involved: the script is plumbing, and the recorded content
is the model's own verbatim turn.

The script itself lives with the skill it belongs to, at
[`skills/memory-flywheel/scripts/supervise.py`](../../skills/memory-flywheel/scripts/supervise.py). This
hook directory ships only the registration, so there is one copy of the code rather than two.

## Why it is a hook and not a habit

`skills/memory-flywheel` shipped tested and working, and had recorded **zero** rounds. Nothing invoked it.
Asking an agent to remember to record its own memory is asking the failing component to fix itself, which
is the same reason `task-ledger` is a hook rather than a rule.

## Install

```bash
node bin/deploy-hooks.mjs --apply --hook memory-supervisor --enable-new
```

`--enable-new` is required because this hook is off until you ask for it. The deployer never turns on a
hook you have not opted into.

## Enabling it

Off by default even once registered. Turn it on with either:

- `AGENT_HARNESS_MEM_SUPERVISE=1` in the environment, or
- a `supervise=on` line in `supervise.conf` next to the deployed script.

Every path is guarded and non-fatal; an error is logged to the memory root rather than crashing the turn.

## Where memory lands

`<project>/.agent/memory/`, beside the task ledger. Memory belongs with the project it is about, so it
survives being copied to another machine and shows up in a diff, rather than accumulating in a hidden
home folder nobody looks at.

| Layer | Path | Granularity |
|---|---|---|
| Index | `.agent/memory/INDEX.md` | Coarse: one line per round |
| Rounds | `.agent/memory/rounds/NNNN-round.md` | Fine: the verbatim round |
