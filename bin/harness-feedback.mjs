#!/usr/bin/env node
// harness-feedback.mjs — record that a harness feature did not fit the task, so it can be upgraded.
//
// Why this exists: `rules/native-capability-first` tells an agent to judge each harness feature before
// following it, and to use its own ability when the feature would produce a worse result. Skipping a bad
// fit SILENTLY means every future session pays the same tax. This script is the write end of the feedback
// loop: it appends a structured entry to docs/harness-feedback/QUEUE.md. `/harness-sync` is the read end —
// it drains the queue and turns entries into real edits.
//
// The queue is append-only markdown so a human can read it directly and an agent can parse it.
//
//   node bin/harness-feedback.mjs --feature rules/phased-planning --verdict native-better \
//        --why "forced a 3-phase plan onto a one-line fix" \
//        --proposal "narrow the trigger to 3+ files AND 5+ tool calls"
//   node bin/harness-feedback.mjs --list          # show open entries
//   node bin/harness-feedback.mjs --list --all    # include resolved entries
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const QUEUE_REL = "docs/harness-feedback/QUEUE.md";

export const VERDICTS = {
  "native-better": "The model outperforms the feature on this task shape → narrow its trigger or retire it.",
  "needs-update": "Right in principle, stale in detail → rewrite the stale part.",
  "missing-capability": "Native ability revealed something the harness should capture → add it.",
};

const QUEUE_HEADER = `# Harness feedback queue

> Append-only record of harness features that did not fit the task at hand. Written by \`bin/harness-feedback.mjs\` under \`rules/native-capability-first\`; drained by \`/harness-sync\`.

## Master TOC

- [How to read this](#how-to-read-this)
- [Entries](#entries)

## How to read this

Each entry is one observation from one real turn, not a decision. Draining means reading the entry,
deciding whether the harness or the observation is wrong, and either editing the feature or marking the
entry \`resolved: rejected\` with a reason. Never delete an entry — flip its \`status\` line so the record of
what was tried survives.

| Verdict | Meaning | Resulting edit |
|---|---|---|
| \`native-better\` | ${VERDICTS["native-better"].split(" → ")[0]}. | ${VERDICTS["native-better"].split(" → ")[1]} |
| \`needs-update\` | ${VERDICTS["needs-update"].split(" → ")[0]}. | ${VERDICTS["needs-update"].split(" → ")[1]} |
| \`missing-capability\` | ${VERDICTS["missing-capability"].split(" → ")[0]}. | ${VERDICTS["missing-capability"].split(" → ")[1]} |

## Entries
`;

export function parseArgs(argv) {
  const out = { list: false, all: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--list") out.list = true;
    else if (a === "--all") out.all = true;
    else if (a.startsWith("--")) {
      const key = a.slice(2);
      const val = argv[i + 1];
      if (val === undefined || val.startsWith("--")) {
        throw new Error(`--${key} needs a value`);
      }
      out[key] = val;
      i++;
    } else {
      throw new Error(`unexpected argument: ${a}`);
    }
  }
  return out;
}

export function validate(args) {
  const problems = [];
  if (!args.feature) problems.push("--feature is required (e.g. rules/phased-planning, skills/foo, hooks/bar)");
  if (!args.verdict) problems.push(`--verdict is required (one of: ${Object.keys(VERDICTS).join(", ")})`);
  else if (!(args.verdict in VERDICTS)) {
    problems.push(`--verdict must be one of: ${Object.keys(VERDICTS).join(", ")} (got "${args.verdict}")`);
  }
  if (!args.why) problems.push("--why is required (one sentence: what the feature cost, what you did instead)");
  if (!args.proposal) problems.push("--proposal is required (one sentence: the edit that would fix it)");
  return problems;
}

export function formatEntry(args, now = new Date().toISOString()) {
  const id = `${now.slice(0, 10)}-${args.feature.replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "")}`;
  return [
    "",
    `### ${id}`,
    "",
    `- **feature**: \`${args.feature}\``,
    `- **verdict**: \`${args.verdict}\` — ${VERDICTS[args.verdict]}`,
    `- **status**: open`,
    `- **filed**: ${now}`,
    `- **agent**: ${args.agent || process.env.CLAUDE_AGENT || process.env.AGENT || "unknown"}`,
    `- **model**: ${args.model || process.env.CLAUDE_MODEL || process.env.ANTHROPIC_MODEL || "unknown"}`,
    `- **why**: ${args.why}`,
    `- **proposal**: ${args.proposal}`,
    "",
  ].join("\n");
}

export function appendEntry(queuePath, entryText) {
  fs.mkdirSync(path.dirname(queuePath), { recursive: true });
  if (!fs.existsSync(queuePath)) fs.writeFileSync(queuePath, QUEUE_HEADER, "utf8");
  fs.appendFileSync(queuePath, entryText, "utf8");
  return queuePath;
}

export function readEntries(queuePath) {
  if (!fs.existsSync(queuePath)) return [];
  const text = fs.readFileSync(queuePath, "utf8");
  const blocks = text.split(/^### /m).slice(1);
  return blocks.map((b) => {
    const id = b.split("\n", 1)[0].trim();
    const field = (k) => (b.match(new RegExp(`^- \\*\\*${k}\\*\\*: (.*)$`, "m")) || [, ""])[1].trim();
    return {
      id,
      feature: field("feature").replace(/`/g, ""),
      verdict: field("verdict").split(" — ")[0].replace(/`/g, ""),
      status: field("status") || "open",
      why: field("why"),
      proposal: field("proposal"),
    };
  });
}

function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (err) {
    console.error(`harness-feedback: ${err.message}`);
    process.exit(1);
  }
  const queuePath = path.join(REPO_ROOT, QUEUE_REL);

  if (args.list) {
    const entries = readEntries(queuePath).filter((e) => args.all || e.status === "open");
    if (!entries.length) {
      console.log(args.all ? "queue is empty" : "no open entries");
      return;
    }
    for (const e of entries) {
      console.log(`${e.status.padEnd(8)} ${e.verdict.padEnd(19)} ${e.feature}`);
      console.log(`         why:      ${e.why}`);
      console.log(`         proposal: ${e.proposal}`);
    }
    console.log(`\n${entries.length} entr${entries.length === 1 ? "y" : "ies"} in ${QUEUE_REL}`);
    return;
  }

  const problems = validate(args);
  if (problems.length) {
    console.error("harness-feedback: cannot file this entry:");
    for (const p of problems) console.error(`  - ${p}`);
    console.error("\nVerdicts:");
    for (const [k, v] of Object.entries(VERDICTS)) console.error(`  ${k.padEnd(20)} ${v}`);
    process.exit(1);
  }

  appendEntry(queuePath, formatEntry(args));
  console.log(`filed: ${args.verdict} on ${args.feature} -> ${QUEUE_REL}`);
  console.log("(/harness-sync drains the queue; this does not block your turn)");
}

// Robust "is this the entry script?" check — comparing import.meta.url to `file://${argv[1]}` breaks when the
// path contains spaces (import.meta.url percent-encodes them), so resolve both back to plain paths.
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) main();
