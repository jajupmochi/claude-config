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
  const obj = {
    $schema: o.schema,
    model: o.model,
    small_model: o.small_model,
    instructions: o.instructions,
    plugin: o.plugin,
  };
  return stableJson(obj);
}
