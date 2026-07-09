#!/usr/bin/env node
// Golden parity test: each projector's rendered manifest must byte-equal the committed file.
// This is what makes the generated manifests trustworthy — a projector change that would alter
// a committed manifest fails here (and in `build.mjs --check`) instead of silently drifting.
//   node adapters/test-projection.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import * as claude from "./claude.mjs";
import * as codex from "./codex.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url))); // adapters/ -> repo root
const source = JSON.parse(readFileSync(join(ROOT, "adapters", "manifest.source.json"), "utf8"));

let pass = 0;
let fail = 0;
for (const p of [claude, codex]) {
  const out = p.render(source);
  const cur = readFileSync(resolve(ROOT, p.target), "utf8");
  if (out === cur) {
    console.log(`PASS parity: ${p.target} (${out.length} bytes)`);
    pass++;
  } else {
    fail++;
    let i = 0;
    while (i < Math.min(out.length, cur.length) && out[i] === cur[i]) i++;
    console.error(`FAIL parity: ${p.target}`);
    console.error(`  first diff at byte ${i}`);
    console.error(`  rendered: ${JSON.stringify(out.slice(i, i + 60))}`);
    console.error(`  current : ${JSON.stringify(cur.slice(i, i + 60))}`);
    console.error(`  lengths : rendered ${out.length} vs current ${cur.length}`);
  }
}
console.log(fail ? `\nprojection: ${fail} FAIL / ${pass} pass` : `\nprojection: all ${pass} parity test(s) PASS`);
process.exit(fail ? 1 : 0);
