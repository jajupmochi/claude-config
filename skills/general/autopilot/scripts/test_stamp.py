#!/usr/bin/env python3
# autopilot-stamp · version: 0.1.0 · created: 2026-06-24 · updated: 2026-06-24
"""Tests for stamp.py (date+version stamping of generated artifacts). Run: python3 test_stamp.py"""
import datetime
import importlib.util
import os
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("stamp", os.path.join(HERE, "stamp.py"))
stamp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stamp)


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def run():
    with tempfile.TemporaryDirectory() as tmp:
        # 1. unstamped, undated doc -> check flags both reasons, exit 1
        f = os.path.join(tmp, "notes.md")
        open(f, "w").write("# Notes\n\nbody\n")
        # created is back-filled from the file's mtime (notes.md has no date-in-name); pin the mtime to a
        # fixed day so the "2026-06-24" assertions below are deterministic instead of "whatever today is".
        _pin = datetime.datetime(2026, 6, 24, 12, 0).timestamp()
        os.utime(f, (_pin, _pin))
        assert stamp.main(["stamp", "check", tmp]) == 1, "unstamped must flag"
        assert not stamp.has_stamp(f) and stamp.needs_filename_date(f)

        # 2. apply: adds frontmatter; created from mtime/date, version 0.1.0, body preserved
        stamp.apply(f, "comparison", "2026-06-24", None)
        fm, body = stamp._split_fm(_read(f))
        assert stamp._get(fm, "autopilot_doc") == "comparison"
        assert stamp._get(fm, "version") == "0.1.0"
        assert stamp._get(fm, "created") == "2026-06-24"
        assert stamp._get(fm, "updated") == "2026-06-24"
        assert "body" in body and "# Notes" in body, "body must survive"

        # 3. re-apply later with --bump minor: created sticky, updated advances, version bumps
        stamp.apply(f, None, "2026-06-25", "minor")
        fm, _ = stamp._split_fm(_read(f))
        assert stamp._get(fm, "created") == "2026-06-24", "created is set-once"
        assert stamp._get(fm, "updated") == "2026-06-25"
        assert stamp._get(fm, "version") == "0.2.0", f"minor bump, got {stamp._get(fm,'version')}"

        # 4. existing non-managed frontmatter keys are preserved
        g = os.path.join(tmp, "report-2026-06-24.md")
        open(g, "w").write("---\ntitle: Q3\nowner: kaspar\n---\nstuff\n")
        stamp.apply(g, "time", "2026-06-24", None)
        fm, body = stamp._split_fm(_read(g))
        assert stamp._get(fm, "title") == "Q3" and stamp._get(fm, "owner") == "kaspar", "preserve other keys"
        assert stamp._get(fm, "autopilot_doc") == "time" and "stuff" in body

        # 5. a dated, stamped file is clean; check over just it exits 0
        assert stamp.main(["stamp", "check", g]) == 0, "stamped+dated file is clean"
        # ...but the still-undated notes.md keeps it flagged at dir level
        assert stamp.main(["stamp", "check", tmp]) == 1

        # 6. rolling docs (plan.md) need a stamp but NOT a date-in-name
        plan = os.path.join(tmp, "plan.md")
        open(plan, "w").write("# Plan\n")
        assert stamp.needs_filename_date(plan) is False, "rolling plan.md exempt from date-in-name"
        stamp.apply(plan, "plan", "2026-06-24", None)
        assert stamp.main(["stamp", "check", plan]) == 0

        # 7. newname: type-prefixed; daily-run is bare date; --time suffix; + version bump arithmetic
        assert stamp._newname("daily-run", "2026-06-24") == "2026-06-24", "daily-run is bare date"
        assert stamp._newname("time", "2026-06-24") == "time-2026-06-24", "others type-prefixed"
        assert stamp._newname("comparison", "2026-06-24", "1530") == "comparison-2026-06-24_1530", "--time suffix"
        assert stamp._bump("1.2.9", "patch") == "1.2.10"
        assert stamp._bump("1.2.9", "minor") == "1.3.0"
        assert stamp._bump("1.2.9", "major") == "2.0.0"
    print("stamp.py: all 7 tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
