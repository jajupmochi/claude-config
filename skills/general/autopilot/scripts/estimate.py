#!/usr/bin/env python3
"""autopilot estimate.py — formal, numeric project time estimation (no guessing).

Implements the model from docs/autopilot/README.md §5:
  - PERT 3-point:    tE = (O + 4M + P)/6 ,  sigma = (P - O)/6
  - agent-rounds:    minutes = rounds * sec_per_round * risk / 60   (avoids human-time anchoring)
  - Monte-Carlo:     roll a target up over historical per-period throughput -> P50/P85/P95 periods
  - calibration:     `log` appends {category, estimate, actual, ai_s, human_s, human_kind, rounds_*}
                     and `coeff` reports per-category actual/estimate ratios to correct future estimates.

SCAFFOLD: formulas + calibration store are real + tested; the team-report doc renderer is a TODO.

Usage:
  estimate.py pert O M P
  estimate.py rounds N SEC_PER_ROUND RISK
  estimate.py mc HISTORY.json TARGET            # HISTORY = JSON list of per-period throughput
  estimate.py log <proj> '<json record>'
  estimate.py coeff <proj>
"""
from __future__ import annotations

import json
import os
import random
import statistics
import sys

BASE = os.path.expanduser("~/.claude/autopilot")


def pert(o: float, m: float, p: float) -> tuple[float, float]:
    return (o + 4 * m + p) / 6.0, (p - o) / 6.0


def rounds_minutes(n: float, sec_per_round: float, risk: float) -> float:
    return n * sec_per_round * risk / 60.0


def monte_carlo(history: list[float], target: float, trials: int = 10000) -> dict:
    samples = [s for s in history if s > 0] or [1.0]
    res = []
    for _ in range(trials):
        done = 0.0
        k = 0
        while done < target and k < 100000:
            done += random.choice(samples)
            k += 1
        res.append(k)
    res.sort()
    pick = lambda q: res[min(len(res) - 1, int(len(res) * q))]  # noqa: E731
    return {"p50": pick(0.50), "p85": pick(0.85), "p95": pick(0.95),
            "mean_periods": round(statistics.mean(res), 2)}


def _store(proj: str) -> str:
    d = os.path.join(BASE, proj)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "estimates.jsonl")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "pert":
        te, sd = pert(*map(float, argv[2:5]))
        print(f"tE={te:.2f} sigma={sd:.2f}")
        return 0
    if cmd == "rounds":
        print(f"{rounds_minutes(float(argv[2]), float(argv[3]), float(argv[4])):.1f} min")
        return 0
    if cmd == "mc":
        hist = json.load(open(argv[2]))
        print(json.dumps(monte_carlo(hist, float(argv[3])), ensure_ascii=False))
        return 0
    if cmd == "log":
        with open(_store(argv[2]), "a") as f:
            f.write(json.dumps(json.loads(argv[3]), ensure_ascii=False) + "\n")
        print("logged")
        return 0
    if cmd == "coeff":
        p = _store(argv[2])
        cats: dict[str, list[float]] = {}
        if os.path.exists(p):
            for line in open(p):
                try:
                    r = json.loads(line)
                    if r.get("estimate"):
                        cats.setdefault(r.get("category", "?"), []).append(r["actual"] / r["estimate"])
                except Exception:  # noqa: BLE001
                    pass
        out = {c: round(statistics.mean(v), 3) for c, v in cats.items()}
        print(json.dumps(out, ensure_ascii=False) or "{}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
