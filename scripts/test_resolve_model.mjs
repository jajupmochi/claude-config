#!/usr/bin/env node
// Tests for scripts/resolve_model.mjs + the models.config.json contract. Run: node scripts/test_resolve_model.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { resolveModel, resolveEffort } from "./resolve_model.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const config = JSON.parse(readFileSync(join(ROOT, "adapters", "models.config.json"), "utf8"));
let pass = 0, fail = 0;
const chk = (n, got, want) => { if (got === want) { console.log(`  ok: ${n}`); pass++; } else { console.error(`  FAIL: ${n} (got ${JSON.stringify(got)} want ${JSON.stringify(want)})`); fail++; } };
const thr = (n, fn) => { try { fn(); console.error(`  FAIL: ${n} (expected throw)`); fail++; } catch { console.log(`  ok: ${n}`); pass++; } };

// 1. resolve by explicit tier
chk("claude/high", resolveModel(config, "claude", "high"), "claude-opus-4-8");
chk("claude/small", resolveModel(config, "claude", "small"), "claude-haiku-4-5");
chk("opencode/small", resolveModel(config, "opencode", "small"), "anthropic/claude-haiku-4-5");

// 2. resolve by task-kind (maps to a tier)
chk("claude research->high", resolveModel(config, "claude", "research"), "claude-opus-4-8");
chk("claude mechanical->small", resolveModel(config, "claude", "mechanical"), "claude-haiku-4-5");
chk("codex implement->mid", resolveModel(config, "codex", "implement"), "gpt-5.5");

// mid tier = Sonnet 5, and its effort = max (the requested change)
chk("claude/mid model == sonnet-5", resolveModel(config, "claude", "mid"), "claude-sonnet-5");
chk("claude mid effort == max", resolveEffort(config, "claude", "mid"), "max");
chk("claude implement->mid effort == max", resolveEffort(config, "claude", "implement"), "max");
chk("claude verify->mid effort == max", resolveEffort(config, "claude", "verify"), "max");
chk("claude high effort == high", resolveEffort(config, "claude", "high"), "high");
chk("claude small effort == low", resolveEffort(config, "claude", "small"), "low");
// opencode declares no effort here → null (it sets effort via its own config)
chk("opencode mid effort == null", resolveEffort(config, "opencode", "mid"), null);

// 3. errors: unknown agent / unknown key / agent missing tier
thr("unknown agent throws", () => resolveModel(config, "nope", "high"));
thr("unknown tier/task throws", () => resolveModel(config, "claude", "bogus"));

// 4. CONTRACT: every agent defines every declared tier (no missing tier = no dead lookup)
for (const [agent, tiers] of Object.entries(config.agents)) {
  for (const t of config.tiers) {
    if (tiers[t]) { pass++; } else { console.error(`  FAIL: ${agent} missing tier ${t}`); fail++; }
  }
}
console.log(`  ok: every agent defines every tier`);

// 5. CONSUMPTION CONTRACT (not a dead knob): opencode.json is generated FROM this config.
const oc = JSON.parse(readFileSync(join(ROOT, "opencode.json"), "utf8"));
chk("opencode.json model == models.config opencode.high", oc.model, config.agents.opencode.high);
chk("opencode.json small_model == models.config opencode.small", oc.small_model, config.agents.opencode.small);

console.log(fail ? `\nresolve_model: ${fail} FAIL / ${pass} pass` : `\nresolve_model: all ${pass} checks PASS`);
process.exit(fail ? 1 : 0);
