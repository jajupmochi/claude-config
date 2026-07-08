# Claude Code Plugins

> 37 Claude Code plugins enabled in the author's `~/.claude/settings.json`, grouped by purpose. **Install command for all**: `/plugin install <name>@<marketplace>` or interactive `/plugin`.

## Master TOC

- [Workflow / quality](#workflow--quality)
- [External integrations](#external-integrations)
- [Specialized / domain](#specialized--domain)
- [Third-party marketplace plugins](#third-party-marketplace-plugins)
- [Install all (one shot)](#install-all-one-shot)

## Workflow / quality

**Context:** `always`. These shape the day-to-day workflow.

| Plugin | Purpose | Install |
|---|---|---|
| `superpowers@claude-plugins-official` | Meta-plugin: brainstorming, planning, debugging, TDD, code review, executing-plans, etc. | `/plugin install superpowers@claude-plugins-official` |
| `code-review@claude-plugins-official` | Slash-command code review on a PR or branch | `/plugin install code-review@claude-plugins-official` |
| `code-simplifier@claude-plugins-official` | Refactor for clarity, consistency, maintainability without behavior changes | `/plugin install code-simplifier@claude-plugins-official` |
| `feature-dev@claude-plugins-official` | Guided feature development with codebase understanding | `/plugin install feature-dev@claude-plugins-official` |
| `claude-md-management@claude-plugins-official` | Audit and improve `CLAUDE.md` files | `/plugin install claude-md-management@claude-plugins-official` |
| `commit-commands@claude-plugins-official` | `/commit`, `/commit-push-pr`, `/clean_gone` | `/plugin install commit-commands@claude-plugins-official` |
| `hookify@claude-plugins-official` | Author / configure hooks from conversation analysis | `/plugin install hookify@claude-plugins-official` |
| `claude-code-setup@claude-plugins-official` | Codebase analyzer + automation recommender | `/plugin install claude-code-setup@claude-plugins-official` |
| `skill-creator@claude-plugins-official` | Create / improve / eval skills | `/plugin install skill-creator@claude-plugins-official` |
| `learning-output-style@claude-plugins-official` | Interactive learning + explanatory output style | `/plugin install learning-output-style@claude-plugins-official` |
| `coderabbit@claude-plugins-official` | CodeRabbit AI code review | `/plugin install coderabbit@claude-plugins-official` |
| `optibot@claude-plugins-official` | Optibot AI review (alternative reviewer) | `/plugin install optibot@claude-plugins-official` |
| `qodo-skills@claude-plugins-official` | Qodo coding rules + PR resolver (alternative reviewer) | `/plugin install qodo-skills@claude-plugins-official` |
| `remember@claude-plugins-official` | Persist session state for clean continuation | `/plugin install remember@claude-plugins-official` |
| `mcp-server-dev@claude-plugins-official` | Build / package MCP servers | `/plugin install mcp-server-dev@claude-plugins-official` |
| `atomic-agents@claude-plugins-official` | Atomic agent design patterns | `/plugin install atomic-agents@claude-plugins-official` |

## External integrations

**Context:** project-dependent (UI work, GitHub integration, design tooling, etc.). Selectively install.

| Plugin | Context | Purpose | Install |
|---|---|---|---|
| `chrome-devtools-mcp@claude-plugins-official` | `ui-project`, `web-perf` | Chrome DevTools (incl. Lighthouse) via MCP | `/plugin install chrome-devtools-mcp@claude-plugins-official` |
| `playwright@claude-plugins-official` | `ui-project` | Playwright browser automation MCP | `/plugin install playwright@claude-plugins-official` |
| `github@claude-plugins-official` | `always` | GitHub PR / issue / actions integration | `/plugin install github@claude-plugins-official` |
| `figma@claude-plugins-official` | `ui-project` | Figma → code, design system extraction | `/plugin install figma@claude-plugins-official` |
| `cloudinary@claude-plugins-official` | `image-or-video-work` | Cloudinary asset hosting + transformations | `/plugin install cloudinary@claude-plugins-official` |
| `microsoft-docs@claude-plugins-official` | `optional` | Query Microsoft / Azure documentation | `/plugin install microsoft-docs@claude-plugins-official` |
| `sourcegraph@claude-plugins-official` | `optional` | Search code at scale via Sourcegraph | `/plugin install sourcegraph@claude-plugins-official` |
| `searchfit-seo@claude-plugins-official` | `static-site`, `web-perf` | SEO audit + content / keyword strategy | `/plugin install searchfit-seo@claude-plugins-official` |
| `data-engineering@claude-plugins-official` | `optional` | Airflow / dbt / data pipeline workflows | `/plugin install data-engineering@claude-plugins-official` |
| `migration-to-aws@claude-plugins-official` | `optional` | AWS migration assistance | `/plugin install migration-to-aws@claude-plugins-official` |

**Note on `searchfit-seo`**: Per the `tool-proactivity` rule, ALWAYS ask before running an SEO audit — long reports bloat context.

## Specialized / domain

**Context:** highly task-specific. Install only when needed.

| Plugin | Context | Purpose |
|---|---|---|
| `huggingface-skills@claude-plugins-official` | `ml-research` | HF Hub workflows: trainer, datasets, papers, evals |
| `product-tracking-skills@claude-plugins-official` | `optional` | Telemetry / tracking plan management |
| `pagerduty@claude-plugins-official` | `optional` | Pre-commit risk scoring vs incident history |
| `circleback@claude-plugins-official` | `optional` | Meeting notes integration |
| `telegram@claude-plugins-official` | `optional` | Telegram channel access |

## Third-party marketplace plugins

| Plugin | Marketplace | Purpose |
|---|---|---|
| `minimax-skills@minimax-skills` | `minimax-skills` (`MiniMax-AI/skills`) | MiniMax AI skill pack: PDF / DOCX / PPTX, multimodal, music, etc. |
| `web-design-skills@garden-skills` | `garden-skills` (`ConardLi/garden-skills`) | Web design engineer + image gen |
| `knowledge-base-skills@garden-skills` | `garden-skills` | RAG knowledge base helpers |
| `image-generation-skills@garden-skills` | `garden-skills` | Image generation skill pack |
| `ui-ux-pro-max@ui-ux-pro-max-skill` | `ui-ux-pro-max-skill` (`nextlevelbuilder/ui-ux-pro-max-skill`) | UI/UX design patterns, color palettes, font pairings |

(Marketplaces themselves are added via `/plugin marketplace add <github-repo-or-url>`. See [cc-marketplaces-and-skill-bundles.md](cc-marketplaces-and-skill-bundles.md).)

## Install all (one shot)

For a fresh CC setup matching the author's defaults, run interactively:

```
/plugin
# then browse and install the workflow / quality block first
```

The `setup/init-agent-harness` skill (P8) automates this for new projects based on selected context tags.
