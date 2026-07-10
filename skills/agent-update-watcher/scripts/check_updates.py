#!/usr/bin/env python3
# agent-update-watcher · version: 0.1.0
"""Watch the agent ecosystem (CLIs / plugins / skills) for updates, with a frequency guard (overhaul task 6).

Balances availability/recency against token+network cost: it only checks when the configured minimum interval
has elapsed, and it compares against a stored `current_version` so it reports ONLY what actually changed —
the agent then decides whether to adopt (LLM-as-component; the checking is deterministic code).

    check_updates.py --config sources.json [--state state.json] [--min-interval-days 7]
                     [--snapshot latest.json] [--force] [--now-days N]

`sources.json`: {"sources": [{"name": "...", "kind": "cli|plugin|skill", "current_version": "1.2.3", "url": "..."}]}
`--snapshot`  : {"<name>": "<latest_version>", ...} — supply latest versions WITHOUT network (used by tests and
                for a two-step "fetch then check" flow). Without it, no network fetch is attempted here (the
                real release-feed fetch is a thin wrapper left to the caller); missing latest => "unknown".
`--now-days`  : integer "today" (days since epoch) for deterministic tests; default = real today.
Exit 0 always (reporting tool). Prints one line per source with an update; a summary to stderr.
"""
import argparse
import datetime
import json
import os
import sys


def _today_days(args):
    if args.now_days is not None:
        return args.now_days
    return (datetime.date.today() - datetime.date(1970, 1, 1)).days


def _load(path, default):
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def main(argv=None):
    ap = argparse.ArgumentParser(prog="check_updates.py")
    ap.add_argument("--config", required=True)
    ap.add_argument("--state", default=None)
    ap.add_argument("--snapshot", default=None)
    ap.add_argument("--min-interval-days", type=int, default=7)
    ap.add_argument("--now-days", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    today = _today_days(args)
    state = _load(args.state, {})
    last = state.get("last_check_days")

    # Frequency guard: skip (cheap) unless forced or the interval has elapsed.
    if not args.force and last is not None and (today - last) < args.min_interval_days:
        print(f"[agent-update-watcher] skipped: checked {today - last}d ago (< {args.min_interval_days}d). Use --force to override.", file=sys.stderr)
        return 0

    cfg = _load(args.config, {"sources": []})
    latest_map = _load(args.snapshot, {})
    updates = []
    for s in cfg.get("sources", []):
        name = s.get("name", "")
        cur = str(s.get("current_version", ""))
        latest = str(latest_map.get(name, "")) if latest_map else ""
        if latest and latest != cur:
            updates.append((name, s.get("kind", ""), cur, latest, s.get("url", "")))

    for name, kind, cur, latest, url in updates:
        print(f"UPDATE\t{kind}\t{name}\t{cur} -> {latest}\t{url}")
    print(f"[agent-update-watcher] {len(updates)} update(s) of {len(cfg.get('sources', []))} source(s).", file=sys.stderr)

    # Record the check so the frequency guard works next time.
    if args.state:
        state["last_check_days"] = today
        with open(args.state, "w", encoding="utf-8") as f:
            json.dump(state, f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
