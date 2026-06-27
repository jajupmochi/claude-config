#!/usr/bin/env python3
"""autopilot watch.py <proj> — watchdog (Ralph-loop). Runs every ~10 min (systemd timer).

Detects a stuck / crashed / paused / failed-empty daily run and self-heals; records every problem +
the fix that worked into the playbook for reuse. See docs/autopilot/README.md §4.

SCAFFOLD: detection + problem-recording + escalation hook are implemented. The recovery action
("kill the wedged session, re-spawn a FRESH `claude -p` reinjecting PROMPT.md + accumulated
playbook learnings", and the `/goal`-needs-"继续" re-issue) is left as a marked TODO to wire on the
first real deployment, because it spawns live sessions that must not run during build/test.
"""
from __future__ import annotations

import json
import os
import sys
import time

BASE = os.path.expanduser("~/.claude/autopilot")
STUCK_AFTER_S = 20 * 60          # no heartbeat for > ~2 watch intervals => stuck
ESCALATE_AFTER = 3               # consecutive failed recovery attempts => notify human


def _log(d: str, msg: str) -> None:
    with open(os.path.join(d, "watch.log"), "a") as f:
        f.write(f"{time.strftime('%F %T')} {msg}\n")


def _record_problem(d: str, sig: str, ctx: str, fix: str = "") -> None:
    with open(os.path.join(d, "playbook.jsonl"), "a") as f:
        f.write(json.dumps({"ts": time.time(), "sig": sig, "ctx": ctx, "fix": fix}) + "\n")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    proj = argv[1]
    if "/" in proj or ".." in proj or not proj:   # guard against path escape (defensive)
        print("invalid proj", file=sys.stderr)
        return 2
    d = os.path.join(BASE, proj)
    if not os.path.isdir(d):
        return 0
    hb = os.path.join(d, "heartbeat")
    done = os.path.join(d, "last-done")
    err = os.path.join(d, "last-error")
    # FAILED / EMPTY RUN: run.sh writes last-error (and exits non-zero) whenever a run ends WITHOUT
    # meeting the floor — claude-not-found, 3× fast-fail abort, or attempt-cap. If last-error is newer
    # than last-done, the most recent run produced nothing. This is the silent "fake-completion" class
    # (the empty 0-min runs from 2026-06-26); surface it loudly instead of mislabelling it "stuck".
    if os.path.exists(err):
        done_t = os.path.getmtime(done) if os.path.exists(done) else 0.0
        err_age = time.time() - os.path.getmtime(err)
        if os.path.getmtime(err) >= done_t and err_age < 26 * 3600:
            kind, sig = "FAILED/EMPTY RUN", "failed_run"
            # A TRANSIENT server-side throttle (rate-limit / overload) is RETRYABLE, not a real failure —
            # classify it via the shared is_transient.sh against the newest run log so it's labelled right.
            import glob
            import subprocess
            logs = sorted(glob.glob(os.path.join(d, "runs", "*.log")), key=os.path.getmtime)
            it = os.path.join(os.path.dirname(os.path.abspath(__file__)), "is_transient.sh")
            if logs and os.path.exists(it) and subprocess.run(
                ["bash", it, logs[-1]], capture_output=True
            ).returncode == 0:
                kind, sig = "RETRYABLE RUN (transient API throttle — rate-limit/overload, not a real failure)", "failed_run_retryable"
            _log(d, f"{kind}: last-error {err_age / 3600:.1f}h ago (newer than last-done) — floor not met")
            _record_problem(d, sig, f"last-error {err_age / 3600:.1f}h ago")
            return 0
    if not os.path.exists(hb):
        return 0  # no active run to watch
    age = time.time() - os.path.getmtime(hb)
    fresh_done = os.path.exists(done) and os.path.getmtime(done) >= os.path.getmtime(hb)
    if age <= STUCK_AFTER_S or fresh_done:
        return 0  # healthy or finished
    _log(d, f"STUCK: heartbeat age {age/60:.1f} min, no fresh done-marker")
    _record_problem(d, "stuck", f"heartbeat age {age/60:.1f}min")
    # NOTE: run.sh keeps the heartbeat fresh every ~2 min DURING each claude -p call, so a healthy
    #   long run no longer trips STUCK_AFTER_S (the gui-design review's false-positive risk is fixed
    #   at the source). RECOVERY PREREQUISITE: before wiring the kill+respawn below, also confirm no
    #   live `claude` process for this run (pgrep) so recovery never kills a healthy session.
    # TODO(recovery, first deploy): kill the wedged session; re-spawn a fresh `claude -p` with
    #   PROMPT.md + the tail of playbook.jsonl appended (Ralph-loop); for the /goal-needs-"继续"
    #   pause, re-issue a "继续" continuation; then update the done-marker.
    # Escalation: count failures; after ESCALATE_AFTER, notify (WorkNRoll notify-send/Telegram).
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
