#!/usr/bin/env node
// Tests for rule-activation.mjs. Run: node bin/rule-activation.test.mjs
import assert from "node:assert";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  BEGIN, END, REPO_ROOT,
  agentTargets, analyze, detectActive, loadIgnores, normalize, registeredRules, renderBlock, stripManagedBlock,
} from "./rule-activation.mjs";

let n = 0;
const ok = (m) => (n++, console.log("  ok:", m));
const tmpDirs = [];
const tmp = () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), "ruleactivation-"));
  tmpDirs.push(d);
  return d;
};
const CLI = path.join(path.dirname(fileURLToPath(import.meta.url)), "rule-activation.mjs");

// Synthetic rules, shaped like registeredRules() output, so the unit tests do not move when the real
// inventory does. A rule with snippet: null exercises the "registered but never authored" path.
const ALPHA = { name: "alpha-rule", rel: "rules/alpha-rule", snippet: "## Alpha rule\n\n- do alpha", hasRule: true };
const BETA = { name: "beta-rule", rel: "rules/beta-rule", snippet: "## Beta rule\n\n- do beta", hasRule: true };
const GAMMA = { name: "gamma-rule", rel: "rules/gamma-rule", snippet: null, hasRule: true };

// The real inventory, read once. Several checks below are only meaningful against a non-empty one, so it
// is asserted here rather than left to go quietly vacuous if the manifest ever fails to parse.
const inventory = registeredRules();
assert.ok(inventory.length >= 20, `expected the manifest rule inventory, got ${inventory.length}`);

const claudeTarget = (file) => ({ file, writable: true });
function withFile(contents) {
  const f = path.join(tmp(), "CLAUDE.md");
  fs.writeFileSync(f, contents, "utf8");
  return f;
}

// 1. normalize: case and punctuation both collapse, so a hand-written heading matches the rule's own wording
assert.strictEqual(normalize("Always-on verification skills"), "always on verification skills");
assert.ok(normalize("Always-on verification skills").includes(normalize("always on verification")));
assert.strictEqual(normalize("  **Root-Cause** / before_fix!  "), "root cause before fix");
assert.strictEqual(normalize("root-cause-before-fix"), normalize("Root Cause Before Fix"));
assert.strictEqual(normalize("###"), "", "punctuation-only input collapses to empty, it does not become a wildcard");
ok("normalize: collapses case, punctuation and separators");

// 2. detectActive: matches on the rule's own name
const byName = detectActive(ALPHA, "# My CLAUDE\n\n## Alpha Rule\n\nI wrote this section myself.\n");
assert.deepStrictEqual(byName, { active: true, evidence: "alpha-rule" });
ok("detectActive: matches on the rule name");

// 3. detectActive: matches on the snippet's first heading when the name itself is nowhere
const headed = { name: "zzz-unfindable-name", rel: "rules/zzz", snippet: "## Tool proactivity\n\n- invoke skills proactively" };
const byHeading = detectActive(headed, "# Notes\n\n## Tool Proactivity\n\nfire skills without being asked\n");
assert.deepStrictEqual(byHeading, { active: true, evidence: "Tool proactivity" }, "evidence is the heading text, without the ## prefix");
assert.strictEqual(detectActive({ ...headed, snippet: null }, "## Tool Proactivity").active, false, "without a snippet there is no heading to match on");
ok("detectActive: matches on the snippet's first heading");

// 4. detectActive: punctuation and case between the two spellings do not matter
assert.strictEqual(detectActive(ALPHA, "the **ALPHA_RULE** section").active, true);
assert.strictEqual(detectActive(ALPHA, "(alpha) rule").active, true, "any run of punctuation reads as one separator");
assert.strictEqual(detectActive(ALPHA, "the rule for alpha is documented").active, false, "matching is on the phrase, not on scattered words");
ok("detectActive: matches across differing punctuation and case");

// 5. detectActive: an unrelated document activates NOTHING. A detector loose enough to match everything
//    would report every rule as reachable and quietly do nothing forever, which is the failure this whole
//    tool exists to catch, so it is checked against the real inventory rather than a synthetic rule.
const unrelated = [
  "# widget-service",
  "",
  "> A tiny HTTP service that resizes uploaded images.",
  "",
  "## Install",
  "",
  "    npm install widget-service",
  "",
  "## Usage",
  "",
  "Start the server on port 8080 and POST a JPEG to /resize. The response carries the scaled",
  "image plus an ETag. Everything in front of it is cached by the CDN.",
  "",
  "| env var | default | meaning |",
  "|---|---|---|",
  "| `PORT` | 8080 | listen port |",
  "| `MAX_BYTES` | 5242880 | reject larger uploads |",
].join("\n");
const falsePositives = inventory.filter((r) => detectActive(r, unrelated).active);
assert.deepStrictEqual(falsePositives.map((r) => r.name), [], "no rule may read as active in an unrelated document");
assert.deepStrictEqual(detectActive(ALPHA, ""), { active: false, evidence: null }, "empty text is inactive, not a crash");
assert.strictEqual(detectActive({ name: "abc", rel: "rules/abc", snippet: null }, "abc abc abc").active, false, "a needle of 3 chars or fewer is too weak to count as evidence");
ok(`detectActive: unrelated document activates none of the ${inventory.length} real rules`);

// 6. stripManagedBlock: removes the block and nothing else
const cleanBase = "# Doc\n\n## A\n\ntext\n\n## B\n\nmore\n";
assert.strictEqual(stripManagedBlock(`${cleanBase}\n${BEGIN}\n\n## generated\n\n${END}\n`), cleanBase);
ok("stripManagedBlock: removes a block cleanly");

// 7. stripManagedBlock: no block at all is an exact identity, including the user's own blank-line spacing
const plain = "# Doc\n\nJust text.\n\n\nWith a wide gap the user left on purpose.\n";
assert.strictEqual(stripManagedBlock(plain), plain);
ok("stripManagedBlock: no block -> byte-identical passthrough");

// 8. stripManagedBlock: a malformed block is left ALONE. Truncating here would eat the user's CLAUDE.md,
//    which is the worst outcome this tool can produce, so both broken orderings are pinned.
const truncated = `# Doc\n\nEverything below must survive.\n\n${BEGIN}\n\n## half-written block\n`;
assert.strictEqual(stripManagedBlock(truncated), truncated, "BEGIN without END must be a no-op, never a truncation");
const reversed = `# Doc\n\n${END}\n\nBody the user wrote.\n\n${BEGIN}\n`;
assert.strictEqual(stripManagedBlock(reversed), reversed, "END before BEGIN must be a no-op");
ok("stripManagedBlock: malformed block -> no-op, file intact");

// 9. stripManagedBlock: text outside the block is returned byte for byte. The user hand-maintains this
//    file, so reflowing their spacing turns every --apply into an unrequested edit of their writing.
const spaced = "# Doc\n\n## A\n\ntext\n\n\n## B\n\nmore\n";
assert.strictEqual(stripManagedBlock(spaced + renderBlock([ALPHA])), spaced, "blank lines outside the block must survive the strip");
ok("stripManagedBlock: content outside the block is not reflowed");

// 10. stripManagedBlock: a stray BEGIN cannot make the strip swallow everything after it. --apply appends
//     a fresh block without removing a leftover marker, so this state is reachable in one command.
const stray = `# Doc\n\n${BEGIN}\n\nA paragraph the user wrote after a half-deleted block.\n\n${renderBlock([ALPHA])}`;
const strayOut = stripManagedBlock(stray);
assert.ok(strayOut.includes("A paragraph the user wrote"), "a stray BEGIN must not let the strip swallow the user's text");
assert.ok(!strayOut.includes("- do alpha"), "the real block is still removed");
ok("stripManagedBlock: a stray BEGIN does not swallow user content");

// 11. renderBlock: well-formed markers, every snippet carried, and a visible placeholder for a rule with none
const block = renderBlock([ALPHA, GAMMA]);
assert.ok(block.startsWith(BEGIN), "block opens with the BEGIN marker");
assert.ok(block.trimEnd().endsWith(END), "block closes with the END marker");
assert.ok(block.includes("- do alpha"), "the snippet text reaches the block");
assert.match(block, /## gamma-rule/);
assert.match(block, /no snippet\.md/, "a rule with no snippet says so instead of emitting nothing");
ok("renderBlock: markers, snippet text, and a placeholder for a missing snippet");

// 12. renderBlock round-trips through stripManagedBlock. This is what makes --apply safe to re-run.
const base = "# My CLAUDE\n\n## Something I wrote\n\nBody text.\n";
const rt = stripManagedBlock(base + renderBlock([ALPHA, BETA, GAMMA]));
assert.strictEqual(rt.replace(/\s+$/, ""), base.replace(/\s+$/, ""), "strip(base + render(rules)) must give back base");
ok("renderBlock -> stripManagedBlock round-trips to the original file");

// 13. The markers are HTML comments (invisible in rendered markdown) and neither contains the other,
//     which is what lets indexOf pair them.
assert.match(BEGIN, /^<!--.*-->$/);
assert.match(END, /^<!--.*-->$/);
assert.notStrictEqual(BEGIN, END);
assert.ok(!BEGIN.includes(END) && !END.includes(BEGIN), "neither marker may contain the other or the pairing breaks");
ok("BEGIN/END: distinct, non-nesting HTML comment markers");

// 14. registeredRules reads the real manifest and every entry resolves to a real RULE.md
for (const r of inventory) {
  assert.ok(r.hasRule, `${r.name}: hasRule should be true`);
  assert.ok(fs.existsSync(path.join(REPO_ROOT, r.rel, "RULE.md")), `${r.rel}/RULE.md missing on disk`);
  assert.ok(r.snippet === null || r.snippet.length > 0, `${r.name}: snippet must be null or non-empty, never ""`);
  assert.strictEqual(r.name, path.basename(r.rel), `${r.rel}: name is the directory basename`);
}
assert.strictEqual(new Set(inventory.map((r) => r.name)).size, inventory.length, "no duplicate rule names in the inventory");
ok(`registeredRules: ${inventory.length} rules, all with a RULE.md on disk`);

// 15. loadIgnores: missing file is empty, comments and blank lines are stripped
const ignHome = tmp();
assert.strictEqual(loadIgnores(ignHome).size, 0, "no ignore file -> empty set");
fs.mkdirSync(path.join(ignHome, ".claude"), { recursive: true });
fs.writeFileSync(path.join(ignHome, ".claude", "agent-harness-rule-activation.ignore"),
  "# I cover these in my own words\nwriting-style\n\n  output-brevity  # inline comment\n", "utf8");
assert.deepStrictEqual([...loadIgnores(ignHome)].sort(), ["output-brevity", "writing-style"]);
ok("loadIgnores: missing file -> empty, comments and blanks stripped");

// 16. agentTargets: writable HOME files for claude and codex, in-repo read-only glob loader for opencode
const t = agentTargets("/fake/home");
assert.strictEqual(t.claude.file, path.join("/fake/home", ".claude", "CLAUDE.md"));
assert.strictEqual(t.codex.file, path.join("/fake/home", ".codex", "AGENTS.md"));
assert.ok(t.claude.writable && t.codex.writable);
assert.strictEqual(t.opencode.writable, false);
assert.strictEqual(t.opencode.loadsByGlob, true);
assert.ok(t.opencode.file.startsWith(REPO_ROOT), "opencode target is the in-repo config, not a HOME path");
ok("agentTargets: claude/codex writable under HOME, opencode read-only in-repo");

// 17. analyze: a rule the user already covered in their own words is active, the rest are missing
const covered = withFile("# My CLAUDE\n\n## Alpha Rule\n\nI already wrote this one myself.\n");
const a17 = analyze("claude", claudeTarget(covered), [ALPHA, BETA, GAMMA]);
assert.strictEqual(a17.exists, true);
assert.strictEqual(a17.results[0].active, true);
assert.strictEqual(a17.results[0].evidence, "alpha-rule");
assert.deepStrictEqual(a17.missing.map((r) => r.name), ["beta-rule", "gamma-rule"]);
const a17missing = analyze("claude", claudeTarget(path.join(tmp(), "absent.md")), [ALPHA, BETA]);
assert.strictEqual(a17missing.exists, false);
assert.deepStrictEqual(a17missing.missing.map((r) => r.name), ["alpha-rule", "beta-rule"], "a target that does not exist yet has everything missing");
ok("analyze: reports the active/missing split, and a missing target file");

// 18. analyze: a target that loads rules by glob needs nothing written
const glob = analyze("opencode", { file: path.join(REPO_ROOT, "opencode.json"), writable: false, loadsByGlob: true }, [ALPHA, BETA, GAMMA]);
assert.strictEqual(glob.results.length, 3, "one result per rule, so the every() below is not vacuous");
assert.ok(glob.results.every((r) => r.active && r.evidence === "loaded by glob"));
assert.deepStrictEqual(glob.missing, [], "nothing is ever written to a glob-loading target");
ok("analyze: loadsByGlob -> all active, nothing missing");

// 19. analyze: an ignored rule counts as active and is never written into the block
const ignored = analyze("claude", claudeTarget(withFile("# My CLAUDE\n")), [ALPHA, BETA], new Set(["beta-rule"]));
const beta19 = ignored.results.find((r) => r.rule.name === "beta-rule");
assert.strictEqual(beta19.active, true);
assert.strictEqual(beta19.evidence, "ignored by user");
assert.deepStrictEqual(ignored.missing.map((r) => r.name), ["alpha-rule"], "an ignored rule is not written into the block");
ok('analyze: an ignored name -> active, evidence "ignored by user"');

// 20. analyze: a rule already inside the managed block is active AND still listed for the rewrite. The
//     block is regenerated rather than appended to, so leaving its current rules out of `missing` would
//     delete them the moment one new rule needs activating.
const withBlock = withFile(`# My CLAUDE\n\nhand-written section.\n\n${renderBlock([ALPHA])}`);
const a20 = analyze("claude", claudeTarget(withBlock), [ALPHA, BETA]);
const alpha20 = a20.results.find((r) => r.rule.name === "alpha-rule");
assert.strictEqual(alpha20.active, true);
assert.strictEqual(alpha20.evidence, "managed block");
assert.strictEqual(alpha20.managed, true);
assert.ok(a20.outside.includes("hand-written section."), "the user's own text is outside the block");
assert.ok(!a20.outside.includes("- do alpha"), "the block itself is not part of `outside`");
assert.deepStrictEqual(a20.missing.map((r) => r.name), ["alpha-rule", "beta-rule"], "regenerating the block must re-emit the rules already in it");
ok("analyze: a rule in the managed block stays in the regenerated block");

// --- CLI ---------------------------------------------------------------------------------------------
// Everything below writes to $HOME/.claude/CLAUDE.md, so prove the HOME override actually moves
// os.homedir() BEFORE running --apply. Without this guard a broken override rewrites the real file.
const cliHome = tmp();
const probe = spawnSync(process.execPath, ["-e", "process.stdout.write(require('node:os').homedir())"],
  { encoding: "utf8", env: { ...process.env, HOME: cliHome } });
assert.strictEqual(probe.stdout, cliHome, "HOME override must move os.homedir(); refusing to run --apply against the real HOME");
const runCli = (args, home) => spawnSync(process.execPath, [CLI, ...args], { encoding: "utf8", env: { ...process.env, HOME: home } });
const claudeMd = (home) => path.join(home, ".claude", "CLAUDE.md");
ok("CLI: HOME override verified, --apply is sandboxed to a temp dir");

// 21. --check exits 1 while rules are inert and 0 once --apply has written them
assert.strictEqual(runCli(["--check", "--agent", "claude"], cliHome).status, 1, "--check must exit 1 while rules are inert");
const applied = runCli(["--apply", "--agent", "claude"], cliHome);
assert.strictEqual(applied.status, 0, `--apply should exit 0: ${applied.stderr}`);
assert.ok(fs.existsSync(claudeMd(cliHome)), "--apply created the target file in the sandboxed HOME");
const checked = runCli(["--check", "--agent", "claude"], cliHome);
assert.strictEqual(checked.status, 0, `--check must exit 0 after --apply:\n${checked.stdout}`);
const counts = checked.stdout.match(/(\d+)\/(\d+) rules reachable/);
assert.ok(counts && counts[1] === counts[2], `every rule should be reachable after --apply, got ${counts?.[0]}`);
ok(`CLI: --check 1 -> --apply -> --check 0 (${counts[0]})`);

// 22. --apply is idempotent: a second run leaves the file byte for byte identical
const pass1 = fs.readFileSync(claudeMd(cliHome), "utf8");
assert.ok(pass1.includes(BEGIN) && pass1.includes(END) && pass1.length > 1000,
  "the first --apply wrote a real block, so comparing the two runs is not a comparison of two empty files");
assert.strictEqual(runCli(["--apply", "--agent", "claude"], cliHome).status, 0);
assert.strictEqual(fs.readFileSync(claudeMd(cliHome), "utf8"), pass1, "a second --apply must not change a single byte");
ok("CLI: --apply twice -> byte-identical file");

// 23. --apply preserves rules it activated earlier when the set of missing rules changes. Un-ignoring one
//     rule is the cheapest way to reach that state, and adding a rule to the manifest reaches the same one.
const unIgnoreHome = tmp();
const victim = inventory.find((r) => r.name === "phased-planning");
const returning = inventory.find((r) => r.name === "writing-style");
assert.ok(victim?.snippet && returning, "this test assumes phased-planning (with a snippet) and writing-style are registered");
const ignoreFile = path.join(unIgnoreHome, ".claude", "agent-harness-rule-activation.ignore");
fs.mkdirSync(path.dirname(ignoreFile), { recursive: true });
fs.writeFileSync(ignoreFile, "# covered in my own words for now\nwriting-style\n", "utf8");
assert.strictEqual(runCli(["--apply", "--agent", "claude"], unIgnoreHome).status, 0);
const victimHeading = victim.snippet.split("\n")[0];
assert.ok(fs.readFileSync(claudeMd(unIgnoreHome), "utf8").includes(victimHeading), "first --apply activated phased-planning");

fs.rmSync(ignoreFile);
assert.strictEqual(runCli(["--apply", "--agent", "claude"], unIgnoreHome).status, 0);
const pass2 = fs.readFileSync(claudeMd(unIgnoreHome), "utf8");
assert.ok(pass2.includes(victimHeading), "activating one more rule must not delete the rules already in the block");
const recheck = runCli(["--check", "--agent", "claude"], unIgnoreHome);
assert.strictEqual(recheck.status, 0, `every rule must still be reachable after the second --apply:\n${recheck.stdout}`);
ok("CLI: a newly missing rule is added without dropping the ones already activated");

// 24. --dry-run reports without touching the file
const dryHome = tmp();
const dry = runCli(["--apply", "--dry-run", "--agent", "claude"], dryHome);
assert.strictEqual(dry.status, 0);
assert.match(dry.stdout, /--dry-run: would write \d+ rule\(s\)/);
assert.ok(!fs.existsSync(claudeMd(dryHome)), "--dry-run must not create the target file");
ok("CLI: --dry-run reports without writing");

// 25. an unknown agent name fails loudly instead of silently doing nothing
const bogus = runCli(["--check", "--agent", "emacs"], tmp());
assert.strictEqual(bogus.status, 1, "an unknown agent must exit 1");
assert.match(bogus.stderr, /unknown agent/);
ok("CLI: unknown agent exits 1 with a reason");

for (const d of tmpDirs) fs.rmSync(d, { recursive: true, force: true });
console.log(`\nrule-activation.mjs: all ${n} checks PASS`);
