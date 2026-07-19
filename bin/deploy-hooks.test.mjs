#!/usr/bin/env node
// Tests for deploy-hooks.mjs. Run: node bin/deploy-hooks.test.mjs
//
// This script edits ~/.claude/settings.json, so the checks that matter are the ones about restraint: it
// must not duplicate an entry, must not silently enable a hook the user never opted into, and must not
// copy dev artifacts into the live hooks directory. Every one of those was a real defect the first dry
// run exposed.
import assert from "node:assert";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  inventoryHooks, hookScripts, hookSnippet, mergeHooks, commandScript, REPO_ROOT,
} from "./deploy-hooks.mjs";

let n = 0;
const ok = (m) => (n++, console.log("  ok:", m));
const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), "deployhooks-"));

// 1. The inventory is read from the manifest, and every entry exists on disk.
const hooks = inventoryHooks();
assert(hooks.length >= 5, `expected the real hook inventory, got ${hooks.length}`);
for (const rel of hooks) assert(fs.existsSync(path.join(REPO_ROOT, rel)), `${rel} exists`);
ok(`inventory: ${hooks.length} hooks, all present on disk`);

// 2. Test files are NOT deployable. Copying them puts files in the live directory that nothing runs.
const rgScripts = hookScripts("hooks/review-gate").map((f) => path.basename(f));
assert(rgScripts.includes("core.sh") && rgScripts.includes("gate.sh"), rgScripts);
assert(rgScripts.includes("blockrule.sh") && rgScripts.includes("statsbar.sh"), rgScripts);
for (const f of rgScripts) {
  assert(!f.startsWith("test_"), `a test file must not be deployable: ${f}`);
  assert(!/\.test\.(mjs|js|py)$/.test(f), `a test file must not be deployable: ${f}`);
}
assert(fs.existsSync(path.join(REPO_ROOT, "hooks/review-gate/scripts/test_core.sh")),
  "the test file exists in the repo — it is excluded from deployment, not missing");
ok(`hookScripts: ${rgScripts.length} deployable, every test_* excluded`);

// 3. commandScript pulls the script out of a command, ignoring env prefixes and interpreters. Exact
//    string matching missed a real registered ssh-guard entry because of its env prefix.
assert.strictEqual(commandScript('"$HOME/.claude/hooks/review-gate/gate.sh"'), "$HOME/.claude/hooks/review-gate/gate.sh");
assert.strictEqual(commandScript('SSH_GUARD_STATE="$HOME/x" bash "$HOME/.claude/agent-harness/hooks/ssh-guard/ssh-guard.sh"'),
  "$HOME/.claude/agent-harness/hooks/ssh-guard/ssh-guard.sh");
assert.strictEqual(commandScript('python3 "$HOME/.claude/hooks/memory-flywheel/supervise.py"'),
  "$HOME/.claude/hooks/memory-flywheel/supervise.py");
assert.strictEqual(commandScript("jq -r '.tool_input.file_path'"), "jq -r '.tool_input.file_path'");
ok("commandScript: survives env prefixes, interpreters and quoting");

// 4. A hook the user has not registered is NOT enabled by default. Deploying one hook must never turn
//    on another as a side effect.
const snippet = { hooks: { Stop: [{ hooks: [{ type: "command", command: '"$HOME/.claude/hooks/new-thing/x.sh"' }] }] } };
const settings = { hooks: {} };
const { added, skipped } = mergeHooks(settings, snippet);
assert.deepStrictEqual(added, [], "nothing enabled without --enable-new");
assert.strictEqual(skipped.length, 1, "and the skip is reported, not hidden");
assert.deepStrictEqual(settings.hooks.Stop, [], "settings untouched");
ok("mergeHooks: an unregistered hook stays off unless explicitly enabled");

// 5. With enableNew it registers, and a second pass does not duplicate.
const s2 = { hooks: {} };
assert.strictEqual(mergeHooks(s2, snippet, { enableNew: true }).added.length, 1);
assert.strictEqual(s2.hooks.Stop.length, 1);
assert.strictEqual(mergeHooks(s2, snippet, { enableNew: true }).added.length, 0, "idempotent");
assert.strictEqual(s2.hooks.Stop.length, 1, "no duplicate group");
ok("mergeHooks: --enable-new registers once and is idempotent");

// 6. An already-registered command is recognised even when it carries an env prefix.
const s3 = { hooks: { PreToolUse: [{ hooks: [{ type: "command", command: 'FOO=1 bash "$HOME/h/ssh-guard.sh"' }] }] } };
const bare = { hooks: { PreToolUse: [{ hooks: [{ type: "command", command: 'bash "$HOME/h/ssh-guard.sh"' }] }] } };
assert.strictEqual(mergeHooks(s3, bare, { enableNew: true }).added.length, 0,
  "the env-prefixed entry must count as already registered");
assert.strictEqual(s3.hooks.PreToolUse.length, 1, "no duplicate registration");
ok("mergeHooks: an env-prefixed existing entry is not re-registered");

// 7. A user's hand-edited entry is preserved rather than replaced with ours.
const s4 = { hooks: { Stop: [{ hooks: [{ type: "command", command: 'MINE=1 "$HOME/.claude/hooks/review-gate/gate.sh"', timeout: 999 }] }] } };
mergeHooks(s4, { hooks: { Stop: [{ hooks: [{ type: "command", command: '"$HOME/.claude/hooks/review-gate/gate.sh"', timeout: 60 }] }] } }, { enableNew: true });
assert.strictEqual(s4.hooks.Stop.length, 1);
assert.strictEqual(s4.hooks.Stop[0].hooks[0].timeout, 999, "the user's own timeout survives");
ok("mergeHooks: a hand-edited entry is left alone, not overwritten");

// 8. A malformed snippet is reported by name rather than crashing the run.
const root = tmp();
fs.mkdirSync(path.join(root, "hooks", "bad"), { recursive: true });
fs.writeFileSync(path.join(root, "hooks", "bad", "settings.snippet.json"), "{not json");
assert.throws(() => hookSnippet("hooks/bad", root), /not valid JSON/);
fs.rmSync(root, { recursive: true, force: true });
ok("hookSnippet: a malformed snippet names the file it came from");

// 9. Dry-run is the default and writes nothing.
const cli = path.join(path.dirname(fileURLToPath(import.meta.url)), "deploy-hooks.mjs");
const sp = path.join(os.homedir(), ".claude", "settings.json");
const before = fs.existsSync(sp) ? fs.readFileSync(sp, "utf8") : null;
const dry = spawnSync(process.execPath, [cli], { encoding: "utf8" });
assert.strictEqual(dry.status, 0, dry.stderr);
assert.match(dry.stdout, /dry-run/);
const after = fs.existsSync(sp) ? fs.readFileSync(sp, "utf8") : null;
assert.strictEqual(after, before, "a dry run must not modify settings.json");
ok("CLI: dry-run by default, settings.json byte-identical afterwards");

// 10. An unknown hook name is refused with the list of real ones.
const bad = spawnSync(process.execPath, [cli, "--hook", "nope"], { encoding: "utf8" });
assert.strictEqual(bad.status, 1);
assert.match(bad.stderr, /no such hook: nope/);
assert.match(bad.stderr, /review-gate/, "the error should list what does exist");
ok("CLI: an unknown --hook exits 1 and lists the real ones");

console.log(`\ndeploy-hooks.mjs: all ${n} tests PASS`);
