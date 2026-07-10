#!/usr/bin/env node
// Tests for deploy-skills.mjs. Run: node bin/deploy-skills.test.mjs
import assert from "node:assert";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { classify, plan, inventorySkills, agentSkillDirs, REPO_ROOT } from "./deploy-skills.mjs";

let n = 0;
const ok = (m) => (n++, console.log("  ok:", m));

function tmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "deployskills-"));
}

// 1. inventory is read from the manifest and every entry resolves to a real SKILL.md in-repo
const skills = inventorySkills();
assert(skills.length >= 10, "expected the canonical skill inventory");
for (const rel of skills) assert(fs.existsSync(path.join(REPO_ROOT, rel, "SKILL.md")), `SKILL.md for ${rel}`);
ok(`inventory: ${skills.length} skills, all have SKILL.md`);

// 2. classify(): a src with a SKILL.md and an ABSENT dst -> "link"
const src0 = path.join(REPO_ROOT, skills[0]);
const root = tmp();
const absent = path.join(root, "nope");
assert.equal(classify(src0, absent), "link");
ok("classify absent -> link");

// 3. classify(): a symlink pointing at THIS src -> "ok"
const good = path.join(root, "good");
fs.symlinkSync(src0, good, "dir");
assert.equal(classify(src0, good), "ok");
ok("classify symlink-to-us -> ok");

// 4. classify(): a REAL directory (user's own) -> "kept" (never clobber)
const real = path.join(root, "real");
fs.mkdirSync(real);
fs.writeFileSync(path.join(real, "SKILL.md"), "---\nname: real\n---\n");
assert.equal(classify(src0, real), "kept");
ok("classify real-dir -> kept (non-clobber)");

// 5. classify(): a symlink to SOMEWHERE ELSE -> "relink" (candidate, guarded at apply time)
const foreignTarget = path.join(root, "foreign-src");
fs.mkdirSync(foreignTarget);
const foreign = path.join(root, "foreign");
fs.symlinkSync(foreignTarget, foreign, "dir");
assert.equal(classify(src0, foreign), "relink");
ok("classify foreign-symlink -> relink");

// 6. classify(): src without SKILL.md -> "nosrc"
assert.equal(classify(root, absent), "nosrc");
ok("classify src-without-SKILL.md -> nosrc");

// 7. plan(): produces one item per (agent x skill), all "link" against a fresh fake HOME
const home = tmp();
const items = plan({ home, agents: ["claude", "opencode"] });
assert.equal(items.length, skills.length * 2, "one item per agent x skill");
assert(items.every((it) => it.action === "link"), "all link on a fresh HOME");
const dirs = agentSkillDirs(home);
assert(items.some((it) => it.dst.startsWith(dirs.claude)) && items.some((it) => it.dst.startsWith(dirs.opencode)));
ok(`plan: ${items.length} items (${skills.length} skills x 2 agents), all link on fresh HOME`);

// 8. plan() respects an existing real dir as "kept" (does not plan to clobber it)
const home2 = tmp();
const name0 = path.basename(skills[0]);
const claudeDir = agentSkillDirs(home2).claude;
fs.mkdirSync(path.join(claudeDir, name0), { recursive: true });
fs.writeFileSync(path.join(claudeDir, name0, "SKILL.md"), "user's own\n");
const items2 = plan({ home: home2, agents: ["claude"] });
const it0 = items2.find((it) => it.name === name0);
assert.equal(it0.action, "kept", "existing real dir must be kept, not clobbered");
ok("plan: pre-existing real skill dir -> kept");

// 9. single-agent plan
const only = plan({ home: tmp(), agents: ["opencode"] });
assert(only.every((it) => it.agent === "opencode") && only.length === skills.length);
ok("plan: single-agent scoping works");

console.log(`\ndeploy-skills.mjs: all ${n} checks PASS`);
