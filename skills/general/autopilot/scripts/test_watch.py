#!/usr/bin/env python3
"""Tests for watch.py detection logic (addresses the gui-design review's test-gap).
Mocks heartbeat / last-done mtimes under a temp BASE. Run: python3 test_watch.py"""
import importlib.util
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("watch", os.path.join(HERE, "watch.py"))
watch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(watch)


def _setup(tmp, proj, hb_age=None, done_age=None, err_age=None):
    d = os.path.join(tmp, proj)
    os.makedirs(d, exist_ok=True)
    now = time.time()
    for name, age in (("heartbeat", hb_age), ("last-done", done_age), ("last-error", err_age)):
        if age is not None:
            p = os.path.join(d, name)
            open(p, "w").write("x")
            os.utime(p, (now - age, now - age))
    return d


def run():
    with tempfile.TemporaryDirectory() as tmp:
        watch.BASE = tmp
        d1 = _setup(tmp, "p1")  # no heartbeat -> healthy/idle
        assert watch.main(["watch", "p1"]) == 0
        assert not os.path.exists(os.path.join(d1, "watch.log")), "no-hb must not log STUCK"

        d2 = _setup(tmp, "p2", hb_age=60)  # fresh heartbeat -> healthy
        assert watch.main(["watch", "p2"]) == 0
        assert not os.path.exists(os.path.join(d2, "watch.log")), "fresh hb is healthy"

        d3 = _setup(tmp, "p3", hb_age=watch.STUCK_AFTER_S + 60)  # stale, no done -> STUCK
        assert watch.main(["watch", "p3"]) == 0
        assert os.path.exists(os.path.join(d3, "watch.log")), "stale hb must log STUCK"
        assert os.path.exists(os.path.join(d3, "playbook.jsonl")), "stale hb must record a problem"

        d4 = _setup(tmp, "p4", hb_age=watch.STUCK_AFTER_S + 60, done_age=1)  # finished
        assert watch.main(["watch", "p4"]) == 0
        assert not os.path.exists(os.path.join(d4, "watch.log")), "fresh done = finished, not stuck"

        # 6. FAILED/EMPTY run: last-error fresh + newer than last-done -> flagged loudly (not "stuck")
        d5 = _setup(tmp, "p5", hb_age=watch.STUCK_AFTER_S + 60, done_age=3600, err_age=60)
        assert watch.main(["watch", "p5"]) == 0
        log5 = os.path.join(d5, "watch.log")
        assert os.path.exists(log5) and "FAILED/EMPTY RUN" in open(log5).read(), "fresh last-error must flag failed run"
        assert os.path.exists(os.path.join(d5, "playbook.jsonl")), "failed run must record a problem"

        # 7. recovered: an OLD last-error followed by a FRESH last-done -> NOT flagged
        d6 = _setup(tmp, "p6", hb_age=watch.STUCK_AFTER_S + 60, done_age=60, err_age=7200)
        assert watch.main(["watch", "p6"]) == 0
        assert not os.path.exists(os.path.join(d6, "watch.log")), "old error + fresh done = healthy, no flag"

        assert watch.main(["watch", "../etc"]) == 2, "proj guard must reject path escape"
    print("watch.py: all 7 tests PASS")
    return 0


if __name__ == "__main__":
    sys.exit(run())
