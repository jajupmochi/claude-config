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
        assert float(lines[0].split("\t")[0]) > 0, "matching round has a positive (idf-weighted) score"

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
            assert float(out_fuzzy.split("\t")[0]) > 0, "fuzzy hit has a positive (idf-weighted) score"

        # 9. graph overlay: a round with NO query keyword is pulled in when LINKED to a keyword hit
        with tempfile.TemporaryDirectory() as root3:
            b3 = ["--root", root3, "--project", "p"]
            _run(["record", *b3, "--kind", "note", "--title", "t1", "--ts", "2026-07-10"], stdin="talks about widgets\n")   # 0001 (hit)
            _run(["record", *b3, "--kind", "note", "--title", "t2", "--ts", "2026-07-10"], stdin="totally unrelated prose\n")  # 0002 (linked, no keyword)
            rc, out = _run(["link", *b3, "--from", "1", "--to", "2"])
            assert rc == 0 and out.strip() == "0001 -> 0002"
            # plain recall for 'widgets' -> only round 1
            _, out_plain = _run(["recall", *b3, "--query", "widgets"])
            paths_plain = [ln.split("\t")[1] for ln in out_plain.strip().splitlines() if ln]
            assert len(paths_plain) == 1 and paths_plain[0].endswith("0001-note.md")
            # --graph recall -> round 1 (keyword) AND round 2 (linked in)
            _, out_graph = _run(["recall", *b3, "--query", "widgets", "--graph"])
            paths_graph = [ln.split("\t")[1] for ln in out_graph.strip().splitlines() if ln]
            assert any(p.endswith("0001-note.md") for p in paths_graph)
            assert any(p.endswith("0002-note.md") for p in paths_graph), "linked round pulled in by --graph"

        # 10. IDF weighting: a rare discriminative term must beat common terms stuffed into other docs.
        # Without IDF this is the real "researchgate drowned by load/chrome" miss the recall eval surfaced.
        with tempfile.TemporaryDirectory() as root4:
            b4 = ["--root", root4, "--project", "p"]
            # round 1: the ONLY doc mentioning "researchgate", once; also has the common words once each
            _run(["record", *b4, "--kind", "note", "--title", "t1", "--ts", "2026-07-10"],
                 stdin="researchgate won't load in chrome\n")  # 0001 (the truly relevant one)
            # rounds 2 & 3: NO "researchgate", but the common query words repeated many times
            _run(["record", *b4, "--kind", "note", "--title", "t2", "--ts", "2026-07-10"],
                 stdin="load load load chrome chrome chrome load chrome\n")  # 0002 (common-word heavy)
            _run(["record", *b4, "--kind", "note", "--title", "t3", "--ts", "2026-07-10"],
                 stdin="chrome load chrome load chrome load chrome load\n")  # 0003 (common-word heavy)
            _, out_idf = _run(["recall", *b4, "--query", "researchgate load chrome", "--top", "1"])
            top = [ln for ln in out_idf.strip().splitlines() if ln][0]
            assert top.endswith("0001-note.md"), f"idf must rank the rare-term doc first, got {out_idf!r}"

    print("mem.py: all 10 tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
