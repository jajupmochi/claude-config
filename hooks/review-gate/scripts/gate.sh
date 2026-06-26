#!/usr/bin/env bash
# review-gate / gate.sh  —  Stop hook (v2).
# On a code-changing turn, before Claude may finish:
#   1. run available deterministic checks (ruff/shellcheck);
#   2. force ONE review round whose feedback is a STRUCTURED MARKDOWN report that
#      (a) names each review FORM + the TOOL it uses, (b) when a minimal function/
#      module changed, mandates per-function/module AI review (DEFAULT ON), and
#      (c) tells Claude to present findings as a markdown list in-session.
# Blocks via {"decision":"block","reason":<md>} until lint is clean AND one review
# round has happened. Loop-guarded (<=MAX_ROUNDS), fail-open on any error.
set +e
command -v jq >/dev/null 2>&1 || exit 0
MAX_ROUNDS=3

IN="$(cat 2>/dev/null)"
sid="$(printf '%s' "$IN" | jq -r '.session_id // empty' 2>/dev/null)"; [ -n "$sid" ] || sid="nosess"
dir="$HOME/.claude/review-state"; log="$dir/$sid.changed"; rnd="$dir/$sid.rounds"; rev="$dir/$sid.reviewed"

[ -s "$log" ] || exit 0
# stale-flag expiry: a .changed left by a long-dead turn (>12h) must not force a review now — clear it.
now="$(date +%s)"; mt="$(stat -c %Y "$log" 2>/dev/null || echo "$now")"
[ $((now - mt)) -gt 43200 ] && { : > "$log"; rm -f "$rnd" "$rev"; exit 0; }

files="$(sort -u "$log" 2>/dev/null | while IFS= read -r f; do
  [ -f "$f" ] || continue
  case "$f" in
    *.py|*.js|*.jsx|*.ts|*.tsx|*.sh|*.bash|*.go|*.rs|*.java|*.rb|*.c|*.cc|*.cpp|*.h|*.hpp|*.lua|*.php) printf '%s\n' "$f" ;;
  esac
done)"
[ -n "$files" ] || { : > "$log"; rm -f "$rnd" "$rev"; exit 0; }

rounds="$(cat "$rnd" 2>/dev/null)"; case "$rounds" in ''|*[!0-9]*) rounds=0;; esac
if [ "$rounds" -ge "$MAX_ROUNDS" ]; then
  printf '[review-gate] max review rounds (%s) reached; allowing stop. Review manually: %s\n' \
    "$MAX_ROUNDS" "$(printf '%s' "$files" | tr '\n' ' ')" >&2
  : > "$log"; rm -f "$rnd" "$rev"; exit 0
fi

# --- deterministic checks (only tools that exist); build MD lines + a failure flag
lint_md=""; lint_fail=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  case "$f" in
    *.py)
      command -v ruff >/dev/null 2>&1 || continue
      o="$(ruff check "$f" 2>&1)"
      if [ $? -ne 0 ]; then lint_fail=1; lint_md="$lint_md
  - FAIL \`ruff\` $f:
\`\`\`
$o
\`\`\`"; else lint_md="$lint_md
  - ok \`ruff\` $f"; fi ;;
    *.sh|*.bash)
      command -v shellcheck >/dev/null 2>&1 || continue
      o="$(shellcheck -S error "$f" 2>&1)"
      if [ $? -ne 0 ]; then lint_fail=1; lint_md="$lint_md
  - FAIL \`shellcheck\` $f:
\`\`\`
$o
\`\`\`"; else lint_md="$lint_md
  - ok \`shellcheck\` $f"; fi ;;
  esac
done <<EOF
$files
EOF
[ -n "$lint_md" ] || lint_md="
  - (no bundled linter matched these file types)"

# --- pass condition: lint clean AND one structured review round already done
if [ "$lint_fail" -eq 0 ] && [ -f "$rev" ]; then
  : > "$log"; rm -f "$rnd" "$rev"; exit 0
fi

# --- detect a minimal function/module change (heuristic across changed files)
has_module=no
while IFS= read -r f; do
  [ -f "$f" ] || continue
  if grep -nE '^[[:space:]]*(async[[:space:]]+)?(def|class|function|func|fn|public|private|protected|module|sub)[[:space:]]|^[[:space:]]*export[[:space:]]+(default[[:space:]]+)?(async[[:space:]]+)?(function|class|const)' "$f" >/dev/null 2>&1; then
    has_module=yes; break
  fi
done <<EOF
$files
EOF

flist="$(printf '%s' "$files" | tr '\n' ' ')"
rounds=$((rounds + 1)); printf '%s' "$rounds" > "$rnd"; touch "$rev"

reason="## review-gate: automatic review of this turn's code

**Changed files:** $flist

**Review forms and tools:**
- **Lint / static analysis** (tools: \`ruff\` / \`shellcheck\` where present):$lint_md
- **Logic & edge cases** (form: manual reasoning) — off-by-one, error handling, does it do what was asked.
- **Security** (form: pattern + reasoning) — injection, secrets/keys, unsafe exec/eval, path traversal, OWASP.
- **Fake-run / over-claims** (tool: \`code-verifier\` skill) — invoke it on any \"it works / tests pass / results show X\" claim.
- **Test-gap** (form: coverage reasoning) — are the changed units covered by tests?
- **Minimal change / blast-radius** (form: diff scope) — is the change minimal? does it avoid touching unrelated code or hot paths?
- **Modularity** (form: structure) — minimal function/module granularity, reusable, not a conflated block.
- **Commit & doc completeness** (form: hygiene) — small named commit(s); docstrings/docs updated for what changed."

if [ "$has_module" = "yes" ]; then
  reason="$reason
- **Per-function/module AI review** (DEFAULT ON) — a minimal function/module changed this turn; review EACH changed function/module individually (correctness, contract/inputs-outputs, side effects)."
fi

if [ "$lint_fail" -ne 0 ]; then
  reason="$reason

**Deterministic checks FAILED — fix first (see FAIL lines above).**"
fi

reason="$reason

**Then present your review as a markdown list in your reply**, e.g.:
\`\`\`md
- track.sh / parse_input(): logic — OK
- gate.sh / lint loop: security — no secrets; ok
- foo.py / load(): test-gap — ISSUE: no test for empty input
\`\`\`
Fix real issues, then finish. (review-gate runs on every code-changing turn and is not skipped.)"

printf '%s' "$reason" | jq -Rs '{decision:"block", reason:.}' 2>/dev/null || exit 0
exit 0
