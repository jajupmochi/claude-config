---
name: autopilot
description: Set up or manage the autopilot daily autonomous project-driver. Configures a daily timer that runs a fresh autorun session to advance a project (features, bug fixes, refactors, design, docs). Use when the user wants to "set up autopilot", schedule autonomous daily work, or configure/inspect the autopilot tool.
policy:
  allow_implicit_invocation: false
---

# autopilot

> Read `../general/autopilot/SKILL.md` for the full Claude source. This
> Codex wrapper maps the autopilot workflow to Codex tooling.

## Codex-specific mappings

| Claude tool | Codex equivalent |
|---|---|
| Claude bash with run_in_background: true | `exec_command` background session |
| Claude Monitor | `write_stdin` polling |
| Claude session timer | Codex cron / scheduled goal |
| /autopilot setup | `/autopilot setup` (same syntax) |

## Quick start

```
/autopilot setup <project-path>
```

The skill reads the full autopilot design from
`docs/autopilot/README.md` and the run prompt from
`docs/autopilot/PROMPT.md`.

## Codex schedule integration

For daily automation, create a Codex goal with `--repeat daily`:

```bash
codex goal create --repeat daily "autorun: advance <project> according to autopilot PROMPT.md"
```
