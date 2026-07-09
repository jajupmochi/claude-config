// Shared projection helpers. Deterministic, LLM-free — the projection is pure code.

/**
 * Canonical JSON serialization for generated manifests.
 * 2-space indent + trailing newline, matching the repo's existing manifest style,
 * so generated output byte-matches hand-authored files (enables the parity gate).
 */
export function stableJson(obj) {
  return JSON.stringify(obj, null, 2) + "\n";
}
