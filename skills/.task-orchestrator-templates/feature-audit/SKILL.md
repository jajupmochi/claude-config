---
name: feature-audit-template
template-for: systematic audit of all features for gaps and missing adaptations
min-capability: low
last-updated: 2026-07-08
template-version: 1
version-history:
  - version: 1
    date: 2026-07-08
    author: codex/deepseek-v3
    changes: Initial template for comprehensive feature auditing
---

# feature-audit-template

## RESEARCH phase

1. Inventory ALL features:
   - Skills (\`ls skills/*/SKILL.md\`)
   - Rules (\`ls rules/*/RULE.md\`)
   - Hooks — Claude (\`ls hooks/*/README.md\`) AND Codex (\`cat hooks.json\`)
   - Scripts (\`ls scripts/*.{sh,js}\`)
   - Templates (\`ls templates/*/TEMPLATE_README.md\`)
2. For each feature, check:
   - Does it have a Claude Code implementation? (source)
   - Does it have a Codex implementation? (wrapper, or mapping)
   - Is the Codex wrapper correct? (tool names mapped, hooks present, auto-load configured)
   - Does it work with non-vision models? (visual features especially)
   - Is it discoverable? (/skills, /plugins, manifest references)
3. Record gaps in audit report

## AUDIT MATRIX

For each feature, fill this table:

| Feature | Claude | Codex | Auto-load | Non-vision safe | Status |
|---|---|---|---|---|
| code-verifier | source skill | wrapper | ✅ YES | ✅ n/a | OK |
| research-critic | source skill | wrapper | ✅ YES | ✅ n/a | OK |
| verify-visual | chrome MCP | screenshot script | ❌ | ✅ YES | FIXED |
| review-gate | Stop hook | hooks.json Stop | n/a | ✅ n/a | FIXED |
| ... | ... | ... | ... | ... | ... |

## Common gaps found

1. Skill has Claude source but no Codex wrapper
2. Codex wrapper exists but has no frontmatter (not discoverable)
3. Codex wrapper has no allow_implicit_invocation (won't auto-load)
4. Codex hook script missing for Claude hook equivalent
5. Claude tool name (Write|Edit|Bash) not mapped to Codex equivalent
6. Visual feature assumes model vision capability

## GENERATE recommendations

For each gap: generate fix recommendation with priority (P0=blocking, P1=important, P2=nice-to-have).
