# Recommendations

> Curated lists of tools, plugins, and skills the author has used or recommends, with **agent-executable install commands**. Each entry says when to install and when to skip.

## Master TOC

- [How to use](#how-to-use)
- [Active recommendations](#active-recommendations)
- [Reference tables (no auto-install)](#reference-tables-no-auto-install)
- [Context-aware install](#context-aware-install)
- [Adding a new entry](#adding-a-new-entry)

## How to use

When an agent (or human) reads these files, the goal is: pick the relevant subset for the current project's context and run the install commands.

The `setup/init-agent-harness` skill (P8) does this composition automatically based on project type. For manual use, browse the index below.

## Active recommendations

| File | Context | Coverage |
|---|---|---|
| [cc-plugins.md](cc-plugins.md) | always | 37 Claude Code plugins (workflow, integrations, specialized) |
| [cc-marketplaces-and-skill-bundles.md](cc-marketplaces-and-skill-bundles.md) | always | 4 third-party marketplaces + 9 skill bundles via `npx skills add` |
| [cli-tools.md](cli-tools.md) | always (selectively) | System (jq, gh, ripgrep, fd, …) + Python user CLIs (uv, ruff, mkdocs, hf, gpustat, …) |
| [tui-for-agents.md](tui-for-agents.md) | agent-workflow / terminal-first | Terminal/TUI stack for driving MULTIPLE AI coding agents (multi-session, sub-agents, diff review, HITL): claude-squad + Zellij/tmux + lazygit + delta; honest gaps on agent-to-agent interaction |
| [js-ui-and-design.md](js-ui-and-design.md) | ui-project | Lucide icons, Radix UI full set, Chakra UI, lenis, d3, visx, recharts, monaco, tanstack table, shadcn ecosystem; icon explorers (yesicon, svgl) |
| [js-animation-and-3d.md](js-animation-and-3d.md) | ui-project + 3d-or-animation | motion, gsap, anime.js, lottie-react, tailwindcss-animate, math-curve-loaders; three, R3F, drei, mediapipe; animated icon catalogues (itshover, useanimations); HTML→video (HyperFrames, Remotion); React Native motion |
| [js-build-test-style.md](js-build-test-style.md) | ui-project | vite, next, electron, vitest, playwright, storybook, tailwindcss + ecosystem, prettier |
| [js-state-data.md](js-state-data.md) | ui-project | pinia, zustand, swr, vueuse, vue-i18n, vue-router, next-themes |
| [web-auditing.md](web-auditing.md) | static-site / web-perf | chrome-devtools MCP (default), lighthouse CLI, lhci, pa11y, axe-core |
| [image-video-pdf.md](image-video-pdf.md) | image-or-video-work | sharp, svgo, imagemin, ffmpeg (via apt), puppeteer |
| [docs-tools.md](docs-tools.md) | docs-site | mkdocs + material, ghp-import, latexmk (via apt) |
| [ml-research.md](ml-research.md) | ml-research | huggingface_hub[cli], datasets, gpustat, kaleido, selenium; experiment tracking platforms (MLflow, Weights & Biases, ClearML) |
| [orchestra-ml-skills.md](orchestra-ml-skills.md) | ml-research | 21-category ML skill stack incl. `0-autoresearch-skill` meta-orchestrator |
| [ai-coding-tools.md](ai-coding-tools.md) | optional | Spec-driven scaffolding (OpenSpec) + paper review (paperreview.ai) |
| [cluster-hpc.md](cluster-hpc.md) | optional | SLURM patterns, free-tier rules, rsync conventions for HPC clusters |
| [reference-projects.md](reference-projects.md) | optional | Standalone demos / template projects worth studying for technique (Canvas 2D isometric, painterly asset pipelines, touch-first UI, …) |

## Reference tables (no auto-install)

| File | Purpose |
|---|---|
| [reference/apt-packages.md](reference/apt-packages.md) | `apt`-installed packages — knowledge table; agent must always ask before installing |
| [reference/vscode-extensions.md](reference/vscode-extensions.md) | VS Code extensions — knowledge table; never auto-install. Some flagged as CC-friendly defaults |

## Context-aware install

Every entry in these files carries a `context:` tag (defined in DISCOVERY.md and propagated here):

| Tag | When applies |
|---|---|
| `always` | Every project benefits |
| `research-pkg` | Python research / ML package |
| `ui-project` | Any frontend / UI work |
| `static-site` | HTML/CSS/JS personal sites, MkDocs, etc. |
| `3d-or-animation` | Three.js, motion graphics, complex animation |
| `ml-research` | ML/AI research workflow |
| `web-perf` | Performance / SEO / accessibility auditing |
| `image-or-video-work` | Image processing, video conversion, SVG optimization |
| `docs-site` | mkdocs / Sphinx / equivalent docs site |
| `electron-or-desktop` | Desktop app shell |
| `optional` | Don't auto-install; ask user when needed |

**Default behavior**: install only entries whose `context:` matches the new project's selected types. Anything tagged `optional` or with non-matching context → **ask the user before installing**.

If the project later expands (e.g., research-pkg adds a UI dashboard), an agent should **lazily** prompt: "this project just gained a UI component — install [list of ui-project tools]?"

## Adding a new entry

See [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md) §"Adding a recommendation". Each entry must include:

- Name + link
- One-line "why use this"
- Install command (agent-executable)
- Provenance (where it came from / who recommends)
- Context tag
- Caveats if any
