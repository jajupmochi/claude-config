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
- [Codex adapter](#codex-adapter)

## Status

**Current Phase:** All 10 phases complete (v0.1.0 shipped 2026-04-29). Post-launch: external publishing tracked in [PUBLISHING.md](PUBLISHING.md). Git history scrubbed via `git filter-repo` to remove pre-rename setup-skill literals + user-specific absolute paths (see commit log for the rewrite).

- P1: Foundation ✓
- P1.5: Discovery (gitignored) ✓
- P2: Rules ✓
- P3: Hooks ✓
- P4: Skills ✓
- P5: Recommendations ✓
- P6: Tooling ✓
- P7: Templates ✓
- P8: Setup skill ✓
- P9: LICENSE + meta-skills + GitHub publish ✓ (https://github.com/jajupmochi/agent-harness)
- P10: Plugin packaging (`.claude-plugin/plugin.json`) ✓
- P11: Codex adapter (`.codex-plugin`, wrapper skills, `hooks.json`, install/verify/update scripts) ✓

See [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) and README's "Build history" for details.

## Rules

✅ 14 rules + index README. Initial 9 populated in P2 (2026-04-29); 5 added 2026-05-21 from global `~/.claude/CLAUDE.md` evolution (end-of-turn-marker, always-on-verification, autorun-mode, multi-round-redesign, latex-edit-policy).

| Rule | Scope | One-line |
|---|---|---|
| [`chinese-output`](rules/chinese-output/RULE.md) | personal | Final user-facing output in Chinese; intermediate stays English |
| [`pre-edit-confirmation`](rules/pre-edit-confirmation/RULE.md) | universal | List exact targets + 1-line plan + wait for explicit "go" before any Edit / Write |
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
| [`bilingual-docs`](rules/bilingual-docs/RULE.md) | optional | `NAME.md` + `NAME.zh.md` convention (consumer-side opt-in via `setup/init-agent-harness`) |
| [`end-of-turn-marker`](rules/end-of-turn-marker/RULE.md) | personal | Every turn ends with `[END:FINAL]` / `[END:WAIT]` / `[END:NEEDS_USER]` on its own line |
| [`always-on-verification`](rules/always-on-verification/RULE.md) | research-pkg | Before any code / test / results claim, invoke `code-verifier` (artifact authenticity) and/or `research-critic` (inferential soundness) |
| [`autorun-mode`](rules/autorun-mode/RULE.md) | personal | When user says "autorun" / "全力跑" / "think a lot" + scope: higher-autonomy cadence + multi-pass review + branch hygiene |
| [`multi-round-redesign`](rules/multi-round-redesign/RULE.md) | ui-project | N-round UI redesign protocol with date-stamped `00-plan.md` + `round-N.html`/`.png`/`.notes.md` + final spec lock + production-lock round |
| [`latex-edit-policy`](rules/latex-edit-policy/RULE.md) | research-pkg | When editing `.tex`/`.sty`/`.cls`/`.bib`: hard fixes direct; soft (content) edits comment-don't-delete with `% [orig YYYY-MM-DD]` inline backup (overrides output-brevity for LaTeX content) |

See [`rules/README.md`](rules/README.md) for usage details and scope-tag definitions.

## Skills

✅ 8 general-bucket skills + index README. Initial 5 populated in P4 (2026-04-29); 2 added 2026-05-21 from user-level always-on gates; 1 added 2026-05-31 (`system-cleanup`, distilled from a real disk-cleanup session).

| Skill | Bucket | Trigger | Purpose |
|---|---|---|---|
| [`verify-template`](skills/general/verify-template/SKILL.md) | general | `/verify` | Run CI gates locally; customize per project |
| [`preview-template`](skills/general/preview-template/SKILL.md) | general | `/preview` | Start local dev server; customize per project type |
| [`long-running-tasks`](skills/general/long-running-tasks/SKILL.md) | general | auto / `/long-running-tasks` | Decision tree: background subagent vs Monitor vs explicit timeout |
| [`verify-visual`](skills/general/verify-visual/SKILL.md) | general | auto on UI changes | chrome-devtools MCP screenshot + 4-axis self-critique against reference |
| [`privacy-redact`](skills/general/privacy-redact/SKILL.md) | general | `/privacy-redact <file>` | Scan + redact usernames, absolute paths, secrets, codenames |
| [`code-verifier`](skills/general/code-verifier/SKILL.md) | general | auto / `/code-verifier` | Three-layer gate before any "tests pass" / "code works" / "results show X" claim — detects FAKE-RUN patterns |
| [`research-critic`](skills/general/research-critic/SKILL.md) | general | auto / `/research-critic` | Six-question audit on every research claim (falsifiability, design, fair comparison, leakage, proportional conclusion, alternatives) |
| [`system-cleanup`](skills/general/system-cleanup/SKILL.md) | general | auto / `/system-cleanup` | Diagnose a full Linux disk (df/du/dpkg/snap/docker) → prioritized, risk-tagged cleanup; safe user-level deletions + sudo items handed to the user; covers VS Code WebStorage bloat, old kernels, NTFS data-disk write failures. Ships `cleanup.sh`. |
| [`figma-design-fetch`](skills/figma-design-fetch/SKILL.md) | general | auto on figma.com URL / `/figma-fetch <node-url>` | Connect the official Figma MCP (OAuth), fetch a design node (code/vector/bitmap/screenshot) to a gitignored `.design-imports/`, then rebuild per-screen with existing components. Encodes the 6 tested gotchas (PKCE expiry, Code Connect paywall, empty variables, low-fi snapshots, 7-day asset URLs, no browser-scraping). |

Future buckets (populated in P7 with templates):

- `research-pkg/` — skills for Python research packages (`new-adapter`, `new-experiment`, …)
- `static-site/` — skills for static personal sites (`new-round`, `deploy-round`, `i18n-sync`)

See [`skills/README.md`](skills/README.md) for usage details.

## Hooks

✅ Populated in P3 (2026-04-29). 2 hooks + index README.

| Hook | Event | Matcher | Context | One-line |
|---|---|---|---|---|
| [`ruff-format-on-edit`](hooks/ruff-format-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | research-pkg / any Python | Auto-format Python files with ruff after Claude edits |
| [`jq-validate-json`](hooks/jq-validate-json/README.md) | `PostToolUse` | `Write\|Edit` | static-site / JSON-config | Block next tool call if Claude wrote invalid JSON to configured paths |

See [`hooks/README.md`](hooks/README.md) for install instructions.

## Recommendations

✅ 15 active files + 2 reference tables + index README. Initial 12 populated in P5 (2026-04-29); 3 added 2026-05-21 (ai-coding-tools, cluster-hpc, reference-projects). Existing files updated with new entries (Chakra UI, anime.js, useanimations, itshover, HyperFrames, math-curve-loaders, React Native motion, yesicon.app, svgl.app, MLflow + W&B + ClearML).

| File | Context | Coverage |
|---|---|---|
| [cc-plugins.md](recommendations/cc-plugins.md) | always | 37 Claude Code plugins (workflow, integrations, specialized) |
| [cc-marketplaces-and-skill-bundles.md](recommendations/cc-marketplaces-and-skill-bundles.md) | always | 4 third-party marketplaces + 9 skill bundles via `npx skills add` |
| [cli-tools.md](recommendations/cli-tools.md) | always (selectively) | System CLIs (jq, gh, ripgrep, fd, …) + Python user CLIs (uv, ruff, mkdocs, hf, …) |
| [js-ui-and-design.md](recommendations/js-ui-and-design.md) | ui-project | Lucide, Radix full set, **Chakra UI**, lenis, d3, visx, recharts, monaco, tanstack/table, shadcn ecosystem; icon explorers (**yesicon.app**, **svgl.app**) |
| [js-animation-and-3d.md](recommendations/js-animation-and-3d.md) | ui-project + 3d-or-animation | motion, gsap, **anime.js**, lottie-react, tailwindcss-animate, **math-curve-loaders**; three, R3F, drei, mediapipe; **animated icon catalogues** (itshover, useanimations); **HTML→video** (HyperFrames, Remotion); **React Native motion** |
| [js-build-test-style.md](recommendations/js-build-test-style.md) | ui-project | vite, next, electron, vitest, playwright, storybook, tailwindcss, prettier |
| [js-state-data.md](recommendations/js-state-data.md) | ui-project | pinia, zustand, swr, vueuse, vue-i18n, vue-router, next-themes |
| [web-auditing.md](recommendations/web-auditing.md) | static-site / web-perf | chrome-devtools MCP (default), lighthouse CLI, lhci, pa11y, axe-core |
| [image-video-pdf.md](recommendations/image-video-pdf.md) | image-or-video-work | sharp, svgo, imagemin, ffmpeg (apt), puppeteer |
| [docs-tools.md](recommendations/docs-tools.md) | docs-site | mkdocs + material, ghp-import, latexmk (apt) |
| [ml-research.md](recommendations/ml-research.md) | ml-research | huggingface_hub[cli], datasets, gpustat, kaleido, selenium; **experiment tracking platforms** (MLflow, Weights & Biases, ClearML) |
| [orchestra-ml-skills.md](recommendations/orchestra-ml-skills.md) | ml-research | 21-category ML skill stack incl. `0-autoresearch-skill` meta-orchestrator |
| [ai-coding-tools.md](recommendations/ai-coding-tools.md) | optional | Spec-driven scaffolding (**OpenSpec**) + paper review (**paperreview.ai**) |
| [cluster-hpc.md](recommendations/cluster-hpc.md) | optional | SLURM patterns, free-tier rules, rsync conventions for HPC clusters |
| [reference-projects.md](recommendations/reference-projects.md) | optional | Standalone demos / template projects to study (e.g. `mykonos-island-voxels` — zero-dependency Canvas 2D isometric builder with painterly assets, layered cache rendering, touch-first UI) |
| [reference/apt-packages.md](recommendations/reference/apt-packages.md) | always (lookup) | apt-installed packages — knowledge table only, never auto-install |
| [reference/vscode-extensions.md](recommendations/reference/vscode-extensions.md) | always (lookup) | VS Code extensions — knowledge table only, CC-friendly defaults flagged |

See [`recommendations/README.md`](recommendations/README.md) for context tags and how `setup/init-agent-harness` (P8) decides what to install per project type.

## Tooling

✅ Populated in P6 (2026-04-29). 3 tooling categories + index README.

| Folder | Context | What it gives |
|---|---|---|
| [python-uv-ruff/](tooling/python-uv-ruff/README.md) | research-pkg | `uv` + `ruff` install steps + canonical `pyproject.template.toml` (extras, ruff config, mypy, pytest) |
| [node-nvm/](tooling/node-nvm/README.md) | ui-project, electron-or-desktop | nvm install + Node 22 LTS + minimal-globals philosophy + scaffold pointers |
| [permissions-allowlist/](tooling/permissions-allowlist/README.md) | always (selectively) | Drop-in `settings.local.snippet.json` of common safe Bash patterns from real projects |

See [`tooling/README.md`](tooling/README.md) for usage.

## Templates

✅ Populated in P7 (2026-04-29). 2 project templates + index README.

| Template | Project type | Includes |
|---|---|---|
| [research-package-py/](templates/research-package-py/TEMPLATE_README.md) | Python research pkg (uv + ruff + pytest) | CLAUDE.template.md, pyproject.template.toml (with research extras: torch/data/logging), .gitignore, .claude/settings.template.json (ruff format hook), .claude/skills/verify/ |
| [personal-cite-static/](templates/personal-cite-static/TEMPLATE_README.md) | Static personal academic site (HTML/CSS/JS, i18n, bilingual) | CLAUDE.template.md (bilingual + visual-verification + iterative-round-file rules), index.template.html (i18n-aware), locales/{en,zh}.template.json, .gitignore, .claude/settings.template.json (jq JSON validity hook), .claude/skills/{preview,verify-visual,i18n-sync}/ |

See [`templates/README.md`](templates/README.md) for usage. The `setup/init-agent-harness` skill (P8) does the substitution + composition automatically.

## Setup

✅ Populated in P8 (2026-04-29). 1 setup skill + index README.

| Skill | Purpose |
|---|---|
| [`init-agent-harness`](setup/init-agent-harness/SKILL.md) | Interactive `/init-agent-harness` slash command. Asks 6 questions (project type, bilingual policy, final-output language, context tags, consumption mode, personal-preference rules), then composes the right subset of rules/hooks/skills/templates/tooling into the project. |

See [`setup/README.md`](setup/README.md) for usage.

## Codex adapter

Merged from branch `codex-adapter` (2026-07-08). This keeps the Claude Code surface intact and adds Codex-specific entrypoints.

| Item | Purpose |
|---|---|
| [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) | Codex plugin manifest with `skills: "./skills/"` |
| [`hooks.json`](hooks.json) | Plugin-bundled Codex hooks for ruff formatting and JSON validation |
| [`skills/init-codex-config`](skills/init-codex-config/SKILL.md) | Apply agent-harness to Codex projects through `AGENTS.md`, `.codex/hooks.json`, and `.agents/skills` |
| [`skills/agent-config-adapter`](skills/agent-config-adapter/SKILL.md) | General workflow for adapting an agent configuration to another agent/model route |
| [`scripts/install-codex-local.js`](scripts/install-codex-local.js) | Symlink skills into `~/.agents/skills`, expose the plugin through the personal marketplace as `INSTALLED_BY_DEFAULT` |
| [`scripts/verify-codex-adapter.js`](scripts/verify-codex-adapter.js) | Local structural checks for the Codex adapter |
| [`scripts/codex-update-safe.js`](scripts/codex-update-safe.js) | Safe Codex CLI updater for release-asset rollout windows |
| [`docs/CODEX_ADAPTATION_PLAN.md`](docs/CODEX_ADAPTATION_PLAN.md) | Full function inventory, research notes, architecture options, and execution plan |

