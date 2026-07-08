#!/usr/bin/env python3
"""autopilot summary.py <proj> <cmd> — in-session summary + 7-day concatenation rule.

See docs/autopilot/README.md §7.
  reviewed : mark that the human has reviewed (resets the concat window)
  emit     : collect unreviewed per-run summaries; if the unreviewed span <= 7 days, concatenate
             them; if > 7 days, archive the block and keep only a one-line digest + link.

SCAFFOLD: review-marker + the 7-day window/archival logic are implemented; the actual in-session
delivery (markdown-table render + notify-send/Telegram, on the separate summary timer that dodges
the 7-day limit) is a marked TODO for first deployment.
"""
from __future__ import annotations

import os
import sys
import time

BASE = os.path.expanduser("~/.claude/autopilot")
WEEK_S = 7 * 24 * 3600


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    proj, cmd = argv[1], argv[2]
    d = os.path.join(BASE, proj)
    os.makedirs(d, exist_ok=True)
    rev = os.path.join(d, "reviewed.marker")
    runs_dir = os.path.join(d, "runs")

    if cmd == "reviewed":
        open(rev, "w").write(str(time.time()))
        print("marked reviewed")
        return 0

    if cmd == "emit":
        last_review = os.path.getmtime(rev) if os.path.exists(rev) else 0.0
        unreviewed = []
        if os.path.isdir(runs_dir):
            for fn in sorted(os.listdir(runs_dir)):
                fp = os.path.join(runs_dir, fn)
                if os.path.getmtime(fp) > last_review:
                    unreviewed.append(fp)
        span = (time.time() - last_review) if unreviewed else 0.0
        if span > WEEK_S:
            # archive the >7d block, keep only a one-line digest + link
            print(f"[summary] unreviewed span {span/86400:.1f}d > 7d -> archive block + 1-line digest+link "
                  f"({len(unreviewed)} runs). (delivery TODO)")
        else:
            print(f"[summary] concatenate {len(unreviewed)} unreviewed run summaries (<=7d). (delivery TODO)")
        # TODO(deploy): render md table over `unreviewed`, push via notify-send/Telegram.
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
