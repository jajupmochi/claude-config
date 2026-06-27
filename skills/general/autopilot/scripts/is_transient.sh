#!/usr/bin/env bash
# autopilot/is_transient.sh <logfile> — exit 0 if the run's tail shows a TRANSIENT server-side throttle
# (Anthropic rate-limit / overload / HTTP 529 — NOT the user's usage cap, NOT a real failure), i.e. a
# retryable blip. Exit 1 otherwise. Shared by run.sh (backoff-retry) and watch.py (label RETRYABLE).
log="${1:?usage: is_transient.sh <logfile>}"
[ -f "$log" ] || exit 1
tail -10 "$log" 2>/dev/null | grep -qiE \
  'temporarily limiting requests|rate.?limit|overloaded_error|\bOverloaded\b|server is (temporarily )?(busy|overloaded)|status code 529|HTTP 529'
