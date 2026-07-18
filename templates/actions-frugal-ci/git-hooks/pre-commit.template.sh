#!/bin/sh
# pre-commit — the fast local tier. Seconds, not minutes, and only on staged files.
# Anything that needs the whole tree belongs in pre-push instead.
#
# Install:
#   cp templates/actions-frugal-ci/git-hooks/pre-commit.template.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# Escape hatch: git commit --no-verify
set -eu

# Refuse to run half-substituted. See the same guard in pre-push.template.sh for
# why an unsubstituted placeholder inside quotes is more dangerous than one that
# breaks the syntax outright.
leftover=$(grep -oE '<[A-Z][A-Z0-9_]+>' "$0" | sort -u || true)
if [ -n "$leftover" ]; then
    echo "pre-commit: this hook still contains unsubstituted template placeholders:" >&2
    printf '  %s\n' $leftover >&2
    echo "pre-commit: fill them in (templates/actions-frugal-ci/TEMPLATE_README.md) or delete the hook." >&2
    exit 1
fi

staged=$(git diff --cached --name-only --diff-filter=ACMR)
[ -z "$staged" ] && exit 0

# Formatter, on staged files only, then restage whatever it rewrote. Formatting is
# the cheapest thing to fix locally and one of the most common reasons a remote lint
# job fails, so it belongs at commit time.
formattable=$(printf '%s\n' "$staged" | grep -E '<FORMATTABLE_FILE_REGEX>' || true)
if [ -n "$formattable" ]; then
    printf '%s\n' "$formattable" | xargs <FORMAT_CMD>
    printf '%s\n' "$formattable" | xargs git add
fi

# Trailing whitespace and conflict markers, both of which otherwise burn a full
# remote run to discover.
if ! git diff --cached --check; then
    echo "pre-commit: whitespace or conflict-marker problems above"
    exit 1
fi

if git diff --cached -U0 | grep -nE '^\+.*(<<<<<<<|>>>>>>>|<DEBUG_STATEMENT_REGEX>)'; then
    echo "pre-commit: the added lines above should not be committed"
    exit 1
fi

exit 0
