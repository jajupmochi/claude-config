#!/usr/bin/env node
/**
 * Local Codex activator for agent-harness.
 *
 * - Symlinks selected Codex wrapper skills into ~/.agents/skills.
 * - Symlinks this repository into ~/plugins/agent-harness.
 * - Creates or updates ~/.agents/plugins/marketplace.json.
 * - Marks the local plugin INSTALLED_BY_DEFAULT for new Codex sessions.
 *
 * Use --dry-run to preview actions.
 */

const fs = require("fs");
const os = require("os");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");
const home = os.homedir();
const dryRun = process.argv.includes("--dry-run");
const force = process.argv.includes("--force");

const skillNames = [
  "init-codex-config",
  "agent-config-adapter",
  "verify-template",
  "preview-template",
  "long-running-tasks",
  "verify-visual",
  "privacy-redact",
  "code-verifier",
  "research-critic",
  "system-cleanup",
  "autoresearch-toolfinder",
];

const agentsSkillsDir = path.join(home, ".agents", "skills");
const personalPluginsDir = path.join(home, "plugins");
const pluginLink = path.join(personalPluginsDir, "agent-harness");
const marketplaceDir = path.join(home, ".agents", "plugins");
const marketplacePath = path.join(marketplaceDir, "marketplace.json");

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
  for (const skillName of skillNames) {
    symlinkDir(path.join(repoRoot, "skills", skillName), path.join(agentsSkillsDir, skillName));
  }

  ensureDir(personalPluginsDir);
  symlinkDir(repoRoot, pluginLink);
  upsertMarketplace();

  console.log("");
  console.log("Codex local activation complete.");
  console.log("The personal marketplace entry is INSTALLED_BY_DEFAULT.");
  console.log("Restart Codex or start a new thread/session before relying on newly discovered skills.");
  console.log("Use /skills for direct skill invocation and /plugins to inspect or install the plugin entry.");
}

main();
