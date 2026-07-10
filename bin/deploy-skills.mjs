#!/usr/bin/env node
// deploy-skills.mjs — make the agent-harness skills discoverable by each agent's NATIVE skill loader.
//
// Why this exists: `bin/install.js` only symlinks ONE skill (init-agent-config) into ~/.claude/skills/;
// the other 15 canonical skills were reachable only by direct path or per-project scaffold, and opencode
// (which reads skills from ~/.config/opencode/skills/) saw NONE of them. This deployer reads the SAME
// canonical list the manifests are built from (adapters/manifest.source.json -> inventory.skills) and
// idempotently symlinks each skill dir into every agent's global skill directory.
//
// Agents + their native skill dirs (verified against the real 2026-07 binaries):
//   claude   -> ~/.claude/skills/<name>
//   opencode -> ~/.config/opencode/skills/<name>   (opencode has NO project-level skill auto-discovery)
//   codex    -> already gets skills via its plugin cache on `codex plugin add`, so it is NOT handled here.
//
// Safety: additive + idempotent + NON-CLOBBERING. A target that already exists is only touched if it is a
// symlink to THIS repo's copy (re-pointed if stale); a real dir or a symlink to somewhere else (e.g. the
// user's own standalone code-verifier) is LEFT ALONE and reported as "kept". Dry-run is the default;
// nothing is written without --apply.
//
//   node bin/deploy-skills.mjs                 # dry-run, all agents
//   node bin/deploy-skills.mjs --apply         # do it
//   node bin/deploy-skills.mjs --agent claude  # one agent (claude|opencode|all)
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export function agentSkillDirs(home) {
  return {
    claude: path.join(home, ".claude", "skills"),
    opencode: path.join(home, ".config", "opencode", "skills"),
  };
}

// Read the canonical skill list from the ONE source the manifests are generated from.
export function inventorySkills(repoRoot = REPO_ROOT) {
  const m = JSON.parse(fs.readFileSync(path.join(repoRoot, "adapters", "manifest.source.json"), "utf8"));
  return (m.inventory?.skills || []).slice();
}

// Classify what should happen to one target path, without writing anything.
// -> "link" (create), "relink" (fix stale symlink to us), "ok" (already ours), "kept" (exists, not ours), "nosrc"
export function classify(src, dst) {
  if (!fs.existsSync(path.join(src, "SKILL.md"))) return "nosrc";
  let st;
  try {
    st = fs.lstatSync(dst);
  } catch {
    return "link"; // absent
  }
  if (st.isSymbolicLink()) {
    let cur = "";
    try {
      cur = path.resolve(path.dirname(dst), fs.readlinkSync(dst));
    } catch {
      /* dangling symlink */
    }
    if (cur === path.resolve(src)) return "ok";
    return "relink"; // symlink, but points elsewhere-but-was-a-symlink -> we may re-point ONLY if it targets a repo skill
  }
  return "kept"; // a real dir/file that is not a symlink -> never clobber
}

// Build the full plan (pure w.r.t. the filesystem it reads; writes nothing).
export function plan({ repoRoot = REPO_ROOT, home = os.homedir(), agents = ["claude", "opencode"] } = {}) {
  const dirs = agentSkillDirs(home);
  const skills = inventorySkills(repoRoot);
  const items = [];
  for (const agent of agents) {
    const base = dirs[agent];
    if (!base) continue;
    for (const rel of skills) {
      const name = path.basename(rel);
      const src = path.join(repoRoot, rel);
      const dst = path.join(base, name);
      items.push({ agent, name, src, dst, action: classify(src, dst) });
    }
  }
  return items;
}

function apply(items) {
  let linked = 0,
    kept = 0,
    skipped = 0;
  for (const it of items) {
    if (it.action === "link" || it.action === "relink") {
      // relink is only safe when the existing symlink also points at one of OUR repo skills; classify()
      // returns "relink" for any foreign symlink, so we guard here to stay strictly non-clobbering.
      if (it.action === "relink") {
        const cur = fs.existsSync(it.dst) ? path.resolve(fs.readlinkSync(it.dst)) : "";
        if (!cur.startsWith(path.resolve(REPO_ROOT))) {
          console.log(`  kept   ${it.agent}/${it.name} (symlink to non-repo target, left alone)`);
          kept++;
          continue;
        }
        fs.rmSync(it.dst);
      }
      fs.mkdirSync(path.dirname(it.dst), { recursive: true });
      fs.symlinkSync(it.src, it.dst, "dir");
      console.log(`  link   ${it.agent}/${it.name}`);
      linked++;
    } else if (it.action === "kept") {
      console.log(`  kept   ${it.agent}/${it.name} (exists, not ours — left alone)`);
      kept++;
    } else if (it.action === "nosrc") {
      console.log(`  SKIP   ${it.agent}/${it.name} (no SKILL.md in source)`);
      skipped++;
    } // "ok" -> silent
  }
  return { linked, kept, skipped };
}

function main(argv) {
  const args = new Set(argv);
  const doApply = args.has("--apply");
  let agents = ["claude", "opencode"];
  const ai = argv.indexOf("--agent");
  if (ai >= 0 && argv[ai + 1] && argv[ai + 1] !== "all") agents = [argv[ai + 1]];
  const items = plan({ agents });
  const counts = items.reduce((a, it) => ((a[it.action] = (a[it.action] || 0) + 1), a), {});
  console.log(`agent-harness skill deploy (${doApply ? "APPLY" : "dry-run"}) — agents: ${agents.join(", ")}`);
  console.log(
    `  plan: link=${counts.link || 0} relink=${counts.relink || 0} ok=${counts.ok || 0} kept=${counts.kept || 0} nosrc=${counts.nosrc || 0}`,
  );
  if (!doApply) {
    for (const it of items.filter((x) => x.action !== "ok")) console.log(`  would ${it.action.padEnd(6)} ${it.agent}/${it.name}`);
    console.log("  (dry-run — re-run with --apply to write symlinks)");
    return 0;
  }
  const r = apply(items);
  console.log(`  done: linked=${r.linked} kept=${r.kept} skipped=${r.skipped}`);
  return 0;
}

// Robust "is this the entry script?" check — comparing import.meta.url to `file://${argv[1]}` breaks when the
// path contains spaces (import.meta.url percent-encodes them), so resolve both back to plain paths.
if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  process.exit(main(process.argv.slice(2)));
}
