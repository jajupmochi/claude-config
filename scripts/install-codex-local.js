#!/usr/bin/env node
/**
 * Local Codex activator for agent-harness.
 *
 * - Symlinks the tested 20-skill Codex user set into ~/.agents/skills.
 * - Symlinks this repository into ~/plugins/agent-harness.
 * - Creates or updates ~/.agents/plugins/marketplace.json.
 * - Marks the local plugin INSTALLED_BY_DEFAULT for new Codex sessions.
 * - Installs user AGENTS.md, absolute-path hooks, and custom agent profiles.
 *
 * Use --dry-run to preview actions.
 */

const fs = require("fs");
const os = require("os");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");
const home = process.env.AGENT_HARNESS_HOME || os.homedir();
const dryRun = process.argv.includes("--dry-run");
const force = process.argv.includes("--force");

const skillLinks = [
  ["agent-config-adapter", "skills/agent-config-adapter"],
  ["agent-update-watcher", "skills/agent-update-watcher"],
  ["autopilot", "skills/general/autopilot"],
  ["autoresearch-toolfinder", "skills/autoresearch-toolfinder"],
  ["code-verifier", "skills/code-verifier"],
  ["figma-authoring-constraints", "skills/figma-authoring-constraints"],
  ["figma-design-fetch", "skills/figma-design-fetch"],
  ["init-agent-config", "setup/init-agent-config"],
  ["init-codex-config", "skills/init-codex-config"],
  ["long-running-tasks", "skills/long-running-tasks"],
  ["memory-flywheel", "skills/memory-flywheel"],
  ["preview-template", "skills/preview-template"],
  ["privacy-redact", "skills/privacy-redact"],
  ["prompt-library", "skills/prompt-library"],
  ["research-critic", "skills/research-critic"],
  ["system-cleanup", "skills/system-cleanup"],
  ["task-relationship-analysis", "skills/task-relationship-analysis"],
  ["tui-installer", "skills/tui-installer"],
  ["verify-template", "skills/verify-template"],
  ["verify-visual", "skills/verify-visual"],
];

const customAgentFiles = [
  "harness-explorer.toml",
  "harness-mechanical.toml",
  "harness-reviewer.toml",
  "harness-worker.toml",
];

const agentsSkillsDir = path.join(home, ".agents", "skills");
const personalPluginsDir = path.join(home, "plugins");
const pluginLink = path.join(personalPluginsDir, "agent-harness");
const marketplaceDir = path.join(home, ".agents", "plugins");
const marketplacePath = path.join(marketplaceDir, "marketplace.json");
const codexHome = path.join(home, ".codex");
const codexAgentsDir = path.join(codexHome, "agents");
const globalAgentsPath = path.join(codexHome, "AGENTS.md");
const globalHooksPath = path.join(codexHome, "hooks.json");

function log(message) {
  console.log(`${dryRun ? "[dry-run] " : ""}${message}`);
}

function ensureDir(dir) {
  if (dryRun) {
    log(`mkdir -p ${dir}`);
    return;
  }
  fs.mkdirSync(dir, { recursive: true });
}

function removeExisting(target) {
  const stat = fs.lstatSync(target);
  if (stat.isDirectory() && !stat.isSymbolicLink()) {
    throw new Error(`${target} exists and is a real directory; use --force only after moving it manually.`);
  }
  fs.rmSync(target, { recursive: true, force: true });
}

function pathEntryExists(target) {
  try {
    fs.lstatSync(target);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") {
      return false;
    }
    throw error;
  }
}

function symlinkDir(source, target) {
  if (!fs.existsSync(source)) {
    throw new Error(`Missing source: ${source}`);
  }

  if (fs.existsSync(target) || fs.lstatSync(path.dirname(target)).isSymbolicLink()) {
    try {
      const current = fs.realpathSync(target);
      if (current === fs.realpathSync(source)) {
        log(`symlink already correct: ${target} -> ${source}`);
        return;
      }
    } catch {
      // Fall through to conflict handling.
    }
    if (!force) {
      log(`skip existing different path: ${target}`);
      return;
    }
    if (dryRun) {
      log(`remove ${target}`);
    } else {
      removeExisting(target);
    }
  }

  if (dryRun) {
    log(`ln -s ${source} ${target}`);
    return;
  }
  fs.symlinkSync(source, target, "dir");
}

function writeUserFile(target, contents) {
  ensureDir(path.dirname(target));
  if (pathEntryExists(target)) {
    const targetStat = fs.lstatSync(target);
    let current;
    try {
      current = fs.readFileSync(target, "utf8");
    } catch (error) {
      if (!(targetStat.isSymbolicLink() && error.code === "ENOENT")) {
        throw error;
      }
    }
    if (current === contents) {
      log(`file already correct: ${target}`);
      return;
    }
    if (!force) {
      log(`skip existing different file: ${target} (re-run with --force after review)`);
      return;
    }
    if (current !== undefined) {
      const stamp = new Date().toISOString().replace(/[-:.TZ]/g, "");
      const backup = `${target}.bak.${stamp}`;
      log(`backup ${target} -> ${backup}`);
      if (!dryRun) {
        fs.copyFileSync(target, backup);
      }
    } else {
      log(`dangling user-file symlink has no readable contents to back up: ${target}`);
    }
    if (targetStat.isSymbolicLink()) {
      log(`replace user-file symlink: ${target}`);
      if (!dryRun) {
        fs.rmSync(target, { force: true });
      }
    }
  }
  log(`write ${target}`);
  if (!dryRun) {
    fs.writeFileSync(target, contents);
  }
}

function renderUserHooks() {
  const hooks = JSON.parse(fs.readFileSync(path.join(repoRoot, "hooks.json"), "utf8"));
  for (const groups of Object.values(hooks.hooks || {})) {
    for (const group of groups) {
      for (const hook of group.hooks || []) {
        if (typeof hook.command === "string" && hook.command.startsWith("./")) {
          hook.command = path.resolve(repoRoot, hook.command);
        }
      }
    }
  }
  return `${JSON.stringify(hooks, null, 2)}\n`;
}

function installUserSurfaces() {
  writeUserFile(globalAgentsPath, fs.readFileSync(path.join(repoRoot, "codex", "AGENTS.md"), "utf8"));
  writeUserFile(globalHooksPath, renderUserHooks());
  ensureDir(codexAgentsDir);
  for (const filename of customAgentFiles) {
    writeUserFile(
      path.join(codexAgentsDir, filename),
      fs.readFileSync(path.join(repoRoot, "codex", "agents", filename), "utf8"),
    );
  }
}

function readMarketplace() {
  if (!fs.existsSync(marketplacePath)) {
    return {
      name: "personal",
      interface: {
        displayName: "Personal",
      },
      plugins: [],
    };
  }
  return JSON.parse(fs.readFileSync(marketplacePath, "utf8"));
}

function writeMarketplace(marketplace) {
  const text = `${JSON.stringify(marketplace, null, 2)}\n`;
  if (dryRun) {
    log(`write ${marketplacePath}`);
    console.log(text);
    return;
  }
  fs.writeFileSync(marketplacePath, text);
}

function upsertMarketplace() {
  ensureDir(marketplaceDir);
  const marketplace = readMarketplace();
  if (!Array.isArray(marketplace.plugins)) {
    marketplace.plugins = [];
  }
  if (!marketplace.name) {
    marketplace.name = "personal";
  }
  if (!marketplace.interface) {
    marketplace.interface = { displayName: "Personal" };
  }

  const entry = {
    name: "agent-harness",
    source: {
      source: "local",
      path: "./plugins/agent-harness",
    },
    policy: {
      installation: "INSTALLED_BY_DEFAULT",
      authentication: "ON_INSTALL",
    },
    category: "Productivity",
  };

  const index = marketplace.plugins.findIndex((plugin) => plugin.name === "agent-harness");
  if (index === -1) {
    marketplace.plugins.push(entry);
  } else {
    marketplace.plugins[index] = entry;
  }
  writeMarketplace(marketplace);
}

function main() {
  console.log("Activating agent-harness for Codex local discovery");
  console.log(`Repository: ${repoRoot}`);

  ensureDir(agentsSkillsDir);
  for (const [skillName, relativeSource] of skillLinks) {
    symlinkDir(path.join(repoRoot, relativeSource), path.join(agentsSkillsDir, skillName));
  }

  ensureDir(personalPluginsDir);
  symlinkDir(repoRoot, pluginLink);
  upsertMarketplace();
  installUserSurfaces();

  console.log("");
  console.log("Codex local activation complete.");
  console.log("The personal marketplace entry is INSTALLED_BY_DEFAULT.");
  console.log("/plugins may label it Admin Installed and omit the enable toggle; that is expected policy state.");
  console.log("Start a new Codex task before relying on AGENTS.md, hooks, MCP, or custom-agent discovery.");
  console.log("Use /skills to inspect skills, /hooks to trust hooks, and codex plugin list to verify installed, enabled status.");
}

main();
