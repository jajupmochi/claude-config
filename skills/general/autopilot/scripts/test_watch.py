#!/usr/bin/env python3
"""Tests for watch.py detection logic (addresses the gui-design review's test-gap).
Mocks heartbeat / last-done mtimes under a temp BASE. Run: python3 test_watch.py"""
import datetime
import importlib.util
import json
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
    print("watch.py: all 7 legacy tests PASS")
    return 0


def _ts(y, mo, d, h, mi):
    return datetime.datetime(y, mo, d, h, mi).timestamp()


def _cyc_setup(home, proj, sid, schedule, last_done, now,
               transcript_age=None, hb=None, attempts=None):
    ad = os.path.join(home, ".claude", "autopilot", proj)
    os.makedirs(ad, exist_ok=True)
    json.dump({"home_session_id": sid, "schedule": schedule},
              open(os.path.join(ad, "cron_state.json"), "w"))
    open(os.path.join(ad, "last-done"), "w").write(str(int(last_done)))
    if transcript_age is not None:                       # home-session transcript mtime = now - age
        pd = os.path.join(home, ".claude", "projects", "proj-x")
        os.makedirs(pd, exist_ok=True)
        tp = os.path.join(pd, sid + ".jsonl")
        open(tp, "w").write("{}")
        os.utime(tp, (now - transcript_age, now - transcript_age))
    if hb is not None:                                   # hb = (cycle_ts, age_seconds)
        open(os.path.join(ad, "run-heartbeat"), "w").write(f"{hb[0]} {now - hb[1]}")
    if attempts is not None:                             # attempts = (cycle_ts, n)
        json.dump({"cycle_ts": attempts[0], "attempts": attempts[1]},
                  open(os.path.join(ad, "recover-state.json"), "w"))
    return ad


def run_cycle():
    """Tests for the in-session cycle-recovery decision (should_recover_cycle) — the two-signal liveness."""
    fails = [0]

    def chk(name, got, want):
        if got != want:
            fails[0] += 1
            print(f"  FAIL: {name} (got {got!r} want {want!r})")

    with tempfile.TemporaryDirectory() as home:
        os.environ["HOME"] = home
        watch.BASE = os.path.join(home, ".claude", "autopilot")
        cyc22 = int(_ts(2026, 7, 1, 22, 0))              # the 22:00 cycle_ts
        now = _ts(2026, 7, 1, 23, 0)                     # 60 min past the 22:00 fire
        os.environ["CYCLE_NOW"] = str(now)

        def decide(proj):
            return watch.should_recover_cycle(proj, now)[:2]

        _cyc_setup(home, "cA", "sidA", "0 22 * * *", _ts(2026, 7, 1, 22, 40), now, transcript_age=1800)
        chk("complete -> no recover", decide("cA"), (False, "complete"))

        nowB = _ts(2026, 7, 1, 22, 10)
        os.environ["CYCLE_NOW"] = str(nowB)
        _cyc_setup(home, "cB", "sidB", "0 22 * * *", 0, nowB, transcript_age=60)
        chk("within-grace -> no recover", watch.should_recover_cycle("cB", nowB)[:2], (False, "within-grace"))
        os.environ["CYCLE_NOW"] = str(now)

        _cyc_setup(home, "cC", "sidC", "0 22 * * *", 0, now, transcript_age=300)
        chk("transcript-fresh -> alive", decide("cC"), (False, "alive"))

        _cyc_setup(home, "cD", "sidD", "0 22 * * *", 0, now, transcript_age=1800, hb=(cyc22, 60))
        chk("hb-fresh-this-cycle -> alive", decide("cD"), (False, "alive"))

        _cyc_setup(home, "cE", "sidE", "0 22 * * *", 0, now, transcript_age=1800)
        chk("dead (frozen, no hb) -> recover", decide("cE")[0], True)

        _cyc_setup(home, "cF", "sidF", "0 22 * * *", 0, now, transcript_age=2700, hb=(cyc22, 60))
        chk("frozen-hard beats zombie hb -> recover", decide("cF")[0], True)

        _cyc_setup(home, "cG", "sidG", "0 22 * * *", 0, now, transcript_age=1800, attempts=(cyc22, 3))
        chk("cap-reached -> no recover", decide("cG"), (False, "cap-reached"))

        _cyc_setup(home, "cH", "sidH", "0 22 * * *", 0, now, transcript_age=1800, hb=(cyc22 - 99999, 60))
        chk("wrong-cycle hb treated stale -> recover", decide("cH")[0], True)

        _cyc_setup(home, "cI", "sidI", "0 22 * * *", _ts(2026, 7, 1, 22, 40), now, transcript_age=1800)
        watch.main(["watch", "cI"])
        chk("main() complete cycle -> no recovery log",
            os.path.exists(os.path.join(home, ".claude", "autopilot", "cI", "watch.log")), False)

    os.environ.pop("CYCLE_NOW", None)
    if fails[0] == 0:
        print("watch.py cycle-recovery: all 9 checks PASS")
    return fails[0]


if __name__ == "__main__":
    rc = run()
    rc += run_cycle()
    sys.exit(1 if rc else 0)
