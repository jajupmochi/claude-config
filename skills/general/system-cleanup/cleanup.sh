#!/usr/bin/env bash
# system-cleanup — interactive, phased disk cleanup for Ubuntu/Debian.
# Run in YOUR OWN terminal (NOT inside Claude Code), so sudo can prompt:
#     bash cleanup.sh
# Every item shows its size and asks y/N before deleting. Nothing is forced.
set -uo pipefail

ask() { read -r -p "  delete this (~$1)? [y/N] " a; [[ "$a" =~ ^[Yy]$ ]]; }
sz()  { du -sh "$@" 2>/dev/null | awk '{s=$1} END{print s?s:"0"}'; }

echo "=== disk before ==="; df -h / | awk 'NR==1||/\/$/'

echo; echo "### Phase 1 — user-level caches (no sudo) ###"
# Ask PER cache — never blanket-delete ~/.cache (that silently nukes the huggingface model cache).
[ -d ~/.cache/uv ]          && { echo "uv Python pkg cache ($(sz ~/.cache/uv)) — the usual biggest";     ask "$(sz ~/.cache/uv)"          && { uv cache clean 2>/dev/null || rm -rf ~/.cache/uv; } && echo "  cleared"; }
[ -d ~/.cache/pip ]         && { echo "pip cache ($(sz ~/.cache/pip))";                                  ask "$(sz ~/.cache/pip)"         && { pip cache purge 2>/dev/null || rm -rf ~/.cache/pip; } && echo "  cleared"; }
command -v npm >/dev/null   && { echo "npm cache";                                                       ask "npm cache"                  && npm cache clean --force >/dev/null 2>&1 && echo "  cleared"; }
[ -d ~/.cache/JetBrains ]   && { echo "JetBrains IDE cache/indexes ($(sz ~/.cache/JetBrains)) — will re-index"; ask "$(sz ~/.cache/JetBrains)" && rm -rf ~/.cache/JetBrains && echo "  cleared"; }
[ -d ~/.cache/huggingface ] && { echo "HuggingFace models/datasets ($(sz ~/.cache/huggingface)) — big models RE-DOWNLOAD SLOWLY"; ask "$(sz ~/.cache/huggingface)" && rm -rf ~/.cache/huggingface && echo "  cleared"; }
WS=~/.config/Code/WebStorage
[ -d "$WS" ]               && { echo "VS Code WebStorage ($(sz "$WS"))";                                 ask "$(sz "$WS")"                && rm -rf "$WS"/*/CacheStorage && echo "  cleared"; }
[ -d ~/.config/Code/CachedExtensionVSIXs ] && { echo "VS Code ext VSIX + Cache";                         ask "VS Code caches"             && rm -rf ~/.config/Code/CachedExtensionVSIXs ~/.config/Code/Cache ~/.config/Code/CachedData && echo "  cleared"; }
[ -d ~/.local/share/Trash ] && { echo "Trash ($(sz ~/.local/share/Trash))";                             ask "$(sz ~/.local/share/Trash)" && rm -rf ~/.local/share/Trash/* && echo "  emptied"; }

echo; echo "### Phase 2 — system (sudo) ###"
if sudo -v 2>/dev/null; then
  echo "old kernels + orphaned deps (review the list!)"; ask "apt autoremove" && sudo apt-get autoremove --purge
  echo "apt archive cache";                              ask "apt clean"      && sudo apt-get clean
  echo "journal logs > 200M";                            ask "journal vacuum" && sudo journalctl --vacuum-size=200M
  echo "disabled snap revisions:"; snap list --all 2>/dev/null | awk '/disabled/{print "   "$1" r"$3}'
  ask "remove disabled snap revisions" && snap list --all 2>/dev/null | awk '/disabled/{print $1, $3}' | while read -r n r; do sudo snap remove "$n" --revision="$r"; done
else
  echo "  (no sudo available — skipping Phase 2; run these yourself)"
fi

echo; echo "### Phase 3 — Docker (if installed) ###"
if command -v docker >/dev/null; then
  docker system df 2>/dev/null   # usually works with no sudo if you are in the docker group
  ask "docker builder prune (build cache only — 100% safe, regenerates)" && docker builder prune -f
  ask "docker system prune (also removes dangling images + stopped containers; keeps named volumes)" && docker system prune -f
fi

echo; echo "=== disk after ==="; df -h / | awk '/\/$/'
