# AI-generated code review — landscape, analysis & the `review-gate` plugin

Reference + analysis behind the `review-gate` hook plugin (see `hooks/review-gate/`). Researched 2026-06-24.
Goal: make review of AI-agent-generated code **enforced on every code-changing turn, in every session, never skipped** — because review (not generation) is now the bottleneck.

> Caveat: head-to-head "bug catch rate" numbers below come from a vendor (Greptile) benchmark; treat as indicative, not neutral.

## 1. Why this matters (2026 data)

| Signal | Figure | Source |
|---|---|---|
| AI-assisted PRs vs human PRs | **~1.7× more defects** | [secondtalent](https://www.secondtalent.com/resources/ai-generated-code-quality-metrics-and-statistics-for-2026/) |
| AI PRs introducing ≥1 OWASP Top-10 issue | **~45%** | [metacto](https://www.metacto.com/blogs/establishing-code-review-standards-for-ai-generated-code) |
| Technical-debt rise within 6 months of AI adoption | **+30–41%** | [quality crisis](https://www.ofashandfire.com/blog/ai-generated-code-quality-crisis) |
| Extra review time for senior engineers | **+20–35%** (now the bottleneck) | [comprehension debt](https://stepto.net/blog/comprehension-debt-ai-code-understanding-2026) |
| "generated 5–7× faster than humans can understand it" | 5 research groups, Feb 2026 | [comprehension debt](https://stepto.net/blog/comprehension-debt-ai-code-understanding-2026) |

## 2. Tool comparison (tabular)

### 2.1 Capability matrix

| Tool | Whole-codebase context | Scope | Runs where | Enforced vs skippable | Auto-trigger | OSS | Pricing (2026) |
|---|---|---|---|---|---|---|---|
| **Greptile** | **Yes** (indexes full repo) | PR diff vs whole repo | Cloud / PR | On-demand + auto-on-PR | On PR | No | ~$30/dev/mo (50 reviews, +$1 overage) |
| **CodeRabbit** | Partial (diff-centric + some context) | PR diff | Cloud / PR (GH/GL/BB/Azure) | auto-on-PR | On PR | No | ~$24/dev/mo |
| **Qodo Merge** (ex-CodiumAI) | Partial + **rules engine** (enforce standards) | PR diff | Cloud / PR | auto-on-PR | On PR | PR-Agent core is OSS | Freemium → paid |
| **Graphite** (Diamond) | Partial | PR + **stacked diffs** workflow | Cloud / PR | auto-on-PR | On PR | No | Per-seat |
| **Anthropic "Claude Code Review"** (managed, 2026-03) | Multi-agent over diff + context | PR | Cloud (Anthropic infra) | auto-on-PR | On PR | No | token-based ~$15–25/review (Team/Ent) |
| **`/code-review` plugin** (official, in Claude Code) | diff + CLAUDE.md + git history | PR | **Local** (your Claude Code) | **On-demand** (you call it) | No | **Yes** | Free (your tokens) |
| **`/security-review`** + claude-code-security-review (GH Action) | diff, security lens | PR / diff | Local or CI | On-demand / CI | CI optional | **Yes** | Free |
| **`review-gate`** (this plugin) | changed files + project linters/tests | **every turn (working tree)** + commit gate | **Local hooks** | **Enforced (hook) — cannot skip** | **Every edit / turn** | **Yes** | Free |

### 2.2 One-liner + best-fit

| Tool | One-liner | Best for |
|---|---|---|
| Greptile | Highest recall via full-repo context (vendor benchmark **82%** bug catch vs CodeRabbit **44%**) | Teams wanting max bugs caught at PR |
| CodeRabbit | Most-installed, broadest PR workflow (summaries, inline, linter integ.) | Fast PR-workflow coverage |
| Qodo Merge | Custom, enforceable team rules engine | Teams with strict coding standards |
| Graphite | Review-as-systems-problem via stacked diffs | High-throughput PR teams |
| Anthropic Claude Code Review | Managed multi-agent PR review, zero setup | Team/Enterprise GitHub orgs |
| `/code-review` | 4-agent local PR review (CLAUDE.md compliance + bug + history, conf ≥80) | On-demand PR check, no SaaS |
| `/security-review` | Claude security pass on a diff | Pre-merge security gate |
| **`review-gate`** | **Local, hook-enforced, runs every code turn, can't be skipped** | **Closing the "review got skipped" gap for solo/agentic dev** |

**Conclusion.** Products (Greptile/CodeRabbit/…) win at **PR-level, full-codebase, cloud** review and are great as a *merge gate*. None of them give **local, every-edit, un-skippable** review — that can only be done with **Claude Code hooks**. So `review-gate` complements (does not replace) the PR-level tools.

Sources: [Greptile 8-tool comparison](https://www.greptile.com/content-library/best-ai-code-review-tools) · [DEV best-of-2026](https://dev.to/heraldofsolace/the-best-ai-code-review-tools-of-2026-2mb3) · [getoptimal](https://getoptimal.ai/blog/best-ai-code-review-tools) · [Claude Code Review docs](https://code.claude.com/docs/en/code-review)

## 3. Approaches & standards (analysis)

- **Two-pass review** — *Run-gate* (what can this code DO? scan for write/exec/install/network verbs) then *Ship-gate* (is it correct? make it prove itself by running/tests). [Read before you run](https://medium.com/@fahimulhaq/read-before-you-run-how-to-review-ai-code-safely-f34aa7e1904f)
- **Treat AI code like code from a stranger** — no intent/accountability/context. [Bright Security](https://brightsec.com/blog/5-best-practices-for-reviewing-and-approving-ai-generated-code/) · [metacto standards](https://www.metacto.com/blogs/establishing-code-review-standards-for-ai-generated-code)
- **Three frameworks**: OWASP Top-10, OWASP Top-10 for LLM Apps, NIST SP 800-218A (SSDF for GenAI).
- **Winning pattern**: full-codebase context + low false-positives + moving from "comment" to "fix" (agentic). [Sourcegraph](https://sourcegraph.com/blog/ai-code-review) · [Cloudflare at scale](https://blog.cloudflare.com/ai-code-review/) · [coding guidelines for AI](https://stackoverflow.blog/2026/03/26/coding-guidelines-for-ai-agents-and-people-too/)

### Claude Code native enforcement mechanisms

| Mechanism | What it gives | Skippable? |
|---|---|---|
| `CLAUDE.md` rules / skills (code-verifier, research-critic) | Guidance the model *should* follow | **Yes (model discretion)** |
| `/code-review`, `/security-review`, subagents | Powerful on-demand review | **Yes (must invoke)** |
| **Hooks** (`PostToolUse`, `Stop`, `PreToolUse`) | **Deterministic, harness-run gates** | **No — always run** |
| Hook `type:"command"` | shell gate (lint/test/track) | no |
| Hook `type:"prompt"` | single Haiku judgment, returns `{ok,reason}` | no |
| Hook `type:"agent"` (experimental) | subagent w/ tool access, reads files/runs cmds | no |
| `PreToolUse permissionDecision:"deny"` | blocks a tool **even under `--dangerously-skip-permissions`** | no |

Refs: [hooks guide](https://code.claude.com/docs/en/hooks-guide) · [security-guidance plugin (model-review-via-hook)](https://code.claude.com/docs/en/security-guidance) · [Auto-reviewing Claude's code (Stop-hook pattern)](https://www.oreilly.com/radar/auto-reviewing-claudes-code/) · [hooks production patterns](https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns) · [code-review plugin README](https://github.com/anthropics/claude-code/blob/main/plugins/code-review/README.md) · [claude-code-security-review](https://github.com/anthropics/claude-code-security-review) · [subagent code-reviewer examples](https://github.com/VoltAgent/awesome-claude-code-subagents)

## 4. `review-gate` design (tiered, hook-enforced)

| Tier | Hook event | Action | Blocks? | Cost |
|---|---|---|---|---|
| **T0** | `PostToolUse(Edit\|Write)` → `track.sh` | log each changed file per session; (`.py` lint already auto-applied by `ruff-format-on-edit`) | no | negligible |
| **T1** | `Stop` → `gate.sh` | on code change: run linters (ruff/shellcheck) + force one review round whose feedback is a **Markdown report** naming each review form + the tool it uses, and — when a minimal function/module changed — mandating **per-function/module AI review (DEFAULT ON)**; Claude must present findings as a **markdown list** in-session. `{"decision":"block"}` until lint-clean + reviewed. Loop-guarded (≤3), fail-open | **yes** | one round + per-module review every code-turn (token cost, see note) |
| **T2** | `PreToolUse(Bash)` (`git commit/push`) → `precommit.sh` | commit is FREE; only remote-publishing (`git push` / `gh pr create\|merge` / `gh release create`) is denied (`exit 2`) unless the project is on `push-whitelist.txt` — **or** a one-shot `allow-push-once` token is armed (`touch ~/.claude/hooks/review-gate/allow-push-once`) for a single user-authorized push, consumed after one push, no whitelist change | **yes** (push only) | negligible |
| **STRICT** (opt-in) | `Stop` → `type:"agent"` hook | model-judged deep review of the diff (reads files, runs tests). Experimental + adds latency | yes | higher |
| **T3** (delegated) | — | PR-level: `/code-review` (+ultra) + CodeRabbit/Greptile + security GH Action | — | — |

Design principles applied: full-context (project linters + changed files), low false-positive (only blocks on real lint failures or the mandatory once-per-changeset review), and *enforced not advisory*.

### Cost / token note (important)

The default **per-function/module AI review** (T1) makes the agent re-read and reason about each changed function/module on **every code-changing turn** and write up findings — this is **noticeably more token-expensive** than lint-only gating. It is a deliberate trade: spend tokens to catch the logic/security/contract bugs that linters miss. To spend less: rely on T0 lint + T2 commit-gate only, narrow the watched file types, or raise the trivial-change threshold. The optional STRICT `type:"agent"` Stop hook costs **even more** (spawns a separate reviewing subagent each turn).

## 5. Deployment (all sessions / every edit / never skip)

1. **Scripts** live in `~/.claude/hooks/review-gate/` (stable path, not on a removable mount). Versioned source in this repo `hooks/review-gate/scripts/`.
2. **Global activation** for every session: the hook block is merged into **`~/.claude/settings.json`** (user scope = all projects). Snippet: `hooks/review-gate/settings.snippet.json`.
3. **Cannot-skip guarantees**: `Stop` block keeps Claude working until review passes; `PreToolUse exit 2` blocks unreviewed commits; for org-hard-enforcement, the same hooks can go in **managed policy settings** (run unless `disableAllHooks` is set *there* too).
4. **STRICT model review** (`type:"agent"` Stop hook): ship-ready in `hooks/review-gate/strict.snippet.json`, off by default (experimental + latency); enable per-need.
5. **Escape hatch** (documented): `disableAllHooks: true` in settings, or `rm ~/.claude/review-state/<session>.changed` to clear a stuck gate.

**Honest trade-off**: literal per-*edit* AI review is wasteful, so the model-judgment review is enforced **once per code-changing turn** at `Stop` (the practical reading of "every edit, never skip"); deterministic checks run continuously. STRICT mode adds true per-turn model review when wanted.

## 6. References (all sources)

**Tools / landscape** — [Greptile comparison](https://www.greptile.com/content-library/best-ai-code-review-tools) · [DEV 2026](https://dev.to/heraldofsolace/the-best-ai-code-review-tools-of-2026-2mb3) · [getoptimal](https://getoptimal.ai/blog/best-ai-code-review-tools) · [Surmado CodeRabbit alternatives](https://www.surmado.com/blog/best-coderabbit-alternatives-2026)
**Practices / standards** — [Read before you run](https://medium.com/@fahimulhaq/read-before-you-run-how-to-review-ai-code-safely-f34aa7e1904f) · [Bright Security](https://brightsec.com/blog/5-best-practices-for-reviewing-and-approving-ai-generated-code/) · [metacto](https://www.metacto.com/blogs/establishing-code-review-standards-for-ai-generated-code) · [GitHub Docs](https://docs.github.com/en/copilot/tutorials/review-ai-generated-code) · [Sourcegraph](https://sourcegraph.com/blog/ai-code-review) · [Cloudflare](https://blog.cloudflare.com/ai-code-review/) · [Stack Overflow](https://stackoverflow.blog/2026/03/26/coding-guidelines-for-ai-agents-and-people-too/)
**Quality data** — [secondtalent metrics](https://www.secondtalent.com/resources/ai-generated-code-quality-metrics-and-statistics-for-2026/) · [comprehension debt](https://stepto.net/blog/comprehension-debt-ai-code-understanding-2026) · [quality crisis](https://www.ofashandfire.com/blog/ai-generated-code-quality-crisis)
**Claude Code mechanisms** — [hooks guide](https://code.claude.com/docs/en/hooks-guide) · [code-review docs](https://code.claude.com/docs/en/code-review) · [security-guidance](https://code.claude.com/docs/en/security-guidance) · [Auto-reviewing (O'Reilly)](https://www.oreilly.com/radar/auto-reviewing-claudes-code/) · [hooks patterns](https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns) · [code-review plugin](https://github.com/anthropics/claude-code/blob/main/plugins/code-review/README.md) · [claude-code-security-review](https://github.com/anthropics/claude-code-security-review) · [subagents blog](https://claude.com/blog/subagents-in-claude-code) · [awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
