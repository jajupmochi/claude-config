---
name: tui-installer
description: Use to install (or just plan) the recommended terminal/TUI stack for driving multiple AI coding agents on Ubuntu — zellij + claude-squad + lazygit + delta. Dry-run by default (prints the plan, installs nothing); --apply asks y/N per tool. When onboarding agent-harness, offer to run --check and ask before installing anything.
policy:
  allow_implicit_invocation: true
---

# tui-installer

Overhaul task 8 (installer half). Turns the recommendation in `recommendations/tui-for-agents.md` into a
runnable, **ask-first** installer. Nothing installs unless the user opts in.

## Use

```
bash scripts/install-tui.sh --check    # report what's installed vs missing
bash scripts/install-tui.sh            # dry-run: print the install plan, install NOTHING (default)
bash scripts/install-tui.sh --apply    # install missing tools, asking y/N per tool
```

The recommended stack (see the recommendation doc for why): **zellij** (multiplexer), **claude-squad** (agent
orchestrator, git-worktree isolation), **lazygit** (diff review + staging), **delta** (highlighted diffs).
Tools without a clean apt/cargo package (claude-squad, lazygit on some distros) are marked `MANUAL:` with the
upstream install URL rather than a fabricated command.

## Onboarding behavior (task 8)

When applying agent-harness to a machine, run `--check` and **ask the user whether to install** the missing
TUI tools — never install unprompted. Re-check periodically (or when the recommendation doc changes) and ask
again if a better tool appears; keep the tool list in sync with `recommendations/tui-for-agents.md`.

## Why dry-run default + fake-install seam

Installing system tools is side-effectful, so the default only *plans*. The detection is testable without
touching the system via `TUI_FAKE_INSTALLED="zellij delta"` (used by `test_install_tui.sh`, 11/11). The actual
package installs are the only non-deterministic part and stay behind `--apply` + a y/N prompt.

Status: v0.1 (check / dry-run plan / apply-with-prompt, tested). Planned: keep the tool table generated from
the recommendation doc, and a "notify when a better tool ships" tie-in with `agent-update-watcher`.
