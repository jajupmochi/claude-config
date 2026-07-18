#!/usr/bin/env node
// rule-activation.mjs — report and fix registered-but-inert rules.
//
// The problem this exists to solve: a rule being registered does NOT mean it loads. `adapters/claude.mjs`
// deliberately emits no rule loader ("rules stay in CLAUDE.md"), so `.claude-plugin/plugin.json`'s `rules[]`
// array is inventory metadata, not a runtime import. A rule reaches the model only if its text is in a file
// the agent actually reads. On this machine that gap left design-modes, test-first, regression-test-on-bugfix,
// incremental-delivery and parity-restoration registered, shipped, documented — and never once in context.
//
// So: --check reports, per rule, whether its text is actually reachable by each agent, and --apply appends
// the missing ones into a regeneratable managed block.
//
//   node bin/rule-activation.mjs --check                 # report all agents, exit 1 if anything is inert
//   node bin/rule-activation.mjs --check --agent claude
//   node bin/rule-activation.mjs --apply --agent claude  # write the managed block
//   node bin/rule-activation.mjs --apply --dry-run       # show the block without writing
//
// opencode is reported but never written: its `opencode.json` carries `instructions: ["rules/*/RULE.md"]`,
// so it already loads every rule from the glob and needs no block.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const BEGIN = "<!-- agent-harness:rules:begin -->";
export const END = "<!-- agent-harness:rules:end -->";

export function agentTargets(home = os.homedir()) {
  return {
    claude: { file: path.join(home, ".claude", "CLAUDE.md"), writable: true },
    codex: { file: path.join(home, ".codex", "AGENTS.md"), writable: true },
    // opencode.json declares instructions: ["rules/*/RULE.md"], so every rule is already loaded by glob.
    opencode: { file: path.join(REPO_ROOT, "opencode.json"), writable: false, loadsByGlob: true },
  };
}

export function registeredRules(repoRoot = REPO_ROOT) {
  const manifest = JSON.parse(fs.readFileSync(path.join(repoRoot, "adapters/manifest.source.json"), "utf8"));
  return (manifest.inventory?.rules ?? []).map((rel) => {
    const name = path.basename(rel);
    const snippetPath = path.join(repoRoot, rel, "snippet.md");
    const rulePath = path.join(repoRoot, rel, "RULE.md");
    return {
      name, rel,
      snippet: fs.existsSync(snippetPath) ? fs.readFileSync(snippetPath, "utf8").trim() : null,
      hasRule: fs.existsSync(rulePath),
    };
  });
}

/**
 * Decide whether a rule's guidance is already reachable in `text`.
 *
 * Deliberately generous: the user hand-maintains their own CLAUDE.md, so the same rule can appear under a
 * heading they wrote themselves rather than verbatim from snippet.md. Over-reporting a rule as missing
 * would duplicate content they already have, which costs tokens on every single turn. Every decision is
 * reported with the evidence that produced it, so a wrong call is visible rather than silent.
 */
/** Collapse punctuation and case so "Always-on verification skills" matches "always on verification". */
export function normalize(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

export function detectActive(rule, text) {
  if (!text) return { active: false, evidence: null };
  const hay = normalize(text);
  const candidates = [rule.name];
  if (rule.snippet) {
    const heading = rule.snippet.split("\n").find((l) => l.startsWith("#"));
    if (heading) candidates.push(heading.replace(/^#+\s*/, "").trim());
  }
  for (const c of candidates) {
    const needle = normalize(c);
    if (needle.length > 3 && hay.includes(needle)) return { active: true, evidence: c };
  }
  return { active: false, evidence: null };
}

/**
 * Rules the user has deliberately covered in their own words, so the detector's miss is expected.
 * Without this, a heavily paraphrased rule reads as inert forever and gets duplicated into the managed
 * block, paying tokens on every turn for text that is already there.
 */
export function loadIgnores(home = os.homedir()) {
  const f = path.join(home, ".claude", "agent-harness-rule-activation.ignore");
  if (!fs.existsSync(f)) return new Set();
  return new Set(fs.readFileSync(f, "utf8").split("\n")
    .map((l) => l.replace(/#.*/, "").trim()).filter(Boolean));
}

/**
 * Remove the managed block and give back everything else byte for byte.
 *
 * The target is the user's hand-maintained CLAUDE.md, so a sloppy strip eats their writing. Three guards.
 * END pairs with the LAST BEGIN before it, so a stray BEGIN left by a partial edit cannot make the strip
 * swallow every line between that marker and the real block. A block missing its END is left alone rather
 * than truncated. Only the newline run at the seam is collapsed, so spacing the user chose elsewhere in the
 * file survives instead of being reflowed on every --apply.
 */
export function stripManagedBlock(text) {
  const j = text.indexOf(END);
  if (j === -1) return text;
  const i = text.lastIndexOf(BEGIN, j);
  if (i === -1) return text;
  const head = text.slice(0, i).replace(/\n+$/, "");
  const tail = text.slice(j + END.length).replace(/^\n+/, "");
  if (!head) return tail;
  if (!tail) return `${head}\n`;
  return `${head}\n\n${tail}`;
}

export function renderBlock(missing) {
  const lines = [
    BEGIN,
    "",
    "# Rules activated by agent-harness",
    "",
    "> Generated by `bin/rule-activation.mjs`. Registered rules whose text was not found elsewhere in this",
    "> file are collected here so they actually reach the model. The block is regenerated in full on every",
    "> `--apply`, so edit `rules/<name>/snippet.md` in the harness rather than editing between these markers.",
    "",
  ];
  for (const r of missing) {
    lines.push(r.snippet || `## ${r.name}\n\n_(no snippet.md — see \`${r.rel}/RULE.md\`)_`, "");
  }
  lines.push(END, "");
  return lines.join("\n");
}

export function analyze(agent, target, rules, ignores = new Set()) {
  const exists = fs.existsSync(target.file);
  const raw = exists ? fs.readFileSync(target.file, "utf8") : "";
  const outside = stripManagedBlock(raw);
  const results = rules.map((r) => {
    if (target.loadsByGlob) return { rule: r, active: true, evidence: "loaded by glob", managed: false, needsBlock: false };
    if (ignores.has(r.name)) return { rule: r, active: true, evidence: "ignored by user", managed: false, needsBlock: false };
    const d = detectActive(r, outside);
    const inBlock = !d.active && raw !== outside && detectActive(r, raw).active;
    return {
      rule: r,
      active: d.active || inBlock,
      evidence: d.evidence || (inBlock ? "managed block" : null),
      managed: inBlock,
      // `active` answers "does this rule reach the model", which the block itself satisfies. `needsBlock`
      // answers the different question "does the block have to carry it", and only text found OUTSIDE the
      // block lets it off. The block is regenerated wholesale, so a rule already in it must be re-emitted:
      // listing only the rules missing everywhere would rewrite the block without them, and activating one
      // new rule would silently deactivate every rule activated before it.
      needsBlock: !d.active,
    };
  });
  return { agent, target, exists, raw, outside, results, missing: results.filter((x) => x.needsBlock).map((x) => x.rule) };
}

function main() {
  const argv = process.argv.slice(2);
  const has = (f) => argv.includes(f);
  const val = (f, d) => (argv.includes(f) ? argv[argv.indexOf(f) + 1] : d);
  const apply = has("--apply");
  const dryRun = has("--dry-run");
  const only = val("--agent", "all");

  const rules = registeredRules();
  const targets = agentTargets();
  const ignores = loadIgnores();
  const verbose = has("--verbose");
  const agents = only === "all" ? Object.keys(targets) : [only];
  if (agents.some((a) => !targets[a])) {
    console.error(`unknown agent (have: ${Object.keys(targets).join(", ")}, or "all")`);
    process.exit(1);
  }

  let inert = 0;
  for (const agent of agents) {
    const a = analyze(agent, targets[agent], rules, ignores);
    const active = a.results.filter((r) => r.active).length;
    console.log(`\n${agent} -> ${a.target.file}${a.exists ? "" : "  (missing)"}`);
    console.log(`  ${active}/${rules.length} rules reachable`);
    if (a.target.loadsByGlob) {
      console.log("  loads every rule via instructions glob; nothing to write");
      continue;
    }
    if (verbose) {
      for (const r of a.results.filter((x) => x.active)) {
        console.log(`  ok     ${r.rule.name.padEnd(28)} matched: ${r.evidence}`);
      }
    }
    // Counted off `active`, not off `missing` — a rule already carried by the managed block reaches the
    // model and is not inert, even though the block has to re-emit it on the next --apply.
    const unreachable = a.results.filter((x) => !x.active);
    for (const r of unreachable) {
      console.log(`  INERT  ${r.rule.name}${r.rule.snippet ? "" : "  (no snippet.md)"}`);
    }
    inert += unreachable.length;

    if (apply && a.missing.length) {
      const block = renderBlock(a.missing);
      if (dryRun) {
        console.log(`  --dry-run: would write ${a.missing.length} rule(s), ${block.length} bytes`);
        continue;
      }
      const base = stripManagedBlock(a.raw).replace(/\s*$/, "\n");
      fs.mkdirSync(path.dirname(a.target.file), { recursive: true });
      fs.writeFileSync(a.target.file, `${base}\n${block}`, "utf8");
      console.log(`  wrote managed block with ${a.missing.length} rule(s)`);
    }
  }

  if (!apply && inert) {
    console.log(`\n${inert} registered rule(s) are inert. Fix: node bin/rule-activation.mjs --apply`);
    process.exit(1);
  }
  console.log(inert && apply ? "" : "\nall registered rules are reachable");
}

// Robust "is this the entry script?" check — comparing import.meta.url to `file://${argv[1]}` breaks when the
// path contains spaces (import.meta.url percent-encodes them), so resolve both back to plain paths.
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) main();
