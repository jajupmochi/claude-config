# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working **on** this repository (i.e. editing the library itself, not consuming it from a downstream project).

## Master TOC

- [Project](#project)
- [Authoritative references](#authoritative-references)
- [Bilingual policy (this repo)](#bilingual-policy-this-repo)
- [Structural conventions](#structural-conventions)
- [Inventory must stay in sync](#inventory-must-stay-in-sync)
- [Commits](#commits)
- [Out of scope](#out-of-scope)

## Project

`agent-harness` — Linlin Jia's curated Claude Code configuration library. The library's *content* (rules, skills, hooks, recommendations, tooling, templates) is meant to be consumed by other projects. **This `CLAUDE.md` governs edits to the library itself.**

## Authoritative references

Read these first rather than re-deriving:

- `docs/PHILOSOPHY.md` — the *why* behind every rule/hook/skill we ship
- `docs/CONTRIBUTING.md` — how to add a new rule, skill, hook, recommendation, or template
- `docs/CONSUMPTION.md` — the three downstream consumption modes the library supports
- `INVENTORY.md` — the master index; **must stay in sync with the actual filesystem state**
- Each `rules/<name>/RULE.md` and `skills/<bucket>/<name>/SKILL.md` is canonical for that item

## Bilingual policy (this repo)

- **Top-level docs** (`README`, `INVENTORY`, `docs/PHILOSOPHY`, `docs/CONSUMPTION`) ship as `NAME.md` (English, canonical) + `NAME.zh.md` (Chinese mirror), with a header line: `> **Language:** English | [中文](NAME.zh.md)` (or the mirror).
- **Content modules** (`RULE.md`, `SKILL.md`, `hooks/*/README.md`, `docs/CONTRIBUTING.md`, etc.) stay **English only** — Claude is the primary reader.
- Adding a new top-level doc → MUST add both files in the same edit batch.
- This library does NOT enforce bilingual policy on consumer projects. That's the `rules/bilingual-docs/` rule, opted-in per project at `setup/init-agent-harness` time.

## Structural conventions

- Every markdown file starts with `# Title`, then `> One-line purpose.`, then `## Master TOC`.
- Directory naming: `kebab-case`. Names with proper nouns keep their casing (rare).
- Frontmatter format for `RULE.md` and `SKILL.md`: see `.claude/skills/new-rule/SKILL.md` and `.claude/skills/new-skill/SKILL.md` (added in Phase 9).
- Don't break links — when renaming, grep for the old path in `INVENTORY.md` and other docs.

## Inventory must stay in sync

`INVENTORY.md` and `INVENTORY.zh.md` are **manually maintained** until Phase 9 ships an auto-gen skill. When adding, removing, or renaming a rule/skill/hook/recommendation/template, update both INVENTORY files in the same edit batch as the content change.

## Commits

- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`.
- One commit per logically distinct change. Don't split inventory updates from the content change they describe.
- One commit per phase during the initial build (P1 commit, P2 commit, ...).
- Don't commit unless the user explicitly asks.
- **Never put a `https://claude.ai/code/session_<id>` URL in a commit message or PR body.** This repo is **public**; that link is account-scoped (nobody else can open it), so it only leaks a private session id into public history as clutter. Keep the `Co-Authored-By:` attribution line if used, but drop the `Claude-Session:` trailer and any PR-body session line.
- **Address the Copilot review after every PR.** GitHub Copilot auto-posts a "Pull request overview" + inline comments on each PR. After creating/merging a PR, fetch Copilot's findings (`gh api repos/<org>/<repo>/pulls/<n>/comments` for inline, `.../reviews` for the overview), analyze each, and **fix the real ones** (skip false-positives, noting why). The fix is itself a PR that Copilot reviews too. **Recursion guard — MANDATORY to avoid an infinite fix→review→fix loop:** at most **2 rounds** of Copilot-driven fixing per originating change, OR stop as soon as Copilot raises **no new actionable findings** — whichever comes first. Never loop past 2 rounds.
- **Fold Copilot's recurring review criteria back into `review-gate`.** After analyzing a batch of Copilot findings, extract the *generalizable* ones (a review THEME Copilot keeps flagging — e.g. "doc/message/name accuracy", "quoting & regex-metachar robustness", "validate input before path/command interpolation") and add them as review forms in `hooks/review-gate/scripts/gate.sh`, so review-gate catches that class proactively next turn instead of waiting for Copilot post-hoc. This closes the loop: each Copilot sweep should make review-gate a little stronger. (Forms 9–10 were added this way, tagged "a GitHub-Copilot-recurring miss".)

## Out of scope

- **Don't rewrite the global `~/.claude/CLAUDE.md`.** That file is the **input** to this library (P2 distills it). Edits to the global file belong in a different session, not here.
- **Don't write content under `rules/`, `skills/`, `hooks/` etc. without checking `INVENTORY.md` first** — duplicate entries will drift apart.
- **Don't pull entries from upstream skill collections** (`.orchestra/skills/`, `.agents/skills/`, `huggingface-skills`, etc.) into this repo. Reference them from `recommendations/` instead — those are upstream-maintained and we shouldn't fork them.
