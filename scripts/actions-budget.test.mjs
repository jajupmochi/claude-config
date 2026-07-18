#!/usr/bin/env node
// Tests for scripts/actions-budget.mjs. Run: node scripts/actions-budget.test.mjs
//
// These exercise the real code paths against real files on disk: the parser runs on
// generated fixture workflows AND on this repository's own .github/workflows, the CLI
// is spawned as a subprocess, and every asserted number is recomputed from the rate
// card rather than pasted in. Nothing is mocked.
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import {
  parseYamlSubset, stripComment, splitKey, globToRegExp, branchMatches,
  expandMatrix, classifyRunner, cronRunsPerMonth, expandCronField,
  costJobs, analyzeRepo, findWorkflowFiles, loadRates,
} from "./actions-budget.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const SCRIPT = join(ROOT, "scripts", "actions-budget.mjs");
const rates = loadRates();

let pass = 0, fail = 0;
const chk = (n, got, want) => {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (ok) { console.log(`  ok: ${n}`); pass++; }
  else { console.error(`  FAIL: ${n} (got ${JSON.stringify(got)} want ${JSON.stringify(want)})`); fail++; }
};
const chkTrue = (n, got) => chk(n, !!got, true);
const near = (n, got, want, tol = 0.02) => {
  if (Math.abs(got - want) <= tol) { console.log(`  ok: ${n}`); pass++; }
  else { console.error(`  FAIL: ${n} (got ${got} want ~${want})`); fail++; }
};

// ---------------------------------------------------------------------------
console.log("\n1. scalar helpers");
// ---------------------------------------------------------------------------
chk("stripComment removes a trailing comment", stripComment("cron: '0 12 * * 1'  # Mondays").trim(), "cron: '0 12 * * 1'");
chk("stripComment keeps a # inside quotes", stripComment(`run: echo "a # b"`), `run: echo "a # b"`);
chk("stripComment keeps a bare # with no leading space", stripComment("color: ab#cd"), "color: ab#cd");
chk("splitKey splits on the first colon-space", splitKey("name: Install via npx"), { key: "name", rest: "Install via npx" });
chk("splitKey ignores a colon with no space", splitKey("name: github:owner/repo"), { key: "name", rest: "github:owner/repo" });
chk("splitKey ignores a colon inside an expression", splitKey("if: ${{ contains(x, 'a: b') }}"), { key: "if", rest: "${{ contains(x, 'a: b') }}" });
chk("splitKey handles a key with an empty value", splitKey("jobs:"), { key: "jobs", rest: "" });
chk("splitKey unquotes a quoted key", splitKey(`"on": push`), { key: "on", rest: "push" });
chk("splitKey returns null for a non-mapping line", splitKey("just a scalar"), null);

// ---------------------------------------------------------------------------
console.log("\n2. YAML subset parser");
// ---------------------------------------------------------------------------
{
  const y = `
name: Demo
on:
  push:
    branches: [main, 'releases/**']
    paths-ignore:
      - '**.md'
  pull_request:
concurrency:
  group: \${{ github.workflow }}-\${{ github.ref }}
  cancel-in-progress: true
jobs:
  build:
    runs-on: \${{ matrix.os }}
    timeout-minutes: 10
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest]
        node: [20, 22]
    steps:
      - uses: actions/checkout@v5
      - name: Run
        run: |
          echo "key: not-a-yaml-key"
          # a comment that must not be parsed
          echo 'done'
      - name: After block scalar
        run: echo ok
`;
  const { doc, warnings } = parseYamlSubset(y);
  chk("parser emits no warnings on a normal workflow", warnings, []);
  chk("top-level name", doc.name, "Demo");
  chk("push branches flow sequence", doc.on.push.branches, ["main", "releases/**"]);
  chk("push paths-ignore block sequence", doc.on.push["paths-ignore"], ["**.md"]);
  chk("pull_request with an empty value is null", doc.on.pull_request, null);
  chk("concurrency group keeps the expression intact", doc.concurrency.group, "${{ github.workflow }}-${{ github.ref }}");
  chk("cancel-in-progress parses as a boolean", doc.concurrency["cancel-in-progress"], true);
  chk("timeout-minutes parses as a number", doc.jobs.build["timeout-minutes"], 10);
  chk("fail-fast parses as a boolean", doc.jobs.build.strategy["fail-fast"], false);
  chk("matrix values keep their types", doc.jobs.build.strategy.matrix.node, [20, 22]);
  chk("block scalar does not leak into the mapping", Object.keys(doc.jobs.build).sort(), ["runs-on", "steps", "strategy", "timeout-minutes"]);
  chk("steps after a block scalar are still found", doc.jobs.build.steps.length, 3);
  chk("last step survives the block scalar", doc.jobs.build.steps[2].name, "After block scalar");
  chkTrue("block scalar body is captured as text", String(doc.jobs.build.steps[1].run).includes("echo 'done'"));
}
{
  const { doc, warnings } = parseYamlSubset("jobs:\n  a:\n    runs-on: ubuntu-latest\n   bad: 1\n");
  chk("malformed indentation returns doc null instead of throwing", doc, null);
  chkTrue("malformed indentation produces a warning", warnings.length > 0);
}
{
  const { warnings } = parseYamlSubset("a: &anchor value\nb: *anchor\n");
  chkTrue("anchors are reported rather than silently mis-parsed", warnings.some((w) => /anchor/i.test(w)));
}
{
  const { doc } = parseYamlSubset("on: push\njobs:\n  a:\n    runs-on: ubuntu-latest\n");
  chk("string form of on:", doc.on, "push");
  const { doc: d2 } = parseYamlSubset("on: [push, pull_request]\njobs: {}\n");
  chk("array form of on:", d2.on, ["push", "pull_request"]);
}
{
  const { doc } = parseYamlSubset("on:\n  schedule:\n    # weekly\n    - cron: '0 6 * * 1'\n    - cron: '0 6 * * 4'\n");
  chk("schedule sequence of mappings", doc.on.schedule, [{ cron: "0 6 * * 1" }, { cron: "0 6 * * 4" }]);
}
{
  const { doc } = parseYamlSubset("jobs:\n  a:\n    runs-on: [self-hosted, linux, x64]\n");
  chk("runs-on as a label list", doc.jobs.a["runs-on"], ["self-hosted", "linux", "x64"]);
}
{
  const { doc } = parseYamlSubset("steps:\n- uses: actions/checkout@v5\n  with:\n    fetch-depth: 0\n- run: make\n");
  chk("sequence at the same indent as its key", doc.steps.length, 2);
  chk("compact mapping continuation lines attach to the right item", doc.steps[0].with["fetch-depth"], 0);
}

// ---------------------------------------------------------------------------
console.log("\n3. branch filters");
// ---------------------------------------------------------------------------
chk("glob * does not cross a slash", globToRegExp("releases/*").test("releases/v1/x"), false);
chk("glob ** crosses slashes", globToRegExp("releases/**").test("releases/v1/x"), true);
chk("branches [main] matches main", branchMatches({ branches: ["main"] }, "main"), true);
chk("branches [main] rejects a topic branch", branchMatches({ branches: ["main"] }, "topic/x"), false);
chk("no filter matches anything", branchMatches({}, "topic/x"), true);
chk("negation excludes", branchMatches({ branches: ["**", "!main"] }, "main"), false);
chk("negation leaves others included", branchMatches({ branches: ["**", "!main"] }, "topic/x"), true);
chk("branches-ignore excludes", branchMatches({ "branches-ignore": ["docs/**"] }, "docs/a"), false);
chk("branches-ignore admits others", branchMatches({ "branches-ignore": ["docs/**"] }, "main"), true);

// ---------------------------------------------------------------------------
console.log("\n4. matrix expansion");
// ---------------------------------------------------------------------------
{
  const cap = rates.thresholds.matrixExpansionCap;
  chk("no strategy is one job", expandMatrix(undefined, cap).combos.length, 1);
  chk("cartesian product", expandMatrix({ matrix: { os: ["a", "b"], node: [1, 2, 3] } }, cap).combos.length, 6);
  chk("exclude removes a combination", expandMatrix({ matrix: { os: ["a", "b"], node: [1, 2], exclude: [{ os: "a", node: 1 }] } }, cap).combos.length, 3);
  chk("include-only builds one job per entry", expandMatrix({ matrix: { include: [{ os: "a" }, { os: "b" }, { os: "c" }] } }, cap).combos.length, 3);
  chk("include extends a matching combination", expandMatrix({ matrix: { os: ["a", "b"], include: [{ os: "a", extra: 1 }] } }, cap).combos.find((c) => c.os === "a").extra, 1);
  chk("include adds a new combination when nothing matches", expandMatrix({ matrix: { os: ["a"], include: [{ os: "z" }] } }, cap).combos.length, 2);
  const capped = expandMatrix({ matrix: { a: Array.from({ length: 20 }, (_, i) => i), b: Array.from({ length: 20 }, (_, i) => i) } }, 50);
  chk("expansion cap truncates", capped.combos.length, 50);
  chkTrue("expansion cap warns", capped.warnings.some((w) => /cap/.test(w)));
  chkTrue("matrix expression warns", expandMatrix({ matrix: "${{ fromJSON(needs.x.outputs.m) }}" }, cap).warnings.length > 0);
}

// ---------------------------------------------------------------------------
console.log("\n5. runner classification");
// ---------------------------------------------------------------------------
chk("ubuntu-latest", classifyRunner("ubuntu-latest", {}, rates).cls, "linux");
chk("ubuntu-24.04", classifyRunner("ubuntu-24.04", {}, rates).cls, "linux");
chk("windows-latest", classifyRunner("windows-latest", {}, rates).cls, "windows");
chk("macos-latest", classifyRunner("macos-latest", {}, rates).cls, "macos");
chk("ubuntu-24.04-arm", classifyRunner("ubuntu-24.04-arm", {}, rates).cls, "linux-arm");
chk("windows-11-arm", classifyRunner("windows-11-arm", {}, rates).cls, "windows-arm");
chk("macos-13-xlarge", classifyRunner("macos-13-xlarge", {}, rates).cls, "macos-large");
chk("self-hosted label list", classifyRunner(["self-hosted", "linux", "x64"], {}, rates).cls, "self-hosted");
chk("matrix expression resolves against the combination", classifyRunner("${{ matrix.os }}", { os: "macos-latest" }, rates).cls, "macos");
chk("unresolved expression is unknown", classifyRunner("${{ matrix.os }}", {}, rates).cls, "unknown");
chk("unresolved expression is flagged unresolved", classifyRunner("${{ matrix.os }}", {}, rates).resolved, false);
chk("an unrecognised custom label is unknown, not Linux", classifyRunner("my-big-runner-8core", {}, rates).cls, "unknown");
chk("runner group object form", classifyRunner({ group: "ubuntu-runners", labels: ["ubuntu-latest"] }, {}, rates).cls, "linux");

// ---------------------------------------------------------------------------
console.log("\n6. cron frequency");
// ---------------------------------------------------------------------------
chk("field * expands fully", expandCronField("*", 0, 59, null).size, 60);
chk("field */5 expands by step", expandCronField("*/5", 0, 59, null).size, 12);
chk("field list and range", [...expandCronField("1,3-5", 0, 59, null)], [1, 3, 4, 5]);
chk("out-of-range field is rejected", expandCronField("99", 0, 59, null), null);
near("weekly cron is ~4.27 runs/month", cronRunsPerMonth("0 12 * * 1"), (52 * 30) / 365);
near("every 5 minutes is 8640 runs/month", cronRunsPerMonth("*/5 * * * *"), 8640, 1);
near("daily cron is ~30 runs/month", cronRunsPerMonth("0 3 * * *"), 30, 0.1);
near("monthly cron is ~0.99 runs/month", cronRunsPerMonth("0 0 1 * *"), (12 * 30) / 365);
chk("a 4-field cron is rejected", cronRunsPerMonth("0 12 * *"), null);
chk("a non-numeric cron field is rejected", cronRunsPerMonth("0 12 * * bogus"), null);

// ---------------------------------------------------------------------------
console.log("\n7. cost model");
// ---------------------------------------------------------------------------
{
  const linuxRate = rates.billing.usdPerMinute.linux;
  const macRate = rates.billing.usdPerMinute.macos;
  const one = costJobs([{ cls: "linux" }], rates, 0.1);
  chk("a sub-minute job still bills the round-up minute", one.wallMinutesEstimate, rates.billing.roundUpPerJobMinutes);
  chk("a sub-minute Linux job costs one Linux minute", one.usdEstimate, linuxRate);
  const mac = costJobs([{ cls: "macos" }], rates, 1);
  near("one macOS minute is ~10.33 Linux-equivalent minutes", mac.linuxEqMinutesEstimate, macRate / linuxRate);
  const sh = costJobs([{ cls: "self-hosted" }], rates, 60);
  chk("a self-hosted job consumes no included minutes", sh.linuxEqMinutesEstimate, 0);
  const mixed = costJobs([{ cls: "linux" }, { cls: "linux" }, { cls: "macos" }], rates, 3);
  chk("floor counts one minute per job regardless of duration", mixed.wallMinutesFloor, 3);
  chk("estimate rounds the per-job assumption up", mixed.wallMinutesEstimate, 9);
  near("mixed cost adds up", mixed.usdEstimate, 3 * (2 * linuxRate) + 3 * macRate, 1e-6);
  chk("byClass counts each runner class", mixed.byClass, { linux: 2, macos: 1 });
}

// ---------------------------------------------------------------------------
console.log("\n8. end-to-end analysis on fixture repositories");
// ---------------------------------------------------------------------------
const tmp = mkdtempSync(join(tmpdir(), "actions-budget-"));
const mkRepo = (name, files) => {
  const dir = join(tmp, name);
  mkdirSync(join(dir, ".github", "workflows"), { recursive: true });
  for (const [f, body] of Object.entries(files)) writeFileSync(join(dir, ".github", "workflows", f), body);
  return dir;
};

const WASTEFUL = `name: Everything
on:
  push:
  pull_request:
jobs:
  test:
    runs-on: \${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - run: make test
`;
const FRUGAL = `name: PR fast
on:
  pull_request:
    paths:
      - 'src/**'
  push:
    branches: [main]
    paths:
      - 'src/**'
concurrency:
  group: \${{ github.workflow }}-\${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - run: make test
`;

{
  const repo = mkRepo("wasteful", { "ci.yml": WASTEFUL });
  chk("workflow discovery finds the file", findWorkflowFiles(repo).length, 1);
  const a = analyzeRepo(repo, { rates });
  const ids = a.findings.map((f) => f.id);
  chk("three-OS matrix expands to three jobs", a.workflows[0].cost.jobs, 3);
  chkTrue("flags the missing concurrency group", ids.includes("missing-concurrency"));
  chkTrue("flags the missing paths filter", ids.includes("missing-paths-filter"));
  chkTrue("flags the push/pull_request double run", ids.includes("push-pr-double-run"));
  chkTrue("flags the non-Linux runners", ids.includes("non-linux-runner"));
  chkTrue("flags the missing timeout", ids.includes("missing-timeout"));
  chk("counts two non-Linux findings (macOS and Windows)", a.findings.filter((f) => f.id === "non-linux-runner").length, 2);
  chk("an unfiltered push fires on a topic branch too", a.scenarios.push_feature.jobs, 3);
  chk("a PR update therefore costs both runs", a.scenarios.pr_update.jobs, 6);
  const r = rates.billing.usdPerMinute;
  near("PR-update floor matches the rate card", a.scenarios.pr_update.linuxEqMinutesFloor, (2 * (r.linux + r.macos + r.windows)) / r.linux, 0.05);
}
{
  const repo = mkRepo("frugal", { "ci.yml": FRUGAL });
  const a = analyzeRepo(repo, { rates });
  const warns = a.findings.filter((f) => f.level === "warn" || f.level === "error");
  chk("a well-configured workflow raises no warnings", warns.map((w) => w.id), []);
  chk("one Linux job", a.scenarios.pull_request.jobs, 1);
  chk("a main-only push filter keeps topic pushes free", a.scenarios.push_feature.jobs, 0);
  chk("PR update costs exactly one job", a.scenarios.pr_update.jobs, 1);
  chk("one Linux job floors at one Linux-equivalent minute", a.scenarios.pr_update.linuxEqMinutesFloor, 1);
}
{
  const repo = mkRepo("reusable", {
    "caller.yml": `name: Caller
on:
  pull_request:
jobs:
  call:
    uses: ./.github/workflows/_shared.yml
  remote:
    uses: some-org/some-repo/.github/workflows/x.yml@v1
`,
    "_shared.yml": `name: Shared
on:
  workflow_call:
jobs:
  a:
    runs-on: ubuntu-latest
  b:
    runs-on: macos-latest
`,
  });
  const a = analyzeRepo(repo, { rates });
  const caller = a.workflows.find((w) => w.file.endsWith("caller.yml"));
  chk("a local reusable workflow is followed and expanded", caller.cost.jobs, 3);
  chk("the callee's runner classes are counted", caller.cost.byClass, { linux: 1, macos: 1, unknown: 1 });
  chk("a workflow_call-only workflow does not run on its own for a PR", a.workflows.find((w) => w.file.endsWith("_shared.yml")).runsOn.pull_request, false);
  chkTrue("a remote reusable workflow is reported as unknown", a.findings.some((f) => /remote reusable/.test(f.message)));
}
{
  const repo = mkRepo("broken", { "ci.yml": "jobs:\n  a:\n    runs-on: ubuntu-latest\n   oops: 1\n" });
  const a = analyzeRepo(repo, { rates });
  chkTrue("an unparseable workflow is an error finding, not a crash", a.findings.some((f) => f.id === "parse-failed" && f.level === "error"));
  chk("an unparseable workflow contributes no phantom jobs", a.scenarios.pr_update.jobs, 0);
}
{
  const repo = mkRepo("empty", {});
  const a = analyzeRepo(repo, { rates });
  chkTrue("a repo with no workflows says so", a.findings.some((f) => f.id === "no-workflows"));
  chk("a repo with no workflows projects zero minutes", a.monthly.estimate, 0);
}
{
  const repo = mkRepo("selfhosted", {
    "ci.yml": `name: SH
on:
  pull_request:
jobs:
  a:
    runs-on: [self-hosted, linux]
    timeout-minutes: 5
`,
  });
  const a = analyzeRepo(repo, { rates });
  chkTrue("a self-hosted runner is flagged with the fork risk", a.findings.some((f) => f.id === "self-hosted-runner" && /fork pull request/.test(f.message)));
  chk("a self-hosted job draws down no allowance", a.scenarios.pr_update.linuxEqMinutesEstimate, 0);
}
{
  const repo = mkRepo("scheduled", {
    "ci.yml": `name: Nightly
on:
  schedule:
    - cron: '0 3 * * *'
jobs:
  a:
    runs-on: ubuntu-latest
    timeout-minutes: 5
`,
  });
  const a = analyzeRepo(repo, { rates, pushesPerDay: 0, mergesPerDay: 0 });
  near("a nightly job costs ~30 x minutes-per-job per month", a.monthly.estimate, 30 * rates.assumptions.defaultMinutesPerJob, 0.5);
  chkTrue("the schedule cost is reported", a.findings.some((f) => f.id === "schedule-cost"));
}
{
  // Savings arithmetic: the tiered scheme's headline claim must hold in the tool too.
  const before = analyzeRepo(mkRepo("before", { "ci.yml": WASTEFUL }), { rates, pushesPerDay: 10, mergesPerDay: 1 });
  const after = analyzeRepo(mkRepo("after", { "ci.yml": FRUGAL }), { rates, pushesPerDay: 10, mergesPerDay: 1 });
  chkTrue("the frugal layout projects far fewer minutes than the wasteful one", after.monthly.estimate < before.monthly.estimate / 10);
  console.log(`     (wasteful ${before.monthly.estimate} min/month vs frugal ${after.monthly.estimate} min/month)`);
}

// ---------------------------------------------------------------------------
console.log("\n9. this repository's own workflows");
// ---------------------------------------------------------------------------
{
  const a = analyzeRepo(ROOT, { rates });
  chk("both workflows parse", a.workflows.filter((w) => w.parsed).length, 2);
  chk("no parse errors on real files", a.findings.filter((f) => f.level === "error").length, 0);
  chk("a PR update fans out to 12 jobs", a.scenarios.pr_update.jobs, 12);
  chk("ten Linux and two macOS jobs", a.scenarios.pr_update.byClass, { linux: 10, macos: 2 });
  chkTrue("the macOS matrix is flagged", a.findings.some((f) => f.id === "non-linux-runner" && /macos/.test(f.message)));
  chk("push:branches [main] keeps topic pushes free", a.scenarios.push_feature.jobs, 0);
}

// ---------------------------------------------------------------------------
console.log("\n10. command line interface");
// ---------------------------------------------------------------------------
{
  const run = (args, cwd = ROOT) => spawnSync(process.execPath, [SCRIPT, ...args], { cwd, encoding: "utf8" });
  const text = run([ROOT]);
  chk("text mode exits 0", text.status, 0);
  chkTrue("text mode prints the findings header", /Findings — \d+ error/.test(text.stdout));
  const json = run([ROOT, "--json"]);
  chk("json mode exits 0", json.status, 0);
  const parsed = JSON.parse(json.stdout);
  chk("json mode reports the same job count", parsed.scenarios.pr_update.jobs, 12);
  chk("json mode reports the rate card date", parsed.ratesAsOf, rates._asOf);
  const failing = run([join(tmp, "wasteful"), "--fail-on", "warn"]);
  chk("--fail-on warn exits 1 on a wasteful repo", failing.status, 1);
  const clean = run([join(tmp, "frugal"), "--fail-on", "warn"]);
  chk("--fail-on warn exits 0 on a frugal repo", clean.status, 0);
  chk("an unknown plan exits 2", run([ROOT, "--plan", "platinum"]).status, 2);
  chk("a negative numeric option exits 2", run([ROOT, "--minutes-per-job", "-3"]).status, 2);
  chk("a non-numeric option exits 2", run([ROOT, "--pushes-per-day", "lots"]).status, 2);
  chk("a missing path exits 2", run([join(tmp, "does-not-exist")]).status, 2);
  chk("--help exits 0", run(["--help"]).status, 0);
  const teamPlan = JSON.parse(run([ROOT, "--json", "--plan", "team"]).stdout);
  chk("--plan team uses the team allowance", teamPlan.monthly.planIncludedMinutes, rates.plans.team.includedMinutes);
}

rmSync(tmp, { recursive: true, force: true });

// --visibility must actually change the report, not just be accepted. A flag that validates its input
// and then changes nothing is a dead knob: it reads as a working control and silently is not.
{
  const run = (extra) => spawnSync(process.execPath, [SCRIPT, ROOT, ...extra], { encoding: "utf8" });
  const dflt = run([]);
  const pub = run(["--visibility", "public"]);
  const priv = run(["--visibility", "private"]);
  chkTrue("no --visibility -> report states it assumes private", /visibility-unknown/.test(dflt.stdout));
  chkTrue("--visibility public reaches the findings", /visibility-public/.test(pub.stdout));
  chkTrue("public says the minutes are not billed", /informational rather than billed/.test(pub.stdout));
  chkTrue("--visibility private reaches the findings", /visibility-private/.test(priv.stdout));
  chkTrue("private names whose allowance is drawn down", /account that OWNS the repo/.test(priv.stdout));
  chkTrue("the two values produce different reports", pub.stdout !== priv.stdout);
  const bad = run(["--visibility", "sideways"]);
  chk("an unknown visibility exits 2", bad.status, 2);
  chkTrue("the error lists the accepted values", /known: public, private/.test(bad.stderr));
}


console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
