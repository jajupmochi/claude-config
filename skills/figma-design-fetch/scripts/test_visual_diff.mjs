#!/usr/bin/env node
// Tests for visual-diff.mjs. Run: node skills/figma-design-fetch/scripts/test_visual_diff.mjs
// pixelmatch/pngjs are the frontend repo's deps; this test installs them into a temp dir (best-effort) and
// exercises the pure compare() helper. Skips gracefully if they can't be installed offline.
import assert from "node:assert";
import { execSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const { compare } = await import(path.join(HERE, "visual-diff.mjs"));

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "vdiff-"));
let PNG, pixelmatch;
try {
  execSync("npm i --prefix . --no-save --silent pixelmatch pngjs", { cwd: tmp, stdio: "ignore" });
  PNG = (await import(path.join(tmp, "node_modules/pngjs/lib/png.js"))).PNG;
  const pm = await import(path.join(tmp, "node_modules/pixelmatch/index.js"));
  pixelmatch = pm.default || pm;
} catch {
  console.log("test_visual_diff: SKIP — could not install pixelmatch/pngjs offline (script is dep-checked at runtime).");
  process.exit(0);
}

function png(w, h, fill) {
  const p = new PNG({ width: w, height: h });
  for (let i = 0; i < p.data.length; i += 4) {
    p.data[i] = fill[0]; p.data[i + 1] = fill[1]; p.data[i + 2] = fill[2]; p.data[i + 3] = 255;
  }
  return PNG.sync.write(p);
}

let n = 0;
const ok = (m) => (n++, console.log("  ok:", m));

// 1. identical images → fraction 0
let r = compare(PNG, pixelmatch, png(20, 20, [10, 20, 30]), png(20, 20, [10, 20, 30]), { pixel: 0.1 });
assert(!r.sizeMismatch && r.fraction === 0, `identical should be 0, got ${JSON.stringify(r.fraction)}`);
ok("identical images → mismatch fraction 0");

// 2. fully different images → fraction 1 (all pixels differ)
r = compare(PNG, pixelmatch, png(20, 20, [0, 0, 0]), png(20, 20, [255, 255, 255]), { pixel: 0.1 });
assert(!r.sizeMismatch && r.fraction === 1, `all-different should be 1, got ${r.fraction}`);
ok("fully different images → mismatch fraction 1");

// 3. small local difference → small positive fraction, below a 2% threshold only if few pixels differ
const a = new PNG({ width: 10, height: 10 });
const b = new PNG({ width: 10, height: 10 });
for (let i = 0; i < a.data.length; i += 4) { for (const p of [a, b]) { p.data[i] = 5; p.data[i + 1] = 5; p.data[i + 2] = 5; p.data[i + 3] = 255; } }
b.data[0] = 250; // flip one pixel's red channel
r = compare(PNG, pixelmatch, PNG.sync.write(a), PNG.sync.write(b), { pixel: 0.1 });
assert(!r.sizeMismatch && r.mismatched === 1 && Math.abs(r.fraction - 1 / 100) < 1e-9, `one-pixel diff, got ${JSON.stringify(r)}`);
ok("one changed pixel of 100 → fraction 0.01 (would PASS a 2% threshold)");

// 4. size mismatch → hard flag (comparing different sizes is meaningless)
r = compare(PNG, pixelmatch, png(20, 20, [0, 0, 0]), png(21, 20, [0, 0, 0]), { pixel: 0.1 });
assert(r.sizeMismatch === true, "different sizes must be flagged");
ok("size mismatch → sizeMismatch flag (exit 2 path)");

fs.rmSync(tmp, { recursive: true, force: true });
console.log(`\nvisual-diff.mjs: all ${n} checks PASS`);
