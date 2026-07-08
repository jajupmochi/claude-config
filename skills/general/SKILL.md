---
name: agent-harness-general
description: Audit the source agent-harness general skill catalog. Use only when maintaining or adapting this repository's original reusable skill set.
---

# agent-harness general skill catalog

This directory is the source catalog used by Claude Code and by the Codex
wrappers in sibling top-level skill directories.

When maintaining the catalog:

1. Read `../README.md` and `../../INVENTORY.md` before changing entries.
2. Keep each source skill under `general/<skill-name>/SKILL.md`.
3. Keep the top-level Codex wrapper with the same skill name in sync when a
   source skill changes.
4. Do not move these source folders unless the Claude manifest and setup skill
   are updated in the same change.

Source skills:

- `general/verify-template/SKILL.md`
- `general/preview-template/SKILL.md`
- `general/long-running-tasks/SKILL.md`
- `general/verify-visual/SKILL.md`
- `general/privacy-redact/SKILL.md`
- `general/code-verifier/SKILL.md`
- `general/research-critic/SKILL.md`
- `general/system-cleanup/SKILL.md`
- `general/autoresearch-toolfinder/SKILL.md`
- `general/autopilot/SKILL.md`
