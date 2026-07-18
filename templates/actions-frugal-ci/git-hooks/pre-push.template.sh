#!/bin/sh
# pre-push — the expensive local tier. Runs the same checks the remote fast tier
# runs, so a push that would have failed CI fails here instead, on hardware you
# already pay for. Every push it stops is a full remote run you do not spend.
#
# Install:
#   cp templates/actions-frugal-ci/git-hooks/pre-push.template.sh .git/hooks/pre-push
#   chmod +x .git/hooks/pre-push
# Or let lefthook manage it, which survives a fresh clone. See lefthook.template.yml.
#
# Escape hatch, for a work-in-progress push to your own branch:
#   SKIP_PREPUSH=1 git push
#
# Target: under 90 seconds. Past that people start reaching for the escape hatch,
# and a hook that gets bypassed saves nothing.
set -eu

# Refuse to run half-substituted. An unfilled placeholder in an executing hook is
# either a shell syntax error (loud, and it blocks the push) or, when the token sits
# inside quotes, a pattern that silently matches nothing. The second case is the
# dangerous one, a hook that appears to pass while checking nothing. The shell parses
# a script incrementally, so this guard runs and reports before any later syntax
# error is reached.
#
# Note for anyone editing this file: do not write a bracketed uppercase token in a
# comment here. The guard scans its own source, so such a token would make the hook
# reject itself on every run.
leftover=$(grep -oE '<[A-Z][A-Z0-9_]+>' "$0" | sort -u || true)
if [ -n "$leftover" ]; then
    echo "pre-push: this hook still contains unsubstituted template placeholders:" >&2
    printf '  %s\n' $leftover >&2
    echo "pre-push: fill them in (templates/actions-frugal-ci/TEMPLATE_README.md) or delete the hook." >&2
    exit 1
fi

if [ "${SKIP_PREPUSH:-}" = "1" ]; then
    echo "pre-push: skipped via SKIP_PREPUSH=1"
    exit 0
fi

ZERO=0000000000000000000000000000000000000000
have_commits=0

# stdin gives one line per ref: <local_ref> <local_oid> <remote_ref> <remote_oid>
while read -r _local_ref local_oid _remote_ref _remote_oid; do
    [ "$local_oid" = "$ZERO" ] && continue # branch deletion, nothing to check
    have_commits=1
done

if [ "$have_commits" = "0" ]; then
    exit 0
fi

log=$(mktemp)
trap 'rm -f "$log"' EXIT INT TERM

step() {
    label=$1
    shift
    printf 'pre-push: %s ... ' "$label"
    if "$@" >"$log" 2>&1; then
        echo "ok"
    else
        echo "FAILED"
        cat "$log"
        echo ""
        echo "pre-push: $label failed. Fix it locally rather than spending a remote run."
        echo "          Override with SKIP_PREPUSH=1 git push"
        exit 1
    fi
}

# Keep this list identical to the fast tier in .github/workflows/_checks.reusable.yml.
# When the two drift the hook stops predicting the remote result, and people stop
# trusting it.
step "lint" <LINT_CMD>
step "types" <TYPECHECK_CMD>
step "unit tests" <UNIT_TEST_CMD>

# Report what this push will cost on GitHub's runners. Advisory by default. Add
# --fail-on warn to make a wasteful workflow change block the push instead.
if command -v node >/dev/null 2>&1 && [ -f scripts/actions-budget.mjs ]; then
    node scripts/actions-budget.mjs . || true
fi

echo "pre-push: all local checks passed"
