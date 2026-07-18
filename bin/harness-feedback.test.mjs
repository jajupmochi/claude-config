#!/usr/bin/env node
// Tests for harness-feedback.mjs. Run: node bin/harness-feedback.test.mjs
import assert from "node:assert";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { parseArgs, validate, formatEntry, appendEntry, readEntries, VERDICTS } from "./harness-feedback.mjs";

let n = 0;
const ok = (m) => (n++, console.log("  ok:", m));
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "harnessfb-"));

// 1. parseArgs: key/value pairs and bare flags
const a1 = parseArgs(["--feature", "rules/x", "--verdict", "native-better", "--why", "w", "--proposal", "p"]);
assert.deepStrictEqual(a1, { list: false, all: false, feature: "rules/x", verdict: "native-better", why: "w", proposal: "p" });
assert.deepStrictEqual(parseArgs(["--list", "--all"]), { list: true, all: true });
ok("parseArgs: pairs and flags");

// 2. parseArgs: a flag consuming the next flag as its value is an error, not a silent swallow
assert.throws(() => parseArgs(["--feature", "--verdict"]), /--feature needs a value/);
assert.throws(() => parseArgs(["--why"]), /--why needs a value/);
assert.throws(() => parseArgs(["stray"]), /unexpected argument/);
ok("parseArgs: rejects missing values and stray args");

// 3. validate: every required field is actually enforced
assert.strictEqual(validate(a1).length, 0, "a complete arg set validates clean");
assert.strictEqual(validate({}).length, 4, "all four fields reported missing");
const badVerdict = validate({ ...a1, verdict: "sounds-bad" });
assert.strictEqual(badVerdict.length, 1);
assert.match(badVerdict[0], /--verdict must be one of/);
ok("validate: required fields + verdict whitelist");

// 4. every documented verdict passes validation (the table and the checker cannot drift apart)
for (const v of Object.keys(VERDICTS)) {
  assert.strictEqual(validate({ ...a1, verdict: v }).length, 0, `verdict ${v} accepted`);
}
ok(`validate: all ${Object.keys(VERDICTS).length} documented verdicts accepted`);

// 5. formatEntry: stable id, and every field reaches the output
const entry = formatEntry({ ...a1, why: "forced a 3-phase plan onto a one-line fix", proposal: "narrow the trigger" }, "2026-07-18T12:00:00.000Z");
assert.match(entry, /^\n### 2026-07-18-rules-x$/m);
assert.match(entry, /- \*\*feature\*\*: `rules\/x`/);
assert.match(entry, /- \*\*verdict\*\*: `native-better`/);
assert.match(entry, /- \*\*status\*\*: open/);
assert.match(entry, /forced a 3-phase plan onto a one-line fix/);
assert.match(entry, /narrow the trigger/);
ok("formatEntry: id + all fields present");

// 6. appendEntry: creates the queue with its header, then appends without re-adding the header
const root = tmp();
const q = path.join(root, "docs", "harness-feedback", "QUEUE.md");
assert.ok(!fs.existsSync(q), "queue does not exist yet");
appendEntry(q, entry);
let text = fs.readFileSync(q, "utf8");
assert.match(text, /^# Harness feedback queue/, "header written on first append");
assert.strictEqual(text.split("### ").length - 1, 1, "one entry");

appendEntry(q, formatEntry({ ...a1, feature: "skills/y", verdict: "needs-update", why: "w2", proposal: "p2" }, "2026-07-19T00:00:00.000Z"));
text = fs.readFileSync(q, "utf8");
assert.strictEqual(text.match(/^# Harness feedback queue/gm).length, 1, "header not duplicated");
assert.strictEqual(text.split("\n### ").length - 1, 2, "two entries");
ok("appendEntry: creates with header, appends idempotently");

// 7. readEntries round-trips what appendEntry wrote
const entries = readEntries(q);
assert.strictEqual(entries.length, 2);
assert.strictEqual(entries[0].feature, "rules/x");
assert.strictEqual(entries[0].verdict, "native-better");
assert.strictEqual(entries[0].status, "open");
assert.strictEqual(entries[0].proposal, "narrow the trigger");
assert.strictEqual(entries[1].feature, "skills/y");
assert.strictEqual(entries[1].verdict, "needs-update");
ok("readEntries: round-trips both entries with correct fields");

// 8. readEntries on a missing file is empty, not a crash
assert.deepStrictEqual(readEntries(path.join(root, "nope.md")), []);
ok("readEntries: missing file -> []");

// 9. The CLI entry point actually RUNS. Exercised as a real subprocess because a broken main() guard
//    (e.g. comparing import.meta.url to `file://${argv[1]}` under a path containing spaces) makes the
//    script exit 0 having done nothing — which no in-process test of the exported functions can catch.
const cli = path.join(path.dirname(fileURLToPath(import.meta.url)), "harness-feedback.mjs");
const good = spawnSync(process.execPath, [cli, "--list"], { encoding: "utf8" });
assert.strictEqual(good.status, 0, `--list should exit 0, got ${good.status}`);
assert.ok(good.stdout.trim().length > 0, "--list must print something, not silently no-op");

const bad = spawnSync(process.execPath, [cli, "--feature", "rules/x", "--verdict", "bogus", "--why", "w", "--proposal", "p"], { encoding: "utf8" });
assert.strictEqual(bad.status, 1, `an invalid verdict must exit 1, got ${bad.status}`);
assert.match(bad.stderr, /--verdict must be one of/, "the failure reason must reach stderr");
ok("CLI: --list runs and prints; an invalid verdict exits 1 with a reason");

fs.rmSync(root, { recursive: true, force: true });
console.log(`\nharness-feedback.mjs: all ${n} tests PASS`);
