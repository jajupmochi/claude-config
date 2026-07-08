# Philosophy

> Why these rules exist. The "why" is what makes them stick — without it, every new project re-invents them, and the lessons of the previous project don't carry forward.

> **Language:** English | [中文](PHILOSOPHY.zh.md)

## Master TOC

- [Origin](#origin)
- [Three core tensions](#three-core-tensions)
- [Conventions adopted](#conventions-adopted)
- [Conventions rejected](#conventions-rejected)
- [Living document](#living-document)

## Origin

Across half a dozen projects (`liulian-python`, `swiss-river-network-benchmark`, `AI_Mur4Cast`, `jajupmochi.github.io`, etc.) the same Claude Code rules kept getting re-invented:

- "Plan before implementing"
- "Use uv + ruff for Python"
- "Bilingual docs for human-facing content"
- "Format on `PostToolUse:Write|Edit`"
- "Authoritative references" section pointing at sub-docs
- Conventional Commits

Each project's CLAUDE.md drifted slightly from the others. New projects copy-pasted rules from the most-recent project (which had inherited from the one before it). Bugs propagated. Improvements didn't.

This library is the consolidation. The cost of one shared distillation is paid once; every new project benefits.

## Three core tensions

### 1. Speed vs. control

Claude is fastest when fully autonomous. But destructive ops, mid-session refactors, and over-eager skill invocation cost real human review cycles.

**Resolution:** explicit "go" gates for destructive / hard-to-reverse / cross-file edits; auto-fire for tools that match a routine task; an opt-in `tool-proactivity` rule for cases where the user wants more autonomy.

### 2. Density vs. discoverability

A 5-page CLAUDE.md captures everything but Claude won't load it all into working memory. A one-page CLAUDE.md is loaded in full but misses cases.

**Resolution:** keep CLAUDE.md minimal — apply the "would Claude get this wrong" test to every line. Push verbosity into linked rules / skills / `@imports`. Use `INVENTORY.md` as the navigable index.

### 3. Project-specific vs. universal

Static-site rules (i18n parity, bilingual docs, visual verification) don't apply to ML research packages. Universal rules (plan-before-edit, Chinese output) apply to everything.

**Resolution:** every rule has a `scope:` field in its frontmatter (e.g. `universal`, `python-research`, `static-site`, `ml-experiment`). The `setup/init-agent-harness` skill asks the user which scopes apply per new project, and only writes those rules in.

## Conventions adopted

These show up across nearly all of Linlin's projects and are worth standardizing:

- **Conventional Commits** — `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`.
- **uv + ruff** for all Python — no `pip`, no `black`. Even when `pyproject.toml` still has a `[tool.black]` block, ruff is canonical.
- **`pyproject.toml` extras** for optional deps with `ImportError` capture and helpful install hint.
- **Master TOC** on every markdown file.
- **`NAME.md` + `NAME.zh.md`** for human-facing docs (opt-in per project).
- **`PostToolUse: Write|Edit`** format hook (Python: ruff; JSON: jq).
- **chrome-devtools MCP** for visual verification on UI work.
- **Phased planning** for non-trivial tasks.
- **Pre-edit confirmation** with explicit "go".
- **Authoritative references** pointer in CLAUDE.md (don't re-derive what's in a sub-doc).

## Conventions rejected

These appear in some projects but are too specialized or heavyweight for general adoption:

- **Hierarchy IDs (`H1.M2.G3.T4`)** — only `jajupmochi.github.io` uses these because it has a real long-lived roadmap. Most projects don't need it; `git log` + a short PLAN.md is enough.
- **`UPDATES.md` daily log doctrine** — overkill for short-lived projects. Available in the static-site template if needed.
- **Black** — consolidating on `ruff format` only. Leftover `[tool.black]` blocks in `pyproject.toml` are technical debt to clean up, not config to honor.
- **Per-project CLAUDE.local.md** — only the personal-site needs one (job-hunt context, ML researcher framing). For most projects, the global `~/.claude/CLAUDE.md` covers personal preferences.

## Living document

Updates here trail the corresponding rule edits. When a `RULE.md` changes its rationale, this doc gets updated in the same batch. The list of "adopted" and "rejected" conventions is empirical — based on what's actually working across Linlin's projects, not on a-priori best practices.
