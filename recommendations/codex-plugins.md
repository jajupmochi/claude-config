# Codex Plugins & Tools

> Plugins, MCP servers, and external tools approved for use with Codex.
> Installed tools are auto-invoked per the `tool-proactivity` rule.

## Plugin auto-invocation

Codex plugins listed below are trusted to fire without re-confirmation when the task matches, per the `tool-proactivity` workflow rule. Destructive operations, SEO audits, and cost-heavy external API calls still require explicit approval.

## Active Codex Plugins

| Plugin | Purpose | Auto-fire | Notes |
|---|---|---|---|
| **superpowers** | Productivity meta-plugin (batch tasks, subagents, session orchestration) | ✅ when task is complex or multi-step | Install: search "superpowers" in /plugins |
| **chrome-devtools** | Browser automation, screenshots, console, network inspection | ✅ for UI work, debugging, visual verification | Used by `verify-visual` skill |
| **figma** | Figma design file access and asset extraction | ✅ when user references Figma URLs | OAuth required |
| **replayio** | Time-travel browser recording and debugging | ✅ when browser testing is involved | Used by `verify-visual` |
| **expo** | React Native / Expo mobile development workflow | ✅ when working in Expo projects | CICD workflows included |
| **mem** | Persistent memory across sessions (Codex native) | — | Enable in Codex settings |
| **mixpanel** | Product analytics querying | ✅ when user asks about analytics | Read-only by default |
| **convex** | Backend-as-a-service for real-time apps | ✅ when working with Convex projects | |

## MCP Servers (approved)

| Server | Purpose | Auto-fire |
|---|---|---|
| **chrome-devtools MCP** | Browser automation, screenshots, console | ✅ for UI verification |
| **figma MCP** | Figma API access | ✅ when user references Figma |
| **github MCP** | PR review, issue management, repo operations | ✅ for git workflows |
| **openai-developer-docs MCP** | Official OpenAI/Codex documentation | ✅ for docs questions |
| **linear MCP** | Issue tracking and project management | ✅ when user mentions tickets |

## External tools (CLI-based)

| Tool | Purpose | Install |
|---|---|---|
| **Playwright** | Cross-browser testing and screenshots | `npx playwright install chromium` |
| **BackstopJS** | Visual regression testing | `npm install -g backstopjs` |
| **gh CLI** | GitHub operations (PRs, issues, CI) | Pre-installed on most systems |
| **jq** | JSON processing | `apt install jq` / `brew install jq` |
| **ripgrep (rg)** | Fast code search | `apt install ripgrep` / `brew install ripgrep` |
| **uv** | Python package manager | `curl -LsSf https://astral.sh/uv/install.sh | sh` |
| **ruff** | Python linter + formatter | Installed via `uv` |

## Integration

- The `tool-proactivity` rule authorizes auto-invocation of installed plugins
- The `plugin-preflight` rule requires verifying a plugin is installed before invoking
- New plugins are added to this list after testing with both GPT-5.5 and DeepSeek models
