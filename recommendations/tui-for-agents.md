# Terminal / TUI Setup for Orchestrating AI Coding Agents

**Task 8 — grounded recommendation doc.** Target environment: Ubuntu, where full
IDEs (VS Code / JetBrains) are unstable and crash. Goal: a terminal-first stack
that gives VS-Code-like capability for driving multiple AI coding agents, with:

1. **Multiple concurrent sessions**
2. **Multiple sub-agents** + switching / interacting between them
3. **Interaction between sessions / sub-agents**
4. **Code diff review**
5. **Human-in-the-loop (HITL)** approve / reject flows

Throughout, "verified" means a claim was checked against the tool's own GitHub /
site; "unverified" means it appeared in secondary write-ups only and should be
confirmed before relying on it.

---

## TL;DR recommendation

- **Primary stack:** `zellij` (workspace/multiplexer) + **claude-squad** (agent
  session orchestrator with git-worktree isolation) + `lazygit` + `delta`
  (diff review + staging) + each agent CLI's own built-in HITL prompt.
- **Runner-up multiplexer:** `tmux` — pick it over Zellij if you live on SSH /
  remote servers or need the mature scripting ecosystem (claude-squad itself is
  built on tmux, so tmux is effectively always present under the hood).
- **Honest gap:** no single terminal tool cleanly does requirement (3),
  *rich interaction between running agents*. The orchestrators give you
  side-by-side isolation and manual hand-off; true agent-to-agent messaging
  exists only in newer, less-proven tools (see the gaps section).

---

## 1. Terminal multiplexers / workspace TUIs

These give you the multi-pane, multi-session canvas. They satisfy (1) directly
and (2) by convention (one agent per pane/tab). They do **not** know anything
about agents, diffs, or approvals — they are the substrate.

### tmux
- **What:** The veteran terminal multiplexer. Panes, windows, detachable
  sessions that survive SSH drops. Unix-philosophy: minimal, scriptable,
  universally available.
- **Maps to reqs:** (1) strong — detachable persistent sessions; (2) manual —
  one agent per pane/window, switch with prefix keys; (3) only via scripting
  (`send-keys` to pipe text between panes); (4)/(5) — none natively (delegated to
  the agent CLI + a diff tool).
- **Install (Ubuntu):** `sudo apt install tmux`
- **License:** ISC. **URL:** <https://github.com/tmux/tmux>

### Zellij
- **What:** Modern Rust multiplexer. Sensible defaults with **no config file**,
  on-screen keybinding hints, **floating and pinned panes** (a log/monitor pane
  that stays on top — tmux cannot do this with its strictly-tiled panes),
  layouts, and a WASM-sandboxed plugin system.
- **Maps to reqs:** (1) strong — sessions persist like tmux, work identically
  over SSH; (2) manual but the floating/pinned panes make watching several
  agents at once nicer; (3) via layouts + plugins (still not agent-aware); (4)/(5)
  — none natively.
- **Why it wins for many agent panes:** pinned floating panes let you keep one
  agent's output hovering while you work others; zero-config first run; visual
  keybinding hints lower the cognitive load of juggling many panes.
- **Install (Ubuntu):** `cargo install zellij` — or download the release binary
  from GitHub (`bash <(curl -L zellij.dev/launch)`), or `sudo snap install zellij`.
  *(No official apt package.)*
- **License:** MIT. **URL:** <https://github.com/zellij-org/zellij>

### WezTerm
- **What:** GPU-accelerated terminal **emulator** with *built-in* multiplexing
  (so you don't strictly need tmux/Zellij). Lua-configured; multiplexing works
  locally and over SSH domains.
- **Maps to reqs:** (1) yes — panes/tabs/workspaces, and its mux server persists;
  (2) manual; (3) via Lua scripting; (4)/(5) — none natively. **Caveat for this
  user:** WezTerm needs a GUI environment (it *is* the terminal window). On an
  Ubuntu box where the graphical stack is the thing that crashes, a GUI-bound
  emulator is a weaker bet than a multiplexer you can run inside any stable
  terminal (or headless over SSH). tmux/Zellij survive a GUI restart; WezTerm's
  window does not.
- **Install (Ubuntu):** official apt repo, or `sudo apt install wezterm` from
  their repo; also Flatpak.
- **License:** MIT. **URL:** <https://github.com/wezterm/wezterm>

**Multiplexer pick: Zellij** for a fresh setup (floating panes + zero-config),
with **tmux** as the safe, ubiquitous fallback — and note tmux is a hard
dependency of claude-squad anyway.

---

## 2. Agent-orchestration TUIs built for AI CLIs

These are the category that actually maps to the hard requirements (2), (3),
(5). They wrap the agent CLIs, give each task an isolated git worktree, and put
many agents behind one TUI.

### claude-squad  *(verified — primary pick in this category)*
- **What:** Go TUI that manages multiple AI terminal agents at once. Each task
  gets an **isolated git worktree** (same repo, own branch, own working dir), and
  each agent runs in its own **tmux** session under the hood. Supported agents
  via configurable launch commands: **Claude Code, Codex, Gemini, Aider,
  OpenCode, Amp**.
- **Maps to reqs:**
  - (1) **Multiple sessions** — core purpose; many agents in parallel, each
    isolated.
  - (2) **Multiple sub-agents + switching** — central instance list; select/
    switch between agent instances in one terminal.
  - (3) **Interaction between sessions** — *limited.* Isolation is the point, so
    cross-agent talk is manual (you review one worktree's branch, then feed
    results to another). No built-in agent-to-agent message bus.
  - (4) **Diff review** — yes: "checkout" a change to **pause** the session and
    review modifications before committing.
  - (5) **HITL** — yes: review-before-apply, plus an optional **auto-accept**
    mode for background completion when you want to let it run.
- **Install (Ubuntu):**
  - Homebrew (Linuxbrew): `brew install claude-squad` then optionally
    `ln -s "$(brew --prefix)/bin/claude-squad" "$(brew --prefix)/bin/cs"`
  - or the upstream install script from the README.
  - **Prereqs:** `tmux` and `gh` (GitHub CLI).
- **License:** AGPL-3.0. **URL:** <https://github.com/smtg-ai/claude-squad>
- **Note on "Crystal":** the older *Crystal* multi-agent tool has been rebranded
  **Nimbalyst** — treat "Crystal" as a legacy name, not a separate current
  option. (<https://nimbalyst.com/>)

### opencode  *(verified — strong single-agent TUI with native multi-session)*
- **What:** Popular open-source terminal-native coding agent (Bubble Tea TUI). A
  **persistent background server** + TUI client, so sessions survive terminal
  disconnects / SSH drops / sleep. Connects to many model providers (Anthropic,
  OpenAI, Gemini, Bedrock, OpenRouter, …). Stores conversations/sessions in
  SQLite; LSP support; tracks file changes during a session.
- **Maps to reqs:** (1) **native multiple concurrent sessions**, each with its
  own context/history/model — e.g. a "research" session separate from an
  "implementation" one; (2) sessions ≈ sub-agents, switch within the TUI; (3)
  not a cross-agent bus (sessions are independent); (4) it tracks and shows file
  changes; (5) built-in permission/approval prompts (see §4).
- **Install (Ubuntu):** `npm i -g opencode-ai` (or the install script / release
  binary). **License:** MIT.
- **URL:** <https://github.com/sst/opencode>  *(note: an older repo lives at
  `opencode-ai/opencode`; the actively maintained one is `sst/opencode`.)*

### Newer orchestrators *(exist per listings; deeper feature claims UNVERIFIED)*

These appear in curated directories and secondary write-ups and are worth a look,
but I could not fully verify each feature against the source in this pass — treat
specifics as **unverified** until you check the repo:

- **agent-deck** — "Terminal session manager for AI coding agents. One TUI for
  Claude, Gemini, OpenCode, Codex, and more." Worktree-aware, MCP integration.
  <https://github.com/asheshgoplani/agent-deck> *(repo confirmed to exist;
  feature depth unverified)*
- **Conduit** — run Claude Code / Codex / Gemini side-by-side, tab-based session
  management, real-time streaming, token tracking. <https://getconduit.sh/>
  *(site returned 403 to automated fetch; unverified)*
- **thurbox** — multi-session TUI orchestrator over persistent tmux sessions,
  git-worktree isolation, remote SSH sessions, and **inter-session messaging**
  (would address req 3). *Unverified — confirm before relying on it.*
- **amux** — "agent multiplexer" for dozens of parallel Claude Code sessions,
  web dashboard, watchdog, kanban, **agent-to-agent REST API**. *Unverified.*
- **hcom** — shared **messaging / event bus** that hooks Claude Code, Codex,
  OpenCode and others so agents can message/observe/spawn each other mid-turn
  (directly targets req 3). *Unverified — most interesting for interaction, least
  proven.*
- **ntm (Named Tmux Manager)** — spawn/tile/coordinate multiple agents across
  tmux panes with a command palette. *Unverified.*

Curated directories to track for new entrants:
<https://github.com/bradAGI/awesome-cli-coding-agents> and
<https://github.com/andyrewlee/awesome-agent-orchestrators>.

---

## 3. TUI diff / review tools (req 4)

The orchestrator pauses the agent; these let you actually *read* the change and
stage it. Two axes: a **git TUI** (navigate/stage/commit) and a **diff pager**
(make the diff readable). Best results combine one of each.

### lazygit  *(git TUI — pick)*
- **What:** Full-featured terminal UI for git: staging by file/hunk/line,
  interactive rebase, custom patches, **worktree support** (pairs naturally with
  claude-squad's worktrees), branch management.
- **Maps to reqs:** (4) strong — the primary human review + stage + commit
  surface after an agent edits; (5) it *is* the human gate for what gets
  committed. Can use **delta** or **difftastic** as its diff pager
  (`git.paging.externalDiffCommand`).
- **Install (Ubuntu):** `sudo apt install lazygit` (recent releases) or
  `go install github.com/jesseduffield/lazygit@latest`, or via `brew`.
- **License:** MIT. **URL:** <https://github.com/jesseduffield/lazygit>

### gitui
- **What:** Blazing-fast Rust git TUI. Lighter and quicker to start than lazygit
  on very large repos.
- **Maps to reqs:** (4) yes — stage/commit/diff; slightly fewer power features
  than lazygit (e.g. interactive-rebase workflows are less deep).
- **Choose it when:** huge repos where startup speed / memory matter.
- **Install (Ubuntu):** `cargo install gitui` (or release binary).
- **License:** MIT. **URL:** <https://github.com/gitui-org/gitui>

### delta (git-delta)  *(diff pager — pick)*
- **What:** Syntax-highlighting pager for git diffs: line numbers, side-by-side
  view, themes, word-level highlighting. Configured as git's `core.pager` and/or
  as lazygit's pager.
- **Maps to reqs:** (4) makes every diff far more readable; pure viewer (no
  staging). Best combined with lazygit for the staging half.
- **Install (Ubuntu):** `sudo apt install git-delta` (the binary is `delta`), or
  `cargo install git-delta`.
- **License:** MIT. **URL:** <https://github.com/dandavison/delta>

### difftastic (difft)
- **What:** **Structural** diff — parses syntax and diffs the tree, so it ignores
  noise like reflowed whitespace and shows semantically meaningful changes.
  Minimalist output.
- **Maps to reqs:** (4) excellent for "what actually changed structurally,"
  complementary to delta's line-level highlighting. Use as a git external diff or
  as lazygit's `externalDiffCommand: difft --color=always`.
- **Install (Ubuntu):** `sudo apt install difftastic` (recent) or
  `cargo install difftastic`. **License:** MIT.
- **URL:** <https://github.com/Wilfred/difftastic>

**Diff pick:** **lazygit + delta** as the default (readable diffs + full staging),
add **difftastic** as a toggle for structural review of gnarly refactors.

---

## 4. Human-in-the-loop / approval (req 5)

The strongest, most-proven HITL surface is **inside each agent CLI itself** — the
orchestrator just puts several of these prompts side by side. Verified specifics
for Claude Code (the primary agent this harness targets):

### Claude Code permission modes (verified)
- **Default = human-in-the-loop.** As of the v2.1.200-era change, the default
  requires **positive human authorization for every state-changing action** (file
  write, shell command, network call) unless the developer opts out.
- **Modes** (cycle with **Shift+Tab**):
  - **Manual / default** — pause and require explicit approval for each action.
  - **acceptEdits** — auto-approve in-workspace file edits, still pause for shell
    + network.
  - **Plan mode** — read-only; investigates and proposes, touches nothing until
    approved.
  - **Auto mode** — delegates authorization to a classifier model (explicit opt-in).
- **The prompt:** Claude shows exactly what it plans to do and waits; you pick
  **Allow**, **Deny** (and can tell it to try differently), or **approve for the
  rest of the session**.
- **Docs:** <https://code.claude.com/docs/en/agent-sdk/user-input> and the permission
  modes overview in the Claude Code docs.

### Other agent CLIs
- **opencode** — interactive permission prompts by default; `--dangerously-skip-permissions`
  exists for headless runs (leave prompts on for HITL).
- **Codex / Aider / Gemini CLI** — each has its own approve/confirm-before-apply
  flow; behavior varies by tool and version (confirm per-tool).

### Review-gate layer (harness-owned)
This repo already ships a **review-gate** concept (a mandatory AI-code-review /
approval gate on code-changing turns). That is the natural place to add a
harness-level HITL surface that is *independent of any one agent CLI* — a single
approve/reject gate that every agent's output funnels through before commit,
complementing (not replacing) each CLI's own prompt.

---

## Comparison table

| Tool | Category | (1) Multi-session | (2) Multi-agent + switch | (3) Inter-agent interaction | (4) Diff review | (5) HITL | Install (Ubuntu) | License |
|---|---|---|---|---|---|---|---|---|
| tmux | Multiplexer | Strong (detach/persist) | Manual (pane/window) | Scripting only (`send-keys`) | No | No | `apt install tmux` | ISC |
| Zellij | Multiplexer | Strong | Manual + floating panes | Layouts/plugins only | No | No | `cargo install zellij` | MIT |
| WezTerm | Emulator+mux | Yes (GUI-bound) | Manual | Lua scripting | No | No | apt repo / flatpak | MIT |
| **claude-squad** | Agent orchestrator | **Strong (worktrees)** | **Yes (instance list)** | Limited (manual hand-off) | **Yes (checkout/pause)** | **Yes (review + auto-accept)** | `brew install claude-squad` | AGPL-3.0 |
| opencode | Agent CLI + TUI | Native multi-session | Sessions-as-agents | No bus | Tracks file changes | Built-in prompts | `npm i -g opencode-ai` | MIT |
| lazygit | Git TUI | n/a | n/a | n/a | **Strong (+worktrees)** | Human commit gate | `apt install lazygit` | MIT |
| gitui | Git TUI | n/a | n/a | n/a | Yes (fast) | Human commit gate | `cargo install gitui` | MIT |
| delta | Diff pager | n/a | n/a | n/a | **Readable diffs** | n/a | `apt install git-delta` | MIT |
| difftastic | Diff (structural) | n/a | n/a | n/a | Structural diffs | n/a | `apt install difftastic` | MIT |
| agent-deck* | Agent orchestrator | Yes* | Yes* | Unknown* | Unknown* | Unknown* | see repo | see repo |
| hcom* | Agent message bus | via agents* | via agents* | **Yes (bus)** * | No* | No* | see repo | see repo |

`*` = **unverified**; confirm against the source before relying on it.

---

## Recommendation

**Primary pick:** **claude-squad** as the orchestration brain, run inside a
**Zellij** (or tmux) session, with **lazygit + delta** for review/staging and
each agent CLI's **native HITL prompt** as the approve/reject gate.

Why:
1. It is the **most-proven, verified** tool that actually satisfies requirements
   (1), (2), (4), and (5) at once: many agents in parallel, isolated per-task git
   worktrees, one instance list to switch between, checkout-to-review, and
   auto-accept when you want to let it run.
2. It supports the exact agent set this harness cares about (Claude Code, Codex,
   opencode, Aider, Gemini, Amp) via configurable launch commands.
3. It builds on **tmux**, so it composes cleanly with a standard multiplexer
   workflow and survives SSH/GUI instability — important on this Ubuntu box.
4. AGPL-3.0 is fine for internal/dev tooling (note the copyleft if you'd ever
   redistribute a modified binary).

**Runner-up:** **opencode's built-in multi-session TUI** if you'd rather not add
an orchestrator — it gives native concurrent sessions, survives disconnects via
its persistent server, and has built-in permission prompts. It's weaker on
requirement (2)/(3) because sessions are independent (no worktree isolation per
task, no cross-session bus), but it's a single MIT-licensed binary and very low
friction.

**Multiplexer under both:** **Zellij** for a fresh local setup (floating panes to
watch several agents; zero config), **tmux** if you're SSH-heavy or want the
mature ecosystem.

### Honest gaps (requirements no proven tool fully meets)
1. **Requirement (3) — rich interaction *between* running agents.** The verified
   orchestrators deliberately *isolate* agents (worktrees) and offer only manual
   hand-off. True agent-to-agent messaging (a shared event bus) exists only in
   **unverified** newer tools (**hcom**, **amux**'s agent REST API,
   **thurbox**'s inter-session messaging). If (3) is a hard requirement, the
   harness should either (a) evaluate/verify one of these, or (b) build a thin
   message-bus of its own (e.g. a shared file/socket the review-gate already
   could own).
2. **Unified cross-agent HITL.** HITL today lives inside each CLI. A single
   harness-level approve/reject gate that *all* agents funnel through (the
   review-gate layer) is not something an off-the-shelf TUI provides — it's a
   build-it opportunity for this repo.
3. **No terminal tool replaces an IDE's editor-integrated inline diff review.**
   lazygit + delta is close and often better for agent-generated diffs, but
   there's no in-terminal "click a squiggle" affordance.

---

## Installer approach for agent-harness

A "TUI stack" installer the harness could offer:

1. **Detect what's present** — probe `PATH` for `tmux`, `zellij`, `wezterm`,
   `claude-squad`/`cs`, `opencode`, `lazygit`, `gitui`, `delta`, `difft`, and the
   agent CLIs; report a checklist of present/missing.
2. **Offer a curated install** with the right package manager per tool (they
   split across `apt`, `cargo`, `npm`, `brew`):
   - apt: `tmux`, `lazygit`, `git-delta`, `difftastic` (where packaged)
   - cargo: `zellij`, `gitui` (and cargo fallbacks for delta/difftastic on older Ubuntu)
   - npm: `opencode-ai`
   - brew/script: `claude-squad` (+ its `tmux`/`gh` prereqs)
   Present it as opt-in per tool, not a silent bulk install.
3. **Wire sane defaults** — set git's pager to delta, drop a lazygit pager config,
   and (optionally) a Zellij layout that opens an agent pane + a pinned
   lazygit/log pane.
4. **Detect when a better tool appears** — keep a small **declarative registry**
   (a YAML/JSON list of candidate tools with name, category, repo, install
   command, and a "last-verified" date; front-end-editable, no code change to
   add a tool). A periodic check (e.g. against
   `awesome-cli-coding-agents` / `awesome-agent-orchestrators` and each repo's
   latest release) flags: new entrants in the orchestrator category, and version
   bumps of installed tools. Surface findings as a "review these" report rather
   than auto-switching — the category is moving fast and many entrants are still
   unverified.

---

## Sources

- claude-squad — <https://github.com/smtg-ai/claude-squad>
- Zellij — <https://github.com/zellij-org/zellij>
- tmux — <https://github.com/tmux/tmux>
- WezTerm — <https://github.com/wezterm/wezterm>
- opencode — <https://github.com/sst/opencode>
- lazygit — <https://github.com/jesseduffield/lazygit>
- gitui — <https://github.com/gitui-org/gitui>
- delta — <https://github.com/dandavison/delta>
- difftastic — <https://github.com/Wilfred/difftastic>
- Claude Code approvals / user input — <https://code.claude.com/docs/en/agent-sdk/user-input>
- awesome-cli-coding-agents — <https://github.com/bradAGI/awesome-cli-coding-agents>
- awesome-agent-orchestrators — <https://github.com/andyrewlee/awesome-agent-orchestrators>
- agent-deck — <https://github.com/asheshgoplani/agent-deck>
- tmux vs Zellij (2026) — <https://dasroot.net/posts/2026/02/terminal-multiplexers-tmux-vs-zellij-comparison/>
- delta + lazygit setup — <https://www.lorenzobettini.it/2025/06/better-diffs-in-lazygit-with-delta/>
