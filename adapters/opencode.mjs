// opencode projector: canonical manifest.source.json -> opencode.json (repo root)
// Pure function (no I/O, no LLM). opencode has NO static plugin manifest — plugins are JS —
// so we emit a real `opencode.json` (JSONC-compatible) rather than inventing a manifest.
// Mapping: rules -> instructions[]; hooks -> plugin[] (names only; hook LOGIC is a separate
// JS port); skills are read natively from .claude/skills/; model/small_model are task-10 defaults.
// Key order follows the opencode convention ($schema first). Source: opencode.ai/docs.
import { stableJson } from "./lib/emit.mjs";

export const target = "opencode.json";

export function render(source) {
  const o = source.opencode;
  // model tiers come from adapters/models.config.json (single source of truth for task 10),
  // attached to `source.models` by build.mjs / test-projection.mjs.
  const oc = source.models?.agents?.opencode;
  if (!oc || !oc.high || !oc.small) {
    throw new Error("opencode projector: source.models.agents.opencode.{high,small} missing (load adapters/models.config.json)");
  }
  const obj = {
    $schema: o.schema,
    model: oc.high,
    small_model: oc.small,
    instructions: o.instructions,
    plugin: o.plugin,
  };
  return stableJson(obj);
}
