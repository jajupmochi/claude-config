#!/usr/bin/env node
// visual-diff.mjs — the OBJECTIVE gate for the Figma→code visual self-check (step 4 of figma-design-fetch).
//
// Compares an implementation screenshot against the Figma get_screenshot at the SAME pixel dimensions and a
// FIXED DPR, computes the mismatch fraction with pixelmatch, and EXITS NON-ZERO if it exceeds a numeric
// threshold — so "it matches" is a number, not the model's opinion. Writes a diff PNG next to the inputs.
//
//   node visual-diff.mjs <impl.png> <figma.png> [--threshold 0.02] [--dpr 2] [--out diff.png] [--pixel 0.1]
//
//   --threshold  max allowed mismatched-pixel FRACTION (0..1). Default 0.02 (2%). Exceed → exit 1.
//   --dpr        the DPR both screenshots were captured at (informational; recorded in the report). Default 1.
//   --pixel      per-pixel color threshold passed to pixelmatch (0..1, lower = stricter). Default 0.1.
//   --out        diff image path. Default: <impl basename>.diff.png next to impl.
//
// Exit codes: 0 = within threshold · 1 = mismatch over threshold · 2 = bad input / missing deps / size mismatch.
//
// Requires `pixelmatch` and `pngjs` (add them to the frontend repo: `npm i -D pixelmatch pngjs`). Both images
// MUST be the exact same width×height — capture the impl with Playwright `browser_resize` to the Figma frame's
// size at the same DPR; a size mismatch is a hard error (comparing different sizes is meaningless).
import fs from "node:fs";
import path from "node:path";

function parseArgs(argv) {
  const a = { threshold: 0.02, dpr: 1, pixel: 0.1, out: null, _: [] };
  for (let i = 0; i < argv.length; i++) {
    const t = argv[i];
    if (t === "--threshold") a.threshold = parseFloat(argv[++i]);
    else if (t === "--dpr") a.dpr = parseFloat(argv[++i]);
    else if (t === "--pixel") a.pixel = parseFloat(argv[++i]);
    else if (t === "--out") a.out = argv[++i];
    else a._.push(t);
  }
  return a;
}

async function loadDeps() {
  try {
    const [{ PNG }, pm] = await Promise.all([import("pngjs"), import("pixelmatch")]);
    return { PNG, pixelmatch: pm.default || pm };
  } catch {
    console.error("visual-diff: missing deps. In the frontend repo run:  npm i -D pixelmatch pngjs");
    process.exit(2);
  }
}

export function compare(PNG, pixelmatch, implBuf, figmaBuf, { pixel }) {
  const a = PNG.sync.read(implBuf);
  const b = PNG.sync.read(figmaBuf);
  if (a.width !== b.width || a.height !== b.height) {
    return { sizeMismatch: true, a: { w: a.width, h: a.height }, b: { w: b.width, h: b.height } };
  }
  const diff = new PNG({ width: a.width, height: a.height });
  const mismatched = pixelmatch(a.data, b.data, diff.data, a.width, a.height, { threshold: pixel });
  const total = a.width * a.height;
  return { sizeMismatch: false, mismatched, total, fraction: mismatched / total, diff, PNG, width: a.width, height: a.height };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const [impl, figma] = args._;
  if (!impl || !figma) {
    console.error("usage: visual-diff.mjs <impl.png> <figma.png> [--threshold 0.02] [--dpr 2] [--pixel 0.1] [--out diff.png]");
    process.exit(2);
  }
  for (const f of [impl, figma]) if (!fs.existsSync(f)) { console.error(`visual-diff: no such file: ${f}`); process.exit(2); }

  const { PNG, pixelmatch } = await loadDeps();
  const r = compare(PNG, pixelmatch, fs.readFileSync(impl), fs.readFileSync(figma), { pixel: args.pixel });

  if (r.sizeMismatch) {
    console.error(`visual-diff: SIZE MISMATCH impl ${r.a.w}x${r.a.h} vs figma ${r.b.w}x${r.b.h} — recapture at the ` +
      `same frame size + DPR (Playwright browser_resize). Comparing different sizes is meaningless.`);
    process.exit(2);
  }

  const out = args.out || path.join(path.dirname(impl), path.basename(impl).replace(/\.png$/i, "") + ".diff.png");
  fs.writeFileSync(out, PNG.sync.write(r.diff));

  const pct = (r.fraction * 100).toFixed(3);
  const thr = (args.threshold * 100).toFixed(3);
  const pass = r.fraction <= args.threshold;
  console.log(`visual-diff @dpr${args.dpr} ${r.width}x${r.height}: mismatch ${r.mismatched}/${r.total} = ${pct}% ` +
    `(threshold ${thr}%) → ${pass ? "PASS" : "FAIL"} · diff: ${out}`);
  process.exit(pass ? 0 : 1);
}

if (import.meta.url === `file://${process.argv[1]}` || (process.argv[1] && path.resolve(process.argv[1]) === new URL(import.meta.url).pathname)) {
  main();
}
