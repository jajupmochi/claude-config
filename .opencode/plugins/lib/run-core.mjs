// .opencode/plugins/lib/run-core.mjs
// Verifiable helper for the opencode review-gate plugin: run the SHARED review-gate core.sh
// (hooks/review-gate/scripts/core.sh — the same forms logic Claude & Codex use) over git-detected
// changes, and return { review, block }. This layer does NOT depend on opencode's plugin API, so it is
// unit-tested without an opencode install (see review-gate.test.mjs). The plugin file wires this into
// opencode's session hook.
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";

function git(repoRoot, args) {
  try {
    // stdio: swallow stderr so a non-repo dir doesn't spray git usage text to the console.
    return execFileSync("git", args, { cwd: repoRoot, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  } catch {
    return "";
  }
}

// Staged + unstaged + untracked, de-duplicated, as absolute paths (core.sh filters to code files itself).
export function gitChangedFiles(repoRoot) {
  const lines = [
    ...git(repoRoot, ["diff", "--cached", "--name-only"]).split("\n"),
    ...git(repoRoot, ["diff", "--name-only"]).split("\n"),
    ...git(repoRoot, ["ls-files", "--others", "--exclude-standard"]).split("\n"),
  ]
    .map((s) => s.trim())
    .filter(Boolean);
  return [...new Set(lines)].map((f) => join(repoRoot, f));
}

// Returns { review: string, block: boolean }. review is "" (and block false) when no review is due.
export function runReviewCore({ repoRoot, coreSh, stateDir, sid }) {
  if (!coreSh || !existsSync(coreSh)) return { review: "", block: false };
  try {
    mkdirSync(stateDir, { recursive: true });
    const changed = gitChangedFiles(repoRoot);
    writeFileSync(join(stateDir, `${sid}.changed`), changed.length ? changed.join("\n") + "\n" : "");
    const out = execFileSync("bash", [coreSh], {
      env: { ...process.env, RG_STATE_DIR: stateDir, RG_SID: sid },
      encoding: "utf8",
    });
    const review = (out || "").trim();
    return { review, block: review.length > 0 };
  } catch {
    return { review: "", block: false }; // fail-open, never break the session
  }
}
