// Tests for the opencode review-gate helper (lib/run-core.mjs). Run: node .opencode/plugin/review-gate.test.mjs
// Verifies the core.sh invocation (the part that does NOT need an opencode install): a code change yields
// the shared forms review + block; a non-git dir yields an empty, non-blocking result.
import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { runReviewCore } from "./lib/run-core.mjs";

const REPO = dirname(dirname(dirname(fileURLToPath(import.meta.url)))); // .opencode/plugin/ -> repo root
const CORE = join(REPO, "hooks", "review-gate", "scripts", "core.sh");
let pass = 0, fail = 0;
const chk = (n, got, want) => { if (got === want) { console.log(`  ok: ${n}`); pass++; } else { console.error(`  FAIL: ${n} (got ${JSON.stringify(got)} want ${JSON.stringify(want)})`); fail++; } };
const ctn = (n, s, sub) => { if (String(s).includes(sub)) { console.log(`  ok: ${n}`); pass++; } else { console.error(`  FAIL: ${n} (missing ${JSON.stringify(sub)})`); fail++; } };

// 1. a git repo with a staged code file -> forms review + block
{
  const T = mkdtempSync(join(tmpdir(), "og-"));
  const repo = join(T, "repo"), home = join(T, "home");
  mkdirSync(repo); mkdirSync(home);
  const g = (args) => execFileSync("git", args, { cwd: repo });
  g(["init", "-q"]); g(["config", "user.email", "t@t"]); g(["config", "user.name", "t"]); g(["checkout", "-q", "-b", "work"]);
  writeFileSync(join(repo, "a.go"), "package p\nfunc F() int { return 1 }\n");
  g(["add", "a.go"]);
  const r = runReviewCore({ repoRoot: repo, coreSh: CORE, stateDir: join(home, "state"), sid: "s1" });
  chk("staged code -> block", r.block, true);
  ctn("  forms review text present", r.review, "review-gate: automatic review");
  ctn("  changed file listed", r.review, "a.go");
}

// 2. a non-git directory -> empty, non-blocking (fail-open)
{
  const T = mkdtempSync(join(tmpdir(), "og-"));
  const r = runReviewCore({ repoRoot: T, coreSh: CORE, stateDir: join(T, "state"), sid: "s2" });
  chk("non-git dir -> no block", r.block, false);
  chk("  empty review", r.review, "");
}

// 3. missing core.sh -> empty, non-blocking
{
  const T = mkdtempSync(join(tmpdir(), "og-"));
  const r = runReviewCore({ repoRoot: T, coreSh: join(T, "nope.sh"), stateDir: join(T, "state"), sid: "s3" });
  chk("missing core.sh -> no block", r.block, false);
}

console.log(fail ? `\nopencode review helper: ${fail} FAIL / ${pass} pass` : `\nopencode review helper: all ${pass} checks PASS`);
process.exit(fail ? 1 : 0);
