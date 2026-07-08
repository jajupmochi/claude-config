#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");
const errors = [];

function readJson(relativePath) {
  const filePath = path.join(repoRoot, relativePath);
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    errors.push(`${relativePath}: ${error.message}`);
    return null;
  }
}

function requireFile(relativePath) {
  if (!fs.existsSync(path.join(repoRoot, relativePath))) {
    errors.push(`missing ${relativePath}`);
  }
}

function requireExecutable(relativePath) {
  const filePath = path.join(repoRoot, relativePath);
  requireFile(relativePath);
  if (!fs.existsSync(filePath)) {
    return;
  }
  const mode = fs.statSync(filePath).mode;
  if ((mode & 0o111) === 0) {
    errors.push(`${relativePath} is not executable`);
  }
}

function validateManifest() {
  const manifest = readJson(".codex-plugin/plugin.json");
  if (!manifest) {
    return;
  }
  for (const field of ["name", "version", "description", "skills", "interface"]) {
    if (!manifest[field]) {
      errors.push(`plugin manifest missing ${field}`);
    }
  }
  if (manifest.skills !== "./skills/") {
    errors.push("plugin manifest skills must be ./skills/");
  }
  const iface = manifest.interface || {};
  for (const field of ["displayName", "shortDescription", "longDescription", "developerName", "category", "capabilities", "defaultPrompt"]) {
    if (!iface[field]) {
      errors.push(`plugin interface missing ${field}`);
    }
  }
}

function parseFrontmatter(contents) {
  if (!contents.startsWith("---\n")) {
    return null;
  }
  const end = contents.indexOf("\n---", 4);
  if (end === -1) {
    return null;
  }
  const frontmatter = {};
  for (const line of contents.slice(4, end).split("\n")) {
    const match = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(line);
    if (match) {
      frontmatter[match[1]] = match[2].replace(/^"|"$/g, "");
    }
  }
  return frontmatter;
}

function validateSkills() {
  const skillsRoot = path.join(repoRoot, "skills");
  const entries = fs.readdirSync(skillsRoot, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name.startsWith(".")) {
      continue;
    }
    const skillPath = path.join(skillsRoot, entry.name, "SKILL.md");
    if (!fs.existsSync(skillPath)) {
      errors.push(`skills/${entry.name} is missing SKILL.md`);
      continue;
    }
    const frontmatter = parseFrontmatter(fs.readFileSync(skillPath, "utf8"));
    if (!frontmatter) {
      errors.push(`skills/${entry.name}/SKILL.md has invalid frontmatter`);
      continue;
    }
    if (!frontmatter.name) {
      errors.push(`skills/${entry.name}/SKILL.md missing name`);
    }
    if (!frontmatter.description) {
      errors.push(`skills/${entry.name}/SKILL.md missing description`);
    }
  }
}

function validateHooks() {
  const hooks = readJson("hooks.json");
  if (!hooks) {
    return;
  }
  const postToolUse = hooks.hooks && hooks.hooks.PostToolUse;
  if (!Array.isArray(postToolUse) || postToolUse.length === 0) {
    errors.push("hooks.json missing hooks.PostToolUse");
  }
}

function main() {
  requireFile(".claude-plugin/plugin.json");
  requireFile(".codex-plugin/plugin.json");
  requireFile("docs/CODEX_ADAPTATION_PLAN.md");
  requireExecutable("scripts/install-codex-local.js");
  requireExecutable("scripts/verify-codex-adapter.js");
  requireExecutable("scripts/codex-update-safe.js");
  requireExecutable("scripts/codex_ruff_format_on_edit.sh");
  requireExecutable("scripts/codex_jq_validate_json.sh");
  validateManifest();
  validateSkills();
  validateHooks();
  const installer = fs.readFileSync(path.join(repoRoot, "scripts/install-codex-local.js"), "utf8");
  if (!installer.includes('installation: "INSTALLED_BY_DEFAULT"')) {
    errors.push("install-codex-local.js must set marketplace policy.installation to INSTALLED_BY_DEFAULT");
  }
  if (!installer.includes('"system-cleanup"')) {
    errors.push("install-codex-local.js must install the system-cleanup wrapper skill");
  }
  if (!installer.includes('"autoresearch-toolfinder"')) {
    errors.push("install-codex-local.js must install the autoresearch-toolfinder wrapper skill");
  }

  if (errors.length > 0) {
    console.error("Codex adapter verification failed:");
    for (const error of errors) {
      console.error(`- ${error}`);
    }
    process.exit(1);
  }

  console.log("Codex adapter verification passed.");
}

main();
