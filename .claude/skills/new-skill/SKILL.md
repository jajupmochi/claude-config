---
name: new-skill
description: Scaffold a new skill under skills/<bucket>/<kebab-name>/. Creates SKILL.md with proper frontmatter, plus updates INVENTORY.md and skills/README.md in the same edit batch.
---

# /new-skill

Scaffold a new skill following the Claude Code SKILL.md spec.

## Usage

```
/new-skill <bucket>/<kebab-name>
```

E.g.: `/new-skill general/find-duplicates` or `/new-skill research-pkg/new-experiment`

## Pre-flight

- Verify `skills/<bucket>/<kebab-name>/` does not already exist
- Verify `<bucket>` is one of: `general/`, `research-pkg/`, `static-site/`, `productivity/`, `personal/` — or ask the user to add a new bucket if needed

> ⚠️ **Claude Code plugin discovery is TOP-LEVEL only.** CC auto-discovers `skills/<name>/SKILL.md` **one level
> deep** — it does NOT scan `skills/<bucket>/<name>/`. So a skill you want Claude to auto-discover MUST live at
> the top level `skills/<kebab-name>/` (like `memory-flywheel`, `tui-installer`, `figma-design-fetch`). The
> `skills/general/*` copies are reached by Codex (`skills/` glob) and opencode (deploy-skills), NOT by the CC
> plugin. If the skill should be Claude-discoverable, create it at `skills/<kebab-name>/` (bucket is then just
> an organizational tag in INVENTORY, not a path level).

## Steps

1. **Create directory**:

   ```bash
   mkdir -p skills/<bucket>/<kebab-name>
   ```

2. **Ask the user** for:
   - One-line description (becomes `description:` frontmatter — this is what Claude reads to decide auto-invocation)
   - Trigger: `auto` (Claude invokes when matched) / slash-only (user must type `/<name>`) / both
   - Skill body content — what does the skill do?

3. **Write `skills/<bucket>/<kebab-name>/SKILL.md`**:

   ```markdown
   ---
   name: <kebab-name>
   description: <one-line — be specific; this is what Claude matches against>
   <if user-only:> disable-model-invocation: true
   ---

   # /<kebab-name>

   <opening summary line>

   ## Master TOC

   - [Pre-flight](#pre-flight)
   - [Steps](#steps)
   - [Notes for the agent](#notes-for-the-agent)
   - [Companion](#companion)

   ## Pre-flight

   <any verification, e.g. plugin-preflight checks>

   ## Steps

   1. <step>
   2. <step>
   ...

   ## Notes for the agent

   <gotchas, anti-patterns, things to avoid>

   ## Companion

   <related rules / skills / hooks>
   ```

4. **Update `skills/README.md`** — add a row to the skill index table.

5. **Update `INVENTORY.md` AND `INVENTORY.zh.md`** — add a row to the Skills section.

6. **Show the user** the diff and ask for confirmation before committing.

## Frontmatter conventions

- `name` — kebab-case, matches the directory name
- `description` — be specific about WHEN the skill fires. Claude uses this to decide auto-invocation. Vague descriptions cause both false positives and false negatives.
- `disable-model-invocation: true` — set for skills with side effects (deploy, force-push, etc.) that should only fire on explicit user request

## Companion

- `docs/CONTRIBUTING.md` §"Adding a skill" — formal spec
- `skills/README.md` — index of all skills + bucket conventions
- Anthropic's `skill-creator` plugin — for more sophisticated skill authoring with evals
