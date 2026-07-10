# Codex Marketplaces & Skill Bundles

> Third-party marketplaces, skill bundles, and curated collections for Codex.

## Official

| Source | Description |
|---|---|
| **Codex Plugin Directory** | Built-in: /plugins in Codex app. Browse, install, share. |
| **ChatGPT Plugin Store** | For MCP Apps mode: plugins discoverable in the ChatGPT ecosystem |

## Third-Party Marketplaces

| Marketplace | Description | Install |
|---|---|---|
| **Personal marketplace** | Your own plugins via `~/.agents/plugins/marketplace.json` | Local only |
| **Workspace shared** | Plugins shared within your ChatGPT workspace | Codex app → Plugins → Share |

## Skill Bundles (via /skills)

| Bundle | Source | Description |
|---|---|---|
| **agent-harness skills** | This repository | 13 skills: code-verifier, research-critic, verify-visual, task-orchestrator, figma-design-fetch, etc. |
| **superpowers skills** | Plugin | Batch tasks, subagents, session orchestration |
| **openai-docs** | System | Official Codex and OpenAI documentation |
| **plugin-creator** | System | Validate and publish Codex plugins |

## How to add a marketplace

See [Personal marketplace README](%7E/.agents/plugins/README.md) or create `~/.agents/plugins/marketplace.json`:

```json
{
  "name": "personal",
  "plugins": [
    {
      "name": "agent-harness",
      "source": { "source": "local", "path": "./plugins/agent-harness" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Productivity"
    }
  ]
}
```
