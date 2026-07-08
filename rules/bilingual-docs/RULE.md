---
name: bilingual-docs
description: Every human-facing repo doc ships as NAME.md (English canonical) + NAME.zh.md (Chinese mirror), with a one-line language switcher header. Code, identifiers, filenames stay English in both versions.
scope: optional
rationale: Author has bilingual users (or himself reads both). Two side-by-side files are clearer than mixed-language docs and let either language stay canonical for tooling. The setup skill asks per-project whether to opt in.
---

# bilingual-docs

> Every human-facing repo doc ships as `NAME.md` (English canonical) + `NAME.zh.md` (Chinese mirror), side-by-side.

## Master TOC

- [Rule](#rule)
- [Why](#why)
- [Format](#format)
- [What to translate](#what-to-translate)
- [Exceptions](#exceptions)
- [Opt-in](#opt-in)

## Rule

Every repo-level human-facing doc MUST ship in both English and Chinese as **two separate files**:

- `NAME.md` — English, canonical
- `NAME.zh.md` — Chinese mirror

Both files MUST include a one-line language switcher at the top:

- In `NAME.md`: `> **Language:** English | [中文](NAME.zh.md)`
- In `NAME.zh.md`: `> **语言：** [English](NAME.md) | 中文`

Adding a new top-level human-facing doc → MUST add both files in the same edit batch.

## Why

For users (or authors) who read both languages, two side-by-side files are clearer than mixed-language docs. Either language can stay canonical for tooling (search, link-checking, automated translation diff). The mirror is human-friendly without breaking machine consumption.

## Format

```markdown
# Title

> One-sentence purpose.

> **Language:** English | [中文](TITLE.zh.md)

## Master TOC

- ...
```

The Chinese mirror has the same structure — same headings, same TOC anchor IDs, same code blocks — only prose is translated.

## What to translate

- Translate: prose, headings, ordinary text
- Don't translate: code, identifiers, filenames, JSON / YAML keys, URLs, hierarchy IDs (`H1.M2.G3.T4`), status markers (`[✓][~][ ]`)

## Exceptions

- `CLAUDE.md` (Claude is the primary reader; English-only is fine)
- `CLAUDE.local.md` (private file)
- `SKILL.md`, `RULE.md`, hook READMEs (Claude is the primary reader)
- Internal-only research notes, scratch files

## Opt-in

This rule is **opt-in per project** — the `setup/init-agent-harness` skill (P8) asks at scaffold time:

- "需要双语文档吗？(English ↔ Chinese)"
- "主要语言（canonical）是什么？"
- "哪些文件要双语化？(README, INVENTORY, ...)"

If the user opts in, the rule's `snippet.md` gets imported into the new project's `CLAUDE.md` and template docs are scaffolded with the bilingual switcher header.
