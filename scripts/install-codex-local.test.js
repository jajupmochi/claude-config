#!/usr/bin/env node
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const repoRoot = path.resolve(__dirname, "..");
const home = fs.mkdtempSync(path.join(os.tmpdir(), "agent-harness-codex-install-"));

const skillSources = {
  "agent-config-adapter": "skills/agent-config-adapter",
  "agent-update-watcher": "skills/agent-update-watcher",
  autopilot: "skills/general/autopilot",
  "autoresearch-toolfinder": "skills/autoresearch-toolfinder",
  "code-verifier": "skills/code-verifier",
  "figma-authoring-constraints": "skills/figma-authoring-constraints",
  "figma-design-fetch": "skills/figma-design-fetch",
  "init-agent-config": "setup/init-agent-config",
  "init-codex-config": "skills/init-codex-config",
  "long-running-tasks": "skills/long-running-tasks",
  "memory-flywheel": "skills/memory-flywheel",
  "preview-template": "skills/preview-template",
  "privacy-redact": "skills/privacy-redact",
  "prompt-library": "skills/prompt-library",
  "research-critic": "skills/research-critic",
  "system-cleanup": "skills/system-cleanup",
  "task-relationship-analysis": "skills/task-relationship-analysis",
  "tui-installer": "skills/tui-installer",
  "verify-template": "skills/verify-template",
  "verify-visual": "skills/verify-visual",
};

const agentModels = {
  "harness-explorer.toml": "gpt-5.6-terra",
  "harness-mechanical.toml": "gpt-5.6-luna",
  "harness-reviewer.toml": "gpt-5.6-terra",
  "harness-worker.toml": "gpt-5.6-terra",
};

function real(target) {
  return fs.realpathSync(target);
}

try {
  const run = spawnSync(process.execPath, [path.join(repoRoot, "scripts", "install-codex-local.js")], {
    cwd: repoRoot,
    env: { ...process.env, HOME: home, AGENT_HARNESS_HOME: home },
    encoding: "utf8",
  });
  assert.equal(run.status, 0, run.stderr || run.stdout);

  for (const [name, relativeSource] of Object.entries(skillSources)) {
    const target = path.join(home, ".agents", "skills", name);
    assert.equal(real(target), path.join(repoRoot, relativeSource), `skill link ${name}`);
  }
  assert.equal(Object.keys(skillSources).length, 20, "deployed skill contract");

  assert.equal(real(path.join(home, "plugins", "agent-harness")), repoRoot, "plugin link");
  const marketplace = JSON.parse(fs.readFileSync(path.join(home, ".agents", "plugins", "marketplace.json"), "utf8"));
  const plugin = marketplace.plugins.find((item) => item.name === "agent-harness");
  assert.equal(plugin.policy.installation, "INSTALLED_BY_DEFAULT");
  assert.match(run.stdout, /Admin Installed/);
  assert.doesNotMatch(run.stdout, /inspect or install/);

  assert.equal(fs.readFileSync(path.join(home, ".codex", "AGENTS.md"), "utf8"), fs.readFileSync(path.join(repoRoot, "codex", "AGENTS.md"), "utf8"));
  for (const [filename, model] of Object.entries(agentModels)) {
    const contents = fs.readFileSync(path.join(home, ".codex", "agents", filename), "utf8");
    assert.match(contents, new RegExp(`model = "${model.replaceAll(".", "\\.")}"`));
  }

  const hooks = JSON.parse(fs.readFileSync(path.join(home, ".codex", "hooks.json"), "utf8"));
  const commands = Object.values(hooks.hooks)
    .flat()
    .flatMap((entry) => entry.hooks || [])
    .map((hook) => hook.command);
  assert.equal(commands.length, 3);
  for (const command of commands) {
    assert.ok(path.isAbsolute(command), `hook command is absolute: ${command}`);
    assert.ok(command.startsWith(repoRoot), `hook command stays in repo: ${command}`);
  }

  const globalAgentsPath = path.join(home, ".codex", "AGENTS.md");
  const sentinelPath = path.join(home, "outside-agents.md");
  const sentinelContents = "must not be overwritten\n";
  fs.rmSync(globalAgentsPath);
  fs.writeFileSync(sentinelPath, sentinelContents);
  fs.symlinkSync(sentinelPath, globalAgentsPath);

  const forceRun = spawnSync(
    process.execPath,
    [path.join(repoRoot, "scripts", "install-codex-local.js"), "--force"],
    {
      cwd: repoRoot,
      env: { ...process.env, HOME: home, AGENT_HARNESS_HOME: home },
      encoding: "utf8",
    },
  );
  assert.equal(forceRun.status, 0, forceRun.stderr || forceRun.stdout);
  assert.equal(fs.readFileSync(sentinelPath, "utf8"), sentinelContents, "force install must not follow a user-file symlink");
  assert.equal(fs.lstatSync(globalAgentsPath).isSymbolicLink(), false, "force install replaces the symlink itself");
  assert.equal(fs.readFileSync(globalAgentsPath, "utf8"), fs.readFileSync(path.join(repoRoot, "codex", "AGENTS.md"), "utf8"));
  const backups = fs
    .readdirSync(path.join(home, ".codex"))
    .filter((filename) => filename.startsWith("AGENTS.md.bak."));
  assert.equal(backups.length, 1, "force install creates one user-file backup");
  assert.equal(fs.readFileSync(path.join(home, ".codex", backups[0]), "utf8"), sentinelContents);

  const danglingTarget = path.join(home, "must-not-be-created.md");
  fs.rmSync(globalAgentsPath);
  fs.symlinkSync(danglingTarget, globalAgentsPath);
  const danglingRun = spawnSync(
    process.execPath,
    [path.join(repoRoot, "scripts", "install-codex-local.js"), "--force"],
    {
      cwd: repoRoot,
      env: { ...process.env, HOME: home, AGENT_HARNESS_HOME: home },
      encoding: "utf8",
    },
  );
  assert.equal(danglingRun.status, 0, danglingRun.stderr || danglingRun.stdout);
  assert.equal(fs.existsSync(danglingTarget), false, "force install must not follow a dangling user-file symlink");
  assert.equal(fs.lstatSync(globalAgentsPath).isSymbolicLink(), false, "force install replaces a dangling symlink");

  console.log("install-codex-local: isolated 20-skill/user-surface install PASS");
} finally {
  fs.rmSync(home, { recursive: true, force: true });
}
