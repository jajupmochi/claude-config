#!/usr/bin/env node
/**
 * Safe Codex updater.
 *
 * The official installer normally resolves latest through GitHub release metadata.
 * During a release rollout, the latest tag can appear before all package assets
 * are visible to the installer. This wrapper first tries the official command.
 * If that specific release-asset error happens, it retries with CODEX_RELEASE
 * pinned to the latest tag.
 */

const childProcess = require("child_process");
const fs = require("fs");
const https = require("https");
const os = require("os");
const path = require("path");

const INSTALL_URL = "https://chatgpt.com/codex/install.sh";
const ASSET_ERROR = "Could not find Codex package or platform npm release assets";
const repairCache = process.argv.includes("--repair-cache");
const releaseArg = process.argv.find((arg) => /^--release=/.test(arg));
const explicitRelease = releaseArg ? releaseArg.split("=")[1] : (process.env.CODEX_RELEASE || "");

function shQuote(value) {
  return "'" + String(value).replace(/'/g, "'\''") + "'";
}

function runInstaller(release) {
  const env = release ? "CODEX_RELEASE=" + shQuote(release) + " CODEX_NON_INTERACTIVE=1" : "CODEX_NON_INTERACTIVE=1";
  const command = "curl -fsSL " + shQuote(INSTALL_URL) + " | " + env + " sh";
  console.error("Running: " + command);
  const result = childProcess.spawnSync("sh", ["-c", command], { encoding: "utf8" });
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  return result;
}

function getJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "user-agent": "agent-harness-codex-update-safe" } }, (res) => {
      let data = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => { data += chunk; });
      res.on("end", () => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          reject(new Error(String(res.statusCode) + ": " + data.slice(0, 200)));
          return;
        }
        try { resolve(JSON.parse(data)); } catch (error) { reject(error); }
      });
    }).on("error", reject);
  });
}

async function latestReleaseVersion() {
  const release = await getJson("https://api.github.com/repos/openai/codex/releases/latest");
  const version = String(release.tag_name || "").replace(/^rust-v/, "");
  if (!/^\d+\.\d+\.\d+/.test(version)) {
    throw new Error("Could not parse latest Codex release from tag: " + release.tag_name);
  }
  return version;
}

function repairVersionCacheFile(version) {
  const versionPath = path.join(os.homedir(), ".codex", "version.json");
  if (!fs.existsSync(versionPath)) return;
  const current = JSON.parse(fs.readFileSync(versionPath, "utf8"));
  const next = Object.assign({}, current, {
    latest_version: version,
    last_checked_at: new Date().toISOString(),
    dismissed_version: null,
  });
  fs.writeFileSync(versionPath, JSON.stringify(next) + "\n");
  console.error("Updated " + versionPath + " to latest_version=" + version + ".");
}

async function main() {
  const first = runInstaller(explicitRelease);
  if (first.status === 0) {
    const version = explicitRelease || await latestReleaseVersion().catch(() => "");
    if (repairCache && version) repairVersionCacheFile(version);
    return;
  }

  const combined = String(first.stdout || "") + "\n" + String(first.stderr || "");
  if (explicitRelease || !combined.includes(ASSET_ERROR)) {
    process.exit(first.status || 1);
  }

  const version = await latestReleaseVersion();
  console.error("Official latest install path lacked assets. Retrying with CODEX_RELEASE=" + version + ".");
  const second = runInstaller(version);
  if (second.status === 0) {
    if (repairCache) repairVersionCacheFile(version);
    return;
  }
  process.exit(second.status || 1);
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
