// Codex projector: canonical manifest.source.json -> .codex-plugin/plugin.json
// Pure function (no I/O, no LLM). Key order below MUST match the committed manifest
// so the rendered output byte-matches it (parity gate in build.mjs --check).
// Note: the Codex manifest carries its own version/description/author/repository/keywords
// (author uses `url`, repository is a string) and an `interface` block; it points at
// skills via a "./skills/" string rather than the per-item inventory the Claude manifest uses.
import { stableJson } from "./lib/emit.mjs";

export const target = ".codex-plugin/plugin.json";

export function render(source) {
  const s = source.shared;
  const x = source.codex;
  const obj = {
    name: s.name,
    version: x.version,
    description: x.description,
    author: x.author,
    homepage: s.homepage,
    repository: x.repository,
    license: s.license,
    keywords: x.keywords,
    skills: x.skills,
    interface: x.interface,
  };
  return stableJson(obj);
}
