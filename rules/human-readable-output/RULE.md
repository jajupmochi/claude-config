---
name: human-readable-output
description: Write everything the user reads — chat, summaries, committed docs, reports — as plain language a person follows on the first read (what · why · effect). No telegram-style fragments, no process narration, no session-control markers leaking into reports.
scope: personal
rationale: The user repeatedly couldn't tell what was actually done from formulaic, fragmented output — terse AI shorthand, internal process narration, and session-control markers (`[END:WAIT]`, "收敛路径") leaking into reports. A summary a person can't decode is worthless. This refines `output-brevity`: stay lean by cutting whole points, not by compressing sentences into cryptic shorthand. On conflict, readability wins.
---

# human-readable-output

> Say it like a human. Complete sentences, concrete (what · why · effect), understandable on the first read. Never leak internal process narration or session-control markers into anything the user reads.

## Master TOC

- [Rule](#rule)
- [What to keep out of user-facing text](#what-to-keep-out-of-user-facing-text)
- [Why](#why)
- [Companion rules](#companion-rules)

## Rule

Everything the user reads must be plain-language and decodable on the first read:

1. **Complete, natural sentences.** Not telegram-style fragments joined by semicolons, not slash-and-parenthesis phrase piles, not undefined acronyms, not dense walls of text. If a person would have to stop and decode it, rewrite it as a sentence.
2. **Lead with substance, in human words.** Say WHAT you did, WHY, and the EFFECT, so someone who didn't watch understands: "I added a regression test for the validator; it now catches 9 bad configs (verified by a real run)." Not a checklist of opaque fragments.
3. **No internal process narration in reports.** Don't narrate the plumbing — "收敛路径", "本回合补强", "review-gate 复核中", "下回合 commit-only", "Stop 评审覆盖". That's how the machinery works, not what got done.
4. **No session-control markers in docs/summaries.** `[END:WAIT]` / `[END:FINAL]` / `[END:NEEDS_USER]` belong to live turn-control only — they must NEVER appear inside a committed doc or a written report.
5. **Structured content gets structure.** For options with trade-offs, per-item status, pros/cons, or a multi-step plan, use a TABLE or short separated paragraphs over one cramped run-on. Keep prose to short paragraphs of two to four sentences. Bullet/table cells may be concise, but each must be a self-contained, decodable thought.
6. **Refines `output-brevity`.** Stay lean by cutting whole points, NOT by compressing sentences into shorthand. On any conflict between brevity and readability, readability wins.
7. **Fence the final summary top AND bottom with a THICK `━` bar — bar and keyword each on their OWN line.** Put a bounded run of `━` (~14–16 chars — must fit ONE line on a phone; a 24-char bar already wrapped) on its own line, the keyword on its own line, another `━` bar on its own line; then the content; then a closing `━` bar:

    ```
    ━━━━━━━━━━━━━━━━
    📊 本轮小结
    ━━━━━━━━━━━━━━━━

    …content…

    ━━━━━━━━━━━━━━━━
    ```

   The thick `━` bar is far more grabbable than a thin `---`. The reason the bar and keyword go on SEPARATE lines (not inline as `━━━ 本轮小结 ━━━`): an inline bar makes one very long logical line that wraps badly on a phone, burying the keyword mid-wrap. On its own line, a bounded bar stays clean and the keyword stands alone. The same applies to any auto-running post-summary output (e.g. a review-gate review): give it its own `━`-fenced block, don't let it sprawl as raw text.
8. **Make the key points pop; keep details secondary but present.** Lead a complex summary with a one-line at-a-glance (or a 2–3 item mini-TOC), then a **table** or **bold-keyed nested bullets**: bold the key point like a heading, put the detail on the next line / in a sub-bullet. The reader should grasp the headline at a glance and still find the detail underneath. Don't bury the point in a wall of text.
9. **Explain every marker/shorthand at least once, every output.** Whenever you use a label, code, or shorthand the reader might not remember — `H1`/`H46`, an experiment tag, a codename, an abbreviation, `a/b/c` option keys, a one-letter flag — give a brief inline gloss of what it means **in that same output**, even if you (or they) defined it before. The reader has forgotten; never assume recall. (Exempt: standard identifiers in code/paths/commits.)
10. **Tables AND lists must render — put a blank line before AND after them.** A markdown table OR list glued directly to the line above it (no blank line) — especially a `- bullet` / `1.` list sitting right under a `**bold heading**` line — fails to render in many clients (incl. the Claude Code terminal / phone app): the table shows as raw `| … |` text, and the list shows as raw `- …` source or gets swallowed into the paragraph (the user sees "code", not a list). ALWAYS leave a blank line between a heading/paragraph line and the table or list that follows it, and a blank line after the block. Keep a proper table separator (`|---|---|`), and never nest a table inside a blockquote (`>`) or a list item.
11. **Any flat bullet list with MORE THAN 3 items must be numbered (`1. 2. 3. …`), not `-` dashes — and number every nesting level that also exceeds 3.** Four-plus dashes are hard to scan and impossible to refer back to ("which of the 9 bullets?"). With >3 items: number them, or group them into a shallow hierarchy; within any one level, ≤3 items may stay as `-`, but >3 at that level gets numbered so each is identifiable. (The review-gate's 9-item form list is the canonical offender.)

Exceptions that stay as-is: code, identifiers, file paths, commit messages, log lines, machine-facing text.

## What to keep out of user-facing text

| Keep OUT (machinery) | Put IN (the report) |
|---|---|
| `[END:WAIT]`, `[END:FINAL]` | (nothing — these are turn-control only) |
| "收敛路径 / 本回合补强 / 复核中" | "I added a regression test for the validator; it now catches 9 bad configs" |
| bare status fragments | "what · why · effect", each with a clickable link |

## Why

Output is only useful if the reader understands it and can act on it. Formulaic fragments plus leaked process narration mean the user can't tell what happened — it reads as perfunctory. Plain language, concrete specifics, and working links are the difference between a real report and noise.

## Companion rules

Pairs with [`clickable-links`](../clickable-links/RULE.md) (every reference clickable) and [`output-brevity`](../output-brevity/RULE.md) (terse — but terse AND clear, never terse-and-cryptic).
