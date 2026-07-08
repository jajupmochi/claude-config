#!/usr/bin/env python3
"""autopilot floor.py — agent-independent minimum-duration tracker.

Records a run's start time and answers whether the >= floor-minutes floor is met, via a
timer/CLI record (NOT the agent's own judgment). run.sh loops the daily session until
`floor.py <proj> check` passes.

Usage:
  floor.py <proj> start          # record a new run start = now
  floor.py <proj> check          # exit 0 if elapsed >= floor, else 1; prints elapsed/floor
  floor.py <proj> elapsed        # print elapsed minutes
  floor.py <proj> set <minutes>  # set the floor (default 30, no upper cap)
"""
from __future__ import annotations

import json
import os
import sys
import time

BASE = os.path.expanduser("~/.claude/autopilot")


def _state_path(proj: str) -> str:
    d = os.path.join(BASE, proj)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "floor.json")


def _load(proj: str) -> dict:
    p = _state_path(proj)
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except Exception:  # noqa: BLE001  (corrupt -> reset to defaults, fail-safe)
            pass
    return {"floor_min": 30, "start": None}


def _save(proj: str, s: dict) -> None:
    json.dump(s, open(_state_path(proj), "w"))


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    proj, cmd = argv[1], argv[2]
    s = _load(proj)
    if cmd == "set":
        s["floor_min"] = max(0, int(argv[3]))
        _save(proj, s)
        print(f"floor={s['floor_min']}min")
        return 0
    if cmd == "start":
        s["start"] = time.time()
        _save(proj, s)
        print(f"started; floor={s['floor_min']}min")
        return 0
    if not s.get("start"):
        print("no run started")
        return 1
    elapsed = (time.time() - s["start"]) / 60.0
    if cmd == "elapsed":
        print(f"{elapsed:.1f}")
        return 0
    if cmd == "check":
        print(f"elapsed={elapsed:.1f}min floor={s['floor_min']}min")
        return 0 if elapsed >= s["floor_min"] else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
