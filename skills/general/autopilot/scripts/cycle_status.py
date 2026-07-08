#!/usr/bin/env python3
"""
cycle_status.py <proj> — deterministic (NO-LLM, ~0 token) check of whether the current daily-run CYCLE
has completed. The keystone of autopilot's failure-recovery: watch.py, run.sh's idempotent guard, and
PROMPT.md all ask this one script "is this cycle already done?" instead of re-deriving it (or burning
tokens on the agent reasoning about dates).

CROSS-MIDNIGHT SAFE — this is the whole point. A "cycle" is identified by its scheduled fire TIMESTAMP,
never the calendar date. So a run that fires 23:00 and finishes 00:30 the next day still counts as
completing that 23:00 cycle (because last-done 00:30 >= cycle_ts 23:00). Comparing calendar dates would
wrongly call it a different day and trigger a bogus re-run.

Reads  ~/.claude/autopilot/<proj>/cron_state.json  ->  "schedule" (cron string, e.g. "0 22 * * *" or
                                                        "0,40 22 * * *")
       ~/.claude/autopilot/<proj>/last-done         ->  unix ts (int/float) of the last completed run

Prints one line of JSON:
  {"state":"complete"|"incomplete"|"unknown", "cycle_ts":<int>, "last_done":<int>, "overdue_min":<int>,
   "schedule":"..."}
  ("unknown" is emitted on a usage/validation error, or when no cycle time can be resolved.)
Exit code: 0 = complete, 1 = incomplete, 2 = unknown/error (fail-safe: callers treat non-0 as
"not known-complete", i.e. a run is allowed).

`now` is injected via $CYCLE_NOW (unix ts) for deterministic tests; otherwise time.time().
"""
import datetime
import json
import os
import sys
import time


def _now():
    v = os.environ.get("CYCLE_NOW")
    return float(v) if v else time.time()


def parse_fire_times(schedule):
    """autopilot schedules are DAILY: "M H * * *" or "M1,M2 H * * *". Return [(hour, minute), ...].
    Anything unparseable falls back to a single 22:00 fire (safe default)."""
    parts = (schedule or "").split()
    if len(parts) < 2:
        return [(22, 0)]
    mins, hours = parts[0], parts[1]
    out = []
    for h in hours.split(","):
        for m in mins.split(","):
            try:
                hi, mi = int(h), int(m)
            except ValueError:
                continue
            if 0 <= hi < 24 and 0 <= mi < 60:
                out.append((hi, mi))
    return out or [(22, 0)]


def most_recent_fire(fires, now):
    """The most recent scheduled fire timestamp <= now. Scans today AND yesterday so that in the small
    hours (or for a run that crossed midnight) we still resolve to the correct prior-evening cycle."""
    dt = datetime.datetime.fromtimestamp(now)
    cands = []
    for day_offset in (0, 1):
        day = dt.date() - datetime.timedelta(days=day_offset)
        for (h, m) in fires:
            ft = datetime.datetime(day.year, day.month, day.day, h, m).timestamp()
            if ft <= now:
                cands.append(ft)
    return max(cands) if cands else None


def compute(proj, now=None):
    if now is None:
        now = _now()
    base = os.path.expanduser("~/.claude/autopilot/%s" % proj)
    try:
        cs = json.load(open(os.path.join(base, "cron_state.json")))
    except Exception:
        cs = {}
    sched = cs.get("schedule", "0 22 * * *")
    paused_until = cs.get("paused_until", "")     # YYYY-MM-DD (exclusive): cycles before it are SKIPPED
    try:
        last_done = int(float(open(os.path.join(base, "last-done")).read().strip()))
    except Exception:
        last_done = 0
    fires = parse_fire_times(sched)
    cycle_ts = most_recent_fire(fires, now)
    if cycle_ts is None:
        return {"state": "unknown", "reason": "no-cycle", "schedule": sched}, 2
    # SKIP / PAUSE: a set paused_until makes the covered cycles count as done, so the run, the idempotent
    # guard, AND the watchdog all leave them alone (the cron may stay armed — a fired run self-skips at
    # step 0). paused_until is a date; any cycle whose scheduled fire is before 00:00 of that date is
    # skipped. (Set/cleared by skip.sh.)
    if paused_until:
        try:
            pu = datetime.datetime.strptime(paused_until[:10], "%Y-%m-%d").timestamp()
        except Exception:
            pu = 0.0
        if pu and cycle_ts < pu:
            return ({
                "state": "complete", "skipped": True, "paused_until": paused_until,
                "cycle_ts": int(cycle_ts), "last_done": last_done,
                "overdue_min": int((now - cycle_ts) / 60), "schedule": sched,
            }, 0)
    complete = last_done >= cycle_ts
    return ({
        "state": "complete" if complete else "incomplete",
        "cycle_ts": int(cycle_ts),
        "last_done": last_done,
        "overdue_min": int((now - cycle_ts) / 60),
        "schedule": sched,
    }, 0 if complete else 1)


def main(argv):
    if len(argv) < 2:
        print('{"state":"unknown","error":"usage: cycle_status.py <proj>"}')
        return 2
    proj = argv[1]
    if not proj or "/" in proj or ".." in proj:   # path-escape guard — proj is interpolated into a path,
        print('{"state":"unknown","error":"invalid proj"}')   # and run.sh/watch.py call this with it
        return 2
    result, code = compute(proj)
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
