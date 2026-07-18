---
name: doc-writing
description: Use when writing or updating any document a human will read — a design or architecture spec, a feature manual and its in-app guide, an audit / bugfix / test report, a README, release notes, a plan, or a session handoff. Encodes the document requirements mined from two real project sessions (define every term in place, prove every claim and say how a tester re-proves it, full clickable links, mermaid diagrams, nothing stale, remaining tasks highlighted, no secrets) and ships `scripts/doccheck.py` to lint the finished file against the ones a machine can check.
policy:
  allow_implicit_invocation: true
---

# doc-writing

> How to write a document this user accepts, organized by document type, with a linter for the rules a machine can check.

## Master TOC

- [How to use this](#how-to-use-this)
- [The two rules that caused the most friction](#the-two-rules-that-caused-the-most-friction)
- [Universal core](#universal-core)
- [Per document type](#per-document-type)
- [When the requirement depends on context](#when-the-requirement-depends-on-context)
- [Lint before you ship](#lint-before-you-ship)
- [Keeping this skill true](#keeping-this-skill-true)

## How to use this

Read the universal core once. Then read the one section for the type you are writing, and use its skeleton as the outline. Write the document. Run `scripts/doccheck.py` on it before you call it done.

**Marker legend.** Two markers appear throughout, and both mean something specific.

1. `B12` points at consolidated rule 12 in the mined preference set. The linter quotes these ids back in its findings so a rule can be traced to its evidence.
2. `#3` is the position in the frequency ranking, meaning how many separate turns the user spent repeating the point. A high rank is not a matter of taste, it is a record of repeated correction.

The source is two real project sessions from July 2026, 262 prompts total, mined into 102 verbatim preferences and 48 consolidated rules.

## The two rules that caused the most friction

### 1. Define every term you introduce, in place (`B6`, rank `#1`)

Across roughly eight separate turns the user had to stop the work and ask what a word meant. Every one of those words was the agent's own wording, so this friction was self inflicted. The questions looked like this.

> 特别解释一下langchain 4-tool sql是什么东西 · 请解释一下es是什么 · 项目级联是啥？什么入口合并？ · 报告状态静默不达，这个是啥意思？

The rule covers acronyms, product names, internal jargon, and any phrase you coined while writing. Gloss it at first use, inside the sentence, in one of these forms.

| Form | Example |
|---|---|
| Parenthetical | `the ETL (extract, transform, load) job` |
| Dash gloss | `ETL — extract, transform, load — runs nightly` |
| Glossary row | `- **ETL**: the nightly extract, transform, load pass` |

A glossary section at the top does not excuse an unglossed term further down. If you invented the phrase while writing the sentence, that is exactly the case that needs the gloss.

### 2. A manual (手册) AND an in-app guide (引导) per feature, and a guide is a use case flow (`B13`, `B14`, rank `#2`)

Roughly ten turns, including an outright rejection the user asked be recorded permanently.

> Agent的那个引导有点儿奇怪，他就是简单的罗列了一下几个按钮，根本没有整个的流程，所有的引导它是按照功能流程来的，也就是user case来的，即使是同一大模块儿的功能，如果它有好几种使用方式/cases，那实际上应该有好几种，好几个引导才对，而不能单纯的就是把功能罗列一下，请对这个进行一个整体的优化，并且记下这个要求。

What this settles.

1. Every shipped feature gets both artifacts. A written manual, and an interactive guide inside the product. Either may be standalone or folded into the feature surface.
2. A guide is an end to end flow through a real task, never an enumeration of the buttons on screen. Listing controls was rejected by name.
3. One module with N distinct ways of being used gets N guides, one per use case.
4. Manuals and guides land feature by feature as each feature finishes, not batched at the end of the project.
5. Coverage is recursive. The manual and guide system itself, and the bug report module, each need their own manual and guide. There is no meta exemption.

The interactive guide has a fixed navigation contract, listed in [manual](#manual--手册-and-引导).

## Universal core

These apply to every document. The first ten are ranked by how often the user had to repeat them, and the last column names the `doccheck.py` check that enforces the rule mechanically.

| Rank | Rule | What it means when you are writing | Check |
|---|---|---|---|
| `#1` | Define every term in place (`B6`) | Gloss acronyms, product names, and phrases you coined, at first use | `undefined-jargon` |
| `#2` | Manual plus in-app guide per feature (`B13`, `B14`) | Both artifacts, per feature, guides as use case flows | — |
| `#3` | Prove it, say how you proved it, say how I re-prove it (`B2`) | Every claim comes from a real run, and the document states the procedure and how a tester repeats it | `missing-section` |
| `#4` | Full clickable link for every reference (`B4`) | Docs, files, code, commits, PRs, exposure points. Never a bare name or half a URL | `bare-ref` |
| `#5` | Nothing stale (`B9`, `B11`) | Audit the whole document when one wrong statement turns up, and refresh every diagram against the current design | `staleness` |
| `#6` | Diagram anywhere a diagram is possible, in mermaid (`B5`) | Architecture, data flow, storage and cache, plus one for the main logic and one per feature | `missing-diagram` |
| `#7` | Enumerate the inventory first (`B26`, `B27`) | Write the full list of items before changing any of them, then work through it, then review item by item |  — |
| `#8` | Batch what needs the user to the end (`B25`) | One block at the end for every question, authorization, and manual step, after checking whether it could be automated | — |
| `#9` | Deferred work becomes a future task with its risk (`B17`, `B18`) | Named, highlighted, each entry stating the risk and how to avoid it | `missing-section` |
| `#10` | No secret ever reaches a document (`B1`) | Reference where a credential lives, never its value. One leak had to be purged from git history | `secrets` |

Also always true, grouped by what they govern.

**Honesty of content.**

1. Nothing is guessed (`B2`). When something cannot be verified, the document says so instead of asserting it.
2. Cite the source of every fact, and for any number, precise value, or list, include the code and the generation procedure that produced it (`B3`).
3. Label every mock or demo item visibly so nobody reads it as real (`B37`).
4. Say when a behaviour is deliberate rather than an oversight, and record the reasoning (`B19`). The reader has to be able to tell an omission from a decision.
5. Being a prototype never licenses narrowing the analysis (`B29`).

**Writing.**

1. Natural human prose with the AI flavour removed (`B7`). Chinese reads as Chinese, never as a term by term translation of English jargon.
2. One document serves two audiences (`B7`). Deep enough technically for an engineer, while the top level narrative and the diagrams stay legible to a data analyst.
3. Structured, repetitive, or multi field information goes in a table (`B8`). Per entity outcomes get a classification table plus statistics.
4. Schemas, attributes, and storage formats always carry a worked example (`B20`).
5. Names state plainly what the thing is for (`B47`), documents included.

**Placement and delivery.**

1. Survey and cite every existing document on the topic before writing, and fix what you find stale on the way (`B10`, `B43`).
2. One topic, one main document (`B9`). New work merges into it. Scattered related documents get consolidated in, not left as parallel copies.
3. Documentation centralizes in the dedicated docs repo, laid out as one subdirectory for platform wide material plus one per code repo (`B30`).
4. Migrating a document means adding a link in the source repo and keeping the original, with one exception covered in [the decision rules](#when-the-requirement-depends-on-context) (`B31`).
5. A document counts as delivered once it is pushed and findable (`B39`). Verify it renders where it will be read, since a section that fails to render is a defect the user reports (`B12`).
6. Write every newly discovered requirement and every working configuration straight into the relevant document, making the working configuration its default example (`B35`).

## Per document type

### spec — design and architecture

The section skeleton, derived from the document the user promoted to the house template.

1. Purpose and scope
2. Terminology, glossing every term the document uses
3. Problem history — what went wrong before, what the old design was, why it failed
4. Architecture — mermaid architecture diagram, data flow diagram, storage and cache diagram
5. Code and data map — every module, table, and attribute with a full link, each placed at its correct position in the diagrams
6. Storage format, with a worked example
7. Operating it — what CI/CD automates, what a human does, and whether the whole flow runs without an AI agent
8. Per entity outcomes — classification table, statistics, accuracy per method, what needs human checking
9. Special cases and deliberate decisions, each flagged rather than folded silently into the general case
10. How comparable tools solve the same problem
11. Verification — how each claim was proven, and how a tester or frontend engineer re-proves it
12. Remaining tasks and future work, highlighted, each deferred item carrying its risk and how to avoid it

Extra rules for this type.

1. Research established practice before designing a format or scheme, compare the alternatives in writing, and give an explicit recommendation (`B28`).
2. Split every operational procedure into what CI/CD can automate and what a human must do, listing the manual set exhaustively (`B16`).
3. Keep the manual how to alongside any automation plan, even after the automation is scheduled (`B17`).
4. Environment scoped documents stay strictly in scope (`B36`). A production instruction never appears in the staging document.
5. When a diagnostic procedure works, the executed procedure becomes a document, and that document becomes the first reference for that class of failure (`B41`).
6. A written artifact that is also machine input follows an established open source format, lives in a designated location, carries a `description` per entry stating what it verifies, and is executable through one code path (`B44`).

`doccheck --type spec` requires a mermaid diagram, a verification section, and a remaining-tasks section.

### manual — 手册 and 引导

The manual skeleton.

1. What this feature is and what it is for
2. Prerequisites
3. Steps, starting from absolute zero (`B15`). Open the vendor site, create the account, log in. Assume no prior state
4. Screenshots of the surfaces being described (`B38`)
5. The problems hit along the way and how to get past them. The failure history is part of the deliverable, not an appendix
6. How to check it worked, written for the person doing the checking
7. Where to report a bug

The in-app guide contract, all five points from the rejection that produced it.

1. Each guide is one use case flow. A module with several usage cases gets several guides.
2. The guide starts at step 1, never at step 2 or 3.
3. It offers a previous step control and a quit control at every step.
4. On exit it returns the reader to the matching manual page.
5. It records completion per user, and still lets that user run it again.

Extra rules for this type.

1. Anything the user has to perform is broken into explicit numbered steps, not summarized (`B15`).
2. Issues raised by named colleagues are recorded with attribution, executed, and then absorbed into the manual and the guide. They are closed only once absorbed (`B42`).
3. When another team owns the other side of an integration, ship API documentation plus a manual plus a guide aimed at that team (`B42`).
4. Coverage is recursive. The manual system and the bug report module get their own manual and guide (`B13`).

`doccheck --type manual` requires a mermaid diagram and a verification section.

### report — audit, bug fix, test results

Field lists by report subtype. These are the fields the user named, so a report missing one gets sent back.

| Subtype | Required fields |
|---|---|
| Bug fix (`B21`) | Screenshot · ID or number · where the problem was · how it was fixed · what it looks like after · how to verify from the frontend · how to use it · links to the related comments and references |
| Test results (`B23`) | Per test: what functionality it covers · expected result · actual result · cause · effect |
| Feature write up (`B22`) | What it is · what was concretely done · how to test it · what it is for |
| Comparison (`B26`) | Every flow difference and every configuration difference — ports, URLs, credentials, databases, paths, and the rest — produced by enumerating the full inventory first |
| Batch close out (`B24`) | Every change and addition, each with its verification link · the new feature list, each entry explaining how to test it from the user's perspective |

Extra rules for this type.

1. Report the finished subset as it lands rather than holding everything until the batch completes (`B24`). The user verifies in parallel.
2. Root cause before fix. State whether the fault was a regression or pre-existing fragility, and why it started firing now.
3. Everything needing the user's hand, authorization, or decision goes in one block at the end, after checking whether it could be automated instead (`B25`).
4. Alongside an exhaustive report, produce the short paste into chat summary (`B46`).

`doccheck --type report` requires a verification section and a remaining-tasks section.

### readme

The README opens with per audience entry points, and that table is the first thing a newcomer sees (`B33`).

1. One row per role. Frontend, backend, database, and agent developers, QA, end users, marketing, the CEO, and the UI designer.
2. Each role qualified by which platform it belongs to, since the organization runs more than one.
3. Each row lists what to read, marked as must read or read later.
4. If several versions of this table already exist, consolidate them and move the result somewhere more visible.

Extra rules for this type.

1. Process rules everyone must follow go somewhere impossible to miss, backed by a hard enforcement mechanism such as branch protection or a pre-push hook where one exists (`B34`). Analyse the flow for defects before writing it down.
2. Setup instructions start from absolute zero (`B15`).
3. A new repository ships with a sensible file structure, a written explanation of it, a documentation system, and a matching update to the central docs repo (`B32`).

### release-notes

1. What shipped, one entry per item, each stating what it is and how to test it from the user's perspective, each with its link (`B22`, `B24`).
2. Bug fixes with their IDs and verification links (`B21`).
3. The short broadcast summary to paste into chat, pointing at the full document (`B46`).

### plan

The user's standing sequence is list everything, then change one at a time, then review one at a time from several angles (`B27`).

1. Inventory first. The complete list of pages, components, or items to touch, written before anything is touched, so nothing is skipped (`B26`).
2. Research on established practice, a comparison of the alternatives, and an explicit recommendation (`B28`).
3. Phases, each with its deliverables.
4. The automation split, and whether the flow runs without an AI agent (`B16`).
5. Risks, each with how to avoid it (`B17`).
6. Remaining and future tasks, highlighted (`B18`).
7. A mermaid diagram of the flow being planned (`B5`).

`doccheck --type plan` requires a mermaid diagram and a remaining-tasks section.

### handoff

Written when context or budget runs low, and also before any compaction (`B40`).

1. Filename `HANDOFF-YYYY-MM-DD.md`, under `docs/platform/`, on branch `handoff/session-YYYY-MM-DD`.
2. Pushed to the remote, and the reply carries its URL. The next session resumes from that URL.
3. Contents: where things stand · what is done and verified, with links · what is in flight · the exact next step · blockers and the decisions still owed by the user · every link needed to resume without re-deriving anything.

## When the requirement depends on context

Six places where the requirements look contradictory across turns but are not. Each is a decision rule.

| Situation | Decision |
|---|---|
| Exhaustive or short | Both, as two artifacts, never one compromise. The document in the docs repo is the exhaustive record. Anything sent to a chat channel is a short pointer that links to it. |
| Which language | Identifiers, paths, filenames, and document titles stay English. Prose a colleague or the user reads leans Chinese or bilingual. Product UI strings are a separate i18n obligation, not a doc rule. |
| Keep the original or delete it | A document that legitimately belongs to that repo stays, as a copy with a link. A document sitting in the wrong repo is deleted, with a note saying where it went. |
| Run autonomously or checkpoint | Writing and reporting never need a checkpoint. Irreversible or externally visible acts do — renaming ports, deploying to production, merging to main. |
| Where enforcement lives | Enforcement artifacts live in the docs repo behind its own installer. Product repos get no `.claude` folder, and the user's own review gate is never edited. |
| Standalone or embedded manual | Explicitly the agent's judgment call. The user permitted either. |

## Lint before you ship

```
python3 skills/doc-writing/scripts/doccheck.py <file.md> [--type spec|manual|report|readme|release-notes|plan|handoff]
                                               [--json] [--strict]
```

Eight checks, each citing the mined rule it enforces. Exit codes are 0 clean, 1 warnings present, 2 errors present. With `--strict`, info level findings fail too. A secret is always an error and always exits 2, and the matched text is never echoed, because printing it would put the secret back into the session.

| Check | Level | Catches |
|---|---|---|
| `secrets` | error | A credential, token, private absolute path, or address in the text (`B1`) |
| `bare-ref` | warning | A path, filename, commit hash, or PR number that is not a link or a code span (`B4`) |
| `undefined-jargon` | warning | An all caps acronym or coined phrase the document never glosses (`B6`) |
| `missing-diagram` | warning | No mermaid diagram, for the types that require one (`B5`) |
| `missing-section` | warning | No verification or remaining-tasks heading, per type (`B2`, `B18`) |
| `render` | warning | A table or list glued to the line above, a table with no separator row, an unclosed fence (`B12`) |
| `staleness` | warning | `TODO`, `TBD`, `FIXME`, `XXX`, `placeholder`, `待补充` (`B11`) |
| `list-numbering` | info | A flat list of more than 3 items using dashes instead of numbers |

Per type required sections, the acronym stoplist, staleness markers, and filename to type inference live in [`doccheck.config.json`](doccheck.config.json), editable without touching the script. Secret patterns stay in the script on purpose, so a document cannot weaken its own leak check.

The linter covers what a machine can see. It cannot tell you whether a claim was actually verified, whether a guide is a use case flow or a button list, or whether the inventory was enumerated first. Those stay with you.

Tests live in [`scripts/test_doccheck.py`](scripts/test_doccheck.py), 20 cases with a negative case per check, run with `python3 scripts/test_doccheck.py`.

## Keeping this skill true

These rules came from real document work, and real document work is what corrects them. When writing a document reveals that a rule here is wrong, missing, or too broad, file it.

```bash
node ~/.claude/agent-harness/bin/harness-feedback.mjs --feature skills/doc-writing \
  --verdict needs-update --why "..." --proposal "..."
```

Use `--verdict needs-update` when a rule is right in principle but stale in detail, and `--verdict missing-capability` when the document work revealed something this skill should cover and does not. `/harness-sync` drains the queue into real edits.

Filing takes one command and never blocks the document in progress. Write the document first, file second. This is the mechanism behind `B48`, which says a documentation practice that proves out gets written into the harness so it applies by default rather than living in one conversation.
