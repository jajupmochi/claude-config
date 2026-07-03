#!/usr/bin/env python3
"""autopilot watch.py <proj> — watchdog (Ralph-loop). Runs every ~10 min (systemd timer).

Detects a stuck / crashed / paused / failed daily run and self-heals; records every problem + the fix
that worked into the playbook for reuse. See docs/autopilot/README.md §4.

Two detection regimes:
  * IN-SESSION cycle recovery (PR #10 model, the default): the daily run fires inside the user's always-open
    session, so there is NO run.sh wrapper and NONE of its signals (last-error / heartbeat) get written.
    Instead we ask cycle_status.py "did THIS cycle complete?" and, if not, judge liveness from TWO signals
    — the home session's transcript mtime (primary; can't zombie) and run-heartbeat from hb_loop.sh
    (secondary; covers a quiet stretch such as a long subagent). If the cycle is overdue AND the run is not
    alive (died on an API error or anything else), spawn a DETACHED headless run.sh to finish the work —
    run.sh has the idempotent guard (skips if the cycle completed meanwhile) + the is_transient backoff.
    Capped at RECOVER_CAP spawns per cycle, then escalate. This whole path is code-only (~0 token).
  * LEGACY run.sh signals (only when a project is actually driven by headless run.sh): last-error newer
    than last-done => failed/empty run; stale heartbeat => stuck. Preserved unchanged below; it only runs
    for projects that have NO cron_state.json (i.e. not an in-session deployment).
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time

BASE = os.path.expanduser("~/.claude/autopilot")
STUCK_AFTER_S = 20 * 60          # (legacy) no run.sh heartbeat for > ~2 watch intervals => stuck
ESCALATE_AFTER = 3               # consecutive failed recovery attempts => notify human

# --- in-session cycle-recovery thresholds ---
GRACE_S = 15 * 60                # don't even consider recovery until this long past the scheduled fire
ALIVE_TRANSCRIPT_S = 15 * 60     # home transcript advanced within this => run is ALIVE (primary signal)
HB_FRESH_S = 12 * 60             # run-heartbeat this fresh AND for THIS cycle => alive (secondary signal)
FREEZE_HARD_S = 40 * 60          # transcript frozen this long => DEAD even if a (zombie) heartbeat is fresh
RECOVER_CAP = 3                  # max headless recovery spawns per cycle, then escalate + stop


def _log(d: str, msg: str) -> None:
    with open(os.path.join(d, "watch.log"), "a") as f:
        f.write(f"{time.strftime('%F %T')} {msg}\n")


def _record_problem(d: str, sig: str, ctx: str, fix: str = "") -> None:
    with open(os.path.join(d, "playbook.jsonl"), "a") as f:
        f.write(json.dumps({"ts": time.time(), "sig": sig, "ctx": ctx, "fix": fix}) + "\n")


# ---------- in-session cycle recovery (deterministic, testable) ----------

def _cycle_status(proj: str) -> dict | None:
    """Parsed cycle_status.py output for proj (schedule + last-done -> complete/incomplete + cycle_ts)."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cycle_status.py")
    try:
        out = subprocess.run([sys.executable, p, proj], capture_output=True, text=True, timeout=20)
        return json.loads(out.stdout.strip())
    except Exception:
        return None


def _home_transcript_mtime(proj: str) -> float:
    """Newest mtime of the home session's OWN transcript jsonl (looked up via home_session_id). 0 if
    unknown. Deliberately NOT the whole project dir — a *different* session sharing the cwd must not mask
    this run's silence."""
    try:
        sid = json.load(open(os.path.join(BASE, proj, "cron_state.json"))).get("home_session_id", "")
    except Exception:
        sid = ""
    if not sid:
        return 0.0
    hits = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}.jsonl"))
    return max((os.path.getmtime(h) for h in hits), default=0.0)


def _read_run_heartbeat(proj: str):
    """(cycle_ts:int, ts:float) from run-heartbeat, or None."""
    try:
        parts = open(os.path.join(BASE, proj, "run-heartbeat")).read().split()
        return int(parts[0]), float(parts[1])
    except Exception:
        return None


def _recover_attempts(proj: str, cycle_ts) -> int:
    """Headless recoveries already spawned for THIS cycle (auto-resets when cycle_ts changes)."""
    try:
        st = json.load(open(os.path.join(BASE, proj, "recover-state.json")))
        return int(st.get("attempts", 0)) if st.get("cycle_ts") == cycle_ts else 0
    except Exception:
        return 0


def _bump_recover_attempts(proj: str, cycle_ts) -> int:
    n = _recover_attempts(proj, cycle_ts) + 1
    try:
        json.dump({"cycle_ts": cycle_ts, "attempts": n, "ts": time.time()},
                  open(os.path.join(BASE, proj, "recover-state.json"), "w"))
    except Exception:
        pass
    return n


def _recovery_running(proj: str) -> bool:
    """A headless run.sh recovery for this proj is already in flight — never stack a second. The pattern is
    anchored to the exact proj arg ('run.sh <proj>' followed by end-of-cmdline or a space) so a project
    whose name is a prefix of another (e.g. 'creuset' vs 'creuset-docs') can't false-match."""
    try:
        r = subprocess.run(["pgrep", "-f", rf"run\.sh {proj}($| )"], capture_output=True)
        return r.returncode == 0
    except Exception:
        return False


def _liveness(proj: str, now: float, cycle_ts):
    """(alive, transcript_age_s, hb_fresh_this_cycle). Transcript mtime is primary (cannot zombie); the
    heartbeat extends 'alive' through a quiet stretch (long subagent) but only until the transcript has
    been frozen past FREEZE_HARD_S — so a zombie heartbeat can delay recovery by at most that window."""
    tr_age = now - _home_transcript_mtime(proj)
    hb = _read_run_heartbeat(proj)
    hb_fresh = bool(hb and hb[0] == cycle_ts and (now - hb[1]) < HB_FRESH_S)
    alive = (tr_age < ALIVE_TRANSCRIPT_S) or (hb_fresh and tr_age < FREEZE_HARD_S)
    return alive, tr_age, hb_fresh


def should_recover_cycle(proj: str, now: float):
    """Deterministic decision (NO side effects) -> (recover: bool, reason: str, cycle_ts). Any failure
    cause is treated the same: the only question is 'is this cycle overdue AND the run not alive?'."""
    cyc = _cycle_status(proj)
    if not cyc or cyc.get("state") == "unknown":
        return False, "no-cycle-info", None
    cycle_ts = cyc.get("cycle_ts")
    if cyc.get("state") == "complete":
        return False, "complete", cycle_ts
    if cyc.get("overdue_min", 0) * 60 < GRACE_S:
        return False, "within-grace", cycle_ts
    alive, tr_age, hb_fresh = _liveness(proj, now, cycle_ts)
    if alive:
        return False, "alive", cycle_ts
    if _recovery_running(proj):
        return False, "recovery-already-running", cycle_ts
    if _recover_attempts(proj, cycle_ts) >= RECOVER_CAP:
        return False, "cap-reached", cycle_ts
    return True, "dead: incomplete+overdue+idle (tr_age=%.0fm hb_fresh=%s)" % (tr_age / 60, hb_fresh), cycle_ts


def _spawn_recovery(d: str, proj: str) -> None:
    """Launch a DETACHED headless run.sh to finish the cycle (idempotent-guarded + is_transient backoff)."""
    run = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.sh")
    if not os.path.exists(run):
        _log(d, "recovery: run.sh not found — cannot respawn")
        return
    try:
        subprocess.Popen(["bash", run, proj], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    except Exception as e:  # noqa: BLE001
        _log(d, f"recovery: spawn failed: {e}")


def _cycle_recover(d: str, proj: str) -> bool:
    """In-session recovery path. Returns True if it handled this tick (skip the legacy path)."""
    recover, reason, cycle_ts = should_recover_cycle(proj, time.time())
    if reason == "cap-reached":
        _log(d, f"cycle {cycle_ts}: recovery cap ({RECOVER_CAP}) reached — escalating, not respawning")
        _record_problem(d, "recover_cap", f"cycle {cycle_ts} hit {RECOVER_CAP} recoveries")
        return True
    if recover:
        n = _bump_recover_attempts(proj, cycle_ts)
        _log(d, f"cycle {cycle_ts}: {reason} — spawning headless run.sh recovery ({n}/{RECOVER_CAP})")
        _record_problem(d, "cycle_recovery", reason, fix=f"headless run.sh attempt {n}")
        _spawn_recovery(d, proj)
        return True
    return False


# ---------- legacy run.sh-signal detection (only for non-in-session projects) ----------

def _legacy_run_sh_checks(d: str) -> int:
    hb = os.path.join(d, "heartbeat")
    done = os.path.join(d, "last-done")
    err = os.path.join(d, "last-error")
    if os.path.exists(err):
        done_t = os.path.getmtime(done) if os.path.exists(done) else 0.0
        err_age = time.time() - os.path.getmtime(err)
        if os.path.getmtime(err) >= done_t and err_age < 26 * 3600:
            kind, sig = "FAILED/EMPTY RUN", "failed_run"
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
    return 0


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
    # In-session deployments have a cron_state.json (home session + schedule). For those, the cycle path is
    # authoritative and run.sh signals are absent, so handle recovery there and skip the legacy checks.
    if os.path.exists(os.path.join(d, "cron_state.json")):
        if _cycle_recover(d, proj):
            return 0
        return 0
    return _legacy_run_sh_checks(d)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
