#!/usr/bin/env python3
# autopilot-stamp · version: 0.1.0 · created: 2026-06-27 · updated: 2026-06-27
"""autopilot update_check.py <proj> — has autopilot been updated since this project's timer was set up?

CHEAP, code-only, no LLM. Run first on every cron fire so the daily run reconfigures itself with the
latest autopilot config when (and only when) the tool actually changed — without burning tokens to
"check for updates" each time.

How: compares the installed autopilot VERSION (bumped on every autopilot change) against the version
recorded in the project's cron_state.json at setup (`configured_with_version`).

Output (one line) + exit code:
    current                       -> exit 0   (no change; just run normally)
    UPDATED <old> -> <new>        -> exit 10  (re-install + re-arm with the latest config first)
    unknown ...                   -> exit 0   (fail-safe: never block the run on a check error)
"""
from __future__ import annotations

import os
import sys

SKILL = os.path.expanduser("~/.claude/skills/autopilot")
BASE = os.path.expanduser("~/.claude/autopilot")


def _read_version() -> str:
    for p in (os.path.join(SKILL, "VERSION"), os.path.join(BASE, "bin", "VERSION")):
        try:
            with open(p, encoding="utf-8") as f:
                v = f.read().strip()
            if v:
                return v
        except OSError:
            continue
    return ""


def _configured_version(proj: str) -> str:
    import json
    try:
        with open(os.path.join(BASE, proj, "cron_state.json"), encoding="utf-8") as f:
            return str(json.load(f).get("configured_with_version", "")).strip()
    except (OSError, ValueError):
        return ""


def main(argv) -> int:
    if len(argv) < 2 or "/" in argv[1] or ".." in argv[1]:
        print("usage: update_check.py <proj>", file=sys.stderr)
        return 0  # fail-safe
    proj = argv[1]
    cur = _read_version()
    cfg = _configured_version(proj)
    if not cur:
        print("unknown (no installed VERSION)")
        return 0
    if not cfg:
        print(f"unknown (no configured_with_version for {proj}; current {cur})")
        return 0
    if cur != cfg:
        print(f"UPDATED {cfg} -> {cur}")
        return 10
    print("current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
