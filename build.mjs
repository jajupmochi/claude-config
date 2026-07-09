#!/usr/bin/env node
// agent-harness manifest builder.
//   node build.mjs          regenerate every per-agent manifest from adapters/manifest.source.json
//   node build.mjs --check  verify each generated manifest still matches the source (CI drift gate; exit 1 on drift)
//
// This is the hybrid-architecture core: one canonical source -> generated per-agent projections.
// See docs/strategy/agent-harness-overhaul-2026-07-09/ws-a-design.md.
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import * as claude from "./adapters/claude.mjs";
import * as codex from "./adapters/codex.mjs";
import * as opencode from "./adapters/opencode.mjs";

const ROOT = dirname(fileURLToPath(import.meta.url));
const SOURCE = join(ROOT, "adapters", "manifest.source.json");
// Projectors run in this order.
const PROJECTORS = [claude, codex, opencode];

function firstDiff(a, b) {
  let i = 0;
  while (i < Math.min(a.length, b.length) && a[i] === b[i]) i++;
  return i;
}

function main() {
  const check = process.argv.includes("--check");
  const source = JSON.parse(readFileSync(SOURCE, "utf8"));
  let drift = 0;
  let wrote = 0;
  for (const p of PROJECTORS) {
    const out = p.render(source);
    const path = resolve(ROOT, p.target);
    const cur = existsSync(path) ? readFileSync(path, "utf8") : null;
    if (check) {
      if (cur !== out) {
        drift++;
        const i = cur == null ? 0 : firstDiff(out, cur);
        console.error(`DRIFT: ${p.target} differs from canonical source at byte ${i}`);
        if (cur != null) {
          console.error(`  rendered: ${JSON.stringify(out.slice(i, i + 60))}`);
          console.error(`  on-disk : ${JSON.stringify(cur.slice(i, i + 60))}`);
        }
      } else {
        console.log(`ok: ${p.target} matches source`);
      }
    } else if (cur !== out) {
      writeFileSync(path, out);
      wrote++;
      console.log(`wrote: ${p.target}`);
    } else {
      console.log(`unchanged: ${p.target}`);
    }
  }
  if (check && drift) {
    console.error(`\n${drift} manifest(s) drifted. Run \`node build.mjs\` to regenerate, or edit adapters/manifest.source.json.`);
    process.exit(1);
  }
  console.log(check ? "\ncheck OK: all manifests match source" : `\nbuild done: ${wrote} written`);
}

main();
