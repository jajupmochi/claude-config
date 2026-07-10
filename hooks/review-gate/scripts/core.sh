#!/usr/bin/env bash
# review-gate / core.sh — agent-NEUTRAL review computation, shared by every agent's Stop-hook shim
# (Claude gate.sh, Codex, opencode). Extracted from gate.sh so the review LOGIC + the FORMS report live
# in ONE place; only session-id extraction and the native delivery format differ per agent (the shim).
#
# Inputs (env):
#   RG_STATE_DIR  dir holding "$RG_SID.{changed,rounds,reviewed}"  (required)
#   RG_SID        session id                                       (default: nosess)
#   RG_MAX_ROUNDS loop guard                                       (default: 3)
# Contract:
#   - If a review IS needed this turn, prints the STRUCTURED MARKDOWN report to STDOUT and exits 0.
#   - If NO review is needed (nothing changed / stale flag / max-rounds / already lint-clean+reviewed),
#     prints NOTHING to stdout and exits 0.
#   The shim delivers a non-empty stdout in its agent's native format (block vs advisory); empty => allow stop.
#   Fail-open: any internal problem => exit 0 with empty stdout.
set +e
command -v jq >/dev/null 2>&1 || exit 0
MAX_ROUNDS="${RG_MAX_ROUNDS:-3}"
dir="${RG_STATE_DIR:?RG_STATE_DIR required}"; sid="${RG_SID:-nosess}"
log="$dir/$sid.changed"; rnd="$dir/$sid.rounds"; rev="$dir/$sid.reviewed"

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

**Review forms and tools** (numbered so each is identifiable):

1. **Lint / static analysis** (tools: \`ruff\` / \`shellcheck\` where present):$lint_md
2. **Logic & edge cases** (form: manual reasoning) — off-by-one, error handling, does it do what was asked.
3. **Security** (form: pattern + reasoning) — injection, secrets/keys, unsafe exec/eval, path traversal, OWASP.
4. **Fake-run / over-claims** (tool: \`code-verifier\` skill) — invoke it on any \"it works / tests pass / results show X\" claim.
5. **Test-gap** (form: coverage reasoning) — are the changed units covered by tests?
6. **Minimal change / blast-radius** (form: diff scope) — is the change minimal? does it avoid touching unrelated code or hot paths?
7. **Modularity** (form: structure) — minimal function/module granularity, reusable, not a conflated block.
8. **Commit & doc completeness** (form: hygiene) — small named commit(s); docstrings/docs updated for what changed.
9. **Doc/message/name accuracy** (form: consistency — a GitHub-Copilot-recurring miss) — do user-facing messages, docstrings, examples, and any referenced tool/API/flag NAME match what the code ACTUALLY does, and actually EXIST? (e.g. a message saying \"push\" when the gate covers all remote-publishing; an invented tool/API name; a docstring that omits a real output state; a stale example path.)
10. **Robustness / adversarial inputs** (form: edge cases — a GitHub-Copilot-recurring miss) — quoting & embedded spaces, regex metacharacters in interpolated values, path assumptions (trailing slash, un-escaped names), boundary/empty inputs, and stale state an early-exit or error branch leaves behind for other components."

if [ "$has_module" = "yes" ]; then
  reason="$reason
11. **Per-function/module AI review** (DEFAULT ON) — a minimal function/module changed this turn; review EACH changed function/module individually (correctness, contract/inputs-outputs, side effects)."
fi

if [ "$lint_fail" -ne 0 ]; then
  reason="$reason

**Deterministic checks FAILED — fix first (see FAIL lines above).**"
fi

reason="$reason

**Present your review IN CHINESE** (unless the project is English-language), in its OWN block fenced by a
THICK \`━\` bar — a bounded \`━\` bar on its own line, then \`**review-gate 审查**\` on its own line, then a
\`━\` bar, then the bullets, then a closing \`━\` bar — NOT inline \`━━━ kw ━━━\` (wraps badly on a phone),
NOT raw text sprawling after your summary. Use **bold-keyed bullets**, one per changed function/module
(the file + unit in **bold**, then \`维度 — 结论\`); if there are **more than 3**, NUMBER them \`1. 2. 3. …\`
so each is identifiable. e.g.:
\`\`\`md
━━━━━━━━━━━━━━━━
**review-gate 审查**
━━━━━━━━━━━━━━━━
- **track.sh / parse_input()**：logic — OK
- **foo.py / load()**：test-gap — 问题:空输入无测试 → 待修
━━━━━━━━━━━━━━━━
\`\`\`
先修真实问题再收尾。(review-gate 每个改代码的回合都跑,不可跳过。)"

printf '%s' "$reason"
exit 0
