---
name: prompt-library
description: Use to save and reuse good prompts across projects and agents, and to MINE past prompts out of local Claude Code / Codex / Copilot / opencode history. Many prompts recur (a detailed feature spec, a "design the whole thing" brief, a manual/onboarding prompt) and are worth reusing verbatim or as a reference. This curates them as browsable, greppable Markdown — each with the original, an optimized rewrite, and when to use / when NOT to use it — behind a PRIVACY GATE that refuses to store anything still containing paths/emails/tokens/usernames/codenames, so the library stays publishable.
policy:
  allow_implicit_invocation: true
---

# prompt-library

Overhaul task 9. Reusable prompts (e.g. a very detailed feature-update brief; a "design the whole X" prompt
that transfers across sibling projects; a manual/onboarding prompt) get curated once, de-privacy'd, tagged by
scenario, and made easy for a human to find and for an agent to reuse.

## Routing: check the library before writing a prompt from scratch

When a request matches a scenario the library already covers, READ THE ENTRY FIRST and adapt its Optimized
block instead of composing a new prompt. Run `plib.py find --query "<the user's words>"`, or scan the
`By scenario` section of `recommendations/prompt-library/INDEX.md`. Scenarios currently covered include
feature specs and multi-part update briefs, skill authoring, documentation (subsystem docs, completeness
audits, in-app manuals and onboarding), deployment and infrastructure, data-platform and schema work,
research and experiment design, bug triage, reporting, and proposal writing.

Two rules when you reuse one. Read `When NOT to use` before adopting an entry — several of them are
actively wrong for the neighbouring case, and that section is where the judgement lives. And treat the
`Optimized` block as a template with `<placeholders>` to fill, not as text to paste unchanged.

## Use

- **Save** a prompt — the ORIGINAL goes on stdin, the rest as flags. The privacy gate runs over the whole
  rendered document first and REFUSES if anything still looks private:
  ```
  python3 scripts/plib.py add --title "Redesign a dashboard" --scenarios ui,redesign --source claude-code \
      --optimized @optimized.txt --when "Use when …" --when-not "Skip it when …" < original.txt
  ```
  `--optimized`, `--when` and `--when-not` take literal text or `@path`. `--tags`, `--session` and `--date`
  are optional (`--date` defaults to today; leave `--session` empty when publishing — a session id adds
  nothing to a published entry and is mildly identifying).
- **Mine** past prompts out of local agent history — see below.
- **Browse**: read `INDEX.md` (title · scenarios · when to use · source · file, plus a by-scenario index).
  **Find**: `plib.py find --query "terms"`.
- **Just check** some text for private content: `plib.py scan < text` (exit 1 if it finds any).

## Stored format (v2)

Frontmatter `title / scenarios / tags / source / session / date`, then four sections:

| section | holds |
|---|---|
| `## Original` | the prompt as it was actually sent, de-privacy'd. Fenced, so it stays copy-pasteable. |
| `## Optimized` | a rewrite worth reusing: same intent, placeholders where the specifics went. |
| `## When to use` | the situations it fits, concretely. Its first sentence becomes the entry's summary line. |
| `## When NOT to use` | where it misfires, and what to do instead. |

Only `## Original` is required; the other sections are omitted when empty. Files written by v1 (a bare body,
no sections) still read correctly — their whole body is treated as the Original.

## `mine` — pull candidates out of local agent history

```
python3 scripts/plib.py mine --source all --out ~/scratch/candidates [--since 2026-06-01] [--min-len 120] [--limit 200]
```

`--source` takes a comma-separated list of `claude-history`, `claude-transcripts`, `codex`, `copilot-cli`,
`copilot-vscode`, `opencode`, or the aliases `claude`, `copilot`, `all`. It reads, per source:
`~/.claude/history.jsonl`; `~/.claude/projects/*/*.jsonl` (excluding `subagents/`);
`~/.codex/sessions/**/*.jsonl`; `~/.copilot/session-state/*/events.jsonl` and `~/.copilot/jb/*/partition-1.jsonl`;
`~/.config/Code/User/workspaceStorage/*/chatSessions/*.jsonl`; and `~/.local/share/opencode/opencode.db`
(opened READ-ONLY). Everything is filtered for machine-issued text — SDK entrypoints, compaction summaries,
history replays, task notifications and other harness scaffolding — which on a real history is roughly half
of all captured turns.

It emits `candidates.jsonl` (ranked, one JSON per line) and `REVIEW.md` (a table to curate from). It does
NOT publish, for two reasons: the raw text still contains absolute paths and codenames, and writing the
optimized variant plus the scenario tags needs judgement. `mine` refuses an `--out` inside the library root
so raw text cannot land somewhere publishable.

Ranking asks one question: is this prompt REUSABLE, meaning it specifies a repeatable piece of work rather
than a one-off? The score sums five computed signals — length, structure (bullets, requirements, an output
spec), imperative phrasing, generality (penalised per one-off marker: absolute paths, line numbers, bare
filenames, hashes, deictic openings, pasted stack traces), and recurrence of near-identical prompts. Each
candidate carries its signal breakdown, the one-off markers found, and the privacy labels that hit, so
curation can start at the top and see immediately what needs stripping.

## Privacy gate (heuristic, not a guarantee)

`add` and `scan` flag GENERIC private content: absolute `/home` `/media` `/mnt` paths, emails, and
token-shaped strings (`sk-`/`ghp_`/`gho_`/`github_pat_`). `add` scans the whole rendered document, so the
title, every section and every frontmatter value are covered — a match anywhere blocks the save.

**User-specific terms** (your username, your project codenames) are deliberately NOT hardcoded in the tool —
shipping them would publish them (and the repo's own CI privacy scan bans codename literals in content
modules). Put them in a LOCAL, un-published file, one term per line, and the gate will also flag those:

```
export PLIB_PRIVATE_TERMS=~/.config/agent-harness/private-terms.txt   # else this default path is auto-used
```

For anything the heuristic misses, still review manually (pairs with the `privacy-redact` skill).

## Storage

`<root>/prompts/<slug>.md` + a generated `INDEX.md`. Default root `recommendations/prompt-library` so the
library ships with agent-harness and is reusable cross-project. LLM-as-component: store, index, find, scan
and mine are deterministic; the model writes the optimized variant and the when-to-use judgement.

Status: v0.2 (add with the v2 schema / index / find / scan / mine), tested (`test_plib.py`, 24/24), seeded
with a first curated batch of 18 prompts mined from this machine's Claude Code, Copilot and opencode history.
