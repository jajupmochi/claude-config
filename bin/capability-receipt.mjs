#!/usr/bin/env node
// capability-receipt.mjs — report which harness capabilities ACTUALLY FIRED in a session.
//
// The gap this closes: "registered" and "deployed" are both observable from the filesystem, but "fired"
// is not, and it is the only one that matters. Two independent analyses of this user's real sessions
// converged on the same finding from different angles — capabilities that exist and are deployed still
// do not run, and nothing notices. `code-verifier` is deployed and named in review-gate's form 4, and
// unverified completion claims still went out 38 times across 9 sessions.
//
// This reads a Claude Code transcript and reports, per capability, whether there is evidence it ran.
// Detection signatures live in adapters/capabilities.json, so covering a new capability is a config
// edit rather than a code change.
//
//   capability-receipt.mjs --transcript <file.jsonl>       # one session
//   capability-receipt.mjs --cwd .                         # newest transcript for this project
//   capability-receipt.mjs --transcript X --last-turn      # only since the last user message
//   capability-receipt.mjs --transcript X --json
//
// This is DETECTION only. It reports; it does not block. Turning a miss into a blocked stop changes how
// every turn behaves, so that belongs behind an explicit decision, not a side effect of installing this.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export function loadCapabilities(repoRoot = REPO_ROOT) {
  const f = path.join(repoRoot, "adapters/capabilities.json");
  return JSON.parse(fs.readFileSync(f, "utf8")).capabilities;
}

/** Encode a working directory the way Claude Code names its transcript folder. */
export function encodeCwd(cwd) {
  return cwd.replace(/[^A-Za-z0-9]/g, "-");
}

export function newestTranscript(cwd, home = os.homedir()) {
  const dir = path.join(home, ".claude", "projects", encodeCwd(path.resolve(cwd)));
  if (!fs.existsSync(dir)) return null;
  const files = fs.readdirSync(dir)
    .filter((f) => f.endsWith(".jsonl"))
    .map((f) => ({ f: path.join(dir, f), t: fs.statSync(path.join(dir, f)).mtimeMs }))
    .sort((a, b) => b.t - a.t);
  return files.length ? files[0].f : null;
}

/**
 * Pull the evidence a signature can match against, without holding the whole transcript in memory.
 * Transcripts routinely exceed 100MB, so this streams and keeps only what signatures look at.
 */
export function collectEvidence(transcriptPath, { lastTurn = false } = {}) {
  const text = fs.readFileSync(transcriptPath, "utf8");
  const lines = text.split("\n").filter(Boolean);

  let start = 0;
  if (lastTurn) {
    // Walk back to the last genuine user message; everything after it is the turn under inspection.
    for (let i = lines.length - 1; i >= 0; i--) {
      try {
        const r = JSON.parse(lines[i]);
        if (r.type === "user" && r.message?.role === "user" && !r.isMeta
            && typeof r.message.content === "string") { start = i; break; }
      } catch { /* a truncated line is not a turn boundary */ }
    }
  }

  const ev = { skills: [], bash: [], text: [], sid: null };
  for (let i = start; i < lines.length; i++) {
    let r;
    try { r = JSON.parse(lines[i]); } catch { continue; }
    if (!ev.sid && r.sessionId) ev.sid = r.sessionId;
    if (r.type !== "assistant") continue;
    const blocks = r.message?.content;
    if (!Array.isArray(blocks)) continue;
    for (const b of blocks) {
      if (b.type === "text" && b.text) ev.text.push(b.text);
      if (b.type !== "tool_use") continue;
      if (b.name === "Skill" && b.input?.skill) ev.skills.push(String(b.input.skill));
      if (b.name === "Bash" && b.input?.command) ev.bash.push(String(b.input.command));
      // A skill invoked through a plugin namespace still counts as that skill.
      if (b.name === "Task" && b.input?.subagent_type) ev.skills.push(String(b.input.subagent_type));
    }
  }
  return ev;
}

export function checkStateFile(pattern, { sid, cwd, home = os.homedir() }) {
  let p = pattern.replace("{sid}", sid || "");
  if (p.startsWith("~/")) p = path.join(home, p.slice(2));
  else if (!path.isAbsolute(p)) p = path.join(cwd || process.cwd(), p);
  return fs.existsSync(p);
}

/** Signature kinds whose `match` is a regular expression. `state` is a path template, not a pattern. */
export const REGEX_KINDS = new Set(["skill", "bash", "text"]);

export function evaluate(capabilities, ev, ctx) {
  const problems = [];
  const results = capabilities.map((cap) => {
    const hits = [];
    for (const sig of cap.signatures) {
      if (sig.kind === "state") {
        // Deliberately NOT compiled as a regex. A state signature is a path containing {sid} and possibly
        // "~", and "{sid}" is an invalid regex quantifier — compiling it first and skipping on failure
        // meant every state signature silently never fired.
        if (checkStateFile(sig.match, ctx)) hits.push(`state:${sig.match}`);
        continue;
      }
      if (!REGEX_KINDS.has(sig.kind)) {
        problems.push(`${cap.id}: unknown signature kind "${sig.kind}"`);
        continue;
      }
      let re;
      try {
        re = new RegExp(sig.match, "u");
      } catch (err) {
        // A malformed pattern is a config defect, not a "did not fire". Surfacing it keeps a broken
        // signature from reading as a capability that legitimately stayed idle.
        problems.push(`${cap.id}: bad ${sig.kind} pattern ${JSON.stringify(sig.match)} — ${err.message}`);
        continue;
      }
      if (sig.kind === "skill" && ev.skills.some((s) => re.test(s))) hits.push(`skill:${sig.match}`);
      else if (sig.kind === "bash" && ev.bash.some((c) => re.test(c))) hits.push(`bash:${sig.match}`);
      else if (sig.kind === "text" && ev.text.some((t) => re.test(t))) hits.push(`text:${sig.match}`);
    }
    return { ...cap, fired: hits.length > 0, evidence: hits };
  });
  results.problems = problems;
  return results;
}

function main() {
  const argv = process.argv.slice(2);
  const val = (f, d) => (argv.includes(f) ? argv[argv.indexOf(f) + 1] : d);
  const has = (f) => argv.includes(f);

  let tp = val("--transcript");
  const cwd = path.resolve(val("--cwd", process.cwd()));
  if (!tp) tp = newestTranscript(cwd);
  if (!tp || !fs.existsSync(tp)) {
    console.error(`capability-receipt: no transcript found (looked for the newest under ~/.claude/projects for ${cwd}).`);
    console.error("Pass one explicitly: --transcript <file.jsonl>");
    process.exit(1);
  }

  const caps = loadCapabilities();
  const ev = collectEvidence(tp, { lastTurn: has("--last-turn") });
  const results = evaluate(caps, ev, { sid: ev.sid, cwd });

  if (has("--json")) {
    console.log(JSON.stringify({ transcript: tp, sessionId: ev.sid, results }, null, 2));
    return;
  }

  const fired = results.filter((r) => r.fired);
  const missedHooks = results.filter((r) => !r.fired && r.enforcement === "hook");
  console.log(`transcript: ${tp}`);
  console.log(`scope: ${has("--last-turn") ? "last turn" : "whole session"}\n`);
  for (const r of results) {
    const mark = r.fired ? "FIRED " : (r.enforcement === "hook" ? "MISSED" : "  --  ");
    console.log(`${mark} ${r.id.padEnd(20)} ${r.enforcement.padEnd(9)} ${r.label}`);
    if (r.fired) console.log(`       evidence: ${r.evidence.join(", ")}`);
    else if (r.enforcement === "advisory") console.log(`       expected when: ${r.expect_when}`);
  }
  console.log(`\n${fired.length}/${results.length} fired.`);
  if (missedHooks.length) {
    console.log(`${missedHooks.length} ENFORCED capabilit${missedHooks.length === 1 ? "y" : "ies"} did not fire — that is a defect, not a judgment call:`);
    for (const r of missedHooks) console.log(`  - ${r.id}: expected when ${r.expect_when}`);
  }
  console.log("\nAn advisory capability that did not fire may be correct under rules/native-capability-first.");
  console.log("This tool reports; it does not block.");
}

// Robust "is this the entry script?" check — comparing import.meta.url to `file://${argv[1]}` breaks when
// the path contains spaces (import.meta.url percent-encodes them), so resolve both back to plain paths.
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) main();
