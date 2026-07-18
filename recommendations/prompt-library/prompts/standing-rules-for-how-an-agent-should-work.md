---
title: Standing rules for how an agent should work
scenarios: agent-tooling,config,ui
tags: confirmation,preflight,phasing,visual-iteration
source: claude-code
session:
date: 2026-04-28
---

# Standing rules for how an agent should work

> Use once, when you notice you are giving the same corrections in every session.

## Original

```text
Add these rules into the user level configuration for all tasks:

Before making changes, list the exact selectors/files you intend to modify and show me a 1-line plan. Wait for my 'go' before editing.

Before running any plugin command, first verify the plugin is installed and the command is not deprecated. Show me the verification output, then proceed.

For medium and big tasks, break it into numbered phases with explicit deliverables per phase. Show me the full phase plan first, then execute phase 1 and pause for review before continuing.

For UI design tasks which have a reference, always do the following: Here is a reference image of the visual style I want: [attach image or describe precisely]. Iterate on the CSS in [file] autonomously: (1) make a change, (2) use a browser automation tool to navigate and screenshot the target element, (3) compare against the reference and self-critique on color, typography, spacing, ornamentation, (4) repeat up to 8 iterations until visually matching. Show me the screenshot after each iteration with a 1-line rationale. Stop early if you judge the match is excellent.
```

## Optimized

```text
Add these standing rules to my agent configuration, applying to every task.

1. Confirm before editing. List the exact files and symbols you intend to change, plus a one-line
   plan, then wait for my "go". This applies even when the change looks trivial. If my message
   already names the exact target and the intent, treat that as the plan and the go.

2. Preflight any tool you have not used this session. Verify it is installed and not deprecated,
   show me the one-line verification, then use it. If verification fails, stop and tell me rather
   than silently substituting another tool.

3. Phase medium and large work. Anything touching three or more files, or taking more than a handful
   of steps, gets numbered phases with explicit deliverables per phase. Show me the whole phase plan
   first, execute phase 1, then pause for review.

4. For UI work with a visual reference, run an autonomous loop instead of guessing once. Per
   iteration: make one focused change, screenshot the target element in a real browser, critique
   against the reference on colour, typography, spacing and ornamentation by name, and show me the
   screenshot with a one-line rationale for the next change. Cap it at 8 iterations, stop early on a
   good match, and stop and ask if you are not converging after 3. This loop suspends rule 1 for the
   duration, because I pre-authorized it.
```

## When to use

Use once, when you notice you are giving the same corrections in every session. These four cover the
most common failure modes: editing the wrong thing, calling a tool that does not exist, disappearing
into a large task, and one-shot guessing at a visual target.

- Setting up a new machine or a new agent tool.
- After a session went wrong in a way that a standing rule would have prevented.

## When NOT to use

Do not add rule 1 to a fully autonomous run. Confirm-before-edit and unattended operation contradict
each other; pick one per session and say which.

Do not add rule 4 without checking that browser automation is actually available. Without a real
screenshot the loop degrades to blind edits, which is worse than a single considered attempt.

Skip the whole set for a throwaway script. Governance overhead exceeds the value on code you will
delete today.
