# Rules

> Workflow conventions that shape Claude's behavior in a downstream project. Each rule has a long-form `RULE.md` (rationale, examples, exceptions) and a short `snippet.md` (drop-in for `CLAUDE.md` via `@import`).

## Master TOC

- [How to use](#how-to-use)
- [Rule index](#rule-index)
- [Scope tags](#scope-tags)
- [Adding a new rule](#adding-a-new-rule)

## How to use

In a downstream project's `CLAUDE.md`, add `@<path-to-rule>/snippet.md` lines for each rule that applies. Three paths:

- **Raw URL** — `@https://raw.githubusercontent.com/jajupmochi/claude-config/main/rules/<name>/snippet.md`
- **Local clone** — `@~/.claude/claude-config/rules/<name>/snippet.md`
- **Plugin** (P10+) — `/plugin install jajupmochi/claude-config` exposes these via the setup skill.

The `setup/init-claude-config` skill (P8) does this composition automatically based on project type.

## Rule index

| Rule | Scope | When applies |
|---|---|---|
| [`chinese-output`](chinese-output/RULE.md) | personal | User's final-output language preference is Chinese |
| [`pre-edit-confirmation`](pre-edit-confirmation/RULE.md) | universal | Before any Edit / Write / NotebookEdit / MultiEdit |
| [`phased-planning`](phased-planning/RULE.md) | universal | Tasks touching 3+ files / >5 tool calls / multi-step |
| [`plugin-preflight`](plugin-preflight/RULE.md) | universal | Before invoking unfamiliar plugin / MCP / skill |
| [`ui-iteration-loop`](ui-iteration-loop/RULE.md) | ui-project | When user provides a visual reference for UI work |
| [`output-brevity`](output-brevity/RULE.md) | personal | All output — keep terse, no end-of-batch recap |
| [`tool-proactivity`](tool-proactivity/RULE.md) | personal | Installed skills / plugins fire without asking |
| [`no-reread-files`](no-reread-files/RULE.md) | personal | Trust in-session memory of file contents |
| [`clickable-links`](clickable-links/RULE.md) | personal | Every commit / file / line / PR / doc / source reference is a FULL clickable link — never a bare hash, partial path, or half URL |
| [`human-readable-output`](human-readable-output/RULE.md) | personal | User-facing output/docs say it like a human (what · why · effect); no process narration or session-control markers leaking into reports; final summary set off + key points first |
| [`design-artifacts`](design-artifacts/RULE.md) | personal | Designed an API / UI? List endpoints with clickable LOCAL test links (Swagger/Storybook) + give the live preview link + embed a screenshot — in the doc AND the summary |
| [`bilingual-docs`](bilingual-docs/RULE.md) | optional | `NAME.md` + `NAME.zh.md` convention for human-facing docs |
| [`end-of-turn-marker`](end-of-turn-marker/RULE.md) | personal | Every turn ends with `[END:FINAL]` / `[END:WAIT]` / `[END:NEEDS_USER]` on its own line |
| [`always-on-verification`](always-on-verification/RULE.md) | research-pkg | Before any code / test / results claim, invoke `code-verifier` (artifact authenticity) and/or `research-critic` (inferential soundness) |
| [`autorun-mode`](autorun-mode/RULE.md) | personal | When user says "autorun" / "全力跑" / "think a lot" + scope: shift to higher-autonomy cadence with multi-pass review + branch hygiene |
| [`multi-round-redesign`](multi-round-redesign/RULE.md) | ui-project | N-round UI redesign protocol with date-stamped `00-plan.md` + `round-N.html`/`.png`/`.notes.md` + final spec lock + production-lock round |
| [`latex-edit-policy`](latex-edit-policy/RULE.md) | research-pkg | When editing `.tex`/`.sty`/`.cls`/`.bib`: hard fixes direct, soft (content) edits comment-don't-delete with `% [orig YYYY-MM-DD]` inline backup |

## Scope tags

| Tag | Meaning |
|---|---|
| `universal` | Apply to every project |
| `personal` | A user-preference rule. Apply if the user opts in at scaffold time |
| `ui-project` | Apply only to frontend / UI work |
| `optional` | Don't auto-apply; the setup skill asks per project |

The `setup/init-claude-config` skill (P8) reads each rule's frontmatter `scope:` and offers it based on project type.

## Adding a new rule

See [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md) §"Adding a rule". Summary:

1. Create `rules/<kebab-name>/`
2. Add `RULE.md` (frontmatter + body) and `snippet.md` (drop-in for `CLAUDE.md`)
3. Update `INVENTORY.md` and `INVENTORY.zh.md` in the same edit batch
