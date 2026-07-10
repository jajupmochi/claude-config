#!/usr/bin/env python3
"""Tests for check_updates.py (agent-update-watcher). Run: python3 test_check_updates.py"""
import importlib.util
import io
import json
import os
import tempfile
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("cu", os.path.join(HERE, "check_updates.py"))
cu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cu)


def _run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cu.main(argv)
    return rc, out.getvalue(), err.getvalue()


def _write(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def run():
    with tempfile.TemporaryDirectory() as d:
        cfg = os.path.join(d, "sources.json")
        snap = os.path.join(d, "latest.json")
        state = os.path.join(d, "state.json")
        _write(cfg, {"sources": [
            {"name": "claude-code", "kind": "cli", "current_version": "2.1.0", "url": "u1"},
            {"name": "some-plugin", "kind": "plugin", "current_version": "1.0.0", "url": "u2"},
            {"name": "steady", "kind": "skill", "current_version": "3.3.3", "url": "u3"},
        ]})
        _write(snap, {"claude-code": "2.2.0", "some-plugin": "1.0.0", "steady": "3.3.3"})

        # 1. reports ONLY the source whose latest != current
        rc, out, err = _run(["--config", cfg, "--snapshot", snap, "--state", state, "--now-days", "20000"])
        assert rc == 0
        lines = [ln for ln in out.strip().splitlines() if ln.startswith("UPDATE")]
        assert len(lines) == 1, f"one update, got {lines}"
        assert "claude-code" in lines[0] and "2.1.0 -> 2.2.0" in lines[0]
        assert "1 update(s) of 3 source(s)" in err

        # 2. frequency guard: a second check the SAME day is skipped (state was written)
        rc, out, err = _run(["--config", cfg, "--snapshot", snap, "--state", state, "--now-days", "20000"])
        assert "skipped" in err and out.strip() == "", "same-day re-check skipped"

        # 3. after the interval elapses, it checks again
        rc, out, err = _run(["--config", cfg, "--snapshot", snap, "--state", state,
                             "--now-days", "20010", "--min-interval-days", "7"])
        assert "skipped" not in err and out.strip() != "", "checks again after interval"

        # 4. --force overrides the guard even within the interval
        rc, out, err = _run(["--config", cfg, "--snapshot", snap, "--state", state,
                             "--now-days", "20010", "--force"])
        assert "skipped" not in err

        # 5. no snapshot -> no false "update" (latest unknown, nothing reported)
        rc, out, err = _run(["--config", cfg, "--now-days", "30000"])
        assert out.strip() == "" and "0 update(s)" in err

        # 6. empty/missing config -> graceful
        rc, out, err = _run(["--config", os.path.join(d, "nope.json"), "--now-days", "30001"])
        assert rc == 0 and "0 update(s) of 0 source(s)" in err

    print("check_updates.py: all 6 tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
