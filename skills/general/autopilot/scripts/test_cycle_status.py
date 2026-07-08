#!/usr/bin/env python3
"""Tests for cycle_status.py — the cross-midnight-safe cycle-completion check.
Run: python3 test_cycle_status.py"""
import datetime
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cycle_status  # noqa: E402


def ts(y, mo, d, h, mi):
    return datetime.datetime(y, mo, d, h, mi).timestamp()


passed = failed = 0


def chk(name, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print("  FAIL: %s (got %r want %r)" % (name, got, want))


T = tempfile.mkdtemp()
os.environ["HOME"] = T


def setup(proj, schedule, last_done, paused_until=None):
    d = os.path.join(T, ".claude", "autopilot", proj)
    os.makedirs(d, exist_ok=True)
    cs = {"schedule": schedule}
    if paused_until is not None:
        cs["paused_until"] = paused_until
    json.dump(cs, open(os.path.join(d, "cron_state.json"), "w"))
    p = os.path.join(d, "last-done")
    if last_done is None:
        if os.path.exists(p):
            os.remove(p)
    else:
        open(p, "w").write(str(int(last_done)))


def state(proj, now):
    r, code = cycle_status.compute(proj, now=now)
    return r["state"], code, r.get("overdue_min")


# 1. completed: cycle 22:00 day1, last_done 22:35 day1, now 22:40 day1
setup("p1", "0 22 * * *", ts(2026, 7, 1, 22, 35))
chk("completed -> complete", state("p1", ts(2026, 7, 1, 22, 40))[:2], ("complete", 0))

# 2. never done: last_done absent, now 22:50 (50 min past the 22:00 fire)
setup("p2", "0 22 * * *", None)
s, c, od = state("p2", ts(2026, 7, 1, 22, 50))
chk("never-done -> incomplete", (s, c), ("incomplete", 1))
chk("never-done overdue ~50min", od, 50)

# 3. CROSS-MIDNIGHT completion: schedule 23:00; run finished 00:30 next day; check at 00:40
setup("p3", "0 23 * * *", ts(2026, 7, 2, 0, 30))
chk("cross-midnight finish -> complete", state("p3", ts(2026, 7, 2, 0, 40))[:2], ("complete", 0))

# 4. CROSS-MIDNIGHT still-failed: schedule 23:00; last completion 2 nights ago; check 00:10 day2
setup("p4", "0 23 * * *", ts(2026, 6, 30, 23, 20))
s, c, od = state("p4", ts(2026, 7, 2, 0, 10))
chk("cross-midnight cycle unmet -> incomplete", (s, c), ("incomplete", 1))
chk("cross-midnight overdue ~70min (cycle=day1 23:00)", od, 70)

# 5. multi-fire "0,40 22": now 22:50, last_done 22:05 -> most recent fire 22:40, unmet
setup("p5", "0,40 22 * * *", ts(2026, 7, 1, 22, 5))
chk("multi-fire 2nd slot unmet -> incomplete", state("p5", ts(2026, 7, 1, 22, 50))[:2], ("incomplete", 1))

# 6. multi-fire "0,40 22": now 22:30 (before 22:40), last_done 22:05 -> cycle 22:00, met
setup("p6", "0,40 22 * * *", ts(2026, 7, 1, 22, 5))
chk("multi-fire 1st slot met -> complete", state("p6", ts(2026, 7, 1, 22, 30))[:2], ("complete", 0))

# 7. malformed/missing schedule falls back safely (no crash) -> some state returned
setup("p7", "", ts(2026, 7, 1, 22, 35))
r, _ = cycle_status.compute("p7", now=ts(2026, 7, 1, 22, 40))
chk("empty schedule falls back (22:00 default) -> complete", r["state"], "complete")

# 8. SKIP: paused_until = tomorrow -> today's cycle is skipped (state complete + skipped:true, exit 0)
setup("p8", "0 22 * * *", None, paused_until="2026-07-02")
r8, c8 = cycle_status.compute("p8", now=ts(2026, 7, 1, 22, 50))
chk("paused_until tomorrow -> skipped(complete)", (r8["state"], c8, r8.get("skipped")), ("complete", 0, True))

# 9. SKIP is EXCLUSIVE: paused_until == the cycle's own date -> that day RESUMES (not skipped)
setup("p9", "0 22 * * *", None, paused_until="2026-07-01")
r9, c9 = cycle_status.compute("p9", now=ts(2026, 7, 1, 22, 50))
chk("paused_until == cycle date -> resumes that day (not skipped)", (r9["state"], c9), ("incomplete", 1))

# 10. no paused_until -> normal behaviour (regression guard)
setup("p10", "0 22 * * *", None)
chk("no paused_until -> normal incomplete", state("p10", ts(2026, 7, 1, 22, 50))[:2], ("incomplete", 1))

shutil.rmtree(T, ignore_errors=True)
if failed == 0:
    print("cycle_status.py: all %d tests PASS" % passed)
else:
    print("cycle_status.py: %d FAIL / %d pass" % (failed, passed))
sys.exit(1 if failed else 0)
