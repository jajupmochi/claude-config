# Inventory

> Master index of everything currently catalogued in this library. Updated on every add / remove / rename.

> **Language:** English | [中文](INVENTORY.zh.md)

## Master TOC

- [Status](#status)
- [Rules](#rules)
- [Skills](#skills)
- [Hooks](#hooks)
- [Recommendations](#recommendations)
- [Tooling](#tooling)
- [Templates](#templates)
- [Setup](#setup)
- [Repo tooling](#repo-tooling)
- [Codex adapter](#codex-adapter)

## Status

**Current phase:** P1 through P11 complete (v0.1.0 shipped 2026-04-29). External publishing is tracked in [PUBLISHING.md](PUBLISHING.md). Git history was scrubbed with `git filter-repo` to remove pre-rename setup-skill literals and user-specific absolute paths (see the commit log for the rewrite).

Every count below is checked against [`adapters/manifest.source.json`](adapters/manifest.source.json), which is the source of truth. The per-agent manifests are generated from it by `node build.mjs`, and `node build.mjs --check` fails when they drift.

1. P1: Foundation ✓
2. P1.5: Discovery (gitignored) ✓
3. P2: Rules ✓
4. P3: Hooks ✓
5. P4: Skills ✓
6. P5: Recommendations ✓
7. P6: Tooling ✓
8. P7: Templates ✓
9. P8: Setup skill ✓
10. P9: `LICENSE` + meta-skills + GitHub publish ✓ (https://github.com/jajupmochi/agent-harness)
11. P10: Plugin packaging (`.claude-plugin/plugin.json`) ✓
12. P11: Codex adapter (`.codex-plugin`, wrapper skills, `hooks.json`, install/verify/update scripts) ✓

See [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) and README's "Build history" for details.

## Rules

✅ 28 rules + index README. Initial 9 populated in P2 (2026-04-29), 5 added 2026-05-21 from the global `~/.claude/CLAUDE.md` evolution (end-of-turn-marker, always-on-verification, autorun-mode, multi-round-redesign, latex-edit-policy), the rest distilled from later sessions. `native-capability-first` sits at the top because it decides whether the other 27 apply at all.

| Rule | Scope | One-line |
|---|---|---|
| [`native-capability-first`](rules/native-capability-first/RULE.md) | universal | Highest precedence. Before invoking any harness feature, judge whether it fits this task and whether following it would produce a worse result than your own unaided ability. Carries a never-exempt list — the verification gates, the enforcement hooks, privacy, destructive-action confirmations, and the user's own instructions |
| [`chinese-output`](rules/chinese-output/RULE.md) | personal | Final user-facing output in Chinese; intermediate stays English |
| [`pre-edit-confirmation`](rules/pre-edit-confirmation/RULE.md) | universal | List exact targets + 1-line plan + wait for explicit "go" before any Edit / Write |
| [`no-ssh-username-probing`](rules/no-ssh-username-probing/RULE.md) | universal | Confirm the exact SSH user first; try once; ask on failure — never loop candidate usernames (trips fail2ban → self-inflicted IP ban). Enforced by the `ssh-guard` hook |
| [`root-cause-before-fix`](rules/root-cause-before-fix/RULE.md) | personal | Before fixing any bug: git log/blame + compare with baseline branch + "why now?" (regression vs latent) — never patch-first |
| [`fallback-discipline`](rules/fallback-discipline/RULE.md) | personal | Fallback/pass judged by scenario: deploy allows but must log detail; test/dev must fix-on-spot or raise, never silently hide a bug |
| [`phased-planning`](rules/phased-planning/RULE.md) | universal | Break tasks (3+ files OR > ~5 tool calls OR multi-step) into numbered phases with per-phase pause |
| [`plugin-preflight`](rules/plugin-preflight/RULE.md) | universal | Verify plugin / skill / command is installed AND not deprecated before invoking |
| [`ui-iteration-loop`](rules/ui-iteration-loop/RULE.md) | ui-project | Autonomous 8-iteration UI redesign loop with chrome-devtools screenshots and 4-axis self-critique |
| [`output-brevity`](rules/output-brevity/RULE.md) | personal | No end-of-batch recap, don't echo tool output, prefer Edit over Write |
| [`human-readable-output`](rules/human-readable-output/RULE.md) | personal | Write all output (chat and docs) as complete human sentences and tables, not terse AI shorthand; prefer tables for structured info |
| [`writing-style`](rules/writing-style/RULE.md) | personal | De-AI prose tics. No hyphen-joined compound modifiers, no colon or semicolon opening a trailing clause, no filler emphasis words (important, crucial, genuinely). Edit the user's own text minimally and surgically |
| [`tool-proactivity`](rules/tool-proactivity/RULE.md) | personal | Installed plugin / skill / MCP fires without asking when matched (with explicit-approval exceptions) |
| [`no-reread-files`](rules/no-reread-files/RULE.md) | personal | Trust your in-session memory of file contents; re-read only on actual change |
| [`bilingual-docs`](rules/bilingual-docs/RULE.md) | optional | `NAME.md` + `NAME.zh.md` convention (consumer-side opt-in via `setup/init-agent-config`) |
| [`end-of-turn-marker`](rules/end-of-turn-marker/RULE.md) | personal | Every turn ends with `[END:FINAL]` / `[END:WAIT]` / `[END:NEEDS_USER]` on its own line |
| [`always-on-verification`](rules/always-on-verification/RULE.md) | research-pkg | Before any code / test / results claim, invoke `code-verifier` (artifact authenticity) and/or `research-critic` (inferential soundness) |
| [`autorun-mode`](rules/autorun-mode/RULE.md) | personal | When user says "autorun" / "全力跑" / "think a lot" + scope: higher-autonomy cadence + multi-pass review + branch hygiene |
| [`multi-round-redesign`](rules/multi-round-redesign/RULE.md) | ui-project | N-round UI redesign protocol with date-stamped `00-plan.md` + `round-N.html`/`.png`/`.notes.md` + final spec lock + production-lock round |
| [`latex-edit-policy`](rules/latex-edit-policy/RULE.md) | research-pkg | When editing `.tex`/`.sty`/`.cls`/`.bib`: hard fixes direct; soft (content) edits comment-don't-delete with `% [orig YYYY-MM-DD]` inline backup (overrides output-brevity for LaTeX content) |
| [`clickable-links`](rules/clickable-links/RULE.md) | personal | Every commit / file / line / PR / doc / source reference is a full clickable link — never a bare hash, partial path, or half URL |
| [`design-artifacts`](rules/design-artifacts/RULE.md) | personal | Designed an API / UI? List endpoints with clickable local test links (Swagger/Storybook) + give the live preview link + embed a screenshot — in the doc and in the summary |
| [`test-first`](rules/test-first/RULE.md) | personal | Write tests before/alongside any code change, at every level touched; run the full suite with a before and after delta, not just the target test |
| [`design-modes`](rules/design-modes/RULE.md) | personal | Prototyping vs scaling mode — ask up front which one, confirm on switch; sets how much rigor/verification a change gets |
| [`regression-test-on-bugfix`](rules/regression-test-on-bugfix/RULE.md) | universal | Every bug fix MUST ship a regression test that fails on the old code and passes after the fix (red→green); a behavioral fix without one is not done |
| [`incremental-delivery`](rules/incremental-delivery/RULE.md) | universal | Ship completed, independent pieces as they finish (verify → push staging → remote+visual verify → report per piece); don't idle-wait for the whole batch. Hold only genuinely dependent / unverifiable / authorization-gated work |
| [`parity-restoration`](rules/parity-restoration/RULE.md) | universal | Reconciling env↔env (staging↔prod, 1:1 restore)? Enumerate a component and page plan first so nothing is missed, compare each deterministically, then route by direction: reference→target data auto-synced, target→reference additions listed for the owner. Never modify the reference |
| [`commit-discipline`](rules/commit-discipline/RULE.md) | universal | Every commit follows conventional-commit format (`type(scope): description`); no empty or one-word messages. For non-native models, the `commit-msg` hook from `scripts/codex_commit_msg.sh` enforces it |

See [`rules/README.md`](rules/README.md) for usage details and scope-tag definitions.

## Skills

✅ 24 registered skills + index README — the 23 below plus [`init-agent-config`](setup/init-agent-config/SKILL.md), which keeps its own [Setup](#setup) section. Initial 5 populated in P4 (2026-04-29), 2 added 2026-05-21 from user-level always-on gates, the rest distilled from real sessions.

Registration matters beyond bookkeeping. [`bin/deploy-skills.mjs`](bin/deploy-skills.mjs) reads this same list out of [`adapters/manifest.source.json`](adapters/manifest.source.json) and symlinks each entry into every agent's native skill directory, so a skill missing from the manifest is never shipped to opencode no matter how long the directory has existed.

| Skill | Bucket | Trigger | Purpose |
|---|---|---|---|
| [`verify-template`](skills/general/verify-template/SKILL.md) | general | `/verify` | Run CI gates locally; customize per project |
| [`preview-template`](skills/general/preview-template/SKILL.md) | general | `/preview` | Start local dev server; customize per project type |
| [`long-running-tasks`](skills/general/long-running-tasks/SKILL.md) | general | auto / `/long-running-tasks` | Decision tree: background subagent vs Monitor vs explicit timeout |
| [`verify-visual`](skills/general/verify-visual/SKILL.md) | general | auto on UI changes | chrome-devtools MCP screenshot + 4-axis self-critique against reference |
| [`privacy-redact`](skills/general/privacy-redact/SKILL.md) | general | `/privacy-redact <file>` | Scan + redact usernames, absolute paths, secrets, codenames |
| [`code-verifier`](skills/general/code-verifier/SKILL.md) | general | auto / `/code-verifier` | Three-layer gate before any "tests pass" / "code works" / "results show X" claim — detects fake-run patterns (a result hardcoded, a test that asserts nothing, an exception swallowed) |
| [`research-critic`](skills/general/research-critic/SKILL.md) | general | auto / `/research-critic` | Six-question audit on every research claim (falsifiability, design, fair comparison, leakage, proportional conclusion, alternatives) |
| [`system-cleanup`](skills/general/system-cleanup/SKILL.md) | general | auto / `/system-cleanup` | Diagnose a full Linux disk (df/du/dpkg/snap/docker) → prioritized, risk-tagged cleanup; safe user-level deletions + sudo items handed to the user; covers VS Code WebStorage bloat, old kernels, and write failures on an NTFS (Windows filesystem) data disk. Ships `cleanup.sh`. |
| [`linux-freeze-triage`](skills/general/linux-freeze-triage/SKILL.md) | general | auto / `/linux-freeze-triage` | Find the real cause of a Linux freeze/black-screen by evidence (rule out sleep, NVIDIA kernel/userspace mismatch from auto-upgrades, OOM, PCIe link, DPMS hang); bundles a near-zero-cost watchdog + read-only diagnostic battery. Ships `diagnose.sh` + `freeze-watch.sh`. |
| [`figma-design-fetch`](skills/figma-design-fetch/SKILL.md) | general | auto on figma.com URL / `/figma-fetch <node-url>` | Full Figma→code pipeline via the official MCP: OAuth connect, pre-fetch design lint, 5-step flow (extract real values → map to design-system tokens → implement → visual self-check gate → report) to a gitignored `.design-imports/`. Ships `scripts/visual-diff.mjs` (pixelmatch objective gate) + the 6 tested gotchas. |
| [`figma-authoring-constraints`](skills/figma-authoring-constraints/SKILL.md) | general | auto (designer asks / empty variables / pixel-snapshot output) | The 20 Figma-side authoring constraints (variables/tokens, auto layout, components/variants, naming, Dev Mode/Code Connect, no raster placeholders) that make a design cleanly code-able; the design half of the figma-design-fetch pipeline. |
| [`autoresearch-toolfinder`](skills/general/autoresearch-toolfinder/SKILL.md) | general | auto / `/autoresearch-toolfinder` | Find the right autoresearch or research-agent tool from a local cached index of two awesome-autoresearch lists (alvinreal + yibie, 550+ entries). `query.py` returns only the few matches instead of loading the whole catalogue into context; weekly refresh, with upstream changes tracked by content hash. |
| [`autopilot`](skills/general/autopilot/SKILL.md) | general | `/autopilot` | Set up or manage the daily autonomous project driver — a system timer that starts one fresh autorun session a day to advance a project, passing review-gate, re-planning, estimating effort formally, and self-healing when stuck. |
| [`doc-writing`](skills/doc-writing/SKILL.md) | general | auto on any human-facing document / `/doc-writing` | Document preferences mined from two real project sessions (define every term in place, prove every claim and say how a tester re-proves it, full clickable links, a diagram where one helps). Ships [`scripts/doccheck.py`](skills/doc-writing/scripts/doccheck.py), a linter for the mechanically checkable subset. |
| [`task-orchestrator`](skills/task-orchestrator/SKILL.md) | general | auto / `/task-orchestrator` | Research → Design → Plan → Execute → Verify pipeline for every atomic task. Adapts how strict the plan template is to the detected model capability, and records better approaches back into the templates. |
| [`task-relationship-analysis`](skills/task-relationship-analysis/SKILL.md) | general | auto before any 3+ task request | Map how the requested tasks relate (synergies, conflicts, shared substrate, ordering) before executing, so three tasks that share one piece are not built three separate times. Scaffolds a pairwise matrix and a synthesis checklist. |
| [`memory-flywheel`](skills/memory-flywheel/SKILL.md) | general | auto / `/memory-flywheel` | Per-project cross-session working memory so a long session does not lose detail to context compaction. Records each round to a project memory directory, reads a coarse index first, then opens only what keyword recall points at. |
| [`prompt-library`](skills/prompt-library/SKILL.md) | general | `/prompt-library` | Save and reuse good prompts across projects and agents, and mine past ones out of local Claude Code / Codex / Copilot / opencode history into browsable, greppable Markdown. |
| [`agent-update-watcher`](skills/agent-update-watcher/SKILL.md) | general | auto / `/agent-update-watcher` | Track the agent ecosystem (new or updated CLIs, plugins, skills) without constant polling. Checks a declared source list only after a minimum interval, then reports only what changed against the recorded version. |
| [`tui-installer`](skills/tui-installer/SKILL.md) | general | `/tui-installer` | Install, or only plan, the terminal stack for driving several coding agents on Ubuntu (zellij + claude-squad + lazygit + delta). Dry-run by default; `--apply` asks per tool. |
| [`agent-config-adapter`](skills/agent-config-adapter/SKILL.md) | general | auto / `/agent-config-adapter` | Adapt an agent configuration or plugin to another agent or model route — Claude Code, Codex, Gemini, Cursor, local models, or a non-native backend such as DeepSeek. |
| [`init-codex-config`](skills/init-codex-config/SKILL.md) | general | `/init-codex-config` | Scaffold or migrate a project to use agent-harness from Codex through `AGENTS.md`, `.codex/hooks.json`, and `.agents/skills`, leaving the original Claude setup untouched. |
| [`end-of-turn-marker`](skills/end-of-turn-marker/SKILL.md) | general | auto at end of turn | Close every turn with a visible divider header and numbered summary items carrying `[END:FINAL]`, `[END:WAIT]`, or `[END:NEEDS_USER]`. The skill half of the rule of the same name. |

Future buckets (populated in P7 with templates):

- `research-pkg/` — skills for Python research packages (`new-adapter`, `new-experiment`, …)
- `static-site/` — skills for static personal sites (`new-round`, `deploy-round`, `i18n-sync`)

See [`skills/README.md`](skills/README.md) for usage details.

## Hooks

✅ 7 hooks + index README. The first two were populated in P3 (2026-04-29); `typecheck-on-edit`, `block-env-read`, `ssh-guard`, `review-gate`, and `task-ledger` were added later from real sessions.

| Hook | Event | Matcher | Context | One-line |
|---|---|---|---|---|
| [`ruff-format-on-edit`](hooks/ruff-format-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | research-pkg / any Python | Auto-format Python files with ruff after Claude edits |
| [`jq-validate-json`](hooks/jq-validate-json/README.md) | `PostToolUse` | `Write\|Edit` | static-site / JSON-config | Block next tool call if Claude wrote invalid JSON to configured paths |
| [`typecheck-on-edit`](hooks/typecheck-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | frontend / TypeScript | After a `.ts(x)` edit: prettier + `tsc --noEmit`; **type errors exit 2 and block the turn** (Figma→code quality spine) |
| [`block-env-read`](hooks/block-env-read/README.md) | `PreToolUse` | `Read` | any repo with secrets | Deny reading `.env*` so secrets never enter the transcript (exit 2) |
| [`ssh-guard`](hooks/ssh-guard/README.md) | `PreToolUse` | `Bash` | any project with SSH access | Block SSH username-probing (2nd distinct `user@host` in a burst) — the fail2ban-tripping pattern that IP-bans you; enforces `no-ssh-username-probing` (exit 2) |
| [`review-gate`](hooks/review-gate/README.md) | `PostToolUse` + `Stop` + `PreToolUse` | `Write\|Edit`, `Bash` | any repo where an agent writes code | Un-skippable review of every code-changing turn. T0 logs each changed file, T1 blocks the `Stop` until linters are clean and one review round has produced a Markdown report, T2 leaves `git commit` free but blocks remote publishing unless the project is on `push-whitelist.txt` |
| [`task-ledger`](hooks/task-ledger/README.md) | `Stop` + `UserPromptSubmit` | — | any round with more than about ten sub-tasks | One task document per round. The `Stop` gate refuses to end the round while a task is open, a task is marked done without evidence, or a mid-run requirement is untriaged; the `UserPromptSubmit` capture records mid-round requirements before they can be forgotten |

See [`hooks/README.md`](hooks/README.md) for install instructions.

## Recommendations

✅ 21 recommendation files + index README — 19 active lists and 2 reference tables. Initial 12 populated in P5 (2026-04-29), 3 added 2026-05-21 (ai-coding-tools, cluster-hpc, reference-projects), 4 added later (tui-for-agents, github-actions-frugality, codex-marketplaces, codex-plugins). Existing files keep gaining entries (Chakra UI, `anime.js`, useanimations, itshover, HyperFrames, math-curve-loaders, React Native motion, yesicon.app, svgl.app, MLflow + W&B + ClearML).

| File | Context | Coverage |
|---|---|---|
| [cc-plugins.md](recommendations/cc-plugins.md) | always | 37 Claude Code plugins (workflow, integrations, specialized) |
| [cc-marketplaces-and-skill-bundles.md](recommendations/cc-marketplaces-and-skill-bundles.md) | always | 4 third-party marketplaces + 9 skill bundles via `npx skills add` |
| [cli-tools.md](recommendations/cli-tools.md) | always (selectively) | System CLIs (jq, gh, ripgrep, fd, …) + Python user CLIs (uv, ruff, mkdocs, hf, …) |
| [js-ui-and-design.md](recommendations/js-ui-and-design.md) | ui-project | Lucide, Radix full set, **Chakra UI**, lenis, d3, visx, recharts, monaco, tanstack/table, shadcn ecosystem; icon explorers (**yesicon.app**, **svgl.app**) |
| [js-animation-and-3d.md](recommendations/js-animation-and-3d.md) | ui-project + 3d-or-animation | motion, gsap, **`anime.js`**, lottie-react, tailwindcss-animate, **math-curve-loaders**; three, R3F (react-three-fiber), drei, mediapipe; **animated icon catalogues** (itshover, useanimations); **HTML→video** (HyperFrames, Remotion); **React Native motion** |
| [js-build-test-style.md](recommendations/js-build-test-style.md) | ui-project | vite, next, electron, vitest, playwright, storybook, tailwindcss, prettier |
| [js-state-data.md](recommendations/js-state-data.md) | ui-project | pinia, zustand, swr, vueuse, vue-i18n, vue-router, next-themes |
| [web-auditing.md](recommendations/web-auditing.md) | static-site / web-perf | chrome-devtools MCP (default), lighthouse CLI, lhci, pa11y, axe-core |
| [image-video-pdf.md](recommendations/image-video-pdf.md) | image-or-video-work | sharp, svgo, imagemin, ffmpeg (apt), puppeteer |
| [docs-tools.md](recommendations/docs-tools.md) | docs-site | mkdocs + material, ghp-import, latexmk (apt) |
| [ml-research.md](recommendations/ml-research.md) | ml-research | huggingface_hub[cli], datasets, gpustat, kaleido, selenium; **experiment tracking platforms** (MLflow, Weights & Biases, ClearML) |
| [orchestra-ml-skills.md](recommendations/orchestra-ml-skills.md) | ml-research | 21-category ML skill stack incl. `0-autoresearch-skill` meta-orchestrator |
| [ai-coding-tools.md](recommendations/ai-coding-tools.md) | optional | Spec-driven scaffolding (**OpenSpec**) + paper review (**paperreview.ai**) |
| [cluster-hpc.md](recommendations/cluster-hpc.md) | optional | SLURM (the cluster job scheduler) patterns, free-tier rules, and rsync conventions for high performance computing clusters |
| [reference-projects.md](recommendations/reference-projects.md) | optional | Standalone demos / template projects to study (e.g. `mykonos-island-voxels` — zero-dependency Canvas 2D isometric builder with painterly assets, layered cache rendering, touch-first UI) |
| [github-actions-frugality.md](recommendations/github-actions-frugality.md) | always (any repo with workflows) | Keeping remote Actions minutes low — verified 2026 billing facts and rates, ranked levers, a four tier local-to-remote scheme with profiles, self-hosted runner break-even and security, `act` limits, pre-push gates. Ships [`templates/actions-frugal-ci/`](templates/actions-frugal-ci/TEMPLATE_README.md) + [`scripts/actions-budget.mjs`](scripts/actions-budget.mjs) |
| [tui-for-agents.md](recommendations/tui-for-agents.md) | agent-workflow / terminal-first | Terminal stack for driving several coding agents at once (claude-squad + Zellij/tmux + lazygit + delta) with multi-session, sub-agent, diff-review and human-in-the-loop coverage, plus the honest gaps on agent-to-agent interaction |
| [codex-marketplaces.md](recommendations/codex-marketplaces.md) | codex | Third-party marketplaces, skill bundles, and curated collections for Codex |
| [codex-plugins.md](recommendations/codex-plugins.md) | codex | Plugins, MCP servers, and external tools approved for Codex; installed ones auto-invoke per the `tool-proactivity` rule |
| [reference/apt-packages.md](recommendations/reference/apt-packages.md) | always (lookup) | apt-installed packages — knowledge table only, never auto-install |
| [reference/vscode-extensions.md](recommendations/reference/vscode-extensions.md) | always (lookup) | VS Code extensions — knowledge table only, CC-friendly defaults flagged |

See [`recommendations/README.md`](recommendations/README.md) for context tags and how `setup/init-agent-config` (P8) decides what to install per project type.

## Tooling

✅ Populated in P6 (2026-04-29). 3 tooling categories + index README.

| Folder | Context | What it gives |
|---|---|---|
| [python-uv-ruff/](tooling/python-uv-ruff/README.md) | research-pkg | `uv` + `ruff` install steps + canonical `pyproject.template.toml` (extras, ruff config, mypy, pytest) |
| [node-nvm/](tooling/node-nvm/README.md) | ui-project, electron-or-desktop | nvm install + Node 22 LTS (long term support) + minimal-globals philosophy + scaffold pointers |
| [permissions-allowlist/](tooling/permissions-allowlist/README.md) | always (selectively) | Drop-in `settings.local.snippet.json` of common safe Bash patterns from real projects |

See [`tooling/README.md`](tooling/README.md) for usage.

## Templates

✅ 3 templates + index README. The first two were populated in P7 (2026-04-29); `actions-frugal-ci` was added later as an add-on for existing repos rather than a project starter.

| Template | Project type | Includes |
|---|---|---|
| [research-package-py/](templates/research-package-py/TEMPLATE_README.md) | Python research pkg (uv + ruff + pytest) | `CLAUDE.template.md`, `pyproject.template.toml` (with research extras: torch/data/logging), `.gitignore`, `.claude/settings.template.json` (ruff format hook), `.claude/skills/verify/` |
| [personal-cite-static/](templates/personal-cite-static/TEMPLATE_README.md) | Static personal academic site (HTML/CSS/JS, i18n, bilingual) | `CLAUDE.template.md` (bilingual + visual-verification + iterative-round-file rules), `index.template.html` (i18n-aware), `locales/{en,zh}.template.json`, `.gitignore`, `.claude/settings.template.json` (jq JSON validity hook), `.claude/skills/{preview,verify-visual,i18n-sync}/` |
| [actions-frugal-ci/](templates/actions-frugal-ci/TEMPLATE_README.md) | Any repo with GitHub Actions (add-on, not a starter) | Four tier CI that keeps Actions minutes low: `git-hooks/{pre-commit,pre-push}.template.sh` (both refuse to run half-substituted), `lefthook.template.yml`, `.github/workflows/{ci,heavy,_checks.reusable}.template.yml`. Rationale and numbers in [github-actions-frugality.md](recommendations/github-actions-frugality.md) |

See [`templates/README.md`](templates/README.md) for usage. The `setup/init-agent-config` skill (P8) does the substitution + composition automatically.

## Setup

✅ Populated in P8 (2026-04-29). 1 setup skill + index README.

| Skill | Purpose |
|---|---|
| [`init-agent-config`](setup/init-agent-config/SKILL.md) | Interactive `/init-agent-config` slash command. Asks 6 questions (project type, bilingual policy, final-output language, context tags, consumption mode, personal-preference rules), then composes the right subset of rules/hooks/skills/templates/tooling into the project. It is the 24th entry of the manifest's skill list. |

See [`setup/README.md`](setup/README.md) for usage.

## Repo tooling

Scripts that maintain the harness itself rather than a downstream project. They are not part of the six manifest categories, so nothing else indexes them.

| Script | What it does |
|---|---|
| [`build.mjs`](build.mjs) | Generates the per-agent manifests from [`adapters/manifest.source.json`](adapters/manifest.source.json). `--check` exits non-zero when a generated manifest has drifted from the source |
| [`bin/deploy-skills.mjs`](bin/deploy-skills.mjs) | Symlinks every manifest skill into each agent's native skill directory (`~/.claude/skills/`, `~/.config/opencode/skills/`), which is why an unregistered skill never reaches opencode |
| [`bin/rule-activation.mjs`](bin/rule-activation.mjs) | Reports rules that are registered but inert. A rule reaches the model only when its text sits in a file the agent actually reads, and `--apply` appends the missing ones into a regeneratable managed block |
| [`bin/harness-feedback.mjs`](bin/harness-feedback.mjs) | Write end of the `native-capability-first` feedback loop. Appends a structured entry to `docs/harness-feedback/QUEUE.md` when a feature did not fit, so skipping it once turns into fixing it; `/harness-sync` drains the queue |
| [`bin/capability-receipt.mjs`](bin/capability-receipt.mjs) | Reads a session transcript and reports, per capability, whether there is evidence it actually fired. Detection signatures live in `adapters/capabilities.json`, so new coverage is a config edit |
| [`scripts/actions-budget.mjs`](scripts/actions-budget.mjs) | Offline budget check for a repo's GitHub Actions workflows — what fires on a pull request, a merge, and a schedule, the billable minutes floor, and findings such as a missing paths filter or a non-Linux runner |
| [`hooks/review-gate/scripts/statsbar.sh`](hooks/review-gate/scripts/statsbar.sh) | Shared renderer that turns a counted breakdown into an aligned bar chart, so review-gate and task-ledger report the same shape in a terminal and in Markdown |

## Codex adapter

Merged from branch `codex-adapter` (2026-07-08). This keeps the Claude Code surface intact and adds Codex-specific entrypoints.

| Item | Purpose |
|---|---|
| [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) | Codex plugin manifest with `skills: "./skills/"` |
| [`hooks.json`](hooks.json) | Source template rendered to absolute commands in user or project Codex hooks; not declared as a plugin hook |
| [`codex/`](codex) | Canonical user guidance, four custom Agent profiles, and review-only model/MCP config example |
| [`skills/init-codex-config`](skills/init-codex-config/SKILL.md) | Apply agent-harness to Codex projects through `AGENTS.md`, `.codex/hooks.json`, and `.agents/skills` |
| [`skills/agent-config-adapter`](skills/agent-config-adapter/SKILL.md) | General workflow for adapting an agent configuration to another agent/model route |
| [`scripts/install-codex-local.js`](scripts/install-codex-local.js) | Install 20 user skills, policy-installed plugin entry, user `AGENTS.md` and hooks files, and four custom Agents without overwriting different files by default |
| [`scripts/verify-codex-adapter.js`](scripts/verify-codex-adapter.js) | Structural checks paired with isolated installer, model-route, ruff, and review-gate tests |
| [`scripts/codex-update-safe.js`](scripts/codex-update-safe.js) | Safe Codex CLI updater for release-asset rollout windows |
| [`docs/CODEX_ADAPTATION_PLAN.md`](docs/CODEX_ADAPTATION_PLAN.md) | Full function inventory, research notes, architecture options, and execution plan |
