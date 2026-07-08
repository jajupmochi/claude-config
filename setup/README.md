# Setup

> The "install / scaffold" skills that compose `agent-harness` into a fresh project. Inspired by mattpocock's `setup-matt-pocock-skills` pattern.

## Master TOC

- [How to use](#how-to-use)
- [Skill index](#skill-index)
- [Adding a new setup skill](#adding-a-new-setup-skill)

## How to use

In a new (or existing) project where you want to apply the `agent-harness` conventions:

```
/init-agent-harness
```

The skill will ask about the project's type, language preferences, and which categories of tools to install, then compose the right subset of rules / hooks / skills / templates / tooling into the project.

For a fresh / empty directory, this fully scaffolds the project. For an existing project, it adds agent-harness's conventions on top without overwriting your code.

## Skill index

| Skill | Purpose |
|---|---|
| [`init-agent-harness`](init-agent-harness/SKILL.md) | Compose a project's `CLAUDE.md` + `.claude/settings.json` + skills from selected categories. Asks about project type, language, context tags. |

## Adding a new setup skill

If you build alternative setup flows (e.g., a custom-template-based variant), add them here under `setup/<skill-name>/SKILL.md`. Keep the core `init-agent-harness` skill intact — it's the canonical entry point.
