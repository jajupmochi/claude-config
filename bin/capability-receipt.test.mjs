#!/usr/bin/env node
// Tests for capability-receipt.mjs. Run: node bin/capability-receipt.test.mjs
//
// The tool's whole value is telling "fired" apart from "did not fire", so the tests that matter are the
// negative ones: a transcript where a capability is absent must report it absent. A detector that says
// everything fired is worse than no detector, because it manufactures false confidence.
import assert from "node:assert";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  loadCapabilities, encodeCwd, newestTranscript, collectEvidence, checkStateFile, evaluate, REPO_ROOT,
} from "./capability-receipt.mjs";

let n = 0;
const ok = (m) => (n++, console.log("  ok:", m));
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "caprcpt-"));

const asst = (blocks) => JSON.stringify({ type: "assistant", sessionId: "SID1", message: { role: "assistant", content: blocks } });
const usr = (t) => JSON.stringify({ type: "user", sessionId: "SID1", message: { role: "user", content: t } });

// 1. the shipped config parses and every entry is well formed
const caps = loadCapabilities();
assert(caps.length >= 8, `expected a real capability set, got ${caps.length}`);
for (const c of caps) {
  assert(c.id && c.label && c.expect_when, `capability missing fields: ${JSON.stringify(c)}`);
  assert(["hook", "advisory"].includes(c.enforcement), `bad enforcement on ${c.id}: ${c.enforcement}`);
  assert(Array.isArray(c.signatures) && c.signatures.length, `${c.id} has no signatures`);
  for (const s of c.signatures) {
    assert(["skill", "bash", "text", "state"].includes(s.kind), `${c.id}: bad kind ${s.kind}`);
    // Only the regex kinds are patterns. A `state` match is a path template containing {sid}, which is
    // an invalid regex quantifier — compiling it here is what exposed that evaluate() was doing the same
    // thing and silently skipping every state signature.
    if (s.kind !== "state") new RegExp(s.match, "u");
  }
}
ok(`config: ${caps.length} capabilities, all fields valid, all regexes compile`);

// 2. collectEvidence pulls skills, bash commands and assistant text out of a transcript
const root = tmp();
const tp = path.join(root, "t.jsonl");
fs.writeFileSync(tp, [
  usr("do the thing"),
  asst([{ type: "text", text: "starting" },
        { type: "tool_use", name: "Skill", input: { skill: "code-verifier" } }]),
  asst([{ type: "tool_use", name: "Bash", input: { command: "python3 ledger.py check" } }]),
  asst([{ type: "text", text: "done [END:WAIT]" }]),
].join("\n"));
let ev = collectEvidence(tp);
assert.deepStrictEqual(ev.skills, ["code-verifier"]);
assert(ev.bash.some((c) => c.includes("ledger.py check")));
assert(ev.text.some((t) => t.includes("[END:WAIT]")));
assert.strictEqual(ev.sid, "SID1");
ok("collectEvidence: skills, bash commands, text and session id");

// 3. a malformed line must not abort the scan — a live transcript's last line is often truncated
fs.appendFileSync(tp, "\n{not json at all");
ev = collectEvidence(tp);
assert.deepStrictEqual(ev.skills, ["code-verifier"], "a truncated tail must not lose earlier evidence");
ok("collectEvidence: a truncated line is skipped, not fatal");

// 4. --last-turn scopes to everything after the final user message
const tp2 = path.join(root, "t2.jsonl");
fs.writeFileSync(tp2, [
  usr("first request"),
  asst([{ type: "tool_use", name: "Skill", input: { skill: "research-critic" } }]),
  usr("second request"),
  asst([{ type: "tool_use", name: "Skill", input: { skill: "code-verifier" } }]),
].join("\n"));
assert.deepStrictEqual(collectEvidence(tp2).skills.sort(), ["code-verifier", "research-critic"]);
assert.deepStrictEqual(collectEvidence(tp2, { lastTurn: true }).skills, ["code-verifier"],
  "last-turn must exclude the earlier turn's evidence");
ok("--last-turn: scopes to the final user message onward");

// 5. evaluate reports fired vs not, and the NEGATIVE case is the one that matters
const ev2 = collectEvidence(tp2, { lastTurn: true });
const res = evaluate(caps, ev2, { sid: "SID1", cwd: root });
const byId = Object.fromEntries(res.map((r) => [r.id, r]));
assert.strictEqual(byId["code-verifier"].fired, true, "an invoked skill must read as fired");
assert(byId["code-verifier"].evidence.length > 0, "a firing must carry its evidence");
assert.strictEqual(byId["research-critic"].fired, false, "a skill from an EARLIER turn must not read as fired");
assert.strictEqual(byId["memory-flywheel"].fired, false, "a skill never invoked must not read as fired");
ok("evaluate: fired carries evidence; absent capabilities report absent");

// 6. a transcript with no tool use at all fires nothing except what its text proves
const tp3 = path.join(root, "t3.jsonl");
fs.writeFileSync(tp3, [usr("hi"), asst([{ type: "text", text: "hello" }])].join("\n"));
const res3 = evaluate(caps, collectEvidence(tp3), { sid: "NOPE", cwd: root });
const fired3 = res3.filter((r) => r.fired).map((r) => r.id);
assert(!fired3.includes("code-verifier") && !fired3.includes("task-ledger"),
  `an empty transcript must not report capabilities as fired: ${fired3}`);
ok("evaluate: an inert transcript reports (almost) nothing fired");

// 7. text signatures detect a RESULT, which is the only evidence available for a prompt-level rule
const tp4 = path.join(root, "t4.jsonl");
fs.writeFileSync(tp4, [usr("x"), asst([{ type: "text", text: "结果如下 [END:FINAL]" }])].join("\n"));
const res4 = evaluate(caps, collectEvidence(tp4), { sid: "S", cwd: root });
const b4 = Object.fromEntries(res4.map((r) => [r.id, r]));
assert.strictEqual(b4["end-of-turn-marker"].fired, true, "the END marker must be detected in text");
assert.strictEqual(b4["chinese-output"].fired, true, "CJK output must be detected");
const tp5 = path.join(root, "t5.jsonl");
fs.writeFileSync(tp5, [usr("x"), asst([{ type: "text", text: "all done, no marker here" }])].join("\n"));
const b5 = Object.fromEntries(evaluate(caps, collectEvidence(tp5), { sid: "S", cwd: root }).map((r) => [r.id, r]));
assert.strictEqual(b5["end-of-turn-marker"].fired, false, "a missing marker must report as missing");
assert.strictEqual(b5["chinese-output"].fired, false, "English-only output must report chinese-output as absent");
ok("text signatures: detected when present, absent when not (both directions)");

// 8. state signatures resolve ~, {sid} and relative paths
fs.mkdirSync(path.join(root, ".agent", "ledger"), { recursive: true });
fs.writeFileSync(path.join(root, ".agent", "ledger", "ACTIVE"), "r.md\n");
assert.strictEqual(checkStateFile(".agent/ledger/ACTIVE", { cwd: root }), true);
assert.strictEqual(checkStateFile(".agent/ledger/NOPE", { cwd: root }), false);
const fakeHome = tmp();
fs.mkdirSync(path.join(fakeHome, ".claude", "review-state"), { recursive: true });
fs.writeFileSync(path.join(fakeHome, ".claude", "review-state", "ABC.reviewed"), "");
assert.strictEqual(checkStateFile("~/.claude/review-state/{sid}.reviewed", { sid: "ABC", home: fakeHome }), true);
assert.strictEqual(checkStateFile("~/.claude/review-state/{sid}.reviewed", { sid: "XYZ", home: fakeHome }), false);
ok("state signatures: ~, {sid} and relative paths all resolve");

// 9. encodeCwd matches how Claude Code names its transcript directory
assert.strictEqual(encodeCwd("/media/linlin/New Volume1/projects/x"), "-media-linlin-New-Volume1-projects-x");
assert.strictEqual(newestTranscript("/definitely/not/a/real/path", root), null);
ok("encodeCwd + newestTranscript: correct encoding, null when absent");

// 9b. REGRESSION: a state signature must fire. It used to be compiled as a regex first, and "{sid}"
//      threw "Incomplete quantifier", so the catch skipped the check and no state signature ever fired.
const stRoot = tmp();
fs.mkdirSync(path.join(stRoot, ".agent", "ledger"), { recursive: true });
fs.writeFileSync(path.join(stRoot, ".agent", "ledger", "ACTIVE"), "round.md\n");
const stRes = evaluate(caps, { skills: [], bash: [], text: [], sid: "S" }, { sid: "S", cwd: stRoot });
const stLedger = stRes.find((r) => r.id === "task-ledger");
assert.strictEqual(stLedger.fired, true, "an ACTIVE ledger on disk must fire the state signature");
assert(stLedger.evidence.some((e) => e.startsWith("state:")), `expected state evidence: ${stLedger.evidence}`);
assert.deepStrictEqual(stRes.problems, [], `no config problems expected: ${stRes.problems}`);
fs.rmSync(stRoot, { recursive: true, force: true });

// 9c. A malformed pattern is reported as a config problem, not silently read as "did not fire".
const bogus = [{ id: "x", label: "x", enforcement: "advisory", expect_when: "never",
                 signatures: [{ kind: "text", match: "([unclosed" }] }];
const bogusRes = evaluate(bogus, { skills: [], bash: [], text: ["anything"], sid: "S" }, { cwd: "/tmp" });
assert.strictEqual(bogusRes[0].fired, false);
assert.strictEqual(bogusRes.problems.length, 1, "a bad pattern must be surfaced");
assert.match(bogusRes.problems[0], /bad text pattern/);
ok("REGRESSION: state signatures fire; a malformed pattern surfaces instead of reading as idle");

// 9d. REGRESSION: mentioning a capability's file is not running it. These commands were all reported as
//      firings on a real transcript — compiling a script, linting it, or a bare word inside an unrelated
//      alternation. A detector that counts these manufactures confidence, which is worse than none.
const decoy = {
  skills: [], text: [], sid: "S",
  bash: [
    "python3 -m py_compile skills/memory-flywheel/scripts/mem.py",
    "ruff check skills/prompt-library/scripts/plib.py",
    "cat hooks/task-ledger/scripts/ledger.py | head -20",
    "git commit -m 'privacy: redact the config'",
    "ls scripts/ | grep doccheck.py",
    "echo 'run harness-feedback.mjs later'",
  ],
};
for (const r of evaluate(caps, decoy, { sid: "S", cwd: "/definitely/not/real" })) {
  assert.strictEqual(r.fired, false,
    `${r.id} must NOT fire on a command that merely names its file: ${r.evidence}`);
}
// ...and the real invocations still DO fire, so the tightening did not make the detector blind.
const real = {
  skills: [], text: [], sid: "S",
  bash: [
    "python3 mem.py record --root /tmp/m --project p",
    "python3 plib.py find 'deploy'",
    "python3 ledger.py check",
    "python3 doccheck.py docs/X.md --type spec",
    "node bin/harness-feedback.mjs --list",
  ],
};
const realFired = evaluate(caps, real, { sid: "S", cwd: "/definitely/not/real" })
  .filter((r) => r.fired).map((r) => r.id).sort();
assert.deepStrictEqual(realFired,
  ["doc-writing", "harness-feedback", "memory-flywheel", "prompt-library", "task-ledger"],
  `real invocations must still fire, got: ${realFired}`);
ok("REGRESSION: compiling/linting/naming a script does not count as a firing; real invocations still do");

// 10. the CLI runs, and exits 1 with a reason when it cannot find a transcript
const cli = path.join(path.dirname(fileURLToPath(import.meta.url)), "capability-receipt.mjs");
const good = spawnSync(process.execPath, [cli, "--transcript", tp2], { encoding: "utf8" });
assert.strictEqual(good.status, 0, `expected exit 0, got ${good.status}: ${good.stderr}`);
assert.match(good.stdout, /FIRED\s+code-verifier/, "the CLI must report a firing");
assert.match(good.stdout, /does not block/, "the CLI must state that it only reports");
const bad = spawnSync(process.execPath, [cli, "--transcript", path.join(root, "nope.jsonl")], { encoding: "utf8" });
assert.strictEqual(bad.status, 1, "a missing transcript must exit 1");
assert.match(bad.stderr, /no transcript found/);
const js = spawnSync(process.execPath, [cli, "--transcript", tp2, "--json"], { encoding: "utf8" });
assert.strictEqual(js.status, 0);
assert(JSON.parse(js.stdout).results.length === caps.length, "--json must emit every capability");
ok("CLI: reports firings, --json is valid, a missing transcript exits 1 with a reason");

fs.rmSync(root, { recursive: true, force: true });
fs.rmSync(fakeHome, { recursive: true, force: true });
console.log(`\ncapability-receipt.mjs: all ${n} tests PASS`);
