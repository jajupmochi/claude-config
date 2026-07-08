---
name: agent-config-adapter
description: Adapt an existing agent configuration or plugin to a new agent or model route. Use when moving agent-harness or another agent setup between Claude Code, Codex, Gemini, Cursor, local models, or non-native model backends such as DeepSeek routed through another agent.
---

# agent-config-adapter

Use this workflow to port an existing agent configuration without dumping every
rule into the target agent context.

## Inputs to establish

1. Source agent and config root.
2. Target agent and target model route.
3. Whether the model is native to the target agent or routed through a
   compatibility layer.
4. Required capabilities: durable instructions, skills, hooks, MCP/tools,
   slash commands, subagents, browser/computer use, memories, and installers.
5. Non-negotiable isolation constraints: what must not affect the original
   agent setup.

## Adaptation steps

1. Inventory the source configuration:
   - manifests
   - skills
   - hooks
   - rules/instructions
   - MCP/app/tool config
   - install scripts
   - templates
   - tests or validation scripts
2. Research the target agent's current extension surfaces from local docs or
   official docs. For Codex, use the `openai-docs` Codex manual route.
3. Build a mapping table: source item, target surface, required rewrite,
   verification method, and isolation risk.
4. Choose the smallest target entrypoint:
   - instructions file for always-on repo rules
   - skill for reusable workflow
   - plugin for distribution
   - hook for lifecycle enforcement
   - MCP/app for live tools or private external data
5. Implement target-specific wrappers. Keep shared source content as references
   so implicit skill metadata stays small.
6. Verify structurally first, then run one realistic prompt per major workflow.

## Model-route fallbacks

When the target model is not native to the agent, or implicit tool use is weak:

- Prefer explicit skill invocation in user docs and default prompts.
- Split long rule sets into small wrappers that name exactly which references
  to read.
- Use scripts for deterministic checks instead of relying on the model to
  remember every invariant.
- Require command output or file inspection before success claims.
- Avoid hidden global instructions that the routed model may ignore.
- Keep model-specific workarounds in the adapter skill, not in shared rules.

## Deliverables

Every adaptation should leave:

- A plan document with the mapping table and selected architecture.
- Agent-specific manifest/config files.
- A validation command or script.
- Installation notes for the target agent.
- A rollback note explaining which original agent files were not touched.
