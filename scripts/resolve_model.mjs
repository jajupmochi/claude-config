#!/usr/bin/env node
// resolve_model.mjs — deterministic model resolver for the adaptive-model map (task 10).
// Reads adapters/models.config.json and answers "which model should agent A use for tier/task-kind T?".
//   node scripts/resolve_model.mjs <agent> <tier|task-kind> [--effort]
//   e.g. resolve_model.mjs claude research           -> claude-opus-4-8   (research -> high tier)
//        resolve_model.mjs claude mid                -> claude-sonnet-5
//        resolve_model.mjs claude mid --effort       -> max               (spawn the mid sub-agent at max effort)
//        resolve_model.mjs opencode small            -> anthropic/claude-haiku-4-5
// Also exported as resolveModel / resolveEffort(config, agent, key) for programmatic use / tests.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

// Resolve a tier/task-kind key to a concrete tier name (shared by model + effort resolution).
function resolveTier(config, agent, key) {
  const tiers = (config.agents || {})[agent];
  if (!tiers) throw new Error(`unknown agent: ${agent} (known: ${Object.keys(config.agents || {}).join(", ")})`);
  const tier = config.tiers?.includes(key) ? key : (config.task_tier || {})[key];
  if (!tier) throw new Error(`unknown tier/task-kind: ${key} (tiers: ${(config.tiers || []).join(", ")}; task-kinds: ${Object.keys(config.task_tier || {}).join(", ")})`);
  return tier;
}

export function resolveModel(config, agent, key) {
  const tier = resolveTier(config, agent, key);
  const model = ((config.agents || {})[agent] || {})[tier];
  if (!model) throw new Error(`agent ${agent} has no model for tier ${tier}`);
  return model;
}

// Reasoning effort for the tier (Agent-tool enum). Returns null if none is declared for this agent (e.g.
// opencode/codex set effort via their own config, not here) — callers then use the agent's own default.
export function resolveEffort(config, agent, key) {
  const tier = resolveTier(config, agent, key);
  return (((config.effort || {})[agent] || {})[tier]) ?? null;
}

function loadConfig() {
  const root = dirname(dirname(fileURLToPath(import.meta.url)));
  return JSON.parse(readFileSync(join(root, "adapters", "models.config.json"), "utf8"));
}

function main() {
  const args = process.argv.slice(2);
  const wantEffort = args.includes("--effort");
  const [agent, key] = args.filter((a) => a !== "--effort");
  if (!agent || !key) {
    console.error("usage: resolve_model.mjs <agent> <tier|task-kind> [--effort]");
    process.exit(2);
  }
  try {
    const cfg = loadConfig();
    if (wantEffort) {
      const e = resolveEffort(cfg, agent, key);
      process.stdout.write((e ?? "") + "\n"); // empty line = agent's own default effort
    } else {
      process.stdout.write(resolveModel(cfg, agent, key) + "\n");
    }
  } catch (e) {
    console.error(String(e.message || e));
    process.exit(1);
  }
}

// Run main only when invoked directly (not when imported by the test).
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) main();
