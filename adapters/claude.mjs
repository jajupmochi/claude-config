// Claude Code projector: canonical manifest.source.json -> .claude-plugin/plugin.json
// Pure function (no I/O, no LLM). Key order below MUST match the committed manifest
// so the rendered output byte-matches it (parity gate in build.mjs --check).
import { stableJson } from "./lib/emit.mjs";

export const target = ".claude-plugin/plugin.json";

export function render(source) {
  const s = source.shared;
  const c = source.claude;
  const inv = source.inventory;
  const obj = {
    $schema: c.$schema,
    name: s.name,
    version: s.version,
    description: c.description,
    author: s.author,
    license: s.license,
    homepage: s.homepage,
    repository: s.repository,
    keywords: c.keywords,
    skills: inv.skills,
    rules: inv.rules,
    hooks: inv.hooks,
    templates: inv.templates,
    recommendations: inv.recommendations,
    tooling: inv.tooling,
    _notes: c.notes,
  };
  return stableJson(obj);
}
