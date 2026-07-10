#!/usr/bin/env python3
"""Tests for mem.py (deterministic memory-flywheel core). Run: python3 test_mem.py"""
import importlib.util
import io
import os
import tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("mem", os.path.join(HERE, "mem.py"))
mem = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mem)


def _run(argv, stdin=""):
    import sys
    old = sys.stdin
    sys.stdin = io.StringIO(stdin)
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rc = mem.main(argv)
    finally:
        sys.stdin = old
    return rc, buf.getvalue()


def run():
    with tempfile.TemporaryDirectory() as root:
        base = ["--root", root, "--project", "demo"]

        # 1. record two rounds -> deterministic ids + files exist + verbatim body preserved
        rc, out = _run(["record", *base, "--kind", "Research", "--title", "survey memory SOTA",
                        "--keywords", "memory, sota", "--ts", "2026-07-10"], stdin="raw notes: Zep, MemWalker\n")
        assert rc == 0, "record exit"
        p1 = out.strip()
        assert os.path.basename(p1) == "0001-research.md", f"id/kind slug, got {p1}"
        body = open(p1, encoding="utf-8").read()
        assert "raw notes: Zep, MemWalker" in body, "verbatim body preserved"
        assert "id: 0001" in body and "kind: research" in body and "ts: 2026-07-10" in body

        rc, out = _run(["record", *base, "--kind", "design", "--title", "flywheel schema",
                        "--keywords", "schema", "--ts", "2026-07-10"], stdin="chose coarse->fine\n")
        p2 = out.strip()
        assert os.path.basename(p2) == "0002-design.md", f"seq id increments, got {p2}"

        # 2. INDEX.md is the coarse layer: lists both rounds
        idx = open(os.path.join(root, "demo", "INDEX.md"), encoding="utf-8").read()
        assert "0001" in idx and "0002" in idx and "survey memory SOTA" in idx and "flywheel schema" in idx
        assert idx.count("| 000") == 2, "one table row per round"

        # 3. recall ranks by keyword match count; a term only in round 1 returns round 1 first
        rc, out = _run(["recall", *base, "--query", "zep memwalker"])
        assert rc == 0
        lines = [ln for ln in out.strip().splitlines() if ln]
        assert lines and lines[0].endswith("0001-research.md"), f"recall top = round 1, got {out!r}"
        assert int(lines[0].split("\t")[0]) >= 2, "score counts both terms"

        # 4. recall for a term in neither round -> no rows
        rc, out = _run(["recall", *base, "--query", "nonexistentxyz"])
        assert out.strip() == "", "no match -> empty"

        # 5. recall with empty query -> lists all (score 0), capped by --top
        rc, out = _run(["recall", *base, "--query", "", "--top", "1"])
        assert len(out.strip().splitlines()) == 1, "top=1 caps output"

        # 6. index is idempotent (re-run same content -> same file)
        idx_a = open(os.path.join(root, "demo", "INDEX.md"), encoding="utf-8").read()
        _run(["index", *base])
        idx_b = open(os.path.join(root, "demo", "INDEX.md"), encoding="utf-8").read()
        assert idx_a == idx_b, "index idempotent"

        # 7. a title containing '|' must NOT break the Markdown table (escaped, row stays 4 columns)
        _run(["record", *base, "--kind", "note", "--title", "a | b pipe", "--ts", "2026-07-10"], stdin="x\n")
        idx = open(os.path.join(root, "demo", "INDEX.md"), encoding="utf-8").read()
        row = [ln for ln in idx.splitlines() if ln.startswith("| 0003")][0]
        assert "\\|" in row, "pipe in title is escaped"
        # a well-formed row has exactly 5 '|' (4 columns): leading, 3 separators, trailing — un-escaped ones
        bare_pipes = row.replace("\\|", "")
        assert bare_pipes.count("|") == 5, f"row stays 4 columns, got {bare_pipes.count('|')} pipes: {row!r}"

        # 8. fuzzy recall matches VARIANT forms that exact recall misses
        with tempfile.TemporaryDirectory() as root2:
            b2 = ["--root", root2, "--project", "p"]
            _run(["record", *b2, "--kind", "note", "--title", "t", "--ts", "2026-07-10"], stdin="notes about memories and designs\n")
            # exact: querying 'memory' should NOT match 'memories' (differs after the prefix)
            _, out_exact = _run(["recall", *b2, "--query", "memory"])
            assert out_exact.strip() == "", f"exact recall shouldn't match variant, got {out_exact!r}"
            # fuzzy: 'memory' matches 'memories' via shared 4-char prefix -> a hit
            _, out_fuzzy = _run(["recall", *b2, "--query", "memory", "--fuzzy"])
            assert out_fuzzy.strip() != "", "fuzzy recall should match the variant 'memories'"
            assert int(out_fuzzy.split("\t")[0]) >= 1

    print("mem.py: all 8 tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
