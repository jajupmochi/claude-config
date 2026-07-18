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
  printf '[review-gate] max review rounds (%s) reached; allowing stop. Review these manually:\n%s\n' \
    "$MAX_ROUNDS" "$(printf '%s' "$files" | sed 's/^/  /')" >&2
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

# One path per line, not space-joined. A space-joined list is unsplittable the moment a path contains a
# space, and this harness's own checkout lives under "New Volume1" — so the reader could not tell where
# one changed file ended and the next began. Newlines are the only separator a path cannot contain.
flist="$(printf '%s' "$files" | sed 's/^/- /')"
rounds=$((rounds + 1)); printf '%s' "$rounds" > "$rnd"; touch "$rev"

reason="## review-gate: automatic review of this turn's code

**Changed files:**

$flist

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
10. **Robustness / adversarial inputs** (form: edge cases — a GitHub-Copilot-recurring miss) — quoting & embedded spaces, regex metacharacters in interpolated values, path assumptions (trailing slash, un-escaped names), boundary/empty inputs, and stale state an early-exit or error branch leaves behind for other components.
11. **Bug fix → regression test** (rule: \`regression-test-on-bugfix\`) — if this turn FIXES a bug, is there a NEW test that REPRODUCES it (would fail on the pre-fix code, passes now)? A behavioral bug fix without a red→green regression test that locks the bug out is NOT done — add one or state why it's genuinely untestable."

nforms=11
if [ "$has_module" = "yes" ]; then
  nforms=12
  reason="$reason
12. **Per-function/module AI review** (DEFAULT ON) — a minimal function/module changed this turn; review EACH changed function/module individually (correctness, contract/inputs-outputs, side effects)."
fi

if [ "$lint_fail" -ne 0 ]; then
  reason="$reason

**Deterministic checks FAILED — fix first (see FAIL lines above).**"
fi

reason="$reason

**Present your review IN CHINESE** (unless the project is English-language), in its OWN block fenced by a
THICK \`━\` bar. Open it with a markdown HEADING, not a bold line: a terminal markdown renderer colours
headings, and colour is what makes the block findable when scrolling back through a long turn. So: a
bounded \`━\` bar on its own line, then \`## 🔍 review-gate 审查\` on its own line, then a \`━\` bar, then
the body, then a closing \`━\` bar. NOT inline \`━━━ kw ━━━\` (wraps badly on a phone), NOT raw text
sprawling after your summary.

**The body is a MARKDOWN TABLE, one row per changed function/module — never prose bullets.** Prose at this
density is unreadable. Keep every cell to one short clause and push anything longer into the numbered
notes under the table, referenced by row number. Blank line before and after the table, and keep the
\`|---|\` separator row, or it will not render.

Lead with the counts as a bar, generated (do not hand-draw it):
\`\`\`bash
bash \"\$HOME/.claude/hooks/review-gate/statsbar.sh\" --format md --title '本回合审查' --unit 项 \\
  --stat '无问题:N:green' --stat '已修:N:yellow' --stat '待修:N:red'
\`\`\`

Full shape:
\`\`\`md
━━━━━━━━━━━━━━━━
## 🔍 review-gate 审查

━━━━━━━━━━━━━━━━

<statsbar output here>

| # | 文件 / 单元 | 维度 | 结论 |
|---|---|---|---|
| 1 | \`track.sh\` / \`parse_input()\` | logic | ✅ OK |
| 2 | \`foo.py\` / \`load()\` | test-gap | ⚠️ 待修 — 空输入无测试 |
| 3 | \`bar.sh\` / \`flist\` | robustness | 🔧 已修 — 空格路径不可切分 |

详注(仅展开需要解释的行):

2. …
3. …
━━━━━━━━━━━━━━━━
\`\`\`
先修真实问题再收尾。(review-gate 每个改代码的回合都跑,不可跳过。)"

# Delivery split. The brief above is INSTRUCTIONS FOR THE MODEL, but a Stop hook's reason string is
# rendered verbatim into the user's terminal, so sending the whole thing that way dumps ~3KB of internal
# review forms into their transcript on every code-changing turn. Long blocks also re-render badly in the
# CLI, splicing one form's tail into the next, which is what makes the dump look corrupted.
#
# With RG_BRIEF_FILE set, the brief goes to that file and stdout carries a short pointer to it. Enforcement
# is untouched: the caller still blocks on non-empty stdout. With it unset the previous behaviour is byte
# for byte identical, so the Codex and opencode shims keep working until they opt in.
#
# If the write fails we fall back to the full inline brief. Losing the review would be a worse outcome
# than a noisy transcript, so the failure mode degrades toward MORE enforcement, not less.
if [ -n "${RG_BRIEF_FILE:-}" ] \
   && mkdir -p "$(dirname "$RG_BRIEF_FILE")" 2>/dev/null \
   && printf '%s\n' "$reason" > "$RG_BRIEF_FILE" 2>/dev/null; then
  nfiles="$(printf '%s' "$files" | grep -c . 2>/dev/null || echo 0)"
  printf '## review-gate: review required — %s changed file(s)\n\n' "$nfiles"
  printf 'Read the full brief and follow it:\n\n    %s\n\n' "$RG_BRIEF_FILE"
  printf 'It lists the changed files, the %s review forms, and the required output format.\n' "$nforms"
  printf 'Present the review in Chinese in its own `━`-fenced block. Fix real problems before finishing.\n'
  exit 0
fi

printf '%s' "$reason"
exit 0
