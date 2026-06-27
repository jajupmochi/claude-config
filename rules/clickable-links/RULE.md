---
name: clickable-links
description: Every reference (commit, file, line, PR, doc, external source) is a FULL, clickable, navigable link — never a bare hash, partial path, or truncated URL the reader can't jump to.
scope: personal
rationale: The user repeatedly can't act on outputs because references are dead text — a bare commit hash, a `path/to/file.py` that isn't a link, a half URL. They want to click a commit / a file / a source and land there. Half-links waste their time and read as perfunctory.
---

# clickable-links

> Give the WHOLE link, and make it clickable. Never a bare hash, a partial path, or half a URL. If the reader would have to go hunt for it, it's wrong.

## Master TOC

- [Rule](#rule)
- [How to link each kind of thing](#how-to-link-each-kind-of-thing)
- [Why](#why)
- [Anti-patterns](#anti-patterns)

## Rule

Whenever you mention a commit, a file, a line, a PR/issue, a doc, or an external source, render it as a **full, clickable, navigable link** — in chat, in committed docs, and in any summary. Never make the reader copy-paste, guess a path, or "find it themselves". If you can't produce a working link, say so explicitly and give the most specific locator you can (and why a link isn't possible).

## How to link each kind of thing

- **Commit** —
  - Pushed to a remote: `https://github.com/<org>/<repo>/commit/<full-40-char-hash>` (full hash, not the short form).
  - Local-only / not pushed: write `` `<hash>` (local, not pushed — in <repo-abs-path>) `` — never a bare hash with no location.
- **File** — a path the reader can click:
  - In chat (terminal): an **absolute** path, optionally `path:line` (the harness makes `file:line` clickable). Not a bare relative `scripts/x.py` with no anchor.
  - In a committed Markdown doc: a real markdown link `[x.py](relative/or/abs/path)`; for a specific line use `path#L42`.
  - Pushed code: `https://github.com/<org>/<repo>/blob/<branch-or-sha>/<path>#L42` when you want the reader to see it on the web.
- **Line / range** — append `#L42` (or `#L42-L60`) to a file link; in chat use `path:42`.
- **PR / issue** — full URL: `https://github.com/<org>/<repo>/pull/<n>` (not just "PR #5").
- **Doc you wrote / a plan** — a clickable link to the doc, plus a deep link to the exact section/heading when relevant (`doc.md#section-anchor`).
- **External source (web)** — the **complete** URL, never truncated, never "see their site". One source = one full URL.

## Why

References are only useful if the reader can ACT on them. A bare hash, a non-link path, or half a URL means they can't jump — so the reference is dead weight and the work reads as perfunctory. Full clickable links are the difference between "here's exactly where" and "go look for it yourself".

## Anti-patterns

| Don't | Do |
|---|---|
| `commit c6141ac` | `` `c6141ac` (local, not pushed — in `/abs/repo`) `` or `https://github.com/org/repo/commit/c6141ac…` |
| `scripts/validate_config.py` (plain text) | `[validate_config.py](…/scripts/validate_config.py)` or `/abs/.../scripts/validate_config.py:1` |
| "PR #5" | `https://github.com/org/repo/pull/5` |
| "see their careers page" | the full posting URL |
| a URL cut to fit a line | the whole URL, even if long |
