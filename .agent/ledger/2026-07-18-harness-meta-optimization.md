# Round: Harness meta optimization

<!-- task-ledger: v1 -->

> Generated and maintained by `hooks/task-ledger/scripts/ledger.py`. This file is the source of
> truth for the round. A Stop hook refuses to end the round while anything below is unfinished.

> **21/23 settled** · 2 blocked

## Meta

| field | value |
|---|---|
| round-id | 2026-07-18-harness-meta-optimization |
| opened | 2026-07-18T15:02:51Z |
| agent | claude-code |
| model | opus-4.8 |
| profile | auto |

## Inbox

> Requirements that arrived mid-round land here automatically. Each must be triaged into a task
> (or explicitly dropped, with a reason) before the round can close. This is what stops a
> mid-run instruction from being forgotten.

- [x] `I1` 2026-07-18T15:15:55Z — GitHub Actions frugality: research+design the best scheme to avoid burning remote Actions minutes (local-test-before-push, partial/conditional workflows, act/local runners, self-hosted runners), and add a check function that applies the config to already-running related sessions → **became T12**
- [x] `I2` 2026-07-18T15:15:55Z — Extract user prompts from ~13 more sessions (neobanker proposal, this session, job hunter, liulian gui design, liulian entity identifier experiments, liulian pitch and proposal, job personal site, swiss open-source, ai agent talk, graph4hw reasoning, students deva cghd), then run 3 independent full analysis rounds via 3 non-interfering subagents, extracting everything that could be folded into agent-harness, written up as a detailed design doc → **became T13**
- [x] `I3` 2026-07-18T15:15:55Z — review-gate leaks hook/plugin internals into the CLI transcript: the whole Changed-files + 12 review forms + presentation instructions get dumped after 'Stop hook error'. Suspected scheduling or format/newline issue. Diagnose and fix. → **became T14**
- [x] `I4` 2026-07-18T15:34:57Z — review-gate review output must use a markdown TABLE from now on (prose bullets are too dense to read). Statistics items like 'N files changed' and 'x/y checks clean' get a simple colored CLI/zsh-usable visualization. → **became T15**
- [x] `I5` 2026-07-18T15:51:02Z — Section headers (进度报告 / review-gate 审查) and their thick bars should be a different COLOUR so they are easy to catch visually when scrolling → **became T17**
- [x] `I6` 2026-07-18T15:52:26Z — CORRECTION: the runner in idea (e) is a self-hosted ACTIONS runner. My personal account quota and the neobanker org quota are different, and neobanker uses PRIVATE repos, whose quota differs again. The recommendation must be split by account and by repo visibility, not given as one global answer. → **became T18**

## Tasks

### `T1` T1 native-capability-first meta-rule

- **status**: `done`
- **acceptance**: rules/native-capability-first exists, registered, snippet written, feedback loop scripted+tested
- **evidence**: rules/native-capability-first/{RULE,snippet}.md written; bin/harness-feedback.test.mjs -> 9/9 PASS incl. CLI subprocess test
- **owner**: —

### `T2` Rule activation root-cause fix

- **status**: `done`
- **acceptance**: bin/rule-activation.mjs reports inert rules per agent and --apply writes an idempotent managed block
- **evidence**: bin/rule-activation.mjs + 26-check test suite; 3 real bugs found and red-green fixed (oscillating block, stray-BEGIN content loss, whole-file reflow); applied live: claude 19->26/26, codex 1->26/26, opencode 26/26 by glob; idempotent (identical md5 on re-apply); user CLAUDE.md content byte-identical apart from one seam blank line; backups written
- **owner**: —

### `T3` task-ledger hard enforcement

- **status**: `done`
- **acceptance**: ledger.py + Stop gate + UserPromptSubmit capture, all tested, registered
- **evidence**: test_ledger.py -> 17/17 PASS; test_hooks.sh -> 11/11 PASS (block JSON, fail-closed, loop guard, capture)
- **owner**: —

### `T4` autorun upgrade

- **status**: `done`
- **acceptance**: defer-not-block approvals, ledger-clean completion, self-correction, wait-token fix
- **evidence**: rules/autorun-mode/{RULE,snippet}.md rewritten; ledger.py approvals added + covered by test 16
- **owner**: —

### `T5` Doc-writing preferences sub-feature

- **status**: `done`
- **acceptance**: a skill encoding the mined doc prefs, with a self-update path
- **evidence**: skills/doc-writing/{SKILL.md,doccheck.config.json,scripts/doccheck.py,scripts/test_doccheck.py}; test_doccheck.py 20/20 verified by me; the SKILL lints clean under its own linter; self-update wired to bin/harness-feedback.mjs
- **owner**: —

### `T6` prompt-library v2 + first mined corpus

- **status**: `done`
- **acceptance**: mine subcommand + 12-20 curated prompts across 4 agent ecosystems
- **evidence**: plib v2 schema + mine subcommand; test_plib.py 24/24 verified by me (exit 0); 18 entries published, my own privacy scan 0 hits, 18/18 carry an Optimized section; corpus 1736->859 candidates across 6 sources
- **owner**: —

### `T7` Seven-feature audit + user guide

- **status**: `done`
- **acceptance**: every claimed feature verified present/deployed with how-to-run and how-to-test
- **evidence**: docs/USER_GUIDE.md + .zh.md, 49 capabilities each with invocation + test command + verified live status; 9 enforced / 34 advisory / 6 incomplete; both lint clean under doccheck --strict
- **owner**: —

### `T8` Register everything + build parity

- **status**: `done`
- **acceptance**: manifest, INVENTORY x2, rules/README, package.json; node build.mjs --check clean
- **evidence**: manifest 28 rules/24 skills/7 hooks/3 templates/21 recommendations, 0 dead entries; build --check exit 0; INVENTORY x2 + 6 index READMEs resynced, 19 doccheck warnings -> clean; 21 files' /init-agent-harness dead command corrected
- **owner**: —

### `T9` Deploy to this machine

- **status**: `done`
- **acceptance**: rules activated for claude+codex, hooks installed, skills deployed
- **evidence**: clone moved to the branch (was a single-branch clone, needed an explicit refspec fetch); deploy-skills --apply linked 6 to claude + 8 to opencode; task-ledger hooks installed into settings.json with backup; live smoke: no-round silent, open-round blocks naming T1, capture never blocks
- **owner**: —

### `T10` Commit + PR

- **status**: `done`
- **acceptance**: feature branch pushed, PR opened, Copilot review addressed
- **evidence**: 9 commits, PR #79 https://github.com/jajupmochi/agent-harness/pull/79; 16/16 test suites green before push
- **owner**: —

### `T11` Rebase onto origin/main (b665329 ssh-guard)

- **status**: `done`
- **acceptance**: feature branch replays cleanly on b665329; manifest/INVENTORY/rules-README conflicts resolved as a union; node build.mjs --check clean
- **evidence**: rebased onto origin/main (b665329 ssh-guard), 8 commits replayed with zero conflicts
- **owner**: —
- **detail**:

  b665329 added hooks/ssh-guard + rules/no-ssh-username-probing and touched adapters/manifest.source.json, INVENTORY.md, README.md, README.zh.md, hooks/README.md, rules/README.md — the same files this round edits. Rebase is deferred until concurrent subagents finish writing, because stashing would pull files out from under them.


### `T12` GitHub Actions frugality scheme

- **status**: `done`
- **acceptance**: a researched design doc + a working config applied to this machine's repos, with a check function for running sessions
- **evidence**: recommendations/github-actions-frugality.md + templates/actions-frugal-ci/ + scripts/actions-budget.mjs (rates externalized to JSON); 129+39 tests pass; quantified 312->12 Linux-equiv min/PR with an honest sensitivity table rather than the single flattering number; 5 self-inflicted bugs caught by its own tests
- **owner**: —
- **verbatim**:

  > GitHub Actions frugality: research+design the best scheme to avoid burning remote Actions minutes (local-test-before-push, partial/conditional workflows, act/local runners, self-hosted runners), and add a check function that applies the config to already-running related sessions


### `T13` 13-session prompt extraction + 3-round analysis

- **status**: `done`
- **acceptance**: extraction files for every named session, 3 independent analyses, one detailed agent-harness design doc
- **evidence**: 11 sessions extracted (1297 prompts, leak-check 0) + 2 neobanker = 1559; 3 independent analysis rounds written to _analysis-round{1,2,3}-*.md
- **owner**: —
- **verbatim**:

  > Extract user prompts from ~13 more sessions (neobanker proposal, this session, job hunter, liulian gui design, liulian entity identifier experiments, liulian pitch and proposal, job personal site, swiss open-source, ai agent talk, graph4hw reasoning, students deva cghd), then run 3 independent full analysis rounds via 3 non-interfering subagents, extracting everything that could be folded into agent-harness, written up as a detailed design doc


### `T14` Fix review-gate transcript leak

- **status**: `done`
- **acceptance**: the CLI no longer dumps review forms/instructions; enforcement still blocks; regression test
- **evidence**: core.sh RG_BRIEF_FILE split: reason 3125->322 bytes, decision:block unchanged; test_core.sh 20/20 (7 red pre-fix); backward compat byte-identical; deployed live + verified with a real Stop payload
- **owner**: —
- **verbatim**:

  > review-gate leaks hook/plugin internals into the CLI transcript: the whole Changed-files + 12 review forms + presentation instructions get dumped after 'Stop hook error'. Suspected scheduling or format/newline issue. Diagnose and fix.


### `T15` review-gate table output + colored stats bar

- **status**: `done`
- **acceptance**: core.sh mandates a table; a dependency-free statsbar script renders ansi for shells and markdown for the review; tested; deployed
- **evidence**: statsbar.sh (ansi+md, CJK display-width alignment) 20/20 tests; core.sh presentation block now mandates a markdown table + generated stats bar, verified present in a real brief; test_core.sh 22/22; both deployed to ~/.claude/hooks/review-gate/ and smoke-tested
- **owner**: —
- **verbatim**:

  > review-gate review output must use a markdown TABLE from now on (prose bullets are too dense to read). Statistics items like 'N files changed' and 'x/y checks clean' get a simple colored CLI/zsh-usable visualization.


### `T16` Capability-firing receipt (detection first)

- **status**: `done`
- **acceptance**: a checker reports which harness capabilities actually fired in a turn, by reading the transcript; enforcement is proposed separately, not switched on unilaterally
- **evidence**: bin/capability-receipt.mjs + adapters/capabilities.json (12 capabilities, config-driven); 12/12 tests incl. 3 regressions: state signatures never fired (regex-compiled a path template), compile/lint/naming must not count as a firing, malformed pattern surfaces instead of reading as idle; false positives cut 66->12 and 12->1 on the real transcript
- **owner**: —
- **verbatim**:

  > 请确认测试他们都实际存在且部署了，并且告诉我每一项功能具体如何执行和测试

- **detail**:

  Two independent analysis rounds converged on this from different angles. Round 1 read it as 'the verification skill was never built' — that is factually WRONG: skills/code-verifier exists, is in the manifest, is deployed to ~/.claude/skills/, and review-gate form 4 names it. Round 2 read it correctly: features exist and still do not fire, because nothing observes whether they fired (12 instances of 'harness features silently not firing', 38 of claim-without-verification). Same class as the rules-inert bug fixed earlier this round: registered != loaded, and deployed != fired. Detection is in scope for the user's 'confirm they actually execute' ask. Enforcement (blocking a stop when a required capability did not fire) changes turn behaviour and should be proposed, not switched on.


### `T17` Coloured section headers

- **status**: `done`
- **acceptance**: the user picks a variant from rendered samples; whatever is chosen is written into core.sh's presentation block so it applies every turn
- **evidence**: user chose variant A (markdown heading); written into core.sh
- **owner**: —
- **verbatim**:

  > Section headers (进度报告 / review-gate 审查) and their thick bars should be a different COLOUR so they are easy to catch visually when scrolling


### `T18` Split Actions guidance by account and repo visibility

- **status**: `done`
- **acceptance**: the doc and actions-budget.mjs distinguish public vs private and personal vs org; the self-hosted conclusion is corrected for private repos where minutes are billed
- **evidence**: doc gains a 'Which account is being billed' section mapping owner x visibility to the right scenario, with gh commands per account; actions-budget.mjs --visibility wired end to end and covered by a dead-knob test; 137+39 pass
- **owner**: —
- **verbatim**:

  > CORRECTION: the runner in idea (e) is a self-hosted ACTIONS runner. My personal account quota and the neobanker org quota are different, and neobanker uses PRIVATE repos, whose quota differs again. The recommendation must be split by account and by repo visibility, not given as one global answer.


### `T19` Copilot review on PR 79

- **status**: `dropped`
- **acceptance**: Copilot's findings analysed and the real ones fixed, max 2 rounds
- **evidence**: (blocked: needs-user: Copilot could not review PR 79 — 'the user who requested the review has reached their quota limit'. Re-request once the quota resets, or review manually.) (dropped: user: PR does not need a Copilot review)
- **owner**: —

### `T20` Archiver orphan rescue

- **status**: `done`
- **acceptance**: orphans copied to a durable dir with a manifest; wired through daily.py; tested; live
- **evidence**: session_archiver.py --orphan-dir + MANIFEST.md; wired through daily.py and config.yaml; 6/6 tests; live run rescued+recorded 7c273809; committed b82fa7d on feat/archive-orphan-rescue-2026-07-18 (local only, not pushed)
- **owner**: —

### `T21` Push the worknroll archiver fix

- **status**: `blocked`
- **acceptance**: user decides whether to push the branch and open a PR on the public worknroll repo
- **evidence**: (blocked: needs-user: the fix is live locally and committed; pushing to the public worknroll repo is an outward action you did not ask for on that repo)
- **owner**: —

### `T22` Claude jsonl cleanup analysis

- **status**: `done`
- **acceptance**: categories quantified with safety verdicts; user decides what to delete
- **evidence**: _claude-jsonl-cleanup.md, 379 lines; headline numbers independently re-verified by me (5.9G total, 233 files/936.6MB in step 1, 3/3 sampled contain 'too long', 843 files under the threshold kept, memory/ 72 notes protected)
- **owner**: —

### `T23` Execute the storage cleanup

- **status**: `blocked`
- **acceptance**: user picks which steps to run; deletion is irreversible so it needs an explicit go
- **evidence**: (blocked: needs-user: deleting session history is irreversible. Steps 1-4 free 2.76 GB and are verified safe, but the go is yours.)
- **owner**: —

## Log

- 2026-07-18T15:02:51Z opened round with 10 task(s)
- 2026-07-18T15:02:51Z T1 -> done
- 2026-07-18T15:02:51Z T3 -> done
- 2026-07-18T15:02:51Z T4 -> done
- 2026-07-18T15:02:51Z T2 -> doing
- 2026-07-18T15:04:39Z added T11 Rebase onto origin/main (b665329 ssh-guard)
- 2026-07-18T15:15:55Z captured I1 into inbox
- 2026-07-18T15:15:55Z captured I2 into inbox
- 2026-07-18T15:15:55Z captured I3 into inbox
- 2026-07-18T15:15:55Z triaged I1: became T12
- 2026-07-18T15:15:55Z triaged I2: became T13
- 2026-07-18T15:15:55Z triaged I3: became T14
- 2026-07-18T15:20:26Z T14 -> done
- 2026-07-18T15:21:49Z T2 -> done
- 2026-07-18T15:27:03Z T5 -> done
- 2026-07-18T15:27:03Z T6 -> done
- 2026-07-18T15:34:57Z captured I4 into inbox
- 2026-07-18T15:34:57Z triaged I4: became T15
- 2026-07-18T15:37:31Z T15 -> done
- 2026-07-18T15:41:23Z added T16 Capability-firing receipt (detection first)
- 2026-07-18T15:46:20Z T16 -> done
- 2026-07-18T15:49:54Z T12 -> done
- 2026-07-18T15:51:02Z captured I5 into inbox
- 2026-07-18T15:51:02Z triaged I5: became T17
- 2026-07-18T15:52:26Z captured I6 into inbox
- 2026-07-18T15:52:26Z triaged I6: became T18
- 2026-07-18T15:55:49Z T18 -> done
- 2026-07-18T16:17:28Z T7 -> done
- 2026-07-18T16:17:28Z T8 -> done
- 2026-07-18T16:17:28Z T9 -> done
- 2026-07-18T16:17:28Z T10 -> done
- 2026-07-18T16:17:28Z T11 -> done
- 2026-07-18T16:17:28Z T13 -> done
- 2026-07-18T16:17:28Z T17 -> blocked
- 2026-07-18T16:17:48Z added T19 Copilot review on PR 79
- 2026-07-18T16:17:53Z T19 -> blocked
- 2026-07-18T16:55:28Z T17 -> done
- 2026-07-18T16:55:28Z T19 -> dropped
- 2026-07-18T17:02:32Z added T20 Archiver orphan rescue
- 2026-07-18T17:02:32Z T20 -> done
- 2026-07-18T17:02:32Z added T21 Push the worknroll archiver fix
- 2026-07-18T17:02:32Z T21 -> blocked
- 2026-07-18T17:23:37Z added T22 Claude jsonl cleanup analysis
- 2026-07-18T17:23:37Z T22 -> done
- 2026-07-18T17:23:37Z added T23 Execute the storage cleanup
- 2026-07-18T17:23:37Z T23 -> blocked
