#!/usr/bin/env node
// Tests for templates/actions-frugal-ci/. Run: node scripts/actions-frugal-ci.test.mjs
//
// The two git hooks in that template are the only templates in this repository that
// get EXECUTED rather than read, so they need checks the markdown and TOML templates
// do not. An unsubstituted placeholder in a hook is either a shell syntax error or,
// when it sits inside quotes, a pattern that silently matches nothing. The second
// case is the one worth guarding: a hook that appears to pass while checking nothing.
//
// Nothing here is mocked. The hooks are substituted, syntax checked with the real
// shells, and executed inside a throwaway git repository with a real push.
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, chmodSync, rmSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { parseYamlSubset } from "./actions-budget.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const TPL = join(ROOT, "templates", "actions-frugal-ci");
const HOOKS = join(TPL, "git-hooks");
const WORKFLOWS = join(TPL, ".github", "workflows");

let pass = 0, fail = 0;
const chk = (n, got, want) => {
  if (JSON.stringify(got) === JSON.stringify(want)) { console.log(`  ok: ${n}`); pass++; }
  else { console.error(`  FAIL: ${n} (got ${JSON.stringify(got)} want ${JSON.stringify(want)})`); fail++; }
};
const chkTrue = (n, got) => chk(n, !!got, true);

// Stand-ins chosen to be harmless: every command is `true`, every regex matches
// something innocuous. The point is to prove the SHAPE of the script is valid.
const SUBS = {
  "<DEFAULT_BRANCH>": "main",
  "<NODE_VERSION>": "22",
  "<INSTALL_CMD>": "true",
  "<LINT_CMD>": "true",
  "<TYPECHECK_CMD>": "true",
  "<UNIT_TEST_CMD>": "true",
  "<INTEGRATION_TEST_CMD>": "true",
  "<E2E_TEST_CMD>": "true",
  "<FAST_TIMEOUT_MINUTES>": "15",
  "<SOURCE_PATHS>": "src/**",
  "<SOURCE_PATH_REGEX>": "^src/",
  "<HEAVY_LABEL>": "full-ci",
  "<FORMAT_CMD>": "true",
  "<LINT_STAGED_CMD>": "true",
  "<FORMATTABLE_FILE_REGEX>": "\\.txt$",
  "<FORMATTABLE_GLOB>": "*.txt",
  "<LINTABLE_GLOB>": "*.txt",
  "<DEBUG_STATEMENT_REGEX>": "ZZDEBUGZZ",
};

const PLACEHOLDER = /<[A-Z][A-Z0-9_]*>/g;
const substitute = (text, skip = []) => {
  let out = text;
  for (const [k, v] of Object.entries(SUBS)) {
    if (skip.includes(k)) continue;
    out = out.split(k).join(v);
  }
  return out;
};

const tmp = mkdtempSync(join(tmpdir(), "frugal-ci-"));
const writeExec = (name, body) => {
  const p = join(tmp, name);
  writeFileSync(p, body);
  chmodSync(p, 0o755);
  return p;
};
const sh = (bin, args, opts = {}) => spawnSync(bin, args, { encoding: "utf8", ...opts });

// ---------------------------------------------------------------------------
console.log("\n1. every placeholder is documented");
// ---------------------------------------------------------------------------
{
  const readme = readFileSync(join(TPL, "TEMPLATE_README.md"), "utf8");
  const files = [
    ...readdirSync(HOOKS).map((f) => join(HOOKS, f)),
    ...readdirSync(WORKFLOWS).map((f) => join(WORKFLOWS, f)),
    join(TPL, "lefthook.template.yml"),
  ];
  const undocumented = [], unknown = [];
  for (const f of files) {
    for (const token of new Set(readFileSync(f, "utf8").match(PLACEHOLDER) ?? [])) {
      if (!readme.includes(token)) undocumented.push(`${basename(f)}:${token}`);
      if (!(token in SUBS)) unknown.push(`${basename(f)}:${token}`);
    }
  }
  chk("every placeholder appears in TEMPLATE_README.md", undocumented, []);
  chk("every placeholder has a test substitution, so nothing is left unexercised", unknown, []);
  chkTrue("the template actually uses placeholders (the check is not vacuous)", files.some((f) => PLACEHOLDER.test(readFileSync(f, "utf8"))));
}

// ---------------------------------------------------------------------------
console.log("\n2. substituted hooks are valid shell");
// ---------------------------------------------------------------------------
const hookFiles = readdirSync(HOOKS).filter((f) => f.endsWith(".sh"));
chk("both hooks are present", hookFiles.sort(), ["pre-commit.template.sh", "pre-push.template.sh"]);

for (const f of hookFiles) {
  const src = readFileSync(join(HOOKS, f), "utf8");
  const subbed = substitute(src);
  chk(`${f}: no placeholder survives substitution`, subbed.match(PLACEHOLDER), null);
  const p = writeExec(f.replace(".template.sh", ""), subbed);
  chk(`${f}: bash -n accepts it`, sh("bash", ["-n", p]).status, 0);
  chk(`${f}: sh -n accepts it`, sh("sh", ["-n", p]).status, 0);
}

// ---------------------------------------------------------------------------
console.log("\n3. the syntax check has teeth");
// ---------------------------------------------------------------------------
{
  // A placeholder in command position breaks parsing, so `bash -n` must reject it.
  // If this passes, test 2 above would be proving nothing.
  const broken = writeExec("pre-push-broken", substitute(readFileSync(join(HOOKS, "pre-push.template.sh"), "utf8"), ["<LINT_CMD>"]));
  const r = sh("bash", ["-n", broken]);
  chk("an unsubstituted <LINT_CMD> fails bash -n", r.status !== 0, true);
  chkTrue("and says why", /syntax error/i.test(r.stderr));

  // A placeholder inside quotes parses fine. This is the silent case, and the only
  // thing standing between it and a hook that checks nothing is the runtime guard.
  const quiet = writeExec("pre-commit-quiet", substitute(readFileSync(join(HOOKS, "pre-commit.template.sh"), "utf8"), ["<FORMATTABLE_FILE_REGEX>"]));
  chk("a quoted unsubstituted placeholder still passes bash -n", sh("bash", ["-n", quiet]).status, 0);
  const guard = sh("sh", [quiet], { cwd: ROOT });
  chk("but the runtime guard rejects it", guard.status, 1);
  chkTrue("naming the exact leftover token", guard.stderr.includes("<FORMATTABLE_FILE_REGEX>"));
  chkTrue("and pointing at the README", guard.stderr.includes("TEMPLATE_README.md"));
}
{
  // The guard has to win the race against a later syntax error in the same file.
  // The shell parses incrementally, so a top-of-file guard runs first.
  const both = writeExec("pre-push-both", substitute(readFileSync(join(HOOKS, "pre-push.template.sh"), "utf8"), ["<LINT_CMD>"]));
  const r = sh("sh", [both], { input: "" });
  chk("the guard reports before the later syntax error is reached", r.status, 1);
  chkTrue("naming the leftover token rather than printing a parse error", r.stderr.includes("<LINT_CMD>"));
}

// ---------------------------------------------------------------------------
console.log("\n4. the substituted pre-push hook runs end to end");
// ---------------------------------------------------------------------------
{
  const repo = join(tmp, "repo");
  const remote = join(tmp, "remote.git");
  mkdirSync(repo, { recursive: true });
  const git = (...args) => sh("git", args, { cwd: repo });
  sh("git", ["init", "-q", "--bare", remote]);
  git("init", "-q", "-b", "main", ".");
  git("config", "user.email", "test@example.com");
  git("config", "user.name", "test");
  git("remote", "add", "origin", remote);
  writeFileSync(join(repo, "a.txt"), "hello\n");
  git("add", "a.txt");
  git("commit", "-qm", "init");

  mkdirSync(join(repo, ".git", "hooks"), { recursive: true });
  const install = (name) => {
    const p = join(repo, ".git", "hooks", name);
    writeFileSync(p, substitute(readFileSync(join(HOOKS, `${name}.template.sh`), "utf8")));
    chmodSync(p, 0o755);
  };
  install("pre-push");
  install("pre-commit");

  // Query the remote by explicit ref. A bare repository's HEAD defaults to master,
  // so `git log` with no ref would read an empty branch and pass vacuously.
  const remoteLog = () => sh("git", ["--git-dir", remote, "log", "--oneline", "main"]).stdout.trim();
  const remoteCommits = () => (remoteLog() === "" ? 0 : remoteLog().split("\n").length);

  const pushed = git("push", "-q", "origin", "main");
  chk("a clean tree pushes successfully through the hook", pushed.status, 0);
  chkTrue("the commit reached the remote", remoteLog().includes("init"));

  // A failing check has to block the push, otherwise the hook saves nothing.
  const hookPath = join(repo, ".git", "hooks", "pre-push");
  writeFileSync(hookPath, readFileSync(hookPath, "utf8").replace('step "unit tests" true', 'step "unit tests" false'));
  chmodSync(hookPath, 0o755);
  writeFileSync(join(repo, "b.txt"), "second\n");
  git("add", "b.txt");
  git("commit", "-qm", "second");
  const blocked = git("push", "-q", "origin", "main");
  chk("a failing check blocks the push", blocked.status !== 0, true);
  chkTrue("and names the step that failed", (blocked.stdout + blocked.stderr).includes("unit tests"));
  chk("nothing extra reached the remote", remoteCommits(), 1);

  // The escape hatch has to work, or people will delete the hook instead.
  const escaped = sh("git", ["push", "-q", "origin", "main"], { cwd: repo, env: { ...process.env, SKIP_PREPUSH: "1" } });
  chk("SKIP_PREPUSH=1 lets the push through", escaped.status, 0);
  chk("and the second commit lands", remoteCommits(), 2);

  // Deleting a branch sends an all-zero local oid and must not run the checks.
  writeFileSync(hookPath, substitute(readFileSync(join(HOOKS, "pre-push.template.sh"), "utf8")).replace('step "lint" true', 'step "lint" false'));
  chmodSync(hookPath, 0o755);
  git("push", "-q", "origin", "main:refs/heads/scratch");
  const del = git("push", "-q", "origin", ":refs/heads/scratch");
  chk("a branch deletion skips the checks", del.status, 0);
}

// ---------------------------------------------------------------------------
console.log("\n5. substituted workflow templates are well formed");
// ---------------------------------------------------------------------------
{
  const expected = { "ci.template.yml": ["changes", "fast"], "heavy.template.yml": ["full", "platforms"], "_checks.reusable.template.yml": ["checks"] };
  for (const [f, jobs] of Object.entries(expected)) {
    const { doc, warnings } = parseYamlSubset(substitute(readFileSync(join(WORKFLOWS, f), "utf8")));
    chk(`${f}: parses cleanly`, warnings, []);
    chk(`${f}: declares the expected jobs`, Object.keys(doc.jobs ?? {}), jobs);
  }
  const ci = parseYamlSubset(substitute(readFileSync(join(WORKFLOWS, "ci.template.yml"), "utf8"))).doc;
  chk("ci.yml filters push to the default branch, so a PR does not run twice", ci.on.push.branches, ["main"]);
  chk("ci.yml cancels superseded runs conditionally", typeof ci.concurrency["cancel-in-progress"], "string");
  chk("ci.yml keeps the required job on Linux", ci.jobs.changes["runs-on"], "ubuntu-latest");
  chkTrue("ci.yml gates the fast job so a docs-only change reports Success", String(ci.jobs.fast.if).includes("needs.changes.outputs.src"));
  const heavy = parseYamlSubset(substitute(readFileSync(join(WORKFLOWS, "heavy.template.yml"), "utf8"))).doc;
  chkTrue("heavy.yml gates the full suite behind the label", String(heavy.jobs.full.if).includes("full-ci"));
  chkTrue("heavy.yml keeps the platform matrix off pull requests", String(heavy.jobs.platforms.if).includes("push"));
  chk("heavy.yml stops paying for siblings once one fails", heavy.jobs.platforms.strategy["fail-fast"], true);
}

rmSync(tmp, { recursive: true, force: true });

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
