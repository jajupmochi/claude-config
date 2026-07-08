#!/usr/bin/env python3
"""Cheap upstream-update check for the autoresearch tool index.

Compares the stored upstream commit SHA (data/state.json) with the current GitHub HEAD
for each source. One small API call per repo, no catalog download. Prints status and exits
non-zero if any source is stale, so a timer/hook can decide to run update_index.py.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = os.path.join(HERE, "data", "state.json")
UA = {"User-Agent": "autoresearch-toolfinder/1.0 (+jajupmochi/claude-config)"}


def head_sha(owner: str, repo: str, branch: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={branch}&per_page=1"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310
        return json.loads(r.read())[0]["sha"][:12]


def main() -> int:
    if not os.path.exists(SP):
        print("no state.json yet; run: python3 scripts/update_index.py")
        return 1
    with open(SP, encoding="utf-8") as f:
        st = json.load(f)
    stale = False
    for key, s in st["sources"].items():
        try:
            cur = head_sha(s["owner"], s["repo"], s["branch"])
        except Exception as e:  # noqa: BLE001
            print(f"{key:9s}: check failed ({e})")
            continue
        if cur != s.get("sha"):
            print(f"{key:9s}: STALE     stored={s.get('sha')}  upstream={cur}")
            stale = True
        else:
            print(f"{key:9s}: up-to-date ({cur})")
    if stale:
        print("\n-> upstream changed. Refresh with: python3 scripts/update_index.py")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
