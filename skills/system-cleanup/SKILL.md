---
name: system-cleanup
description: Diagnose and plan Linux disk cleanup from Codex using the source agent-harness system-cleanup skill. Use when disk space is low, the user asks to free space, or a data disk or mount is read-only. Advises first and requires confirmation before destructive or sudo cleanup.
---

# system-cleanup

Codex wrapper for `skills/general/system-cleanup/SKILL.md`.

Before acting, read the source skill completely. Resolve the path relative to this wrapper first:

- `../general/system-cleanup/SKILL.md`
- `../general/system-cleanup/cleanup.sh` if the user wants the interactive script

Follow the source skill posture: diagnose first, report the space picture with risk labels, do safe user-level cleanup only after explicit approval, and hand sudo or destructive commands to the user unless they clearly authorize running them in the current environment.
