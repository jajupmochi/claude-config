#!/usr/bin/env node
// deploy-hooks.mjs — install this repo's hooks so they are LIVE, in every session, without a restart.
//
// Why this exists: hooks were being deployed by hand-copying scripts into ~/.claude/hooks/ and hand-editing
// ~/.claude/settings.json. That is not "shipped in the plugin", that is remembering to do it — and a step
// nobody can re-run is a step that silently rots. `adapters/claude.mjs` deliberately emits no hooks into
// .claude-plugin/plugin.json (they would double-fire against settings.json), so the plugin manifest is not
// the install path either. This script is.
//
// It reads the SAME hook list the manifests are built from (adapters/manifest.source.json -> inventory.hooks),
// copies each hook's scripts to ~/.claude/hooks/<name>/, and merges its settings.snippet.json into
// ~/.claude/settings.json.
//
// Effective immediately, in sessions already running. Claude Code watches settings.json and reloads hook
// REGISTRATIONS live, and a hook's script is a separate process re-read from disk on every invocation, so
// neither half needs a restart. Both were verified empirically rather than assumed.
//
// Safety: additive, idempotent, and non-clobbering. A settings entry whose command already appears is left
// alone rather than duplicated. Dry-run is the default; nothing is written without --apply. settings.json is
// backed up before the first change and validated as JSON after, because a malformed settings.json is what
// stops the file watcher and forces the restart this exists to avoid.
//
//   node bin/deploy-hooks.mjs                    # dry-run, all hooks
//   node bin/deploy-hooks.mjs --apply
//   node bin/deploy-hooks.mjs --apply --hook task-ledger
//   node bin/deploy-hooks.mjs --apply --enable-new   # also turn on hooks not yet registered
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export function inventoryHooks(repoRoot = REPO_ROOT) {
  const m = JSON.parse(fs.readFileSync(path.join(repoRoot, "adapters/manifest.source.json"), "utf8"));
  return (m.inventory?.hooks ?? []).filter((rel) => fs.existsSync(path.join(repoRoot, rel)));
}

/** Executable payload of a hook: the files that must exist on disk for its settings entry to resolve. */
export function hookScripts(rel, repoRoot = REPO_ROOT) {
  const dir = path.join(repoRoot, rel, "scripts");
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter((f) => /\.(sh|py|mjs|js)$/.test(f))
    // Tests belong to the repo, not the live hooks directory: nothing there would ever run them, and a
    // copy that nothing runs is a copy that silently drifts.
    .filter((f) => !/^test_/.test(f) && !/\.test\.(mjs|js|py)$/.test(f))
    .map((f) => path.join(dir, f));
}

export function hookSnippet(rel, repoRoot = REPO_ROOT) {
  const f = path.join(repoRoot, rel, "settings.snippet.json");
  if (!fs.existsSync(f)) return null;
  try {
    return JSON.parse(fs.readFileSync(f, "utf8"));
  } catch (err) {
    throw new Error(`${rel}/settings.snippet.json is not valid JSON: ${err.message}`);
  }
}

/**
 * Merge a snippet's hook entries into settings, skipping any whose command is already registered.
 *
 * Matching on the command string is what makes this idempotent AND non-clobbering: re-running never
 * duplicates an entry, and an entry the user edited by hand keeps their version rather than being
 * overwritten with ours.
 */
/** The script a command runs, ignoring any env prefix, interpreter, or quoting around it. */
export function commandScript(command) {
  const m = String(command ?? "").match(/[\w$/.{}~-]*\/[\w.-]+\.(sh|py|mjs|js)/);
  return m ? m[0].replace(/^["']|["']$/g, "") : String(command ?? "").trim();
}

export function mergeHooks(settings, snippet, { enableNew = false } = {}) {
  const added = [];
  const skipped = [];
  const hooks = settings.hooks ?? (settings.hooks = {});
  for (const [event, groups] of Object.entries(snippet.hooks ?? {})) {
    const existing = hooks[event] ?? (hooks[event] = []);
    // Match on the SCRIPT, not the whole command: a registered entry may carry an env prefix
    // (SSH_GUARD_STATE=... bash "$HOME/...") that makes string equality miss it and register a duplicate.
    const registered = new Set(
      existing.flatMap((g) => (g.hooks ?? []).map((h) => commandScript(h.command)))
    );
    for (const group of groups) {
      const fresh = (group.hooks ?? []).filter((h) => {
        if (registered.has(commandScript(h.command))) return false;
        // A hook the user has not registered is one they have not opted into. Turning it on as a side
        // effect of deploying another hook would change how every session behaves without being asked.
        if (!enableNew) { skipped.push(`${event}: ${h.command}`); return false; }
        return true;
      });
      if (!fresh.length) continue;
      existing.push({ ...group, hooks: fresh });
      for (const h of fresh) added.push(`${event}: ${h.command}`);
    }
  }
  return { added, skipped };
}

/** Rewrite a snippet's $HOME-relative command so it points at the deployed copy of that hook. */
export function resolveCommands(snippet, hookName) {
  const json = JSON.stringify(snippet);
  return JSON.parse(json.replaceAll("$HOME/.claude/hooks/" + hookName, "$HOME/.claude/hooks/" + hookName));
}

function main() {
  const argv = process.argv.slice(2);
  const apply = argv.includes("--apply");
  const only = argv.includes("--hook") ? argv[argv.indexOf("--hook") + 1] : null;
  const enableNew = argv.includes("--enable-new");
  const home = os.homedir();
  const settingsPath = path.join(home, ".claude", "settings.json");

  let rels = inventoryHooks();
  if (only) {
    rels = rels.filter((r) => path.basename(r) === only);
    if (!rels.length) {
      console.error(`no such hook: ${only} (have: ${inventoryHooks().map((r) => path.basename(r)).join(", ")})`);
      process.exit(1);
    }
  }

  let settings = {};
  if (fs.existsSync(settingsPath)) {
    try {
      settings = JSON.parse(fs.readFileSync(settingsPath, "utf8"));
    } catch (err) {
      console.error(`refusing to touch a settings.json that does not parse: ${err.message}`);
      process.exit(1);
    }
  }

  console.log(`agent-harness hook deploy (${apply ? "APPLY" : "dry-run"})`);
  let copied = 0, registered = 0;
  const plan = [];
  const notOptedIn = [];

  for (const rel of rels) {
    const name = path.basename(rel);
    const dest = path.join(home, ".claude", "hooks", name);
    for (const src of hookScripts(rel)) {
      const target = path.join(dest, path.basename(src));
      const same = fs.existsSync(target)
        && fs.readFileSync(target, "utf8") === fs.readFileSync(src, "utf8");
      if (same) continue;
      plan.push(`  copy   ${name}/${path.basename(src)}`);
      copied++;
      if (apply) {
        fs.mkdirSync(dest, { recursive: true });
        fs.copyFileSync(src, target);
        if (/\.(sh|py)$/.test(target)) fs.chmodSync(target, 0o755);
      }
    }
    let snippet;
    try {
      snippet = hookSnippet(rel);
    } catch (err) {
      console.error(`  SKIP   ${name}: ${err.message}`);
      continue;
    }
    if (!snippet) continue;
    const { added, skipped } = mergeHooks(settings, resolveCommands(snippet, name), { enableNew });
    for (const sk of skipped) notOptedIn.push(`  ${name} -> ${sk}`);
    for (const a of added) plan.push(`  register ${name} -> ${a}`);
    registered += added.length;
  }

  if (notOptedIn.length) {
    console.log("\n  not enabled (you have not opted into these; pass --enable-new to turn them on):");
    for (const l of notOptedIn) console.log(l);
  }
  if (!plan.length) {
    console.log("  everything is already deployed and registered");
    return;
  }
  for (const line of plan) console.log(line);

  if (!apply) {
    console.log(`\n  ${copied} file(s) to copy, ${registered} entr(ies) to register — re-run with --apply`);
    return;
  }

  if (registered) {
    if (fs.existsSync(settingsPath)) {
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      fs.copyFileSync(settingsPath, `${settingsPath}.bak-${stamp}`);
    }
    const text = JSON.stringify(settings, null, 2) + "\n";
    JSON.parse(text); // a malformed settings.json stops the watcher; never write one
    fs.mkdirSync(path.dirname(settingsPath), { recursive: true });
    fs.writeFileSync(settingsPath, text, "utf8");
  }
  console.log(`\n  done: ${copied} file(s) copied, ${registered} entr(ies) registered`);
  console.log("  live in running sessions: settings.json is watched, and hook scripts are re-read per call");
}

// Robust "is this the entry script?" check — comparing import.meta.url to `file://${argv[1]}` breaks when
// the path contains spaces (import.meta.url percent-encodes them), so resolve both back to plain paths.
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) main();
