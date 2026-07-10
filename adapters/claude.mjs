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
    // CC's plugin.schema.json requires repository to be a STRING (not the npm-style {type,url} object) —
    // verified by the installer's own validation error ("repository: expected string, received object").
    repository: typeof s.repository === "string" ? s.repository : s.repository.url,
    keywords: c.keywords,
    // NOTE: no explicit "skills" array. CC AUTO-DISCOVERS every skills/*/SKILL.md in the plugin; listing them
    // explicitly too makes CC load each skill TWICE (verified: explicit list -> 31 skills w/ dups + ~3.6k tok;
    // auto-discovery only -> 20 clean skills + ~2.0k tok). So we let auto-discovery do it. (`inv.skills` is still
    // the canonical curated list consumed by the codex/opencode projectors and bin/deploy-skills.mjs.)
    rules: inv.rules,
    // NOTE: hooks are intentionally NOT emitted here. CC's plugin hooks want an event-keyed OBJECT
    // ({"Stop":[{hooks:[{type,command}]}]}), not this array of dir paths (the array fails validation). More
    // importantly, on an installed machine the review-gate hook is already delivered via ~/.claude/settings.json;
    // emitting it in the plugin too would DOUBLE-fire it. So the plugin ships SKILLS; hooks stay in settings.json
    // (and rules stay in CLAUDE.md). See docs/PLUGIN_INSTALL.md.
    templates: inv.templates,
    recommendations: inv.recommendations,
    tooling: inv.tooling,
    _notes: c.notes,
  };
  return stableJson(obj);
}
