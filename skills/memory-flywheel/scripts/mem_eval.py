#!/usr/bin/env python3
# memory-flywheel eval harness · version: 0.1.0
"""Runnable recall evaluation for the memory flywheel (overhaul task 5's eval, design → runnable skeleton).

Given a fixtures JSON (a synthetic corpus + queries with known-relevant round ids), this builds a real
memory store via mem.py, runs recall (exact / --fuzzy / --graph per query), and computes recall@k. It is a
harness: plug REAL sessions + gold labels into the same JSON to measure on live data. The metric code is
deterministic; no model call, no network.

    mem_eval.py --fixtures f.json [--k 5]

Fixtures schema:
{
  "rounds":  [{"kind": "...", "title": "...", "keywords": "a,b", "body": "..."}, ...],   # order = ids 1..N
  "links":   [[1, 3], ...],                                                              # optional graph edges
  "queries": [{"query": "...", "fuzzy": false, "graph": false, "relevant": [1, 3]}, ...] # relevant = round ids
}

Prints per-query recall@k and the mean; also exported as evaluate(fixtures, k) -> {"per_query": [...], "mean": x}.
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("mem", os.path.join(HERE, "mem.py"))
mem = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mem)


class _NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _recall_ids(root, project, q, k):
    """Run mem.recall and return the top-k round ids (ints), capturing stdout."""
    import io
    from contextlib import redirect_stdout
    args = _NS(root=root, project=project, query=q.get("query", ""), top=k,
               fuzzy=bool(q.get("fuzzy")), graph=bool(q.get("graph")))
    buf = io.StringIO()
    with redirect_stdout(buf):
        mem.cmd_recall(args)
    ids = []
    for line in buf.getvalue().strip().splitlines():
        if not line:
            continue
        path = line.split("\t")[-1]
        m = re.match(r"(\d+)-", os.path.basename(path))
        if m:
            ids.append(int(m.group(1)))
    return ids[:k]


def evaluate(fixtures, k=5):
    per_query = []
    with tempfile.TemporaryDirectory() as root:
        proj = "eval"
        base = _NS(root=root, project=proj)
        # 1. record rounds -> ids 1..N (mem assigns sequentially)
        for r in fixtures.get("rounds", []):
            import io
            from contextlib import redirect_stdout
            old = sys.stdin
            sys.stdin = io.StringIO(r.get("body", ""))
            try:
                a = _NS(root=root, project=proj, kind=r.get("kind", "note"),
                        title=r.get("title", ""), keywords=r.get("keywords", ""), ts="2026-01-01")
                with redirect_stdout(io.StringIO()):
                    mem.cmd_record(a)
            finally:
                sys.stdin = old
        # 2. links
        import io
        from contextlib import redirect_stdout
        for a, b in fixtures.get("links", []):
            la = _NS(root=root, project=proj, from_id=str(a), to_id=str(b))
            with redirect_stdout(io.StringIO()):
                mem.cmd_link(la)
        # 3. queries
        for q in fixtures.get("queries", []):
            got = set(_recall_ids(root, proj, q, k))
            rel = set(q.get("relevant", []))
            recall = (len(got & rel) / len(rel)) if rel else 0.0
            per_query.append({"query": q.get("query", ""), "recall_at_k": round(recall, 4),
                              "hit": sorted(got & rel), "missed": sorted(rel - got)})
    mean = round(sum(p["recall_at_k"] for p in per_query) / len(per_query), 4) if per_query else 0.0
    return {"k": k, "per_query": per_query, "mean_recall_at_k": mean}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mem_eval.py")
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args(argv)
    with open(args.fixtures, encoding="utf-8") as f:
        fixtures = json.load(f)
    result = evaluate(fixtures, args.k)
    for p in result["per_query"]:
        print(f"recall@{result['k']}={p['recall_at_k']:.2f}  hit={p['hit']} missed={p['missed']}  | {p['query']}")
    print(f"MEAN recall@{result['k']} = {result['mean_recall_at_k']:.4f} over {len(result['per_query'])} queries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
