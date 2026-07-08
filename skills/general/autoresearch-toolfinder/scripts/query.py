#!/usr/bin/env python3
"""Search the local autoresearch tool index and print ONLY the top matches.

Token-efficient: never dumps the whole catalog into context. An agent runs this with
keywords from the user's task and reads back a handful of candidates.

Usage:
    query.py "<keywords>" [--source alvinreal|yibie] [--category SUBSTR] [--limit N] [--json]
    query.py "" --category Finance          # browse a section
    query.py --list-categories              # show available categories + counts
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")


def load() -> dict:
    p = os.path.join(DATA, "index.json")
    if not os.path.exists(p):
        print("Index not built. Run: python3 scripts/update_index.py", file=sys.stderr)
        sys.exit(2)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def staleness() -> str:
    sp = os.path.join(DATA, "state.json")
    if not os.path.exists(sp):
        return ""
    try:
        with open(sp, encoding="utf-8") as f:
            st = json.load(f)
        oldest = min(dt.datetime.fromisoformat(s["synced_at"]) for s in st["sources"].values())
        days = (dt.datetime.now(dt.timezone.utc) - oldest).days
        if days >= 30:
            return f"  (index {days}d old — consider scripts/update_index.py)"
    except Exception:  # noqa: BLE001
        pass
    return ""


def score(e: dict, terms: list[str]) -> int:
    name, cat, desc = e["name"].lower(), e["category"].lower(), e["desc"].lower()
    blob = f"{name} {cat} {desc}"
    sc = 0
    for t in terms:
        if t in name:
            sc += 4
        if t in cat:
            sc += 2
        sc += blob.count(t)
    return sc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("query", nargs="*")
    ap.add_argument("--source")
    ap.add_argument("--category")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list-categories", action="store_true")
    ap.add_argument("--include-discussions", action="store_true",
                    help="include discussion/news/writeup entries (excluded by default; they are not tools)")
    a = ap.parse_args()

    idx = load()
    entries = idx["entries"]

    if a.list_categories:
        counts: dict[tuple[str, str], int] = {}
        for e in entries:
            counts[(e["source"], e["category"])] = counts.get((e["source"], e["category"]), 0) + 1
        for (src, cat), n in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            print(f"{n:4d}  {src:9s}  {cat}")
        return 0

    if a.source:
        entries = [e for e in entries if e["source"] == a.source]
    if a.category:
        entries = [e for e in entries if a.category.lower() in e["category"].lower()]
    elif not a.include_discussions:
        # Exclude non-tool entries (X threads, Reddit, news, blog writeups) by default.
        noise = ("related practices", "notable use case")
        entries = [e for e in entries if not any(m in e["category"].lower() for m in noise)]

    terms = [w.lower() for t in a.query for w in t.split() if w.strip()]
    if terms:
        scored = [(score(e, terms), e) for e in entries]
        scored = [x for x in scored if x[0] > 0]
        scored.sort(key=lambda x: -x[0])
        res = [e for _, e in scored[: a.limit]]
    else:
        res = entries[: a.limit]

    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    q = " ".join(terms) or "ALL"
    print(f"# autoresearch-toolfinder — top {len(res)} of {len(entries)} (query: {q}){staleness()}")
    for i, e in enumerate(res, 1):
        print(f"{i}. {e['name']}  [{e['source']} · {e['category']}]")
        print(f"   {e['url']}")
        if e["desc"]:
            print(f"   {e['desc'][:200]}")
    if not res:
        print("(no matches — try broader keywords, --category to browse, or --list-categories)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
