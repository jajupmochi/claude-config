---
name: prompt-library
description: Use to save and reuse good prompts across projects and agents. Many prompts recur (a detailed feature spec, a "design the whole thing" brief, a manual/onboarding prompt) and are worth reusing verbatim or as a reference. This curates them as browsable, greppable Markdown — with a PRIVACY GATE that refuses to store anything still containing paths/emails/tokens/usernames/codenames, so the library stays publishable.
policy:
  allow_implicit_invocation: true
---

# prompt-library

Overhaul task 9. Reusable prompts (e.g. a very detailed feature-update brief; a "design the whole X" prompt
that transfers across sibling projects; a manual/onboarding prompt) get curated once, de-privacy'd, tagged by
scenario, and made easy for a human to find and for an agent to reuse.

## Use

- **Save** a prompt (body on stdin) — the privacy gate runs first and REFUSES if it still contains private
  content, so you de-privacy before it lands in a publishable library:
  ```
  python3 scripts/plib.py add --title "Redesign a dashboard" --scenarios ui,redesign --source claude-code < prompt.txt
  ```
- **Browse**: read `INDEX.md` (title · scenarios · source · file). **Find**: `plib.py find --query "terms"`.
- **Just check** some text for private content: `plib.py scan < text` (exit 1 if it finds any).

## Privacy gate (heuristic, not a guarantee)

`add` and `scan` flag GENERIC private content: absolute `/home` `/media` `/mnt` paths, emails, and
token-shaped strings (`sk-`/`ghp_`/`gho_`/`github_pat_`). Matches in the body OR the title block the save.

**User-specific terms** (your username, your project codenames) are deliberately NOT hardcoded in the tool —
shipping them would publish them (and the repo's own CI privacy scan bans codename literals in content
modules). Put them in a LOCAL, un-published file, one term per line, and the gate will also flag those:

```
export PLIB_PRIVATE_TERMS=~/.config/agent-harness/private-terms.txt   # else this default path is auto-used
```

For anything the heuristic misses, still review manually (pairs with the `privacy-redact` skill).

## Storage

`<root>/prompts/<slug>.md` (frontmatter: title/scenarios/source/tags + the de-privacy'd body) + `INDEX.md`.
Default root `recommendations/prompt-library` so the library ships with agent-harness and is reusable
cross-project. LLM-as-component: store/index/find/scan are deterministic; the model writes and adapts the
prompt text.

Status: v0.1 (add-with-privacy-gate / index / find / scan), tested (`test_plib.py`, 6/6). Planned: the first
curated batch mined from Claude Code / Codex / Copilot / opencode history (task 9 asks for this — it is
analysis work, not yet done), and per-prompt "optimized variant + when-to-use" notes.
