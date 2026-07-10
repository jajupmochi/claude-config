#!/usr/bin/env python3
"""Tests for mem_eval.py (memory-flywheel recall eval harness). Run: python3 test_mem_eval.py"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("mem_eval", os.path.join(HERE, "mem_eval.py"))
me = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(me)


def run():
    fixtures = {
        "rounds": [
            {"kind": "research", "title": "survey", "keywords": "widgets", "body": "notes about widgets"},   # 1
            {"kind": "design", "title": "schema", "keywords": "schema", "body": "the storage schema"},        # 2
            {"kind": "note", "title": "followup", "keywords": "", "body": "unrelated prose no keyword"},        # 3
        ],
        "links": [[1, 3]],
        "queries": [
            {"query": "widgets", "relevant": [1]},                    # exact finds 1 -> recall 1.0
            {"query": "widgets", "graph": True, "relevant": [1, 3]},  # graph pulls in linked 3 -> recall 1.0
            {"query": "widgets", "relevant": [1, 3]},                 # NO graph -> only 1 of 2 -> recall 0.5
            {"query": "absent", "relevant": [2]},                     # no match -> recall 0.0
        ],
    }
    r = me.evaluate(fixtures, k=5)
    pq = r["per_query"]
    assert pq[0]["recall_at_k"] == 1.0, pq[0]
    assert pq[1]["recall_at_k"] == 1.0, f"graph should retrieve linked round: {pq[1]}"
    assert pq[2]["recall_at_k"] == 0.5, f"no-graph misses the linked round: {pq[2]}"
    assert pq[3]["recall_at_k"] == 0.0, pq[3]
    assert r["mean_recall_at_k"] == round((1.0 + 1.0 + 0.5 + 0.0) / 4, 4), r["mean_recall_at_k"]

    # empty fixtures -> graceful zero
    assert me.evaluate({}, k=5)["mean_recall_at_k"] == 0.0

    # the shipped example fixture runs and is internally consistent (graph query beats plain)
    import json
    ex = json.load(open(os.path.join(HERE, "eval-fixtures.example.json"), encoding="utf-8"))
    rex = me.evaluate(ex, k=5)
    assert len(rex["per_query"]) == 3 and rex["per_query"][1]["recall_at_k"] == 1.0

    print("mem_eval.py: all 3 tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
