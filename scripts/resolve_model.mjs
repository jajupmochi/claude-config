#!/usr/bin/env node
// resolve_model.mjs — deterministic model resolver for the adaptive-model map (task 10).
// Reads adapters/models.config.json and answers "which model should agent A use for tier/task-kind T?".
//   node scripts/resolve_model.mjs <agent> <tier|task-kind>
//   e.g. resolve_model.mjs claude research  -> claude-opus-4-8   (research -> high tier)
//        resolve_model.mjs opencode small   -> anthropic/claude-haiku-4-5
// Also exported as resolveModel(config, agent, key) for programmatic use / tests.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

export function resolveModel(config, agent, key) {
  const agents = config.agents || {};
  const tiers = agents[agent];
  if (!tiers) throw new Error(`unknown agent: ${agent} (known: ${Object.keys(agents).join(", ")})`);
  // key may be a tier directly, or a task-kind that maps to a tier via task_tier.
  const tier = config.tiers?.includes(key) ? key : (config.task_tier || {})[key];
  if (!tier) throw new Error(`unknown tier/task-kind: ${key} (tiers: ${(config.tiers || []).join(", ")}; task-kinds: ${Object.keys(config.task_tier || {}).join(", ")})`);
  const model = tiers[tier];
  if (!model) throw new Error(`agent ${agent} has no model for tier ${tier}`);
  return model;
}

function loadConfig() {
  const root = dirname(dirname(fileURLToPath(import.meta.url)));
  return JSON.parse(readFileSync(join(root, "adapters", "models.config.json"), "utf8"));
}

function main() {
  const [agent, key] = process.argv.slice(2);
  if (!agent || !key) {
    console.error("usage: resolve_model.mjs <agent> <tier|task-kind>");
    process.exit(2);
  }
  try {
    process.stdout.write(resolveModel(loadConfig(), agent, key) + "\n");
  } catch (e) {
    console.error(String(e.message || e));
    process.exit(1);
  }
}

// Run main only when invoked directly (not when imported by the test).
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) main();
