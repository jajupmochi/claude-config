#!/usr/bin/env bash
# install-tui.sh — install (or plan) the recommended terminal/TUI stack for driving AI coding agents.
# See recommendations/tui-for-agents.md. DRY-RUN by default: it prints what it WOULD do and never installs
# unless you pass --apply (which asks y/N per tool). Nothing is forced.
#
#   install-tui.sh --check     # report which tools are installed / missing
#   install-tui.sh             # dry-run: print the install plan (commands), install nothing
#   install-tui.sh --apply     # actually install missing tools, asking y/N per tool
#
# Testability seam: set TUI_FAKE_INSTALLED="zellij delta" to pretend those are installed (used by the tests)
# so detection can be exercised without touching the real system.
set -uo pipefail

# name | probe-binary | install command (Ubuntu-oriented; MANUAL: <url> when there is no clean package) | purpose
TOOLS=(
  "zellij|zellij|cargo install --locked zellij|multiplexer / workspace (many agent panes)"
  "claude-squad|claude-squad|MANUAL: https://github.com/smtg-ai/claude-squad#installation|agent-session orchestrator (git-worktree isolation)"
  "lazygit|lazygit|MANUAL: https://github.com/jesseduffield/lazygit#installation (or: go install github.com/jesseduffield/lazygit@latest)|TUI git: diff review + staging"
  "delta|delta|cargo install git-delta|syntax-highlighted diffs (git pager)"
)

is_installed() {
  local name="$1" bin="$2"
  case " ${TUI_FAKE_INSTALLED:-} " in *" $name "*) return 0 ;; esac
  command -v "$bin" >/dev/null 2>&1
}

mode="dryrun"
case "${1:-}" in
  --check) mode="check" ;;
  --apply) mode="apply" ;;
  --dry-run|"") mode="dryrun" ;;
  -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
  *) echo "unknown option: $1 (use --check | --apply | --dry-run)"; exit 2 ;;
esac

missing=0
for row in "${TOOLS[@]}"; do
  IFS='|' read -r name bin cmd purpose <<<"$row"
  if is_installed "$name" "$bin"; then
    echo "ok       $name — installed ($purpose)"
    continue
  fi
  missing=$((missing + 1))
  case "$mode" in
    check)  echo "MISSING  $name — $purpose" ;;
    dryrun) echo "PLAN     $name — would run: $cmd" ;;
    apply)
      echo "MISSING  $name — $purpose"
      if [[ "$cmd" == MANUAL:* ]]; then
        echo "         (manual install — see ${cmd#MANUAL: }); skipping automatic install"
        continue
      fi
      read -r -p "         install $name via '$cmd'? [y/N] " a
      if [[ "$a" =~ ^[Yy]$ ]]; then eval "$cmd" && echo "         installed $name"; else echo "         skipped"; fi
      ;;
  esac
done

echo "---"
echo "$missing of ${#TOOLS[@]} recommended tools missing."
[ "$mode" = "dryrun" ] && echo "(dry-run — nothing installed. Re-run with --apply to install, or --check to just report.)"
exit 0
