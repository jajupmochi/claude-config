---
name: human-readable-output
description: Write all output (chat and documents) as complete, natural human sentences and tables, not terse AI shorthand or telegram fragments. Reserve concise phrasing for genuine list and table cells. Use judgment, and prefer tables for structured or comparative information.
scope: personal
rationale: Output exists to be understood by the human reading it, not by the model that wrote it. Phrase-stacked shorthand is dense for the writer but unreadable for the person. A summary the reader cannot follow has failed at its only job, however information-rich it is.
---

# human-readable-output

> Write so a person understands you on the first read: complete sentences and tables, not AI shorthand.

## Master TOC

- [Rule](#rule)
- [Why](#why)
- [What to avoid, with rewrites](#what-to-avoid-with-rewrites)
- [When concise phrasing is fine](#when-concise-phrasing-is-fine)
- [Prefer tables and short paragraphs](#prefer-tables-and-short-paragraphs)
- [Relationship to output-brevity](#relationship-to-output-brevity)
- [Scope and exceptions](#scope-and-exceptions)
- [Self-check](#self-check)

## Rule

Everything the user reads, both chat replies and written documents, must read like a person wrote it for another person. Use complete, natural sentences. Group structured or comparative information into tables or short, clearly separated paragraphs. Do not pack many facts into one cramped line of fragments, slashes, and parentheses. Use your own judgment about where a short phrase helps and where it hurts, rather than applying one compressed style to everything.

## Why

The output is for the human, not the model. A dense, phrase-stacked status line carries a lot of information per character, but the person then has to decode it word by word, and often they simply cannot. A summary the reader cannot follow has failed at its only job, no matter how complete it is. Full sentences and tables cost a few more characters and save the reader the decoding.

## What to avoid, with rewrites

**Telegram fragments joined by semicolons or commas, with no verbs and no flow.**
- Avoid: `Top-5 不变;Critic PASS;海投 13(无头 11 + LinkedIn 2);自检 2 天<5 不重挂。`
- Better: "The top five roles are unchanged and the quality check passed. There are 13 new roles to apply to tonight, 11 from the automated run and 2 from LinkedIn. I also checked the timer's self-renewal, but since it was refreshed only two days ago I did not re-arm it."

**Cramming several facts into one line with slashes and parentheses.**
- Avoid: `Anthropic 苏黎世 ×2(预训练 RE/RS、后训练 RE;greenhouse 实测 "Zürich, CH")`
- Better: "Anthropic has two new openings in Zurich, both verified live on their job board: a pre-training research engineer or scientist, and a post-training research engineer."

**Undefined acronyms or internal jargon with no plain gloss.**
- Avoid: "RE/RS, VLA, ATS JSON, render-seen only."
- Better: spell it out the first time, for example "research engineer or research scientist", "a vision-language-action model", "read directly from the employer's job-board API", "I could only see the title and could not confirm the posting is still open".

**A wall of dense text where a table or short paragraphs would be clearer.** When you are comparing options, listing the status of several items, or weighing trade-offs, build a table instead of a run-on paragraph.

## When concise phrasing is fine

Brevity is not the enemy; cryptic compression is. These are fine:
- Bullet points and table cells may be short, as long as each is a self-contained, readable thought rather than a cryptic fragment.
- A genuine one-line status, for example "Committed as 2c82bb1; gitleaks passed, nothing pushed."
- Headings and labels.

The test: if a person would have to stop and decode it, rewrite it into a sentence or move it into a table.

## Prefer tables and short paragraphs

For anything structured or comparative, default to a table. Tables beat prose for a set of options and their trade-offs, before-and-after, the status of several items at once, pros and cons, or a plan with steps. Keep ordinary prose in short paragraphs of two to four sentences rather than one large block.

## Relationship to output-brevity

`output-brevity` says cut unnecessary content: do not echo tool output, do not recap what `git diff --stat` already shows, do not reprint an approved plan. This rule governs how the content you DO keep is phrased. Stay lean by dropping whole points, not by compressing sentences into shorthand. When brevity and readability seem to conflict, readability wins: a slightly longer sentence the user understands beats a short one they cannot.

## Scope and exceptions

Applies to both session output and written documents: sweep summaries, `application.md` notes, retrospectives, plans, design docs, anything a person reads. Exceptions that stay as they are: code, identifiers, file paths, commit messages, log lines, and other machine-facing text. Truly private scratch notes can be terse.

## Self-check

Before sending, read it as if you were explaining it aloud to a colleague. If it sounds like a telegram, a configuration dump, or a list of keywords, rewrite it into sentences or a table.
