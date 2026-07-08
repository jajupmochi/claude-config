#!/usr/bin/env python3
# autopilot-stamp · version: 0.1.0 · created: 2026-06-27 · updated: 2026-06-27
"""Tests for update_check.py. Run: python3 test_update_check.py"""
import importlib.util
import io
import json
import os
import tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("update_check", os.path.join(HERE, "update_check.py"))
uc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(uc)


def run():
    with tempfile.TemporaryDirectory() as tmp:
        skill = os.path.join(tmp, "skills"); base = os.path.join(tmp, "autopilot")
        os.makedirs(skill); os.makedirs(os.path.join(base, "p1"))
        uc.SKILL = skill; uc.BASE = base

        def call():
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = uc.main(["update_check.py", "p1"])
            return rc, buf.getvalue().strip()

        def set_version(v): open(os.path.join(skill, "VERSION"), "w").write(v + "\n")
        def set_cfg(v):
            json.dump({"configured_with_version": v}, open(os.path.join(base, "p1", "cron_state.json"), "w"))

        # 1. no VERSION -> unknown, exit 0 (fail-safe)
        rc, out = call(); assert rc == 0 and out.startswith("unknown"), f"no-version: {rc} {out}"

        # 2. VERSION present, no configured -> unknown, exit 0
        set_version("2026-06-27.1"); rc, out = call()
        assert rc == 0 and out.startswith("unknown"), f"no-cfg: {rc} {out}"

        # 3. matching -> current, exit 0
        set_cfg("2026-06-27.1"); rc, out = call()
        assert rc == 0 and out == "current", f"match: {rc} {out}"

        # 4. differ -> UPDATED, exit 10
        set_version("2026-06-28.1"); rc, out = call()
        assert rc == 10 and out == "UPDATED 2026-06-27.1 -> 2026-06-28.1", f"updated: {rc} {out}"

        # 5. proj path guard -> exit 0 (fail-safe)
        assert uc.main(["update_check.py", "../etc"]) == 0
    print("update_check.py: all 5 tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
