// .opencode/plugins/review-gate.js — opencode review-gate plugin.
// On session idle, runs the SHARED review-gate core.sh (the SAME 12-form logic Claude & Codex use) over
// the project's git changes and surfaces the review. The heavy lifting is in lib/run-core.mjs (unit-tested
// without opencode; see review-gate.test.mjs).
//
// The opencode plugin/hook API wiring below follows opencode.ai/docs (a plugin returns hook handlers; the
// `event` handler receives session events such as `session.idle`). It is intentionally DEFENSIVE — every
// path is guarded so an API mismatch degrades to a NO-OP and can never break an opencode session.
// TODO(verify): confirm the event name + the surfacing call against a real opencode install.
import { join } from "node:path";
import { runReviewCore } from "./lib/run-core.mjs";

export const ReviewGate = async (ctx = {}) => {
  const repoRoot = ctx.directory || ctx.project?.path || process.cwd();
  const coreSh = join(repoRoot, "hooks", "review-gate", "scripts", "core.sh");
  const stateDir = join(process.env.HOME || repoRoot, ".opencode", "review-state");

  return {
    event: async ({ event } = {}) => {
      try {
        if (!event || event.type !== "session.idle") return undefined;
        const sid = String(event.sessionID || event.session_id || "opencode").replace(/[^A-Za-z0-9._-]/g, "_");
        const { review, block } = runReviewCore({ repoRoot, coreSh, stateDir, sid });
        if (!review) return undefined;
        const text = review + "\n\n(review-gate: opencode — present findings, then finish.)";
        try {
          await ctx.client?.session?.message?.({ text });
        } catch {
          console.error(text);
        }
        return block ? { block: true, reason: review } : undefined;
      } catch {
        return undefined; // never break the session
      }
    },
  };
};

export default ReviewGate;
